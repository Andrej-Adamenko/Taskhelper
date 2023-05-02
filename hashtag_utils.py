import re
from typing import List

import telebot
from telebot.types import MessageEntity

import post_link_utils
import utils
from config_utils import DEFAULT_USER_DATA, SUBCHANNEL_DATA

PRIORITY_TAG = "п"
OPENED_TAG = "о"
CLOSED_TAG = "х"
SCHEDULED_TAG = "з"


def find_hashtag_indexes(text: str, entities: List[telebot.types.MessageEntity], main_channel_id: int):
	status_tag_index = None
	user_tag_indexes = []
	priority_tag_index = None

	if entities is None:
		return None, None, None

	main_channel_id_str = str(main_channel_id)

	for entity_index in reversed(range(len(entities))):
		entity = entities[entity_index]
		if entity.type == "hashtag":
			tag = text[entity.offset + 1:entity.offset + entity.length]
			if tag == OPENED_TAG or tag == CLOSED_TAG or tag.startswith(SCHEDULED_TAG):
				status_tag_index = entity_index
				continue

			if main_channel_id_str in SUBCHANNEL_DATA:
				main_channel_users = SUBCHANNEL_DATA[main_channel_id_str]
				if tag in main_channel_users:
					user_tag_indexes.insert(0, entity_index)
					continue

			if tag.startswith(PRIORITY_TAG):
				priority_tag_index = entity_index

	return status_tag_index, user_tag_indexes, priority_tag_index


def insert_default_user_hashtags(main_channel_id: int, hashtags: List[str]):
	main_channel_id_str = str(main_channel_id)
	if main_channel_id_str in DEFAULT_USER_DATA:
		hashtags[0] = OPENED_TAG if hashtags[0] is None else hashtags[0]
		user, priority = DEFAULT_USER_DATA[main_channel_id_str].split(" ")
		hashtags[1] = user
		hashtags[2] = PRIORITY_TAG

	return hashtags


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

	hashtag_entity = MessageEntity(type="hashtag", offset=position, length=len(hashtag))
	entities.append(hashtag_entity)
	entities.sort(key=lambda e: e.offset)

	return text, entities


def insert_hashtags(post_data: telebot.types.Message, hashtags: List[str]):
	text, entities = utils.get_post_content(post_data)

	hashtags_start_position = 0
	if entities and entities[0].type == "text_link" and entities[0].offset == 0:
		hashtags_start_position += entities[0].length + len(post_link_utils.LINK_ENDING)
		if hashtags_start_position > len(text):
			text += " "

	for hashtag in hashtags[::-1]:
		if hashtag is None:
			continue
		text, entities = insert_hashtag_in_post(text, entities, "#" + hashtag, hashtags_start_position)

	utils.set_post_content(post_data, text, entities)

	return post_data


def check_scheduled_tag(text: str, entities: List[telebot.types.MessageEntity], status_tag_index: int):
	status_offset = entities[status_tag_index].offset
	if text[status_offset + 1:].startswith(SCHEDULED_TAG):
		text_after_tag = text[status_offset + 1 + len(SCHEDULED_TAG) + 1:]
		result = re.search("^\d{4}-\d{1,2}-\d{1,2} \d{1,2}:\d{1,2}", text_after_tag)
		if result is None:
			return
		entities[status_tag_index].length += 1 + result.end()
		return True
	return False


def extract_hashtags(post_data: telebot.types.Message, main_channel_id: int, cut_from_text: bool = True):
	text, entities = utils.get_post_content(post_data)

	status_tag_index, user_tag_indexes, priority_tag_index = find_hashtag_indexes(text, entities, main_channel_id)

	extracted_hashtags = []
	if status_tag_index is None:
		extracted_hashtags.append(None)
	else:
		check_scheduled_tag(text, entities, status_tag_index)
		extracted_hashtags.append(entities[status_tag_index])

	if not user_tag_indexes:
		extracted_hashtags.append(None)
	else:
		for user_tag_index in user_tag_indexes:
			extracted_hashtags.append(entities[user_tag_index])

	if priority_tag_index is None:
		extracted_hashtags.append(None)
	else:
		extracted_hashtags.append(entities[priority_tag_index])

	for i in range(len(extracted_hashtags)):
		if extracted_hashtags[i] is None:
			continue

		entity_offset = extracted_hashtags[i].offset
		entity_length = extracted_hashtags[i].length
		extracted_hashtags[i] = text[entity_offset + 1:entity_offset + entity_length]

	if cut_from_text:
		entities_to_remove = [status_tag_index, priority_tag_index]
		if user_tag_indexes:
			entities_to_remove += user_tag_indexes
		entities_to_remove = list(filter(lambda elem: elem is not None, entities_to_remove))
		entities_to_remove.sort(reverse=True)

		for entity_index in entities_to_remove:
			text, entities = utils.cut_entity_from_post(text, entities, entity_index)

		utils.set_post_content(post_data, text, entities)

	return extracted_hashtags, post_data
