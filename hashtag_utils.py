from typing import List

import telebot
from telebot.types import MessageEntity

import post_link_utils
import utils


def insert_hashtag_in_post(text: str, entities: List[telebot.types.MessageEntity], hashtag: str, position: int):
	hashtag_text = hashtag
	if len(text) > position:
		hashtag_text += " "

	text = text[:position] + hashtag_text + text[position:]

	if entities is None:
		entities = []

	for entity in entities:
		if entity.offset >= position:
			entity.offset += len(hashtag_text)

	entity_length = hashtag.find(" ") if " " in hashtag else len(hashtag)

	hashtag_entity = MessageEntity(type="hashtag", offset=position, length=entity_length)
	entities.append(hashtag_entity)
	entities.sort(key=lambda e: e.offset)

	return text, entities


def insert_hashtags(post_data: telebot.types.Message, hashtags: List[str]):
	text, entities = utils.get_post_content(post_data)

	hashtags_start_position = 0
	if entities and entities[0].type == "text_link" and entities[0].offset == 0:
		link_str = post_link_utils.get_link_text(post_data) + post_link_utils.LINK_ENDING
		if text.startswith(link_str):
			hashtags_start_position += len(link_str)
			if hashtags_start_position > len(text):
				text += " "

	for hashtag in hashtags[::-1]:
		if hashtag is None:
			continue
		text, entities = insert_hashtag_in_post(text, entities, "#" + hashtag, hashtags_start_position)

	utils.set_post_content(post_data, text, entities)

	return post_data
