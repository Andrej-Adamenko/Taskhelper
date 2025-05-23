import logging
import time

import telebot
from telebot.apihelper import ApiTelegramException

import comment_utils
import config_utils
import utils
import db_utils
import forwarding_utils
import post_link_utils
import threading

from config_utils import DISCUSSION_CHAT_DATA, DELAY_AFTER_ONE_SCAN

_INTERVAL_UPDATING_THREAD: threading.Thread = None
_UPDATE_STATUS: bool = False


def update_older_message(bot: telebot.TeleBot, main_channel_id: int, main_message_id: int):
	if not db_utils.is_main_message_exists(main_channel_id, main_message_id):
		logging.info(f"Ticket update for {main_channel_id, main_message_id} was skipped because it's not in db")
		return

	try:
		forwarded_message = utils.get_main_message_content_by_id(bot, main_channel_id, main_message_id)
	except ApiTelegramException:
		forwarding_utils.delete_main_message(bot, main_channel_id, main_message_id)
		return

	if forwarded_message is None:
		return

	if utils.get_forwarded_from_id(forwarded_message) != main_channel_id:
		return

	main_channel_message_id = forwarded_message.forward_from_message_id

	forwarded_message.message_id = main_channel_message_id
	forwarded_message.chat = forwarded_message.forward_from_chat
	if not utils.check_content_type(bot, forwarded_message):
		return

	updated_message = post_link_utils.update_post_link(bot, forwarded_message)

	if not updated_message:
		updated_message = forwarded_message

	forwarding_utils.forward_and_add_inline_keyboard(bot, updated_message)

	return main_channel_message_id


def store_discussion_message(bot: telebot.TeleBot, main_channel_id: int, current_msg_id: int, discussion_chat_id: int):
	# retrieve message from discussion chat, get message_id of the message in main channel and save it to db

	try:
		forwarded_message = utils.get_main_message_content_by_id(bot, discussion_chat_id, current_msg_id)
	except ApiTelegramException:
		comment_utils.comment_dispatcher.delete_comment(bot, main_channel_id, discussion_chat_id, current_msg_id)
		return

	if forwarded_message is None:
		return

	forwarded_from_id = utils.get_forwarded_from_id(forwarded_message)
	if forwarded_from_id != main_channel_id:
		return

	main_channel_message_id = forwarded_message.forward_from_message_id
	if discussion_chat_id:
		db_utils.insert_or_update_discussion_message(main_channel_message_id, main_channel_id, current_msg_id)

	return main_channel_message_id


def start_interval_updating(bot: telebot.TeleBot, start_delay: int = 0):
	global _UPDATE_STATUS, _INTERVAL_UPDATING_THREAD

	if _UPDATE_STATUS:
		_UPDATE_STATUS = False
		_INTERVAL_UPDATING_THREAD.join()

	_UPDATE_STATUS = True
	_INTERVAL_UPDATING_THREAD = threading.Thread(target=interval_update_thread, args=(bot, start_delay,))
	_INTERVAL_UPDATING_THREAD.start()


def interval_update_thread(bot: telebot.TeleBot, start_delay: int = 0):
	start_time = time.time()
	last_update_time = 0
	while _UPDATE_STATUS:
		time.sleep(1)
		if (time.time() - start_time) < start_delay:
			continue
		if (time.time() - last_update_time) < (config_utils.UPDATE_INTERVAL * 60):
			continue

		update_in_progress_channel = db_utils.get_unfinished_update_channel()
		if update_in_progress_channel:
			main_channel_id, current_message_id = update_in_progress_channel
			check_main_messages(bot, main_channel_id, current_message_id)

		finished_channels = db_utils.get_finished_update_channels()

		main_channel_ids = db_utils.get_main_channel_ids()
		for main_channel_id in main_channel_ids:
			if main_channel_id in finished_channels:
				continue
			check_main_messages(bot, main_channel_id)

			main_channel_id_str = str(main_channel_id)
			discussion_chat_id = None
			if main_channel_id_str in DISCUSSION_CHAT_DATA:
				discussion_chat_id = DISCUSSION_CHAT_DATA[main_channel_id_str]

			check_discussion_messages(bot, main_channel_id, discussion_chat_id)

		logging.info(f"Interval check is finished")
		db_utils.clear_updates_in_progress()
		if _UPDATE_STATUS and config_utils.HASHTAGS_BEFORE_UPDATE:
			config_utils.HASHTAGS_BEFORE_UPDATE = None
			config_utils.update_config({"HASHTAGS_BEFORE_UPDATE": None})
		last_update_time = time.time()


def check_main_messages(bot: telebot.TeleBot, main_channel_id: int, start_from_message: int = None):
	start_msg_id = start_from_message or utils.get_last_message(bot, main_channel_id)
	if start_msg_id is None:
		return

	for current_msg_id in range(start_msg_id, 0, -1):
		time.sleep(DELAY_AFTER_ONE_SCAN)
		try:
			if not _UPDATE_STATUS:
				raise Exception("Interval update stop requested")

			update_older_message(bot, main_channel_id, current_msg_id)
			db_utils.insert_or_update_channel_update_progress(main_channel_id, current_msg_id)
		except ApiTelegramException as E:
			if E.error_code == 429:
				logging.warning(f"Too many requests - {E}")
				time.sleep(20)
				continue
			logging.error(f"Telegram error during main channel check ({main_channel_id, current_msg_id}) - {E}")
		except Exception as E:
			logging.error(f"Main channel check stopped ({main_channel_id, current_msg_id}) - {E}")
			return

	db_utils.insert_or_update_channel_update_progress(main_channel_id, 0)
	logging.info(f"Main channel check completed in {main_channel_id}")


def check_discussion_messages(bot: telebot.TeleBot, main_channel_id: int, discussion_chat_id: int = None):
	start_msg_id = utils.get_last_message(bot, discussion_chat_id)
	if start_msg_id is None:
		return

	logging.info(f"Starting to check discussion channel: {discussion_chat_id}")
	deleted_messages = db_utils.get_comment_deleted_message_ids(discussion_chat_id, list(range(1, start_msg_id + 1)))

	for current_msg_id in range(start_msg_id, 0, -1):
		if current_msg_id in deleted_messages:
			logging.info(f"Check comment {current_msg_id} in chat {discussion_chat_id} was skipped because it's in db as deleted")
			continue

		time.sleep(DELAY_AFTER_ONE_SCAN)
		try:
			if not _UPDATE_STATUS:
				raise Exception("Interval update stop requested")
			store_discussion_message(bot, main_channel_id, current_msg_id, discussion_chat_id)
		except ApiTelegramException as E:
			if E.error_code == 429:
				logging.warning(f"Too many requests - {E}")
				time.sleep(20)
				continue
			logging.error(f"Telegram error during discussion channel check ({discussion_chat_id, current_msg_id}) - {E}")
		except Exception as E:
			logging.error(f"Discussion channel check stopped ({discussion_chat_id, current_msg_id}) - {E}")
			return

	logging.info(f"Discussion channel check completed in {discussion_chat_id}")

