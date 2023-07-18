import logging
import threading

import telebot

import daily_reminder
import db_utils
import interval_updating_utils
import utils
import forwarding_utils
from config_utils import DISCUSSION_CHAT_DATA
from hashtag_data import HashtagData

_NEXT_ACTION_COMMENT_PREFIX = ":"
_NEXT_ACTION_TEXT_PREFIX = "::"

_COMMENT_LOCK = threading.RLock()


def comment_thread_lock(func):
	def inner_function(*args, **kwargs):
		try:
			_COMMENT_LOCK.acquire(True)
			return func(*args, **kwargs)
		except Exception as E:
			logging.exception(f"Error in {func.__name__} comment function, error: {E}")
		finally:
			_COMMENT_LOCK.release()
	return inner_function


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

	if msg_data.text.startswith(_NEXT_ACTION_COMMENT_PREFIX):
		next_action_text = msg_data.text[len(_NEXT_ACTION_COMMENT_PREFIX):]
		db_utils.insert_or_update_current_next_action(main_message_id, main_channel_id, next_action_text)

	if main_message_id:
		interval_updating_utils.update_older_message(bot, main_channel_id, main_message_id)

	daily_reminder.update_user_last_interaction(main_message_id, main_channel_id, msg_data)
	daily_reminder.set_ticket_update_time(main_message_id, main_channel_id)


@comment_thread_lock
def update_comment(bot: telebot.TeleBot, post_data: telebot.types.Message, hashtag_data: HashtagData):
	main_channel_id = post_data.chat.id
	main_message_id = post_data.message_id

	text, entities = utils.get_post_content(post_data)

	next_action = db_utils.get_next_action_text(main_message_id, main_channel_id)

	if next_action:
		previous_text, current_comment_text = next_action
		current_comment_with_prefix = _NEXT_ACTION_TEXT_PREFIX + current_comment_text
		if text.endswith(current_comment_with_prefix):
			return

		if previous_text and previous_text in text:
			previous_text_index = text.rfind(previous_text)
			text = text[:previous_text_index] + text[previous_text_index + len(previous_text):]  # remove previous comment

		text += current_comment_with_prefix

		keyboard_markup = forwarding_utils.generate_control_buttons(hashtag_data, post_data)

		utils.set_post_content(post_data, text, entities)
		utils.edit_message_content(bot, post_data, reply_markup=keyboard_markup)
		db_utils.update_previous_next_action(main_message_id, main_channel_id, current_comment_with_prefix)
