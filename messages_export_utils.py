import time

from pyrogram import Client

import config_utils
import db_utils
import utils
from config_utils import DISCUSSION_CHAT_DATA, EXPORTED_DISCUSSION_CHATS

_EXPORT_BATCH_SIZE = 200


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


def export_chat_comments(app, discussion_chat_id):
	last_msg_id = db_utils.get_last_message_id(discussion_chat_id)
	if last_msg_id is None:
		return

	messages = export_messages(app, discussion_chat_id, last_msg_id)
	for message in messages:
		if message.reply_to_message is None:
			continue

		main_channel_id = utils.get_key_by_value(DISCUSSION_CHAT_DATA, discussion_chat_id)
		if main_channel_id is None:
			return

		main_channel_id = int(main_channel_id)
		discussion_message_id = message.id
		main_message_id = message.reply_to_message.forward_from_message_id
		if message.sender_chat:
			sender_id = message.sender_chat.id
		else:
			sender_id = message.from_user.id

		db_utils.insert_comment_message(main_message_id, main_channel_id, discussion_message_id, discussion_chat_id, sender_id)


def export_comments_from_discussion_chats(app):
	discussion_chat_ids = list(DISCUSSION_CHAT_DATA.values())
	discussion_chat_ids = [chat_id for chat_id in discussion_chat_ids if chat_id]
	for chat_id in discussion_chat_ids:
		if chat_id in EXPORTED_DISCUSSION_CHATS:
			continue
		export_chat_comments(app, chat_id)
		EXPORTED_DISCUSSION_CHATS.append(chat_id)
		config_utils.update_config({"EXPORTED_DISCUSSION_CHATS": EXPORTED_DISCUSSION_CHATS})
