import logging

import telebot
import time
from telebot.apihelper import ApiTelegramException

import daily_reminder
import db_utils
import interval_updating_utils
import utils
import forwarding_utils
import hashtag_utils
from config_utils import DISCUSSION_CHAT_DATA
from hashtag_data import HashtagData

_NEXT_ACTION_COMMENT_PREFIX = ":"
_NEXT_ACTION_TEXT_PREFIX = "::"


def save_comment(bot: telebot.TeleBot, msg_data: telebot.types.Message):
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
		if msg_text.startswith(_NEXT_ACTION_COMMENT_PREFIX):
			next_action_text = msg_text[len(_NEXT_ACTION_COMMENT_PREFIX):]
			update_next_action(bot, main_message_id, main_channel_id, next_action_text)
		interval_updating_utils.update_older_message(bot, main_channel_id, main_message_id)

		daily_reminder.update_user_last_interaction(main_message_id, main_channel_id, msg_data)
		db_utils.set_ticket_update_time(main_message_id, main_channel_id, int(time.time()))


def update_next_action(bot: telebot.TeleBot, main_message_id: int, main_channel_id: int, next_action: str):
	try:
		post_data = utils.get_main_message_content_by_id(bot, main_channel_id, main_message_id)
	except ApiTelegramException:
		return

	text, entities = utils.get_post_content(post_data)
	for i in range(len(entities)):
		HashtagData.update_scheduled_tag_entity_length(text, entities, i)

	hashtag_data = HashtagData(post_data, main_channel_id)
	if _NEXT_ACTION_TEXT_PREFIX in text:
		prefix_position = text.find(_NEXT_ACTION_TEXT_PREFIX)
		if hashtag_data.is_last_line_contains_only_hashtags():
			last_line_start = text.rfind("\n")
			is_entity_in_next_action = lambda e: (e.offset > prefix_position) and (e.offset + e.length <= last_line_start)

			entities = [e for e in entities if not is_entity_in_next_action(e)]
			entities_to_update = [e for e in entities if e.offset > prefix_position]

			removed_length = last_line_start - prefix_position
			utils.offset_entities(entities_to_update, -removed_length)
			text = text[:prefix_position] + text[last_line_start:]
		else:
			is_entity_remains = lambda e: e.offset > prefix_position
			entities = [e for e in entities if is_entity_remains(e)]

			text = text[:prefix_position]

	next_action_with_prefix = _NEXT_ACTION_TEXT_PREFIX + next_action
	if hashtag_data.is_last_line_contains_only_hashtags():
		last_line_start = text.rfind("\n")
		entities_to_update = [e for e in entities if e.offset > last_line_start]
		utils.offset_entities(entities_to_update, len(next_action_with_prefix))
		text = text[:last_line_start] + next_action_with_prefix + text[last_line_start:]
	else:
		text += next_action_with_prefix
	utils.set_post_content(post_data, text, entities)

	hashtag_data = HashtagData(post_data, main_channel_id)
	keyboard_markup = forwarding_utils.generate_control_buttons(hashtag_data, post_data)

	utils.edit_message_content(bot, post_data, chat_id=main_channel_id,
	                           message_id=main_message_id, reply_markup=keyboard_markup)

	# for compatibility with older versions
	db_utils.insert_or_update_current_next_action(main_message_id, main_channel_id, next_action)
	db_utils.update_previous_next_action(main_message_id, main_channel_id, next_action_with_prefix)


def add_next_action_comment(bot: telebot.TeleBot, post_data: telebot.types.Message):
	main_channel_id = post_data.chat.id
	main_message_id = post_data.message_id

	text, entities = utils.get_post_content(post_data)
	stored_next_action = db_utils.get_next_action_text(main_message_id, main_channel_id)

	if _NEXT_ACTION_TEXT_PREFIX not in text:
		if stored_next_action:
			db_utils.insert_or_update_current_next_action(main_message_id, main_channel_id, "")
		return

	hashtag_data = HashtagData(post_data, main_channel_id)

	next_action_index = text.find(_NEXT_ACTION_TEXT_PREFIX)
	if hashtag_data.is_last_line_contains_only_hashtags():
		last_line_start = text.rfind("\n")
		current_next_action = text[next_action_index + len(_NEXT_ACTION_TEXT_PREFIX):last_line_start]
	else:
		current_next_action = text[next_action_index + len(_NEXT_ACTION_TEXT_PREFIX):]

	if not current_next_action:
		return

	if stored_next_action != current_next_action:
		utils.add_comment_to_ticket(bot, post_data, f"{_NEXT_ACTION_COMMENT_PREFIX}{current_next_action}")
		db_utils.insert_or_update_current_next_action(main_message_id, main_channel_id, current_next_action)
