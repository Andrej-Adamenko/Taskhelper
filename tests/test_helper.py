from typing import List, Union

import pyrogram.types
from telebot.types import MessageEntity, Message, Chat
from unittest.mock import Mock
import re


def create_hashtag_entity_list(text: str):
	entities = []
	match_iterator = re.finditer(r"#\w+", text)
	for match in match_iterator:
		start, end = match.span()
		entity = MessageEntity(type="hashtag", offset=start, length=(end - start))
		entities.append(entity)
	return entities


def create_mock_message(text: str, entities: List[MessageEntity], chat_id: int = None, message_id: int = None):
	message = Mock(spec=Message)
	message.content_type = "text"
	if message_id:
		message.message_id = message_id
		message.id = message_id

	return __set_mock_message(message, text, entities, chat_id, message_id)


def create_mock_pyrogram_message(text: str, entities: List[MessageEntity], chat_id: int = None, message_id: int = None):
	message = Mock(spec=pyrogram.types.Message)
	if message_id:
		message.id = message_id

	return __set_mock_message(message, text, entities, chat_id, message_id)


def __set_mock_message(message: Mock, text: str, entities: List[MessageEntity],
                       chat_id: int = None, message_id: int = None):
	message.text = text
	message.caption = None
	message.empty = False
	message.entities = entities
	message.caption_entities = None
	message.photo = None
	message.video = None
	message.audio = None
	message.document = None
	message.sticker = None
	message.video_note = None
	message.voice = None
	message.location = None
	message.contact = None
	message.venue = None
	message.dice = None
	message.poll = None

	if chat_id:
		message.chat = create_mock_chat(chat_id, "")


	return message

def create_mock_chat(id: int, name: str):
	chat = Mock(spec=Chat)
	chat.id = id
	chat.name = name

	return chat
