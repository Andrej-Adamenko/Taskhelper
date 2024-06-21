from typing import List

from telebot.types import MessageEntity, Message
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


def create_mock_message(text: str, entities: List[MessageEntity]):
	message = Mock(spec=Message)
	message.text = text
	message.entities = entities
	return message
