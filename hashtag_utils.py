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

		# add additional space only if it doesn't already exist
		additional_space = "" if text[position] == " " else " "
		text = text[:position] + hashtag + additional_space + text[position:]

		for entity in entities:
			if entity.offset >= position:
				entity.offset += len(hashtag) + 1

	entity_length = hashtag.find(" ") if " " in hashtag else len(hashtag)

	hashtag_entity = MessageEntity(type="hashtag", offset=offset, length=entity_length)
	entities.append(hashtag_entity)
	entities.sort(key=lambda e: e.offset)

	return text, entities


def is_last_line_contains_only_hashtags(text: str, entities: List[telebot.types.MessageEntity]):
	last_line_start = text.rfind("\n")
	if last_line_start < 0:
		return False

	last_line_start += 1  # skip new line character
	for entity in entities:
		if entity.offset >= last_line_start and entity.type == "hashtag":
			# replace all hashtags in the last line with spaces
			replacement = " " * entity.length
			text = text[:entity.offset] + replacement + text[entity.offset + entity.length:]

	# check if every character in the last line is a space
	last_line_text = text[last_line_start:]
	return all([c == ' ' for c in last_line_text])


def insert_hashtags(post_data: telebot.types.Message, hashtags: List[str]):
	text, entities = utils.get_post_content(post_data)

	if is_last_line_contains_only_hashtags(text, entities):
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
