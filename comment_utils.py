import logging

import telebot
import time
from telebot.apihelper import ApiTelegramException

import forwarding_utils
import db_utils
import interval_updating_utils
import utils

from config_utils import DISCUSSION_CHAT_DATA, HASHTAGS
from hashtag_data import HashtagData


class CommentDispatcher:
	__NEXT_ACTION_COMMENT_PREFIX = ":"
	__NEXT_ACTION_TEXT_PREFIX = "::"

	def save_comment(self, bot: telebot.TeleBot, msg_data: telebot.types.Message):
		discussion_message_id = msg_data.message_id
		discussion_chat_id = msg_data.chat.id

		reply_to_message_id = msg_data.reply_to_message.message_id

		sender_id = msg_data.from_user.id
		db_utils.insert_comment_message(reply_to_message_id, discussion_message_id, discussion_chat_id, sender_id)

		main_channel_id = utils.get_key_by_value(DISCUSSION_CHAT_DATA, discussion_chat_id)
		if main_channel_id is None:
			return

		main_channel_id = int(main_channel_id)
		top_discussion_message_id = db_utils.get_comment_top_parent(discussion_message_id, discussion_chat_id)
		if top_discussion_message_id == discussion_message_id:
			return
		main_message_id = db_utils.get_main_from_discussion_message(top_discussion_message_id, main_channel_id)

		if main_message_id:
			msg_text = msg_data.text or msg_data.caption or ""
			if msg_text.startswith(self.__NEXT_ACTION_COMMENT_PREFIX):
				next_action_text = msg_text[len(self.__NEXT_ACTION_COMMENT_PREFIX):]
				self.update_next_action(bot, main_message_id, main_channel_id, next_action_text, msg_data)
			else:
				self.apply_hashtags(bot, msg_data, main_message_id, main_channel_id)
			interval_updating_utils.update_older_message(bot, main_channel_id, main_message_id)

			self.update_user_last_interaction(main_message_id, main_channel_id, msg_data)
			db_utils.set_ticket_update_time(main_message_id, main_channel_id, int(time.time()))

	def delete_comment(self, bot: telebot.TeleBot, main_channel_id: int, discussion_chat_id: int, discussion_message_id: int):
		reply_comment = db_utils.get_reply_comment_message(discussion_message_id, discussion_chat_id)

		if not reply_comment:
			db_utils.insert_comment_deleted_message(discussion_message_id, discussion_chat_id)
			logging.info("Insert deleted message to db as deleted")
			return

		db_utils.delete_comment_message(discussion_message_id, discussion_chat_id)
		main_message_id = db_utils.get_main_from_discussion_message(reply_comment, main_channel_id)
		post_data = None

		if main_message_id:
			try:
				post_data = utils.get_main_message_content_by_id(bot, main_channel_id, main_message_id)
			except ApiTelegramException as E:
				logging.error(f"Error during getting main message - {E}")

		if post_data:
			hashtag_data = HashtagData(post_data, main_channel_id)
			keyboard = forwarding_utils.generate_control_buttons(hashtag_data, post_data)
			utils.edit_message_keyboard(bot, post_data, keyboard)
			forwarding_utils.forward_to_subchannel(bot, post_data, hashtag_data)

		logging.info(f"Delete comment {discussion_message_id} for message {main_message_id}")

	@staticmethod
	def apply_hashtags(bot: telebot.TeleBot, msg_data: telebot.types.Message, main_message_id: int, main_channel_id: int,
					   main_message_data:telebot.types.Message = None):
		text, entities = utils.get_post_content(msg_data)
		comment_hashtags = [text[e.offset + 1:e.offset + e.length] for e in entities if e.type == "hashtag"]

		opened_hashtag = HASHTAGS["OPENED"]
		closed_hashtag = HASHTAGS["CLOSED"]
		scheduled_hashtag = HASHTAGS["SCHEDULED"]
		user_tags = db_utils.get_channel_user_tags(main_channel_id)
		service_hashtags = [opened_hashtag, closed_hashtag, scheduled_hashtag] + user_tags

		is_service_hashtag_exists = False
		for hashtag in comment_hashtags:
			if hashtag in service_hashtags:
				is_service_hashtag_exists = True
				break

		if not is_service_hashtag_exists and not main_message_data:
			return

		if not main_message_data:
			main_message_data = utils.get_message_content_by_id(bot, main_channel_id, main_message_id)
			if not main_message_data:
				return

		main_message_data.chat.id = main_channel_id
		main_message_data.message_id = main_message_id
		hashtag_data = HashtagData(main_message_data, main_channel_id)

		if is_service_hashtag_exists:
			if opened_hashtag in comment_hashtags or closed_hashtag in comment_hashtags:
				hashtag_data.set_status_tag(opened_hashtag in comment_hashtags)
			for hashtag in comment_hashtags:
				if hashtag in user_tags:
					hashtag_data.add_user(hashtag)
			if scheduled_hashtag in comment_hashtags:
				for i, entity in enumerate(entities):
					hashtag_data.update_scheduled_tag_entity_length(text, entities, i)

				for entity in entities:
					if entity.type != "hashtag":
						continue

					tag = hashtag_data.get_tag_from_entity(entity, text)
					if not hashtag_data.check_scheduled_tag(tag, scheduled_hashtag):
						continue

					entity_text = hashtag_data.get_tag_from_entity(entity, text)
					tag_parts = entity_text.split(" ")
					if len(tag_parts) < 2:
						continue

					hashtag_data.set_scheduled_tag(hashtag_data.extract_scheduled_tag_from_text(text, entity)[len(scheduled_hashtag) + 1:])

		hashtag_data.ignore_comments = True
		forwarding_utils.update_message_and_forward_to_subchannels(bot, hashtag_data)

	def update_next_action(self, bot: telebot.TeleBot, main_message_id: int, main_channel_id: int, next_action: str,
						   comment_msg_data: telebot.types.Message):
		try:
			post_data = utils.get_main_message_content_by_id(bot, main_channel_id, main_message_id)
		except ApiTelegramException:
			return

		text, entities = utils.get_post_content(post_data)
		for i in range(len(entities)):
			HashtagData.update_scheduled_tag_entity_length(text, entities, i)

		hashtag_data = HashtagData(post_data, main_channel_id)
		if self.__NEXT_ACTION_TEXT_PREFIX in text:
			prefix_position = text.find(self.__NEXT_ACTION_TEXT_PREFIX)
			if hashtag_data.is_last_line_contains_only_hashtags():
				last_line_start = text.rfind("\n")
				is_entity_in_next_action = lambda e: (e.offset > prefix_position) and (
							e.offset + e.length <= last_line_start)

				entities = [e for e in entities if not is_entity_in_next_action(e)]
				entities_to_update = [e for e in entities if e.offset > prefix_position]

				removed_length = last_line_start - prefix_position
				utils.offset_entities(entities_to_update, -removed_length)
				text = text[:prefix_position] + text[last_line_start:]
			else:
				is_entity_remains = lambda e: e.offset > prefix_position
				entities = [e for e in entities if is_entity_remains(e)]

				text = text[:prefix_position]

		next_action_with_prefix = self.__NEXT_ACTION_TEXT_PREFIX + next_action
		if hashtag_data.is_last_line_contains_only_hashtags():
			last_line_start = text.rfind("\n")
			entities_to_update = [e for e in entities if e.offset > last_line_start]
			utils.offset_entities(entities_to_update, len(next_action_with_prefix))
			text = text[:last_line_start] + next_action_with_prefix + text[last_line_start:]
		else:
			text += next_action_with_prefix
		utils.set_post_content(post_data, text, entities)

		hashtag_data = HashtagData(post_data, main_channel_id)
		post_data.reply_markup = forwarding_utils.generate_control_buttons(hashtag_data, post_data)

		self.apply_hashtags(bot, comment_msg_data, main_message_id, main_channel_id, post_data)

		# for compatibility with older versions
		db_utils.insert_or_update_current_next_action(main_message_id, main_channel_id, next_action)
		db_utils.update_previous_next_action(main_message_id, main_channel_id, next_action_with_prefix)

	def add_next_action_comment(self, bot: telebot.TeleBot, post_data: telebot.types.Message):
		main_channel_id = post_data.chat.id
		main_message_id = post_data.message_id

		text, entities = utils.get_post_content(post_data)
		stored_next_action = db_utils.get_next_action_text(main_message_id, main_channel_id)

		if self.__NEXT_ACTION_TEXT_PREFIX not in text:
			if stored_next_action:
				db_utils.insert_or_update_current_next_action(main_message_id, main_channel_id, "")
			return

		hashtag_data = HashtagData(post_data, main_channel_id)

		next_action_index = text.find(self.__NEXT_ACTION_TEXT_PREFIX)
		if hashtag_data.is_last_line_contains_only_hashtags():
			last_line_start = text.rfind("\n")
			current_next_action = text[next_action_index + len(self.__NEXT_ACTION_TEXT_PREFIX):last_line_start]
		else:
			current_next_action = text[next_action_index + len(self.__NEXT_ACTION_TEXT_PREFIX):]

		if not current_next_action:
			return

		if stored_next_action != current_next_action:
			utils.add_comment_to_ticket(bot, post_data, f"{self.__NEXT_ACTION_COMMENT_PREFIX}{current_next_action}")
			db_utils.insert_or_update_current_next_action(main_message_id, main_channel_id, current_next_action)

	@staticmethod
	def update_user_last_interaction(main_message_id: int, main_channel_id: int, msg_data: telebot.types.Message):
		user_tags = db_utils.get_tags_from_user_id(msg_data.from_user.id)
		if not user_tags and msg_data.from_user.username:
			user_tags = db_utils.get_tags_from_user_id(msg_data.from_user.username)

		if not user_tags:
			return

		for user_tag in user_tags:
			highest_priority = db_utils.get_user_highest_priority(main_channel_id, user_tag)
			_, priority, _ = db_utils.get_ticket_data(main_message_id, main_channel_id)
			if priority == highest_priority:
				db_utils.insert_or_update_last_user_interaction(main_channel_id, user_tag, int(time.time()))
				logging.info(f"Updated {msg_data.from_user.id, user_tag} user last interaction.")


comment_dispatcher = CommentDispatcher()