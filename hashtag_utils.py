from typing import List

import telebot
from telebot.types import MessageEntity

import utils

def insert_hashtag_in_post(text: str, entities: List[telebot.types.MessageEntity], hashtag: str, position: int | None = None):
	"""
	Inserts hashtag into post content either at the end of the text or at specified position.

	:param position: optional text index for tag to be inserted at instead of the end
	"""
	if entities is None:
		entities = []

	if position is None or len(text) <= position:
		if text.endswith("\n"):
			offset = len(text)
			text += hashtag
		else:
			offset = len(text) + 1
			text += " " + hashtag
	else:
		offset = position
		text = text[:position] + hashtag + " " + text[position:]

		for entity in entities:
			if entity.offset >= position:
				entity.offset += len(hashtag) + 1

	entity_length = hashtag.find(" ") if " " in hashtag else len(hashtag)

	hashtag_entity = MessageEntity(type="hashtag", offset=offset, length=entity_length)
	entities.append(hashtag_entity)
	entities.sort(key=lambda e: e.offset)

	return text, entities


def insert_hashtags(post_data: telebot.types.Message, hashtags: List[str]):
	text, entities = utils.get_post_content(post_data)

	if not text.endswith("\n"):
		text += "\n"

	for hashtag in hashtags:
		if hashtag is None:
			continue
		text, entities = insert_hashtag_in_post(text, entities, "#" + hashtag)

	utils.set_post_content(post_data, text, entities)

	return post_data
