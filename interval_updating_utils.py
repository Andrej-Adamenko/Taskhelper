import logging
import time

from telebot.apihelper import ApiTelegramException

import utils
import db_utils
import forwarding_utils
import post_link_utils
import threading

from config_utils import DISCUSSION_CHAT_DATA, CHANNEL_IDS, UPDATE_INTERVAL, INTERVAL_UPDATE_START_DELAY, \
	DELAY_AFTER_ONE_SCAN

UPDATE_STARTED_MSG_TEXT = "Started updating older posts. When update is complete this message will be deleted."


def update_older_message(bot, main_channel_id, current_msg_id):
	forwarded_message = forwarding_utils.get_message_content_by_id(bot, main_channel_id, current_msg_id)
	if forwarded_message is None:
		return

	if utils.get_forwarded_from_id(forwarded_message) != main_channel_id:
		return

	main_channel_message_id = forwarded_message.forward_from_message_id

	forwarded_message.message_id = main_channel_message_id
	forwarded_message.chat = forwarded_message.forward_from_chat

	updated_message = post_link_utils.update_post_link(bot, forwarded_message)

	if not updated_message:
		updated_message = forwarded_message

	forwarding_utils.forward_and_add_inline_keyboard(bot, updated_message)

	return main_channel_message_id


def store_discussion_message(bot, main_channel_id, current_msg_id, discussion_chat_id):
	forwarded_message = forwarding_utils.get_message_content_by_id(bot, discussion_chat_id, current_msg_id)
	if forwarded_message is None:
		return

	if utils.get_forwarded_from_id(forwarded_message) != main_channel_id:
		return

	main_channel_message_id = forwarded_message.forward_from_message_id
	if discussion_chat_id:
		db_utils.insert_or_update_discussion_message(main_channel_message_id, main_channel_id, current_msg_id)

	return main_channel_message_id


def start_updating_older_messages(bot, main_channel_id, message_id):
	main_channel_id_str = str(main_channel_id)

	bot.edit_message_text(chat_id=main_channel_id, message_id=message_id, text=UPDATE_STARTED_MSG_TEXT)

	if main_channel_id_str in DISCUSSION_CHAT_DATA:
		discussion_chat_id = DISCUSSION_CHAT_DATA[main_channel_id_str]
		check_all_messages(bot, main_channel_id, discussion_chat_id)
	else:
		check_all_messages(bot, main_channel_id)


def start_interval_updating(bot):
	update_thread = threading.Thread(target=interval_update_thread, args=(bot,))
	update_thread.start()


def interval_update_thread(bot):
	time.sleep(INTERVAL_UPDATE_START_DELAY)
	while 1:
		for main_channel_id in CHANNEL_IDS:
			main_channel_id_str = str(main_channel_id)

			discussion_chat_id = None
			if main_channel_id_str in DISCUSSION_CHAT_DATA:
				discussion_chat_id = DISCUSSION_CHAT_DATA[main_channel_id_str]

			check_all_messages(bot, main_channel_id, discussion_chat_id)

		logging.info("Interval check complete")
		time.sleep(UPDATE_INTERVAL * 60)


def get_last_message(bot, channel_id):
	last_message_id = db_utils.get_last_message_id(channel_id)
	if last_message_id is None:
		msg_text = "(This is service message for obtaining last message id, bot will delete it in a moment)"
		last_message = bot.send_message(chat_id=channel_id, text=msg_text)
		last_message_id = last_message.message_id - 1
		bot.delete_message(chat_id=channel_id, message_id=last_message_id)
		db_utils.insert_or_update_last_msg_id(last_message_id, channel_id)

	return last_message_id


def check_all_messages(bot, main_channel_id, discussion_chat_id=None):
	if discussion_chat_id:
		discussion_chat = bot.get_chat(discussion_chat_id)
		current_msg_id = discussion_chat.pinned_message.message_id
	else:
		current_msg_id = get_last_message(bot, main_channel_id)

	last_updated_message_id = current_msg_id

	while current_msg_id > 0:
		time.sleep(DELAY_AFTER_ONE_SCAN)
		try:
			if discussion_chat_id:
				main_channel_message_id = store_discussion_message(bot, main_channel_id, current_msg_id, discussion_chat_id)
				if main_channel_message_id:
					update_older_message(bot, main_channel_id, main_channel_message_id)
					last_updated_message_id = main_channel_message_id
			else:
				update_older_message(bot, main_channel_id, current_msg_id)
		except ApiTelegramException as E:
			if E.error_code == 429:
				logging.warning(f"Too many requests - {E}")
				time.sleep(20)
				continue
			logging.error(f"Error during updating older messages - {E}")
		except Exception as E:
			logging.error(f"Updating older messages stopped because of exception - {E}")
			return

		current_msg_id -= 1
		if discussion_chat_id and current_msg_id <= 0:
			current_msg_id = last_updated_message_id
			discussion_chat_id = None
			logging.info(f"Checked all messages in discussion chat, last updated message id: {last_updated_message_id}")

	logging.info(f"Checked all messages in main channel - id: {main_channel_id}")

