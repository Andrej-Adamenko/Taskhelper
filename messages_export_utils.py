import logging
import time

import config_utils
import db_utils
import user_utils
import core_api
from config_utils import DISCUSSION_CHAT_DATA, EXPORTED_CHATS

_EXPORT_BATCH_SIZE = 50


def export_messages(chat_id: int, last_message_id: int) -> list:
	return core_api.get_messages(chat_id, last_message_id, _EXPORT_BATCH_SIZE)


def export_chat_comments(discussion_chat_id: int) -> bool:
	last_msg_id = db_utils.get_last_message_id(discussion_chat_id)
	if not last_msg_id:
		logging.info(f"Can't find last message in {discussion_chat_id}, export skipped")
		return False

	messages = export_messages(discussion_chat_id, last_msg_id)
	if not messages:
		logging.info(f"Can't export messages in {discussion_chat_id}, export skipped")
		return False

	for message in messages:
		if message.empty and message.id <= last_msg_id:
			db_utils.delete_comment_message(message.id, discussion_chat_id)
			continue
		if message.reply_to_message is None:
			continue

		discussion_message_id = message.id

		reply_to_message_id = message.reply_to_message.id
		if message.sender_chat:
			sender_id = message.sender_chat.id
		else:
			sender_id = message.from_user.id

		db_utils.insert_comment_message(reply_to_message_id, discussion_message_id, discussion_chat_id, sender_id)
		logging.info(f"Exported comment [{reply_to_message_id}, {discussion_message_id}, {discussion_chat_id}]")
	return True


def export_comments_from_discussion_chats():
	discussion_chat_ids = list(DISCUSSION_CHAT_DATA.values())
	discussion_chat_ids = [chat_id for chat_id in discussion_chat_ids if chat_id]
	for chat_id in discussion_chat_ids:
		if chat_id in EXPORTED_CHATS:
			continue

		logging.info(f"Exporting comments from {chat_id}")
		export_chat_comments(chat_id)
		EXPORTED_CHATS.append(chat_id)
		config_utils.update_config({"EXPORTED_CHATS": EXPORTED_CHATS})
		logging.info(f"Successfully exported comments from {chat_id}")


def export_main_channel_messages(main_channel_id: int) -> bool:
	last_msg_id = db_utils.get_last_message_id(main_channel_id)
	if last_msg_id is None:
		logging.info(f"Can't find last message in {main_channel_id}, export skipped")
		return False

	messages = export_messages(main_channel_id, last_msg_id)
	if not messages:
		logging.info(f"Can't export messages in {main_channel_id}, export skipped")
		return False

	for message in messages:
		if message.empty or message.service:
			continue
		user_id = None
		if message.author_signature:
			user_id = user_utils.find_user_by_signature(message.author_signature)

		db_utils.insert_main_channel_message(main_channel_id, message.id, user_id)
		logging.info(f"Exported main message [{main_channel_id}, {message.id}, {user_id}]")
	return True


def export_main_channels():
	main_channel_ids = db_utils.get_main_channel_ids()
	for channel_id in main_channel_ids:
		if channel_id in EXPORTED_CHATS:
			continue
		logging.info(f"Exporting messages from {channel_id}")
		if export_main_channel_messages(channel_id):
			EXPORTED_CHATS.append(channel_id)
			config_utils.update_config({"EXPORTED_CHATS": EXPORTED_CHATS})
			logging.info(f"Successfully exported messages from {channel_id}")


def start_exporting():
	export_comments_from_discussion_chats()
	export_main_channels()
