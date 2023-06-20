import logging
import time

from pyrogram import Client

import config_utils
import db_utils
import user_utils
from config_utils import DISCUSSION_CHAT_DATA, EXPORTED_CHATS

_EXPORT_BATCH_SIZE = 50


def init_pyrogram(api_id: int, api_hash: str, bot_token: str):
	app = Client(
		"pyrogram_bot",
		api_id=api_id, api_hash=api_hash,
		bot_token=bot_token
	)

	app.start()

	return app


def export_messages(app: Client, chat_id: int, last_message_id: int):
	message_ids = list(range(1, last_message_id + 1))
	read_counter = 0
	exported_messages = []

	while read_counter < len(message_ids):
		exported_messages += app.get_messages(chat_id, message_ids[read_counter:read_counter + _EXPORT_BATCH_SIZE])
		read_counter += _EXPORT_BATCH_SIZE
		time.sleep(10)

	return exported_messages


def export_chat_comments(app: Client, discussion_chat_id: int):
	last_msg_id = db_utils.get_last_message_id(discussion_chat_id)
	if last_msg_id is None:
		logging.info(f"Can't find last message in {discussion_chat_id}, export skipped")
		return

	messages = export_messages(app, discussion_chat_id, last_msg_id)
	for message in messages:
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


def export_comments_from_discussion_chats(app: Client):
	discussion_chat_ids = list(DISCUSSION_CHAT_DATA.values())
	discussion_chat_ids = [chat_id for chat_id in discussion_chat_ids if chat_id]
	for chat_id in discussion_chat_ids:
		if chat_id in EXPORTED_CHATS:
			continue

		logging.info(f"Exporting comments from {chat_id}")
		export_chat_comments(app, chat_id)
		EXPORTED_CHATS.append(chat_id)
		config_utils.update_config({"EXPORTED_CHATS": EXPORTED_CHATS})
		logging.info(f"Successfully exported comments from {chat_id}")


def export_main_channel_messages(app: Client, main_channel_id: int):
	last_msg_id = db_utils.get_last_message_id(main_channel_id)
	if last_msg_id is None:
		logging.info(f"Can't find last message in {main_channel_id}, export skipped")
		return

	messages = export_messages(app, main_channel_id, last_msg_id)
	for message in messages:
		if message.empty:
			continue
		user_id = None
		if message.author_signature:
			user_id = user_utils.find_user_by_signature(message.author_signature, main_channel_id)

		db_utils.insert_main_channel_message(main_channel_id, message.id, user_id)
		logging.info(f"Exported main message [{main_channel_id}, {message.id}, {user_id}]")


def export_main_channels(app: Client):
	main_channel_ids = db_utils.get_main_channel_ids()
	for channel_id in main_channel_ids:
		if channel_id in EXPORTED_CHATS:
			continue
		logging.info(f"Exporting messages from {channel_id}")
		export_main_channel_messages(app, channel_id)
		EXPORTED_CHATS.append(channel_id)
		config_utils.update_config({"EXPORTED_CHATS": EXPORTED_CHATS})
		logging.info(f"Successfully exported messages from {channel_id}")

