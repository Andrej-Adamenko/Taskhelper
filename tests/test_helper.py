from typing import List

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
	message.text = text
	message.caption = None
	message.entities = entities

	if chat_id:
		message.chat = Mock(spec=Chat)
		message.chat.id = chat_id

	if message_id:
		message.message_id = message_id
		message.id = message_id

	return message
