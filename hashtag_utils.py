from typing import List, Union

import telebot
from telebot.types import MessageEntity

import utils


def insert_hashtag_in_post(text: str, entities: List[telebot.types.MessageEntity], hashtag: str,
                           position: Union[int, None] = None):
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

		# add additional space only if it doesn't already exist
		additional_space = "" if text[position] == " " else " "
		text = text[:position] + hashtag + additional_space + text[position:]

		for entity in entities:
			if entity.offset >= position:
				entity.offset += len(hashtag + additional_space)

	entity_length = len(hashtag)

	hashtag_entity = MessageEntity(type="hashtag", offset=offset, length=entity_length)
	hashtag_entity.aligned_to_utf8 = True
	entities.append(hashtag_entity)
	entities.sort(key=lambda e: e.offset)

	return text, entities


def insert_hashtags(post_data: telebot.types.Message, hashtags: List[str], is_hashtag_line_present: bool):
	text, entities = utils.get_post_content(post_data)

	if is_hashtag_line_present:
		last_line_start = text.rfind("\n") + 1
		for hashtag in hashtags[::-1]:
			if hashtag is None:
				continue
			text, entities = insert_hashtag_in_post(text, entities, "#" + hashtag, last_line_start)
	else:
		text += "" if text.endswith("\n") else "\n"
		for hashtag in hashtags:
			if hashtag is None:
				continue
			text, entities = insert_hashtag_in_post(text, entities, "#" + hashtag)

	utils.set_post_content(post_data, text, entities)

	return post_data
