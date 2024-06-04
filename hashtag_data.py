import re
import typing
from typing import List

import telebot
from telebot.types import MessageEntity

import config_utils
import db_utils
import hashtag_utils
import post_link_utils
import utils
from config_utils import DEFAULT_USER_DATA, HASHTAGS

PRIORITY_TAG = HASHTAGS["PRIORITY"]
OPENED_TAG = HASHTAGS["OPENED"]
CLOSED_TAG = HASHTAGS["CLOSED"]
SCHEDULED_TAG = HASHTAGS["SCHEDULED"]

POSSIBLE_PRIORITIES = ["1", "2", "3"]


class HashtagData:
	SCHEDULED_DATE_FORMAT_REGEX = "^\d{4}-\d{1,2}-\d{1,2} \d{1,2}:\d{1,2}"

	def __init__(self, post_data: telebot.types.Message, main_channel_id: int):
		self.hashtag_indexes = []
		self.post_data = post_data
		self.main_channel_id = main_channel_id

		hashtags = self.extract_hashtags(post_data, main_channel_id)
		scheduled_tag, status_tag, user_tags, priority_tag = hashtags
		self.scheduled_tag = scheduled_tag
		self.status_tag = status_tag
		self.user_tags = user_tags
		self.priority_tag = priority_tag

		self.other_hashtags = self.extract_other_hashtags(post_data)

	def is_status_missing(self):
		return self.status_tag is None and self.scheduled_tag is None

	def is_opened(self):
		return self.status_tag == OPENED_TAG or self.is_scheduled()

	def is_closed(self):
		return self.status_tag == CLOSED_TAG

	def is_scheduled(self):
		return bool(self.scheduled_tag)

	def get_priority_number(self):
		if self.priority_tag and self.priority_tag != PRIORITY_TAG:
			return self.priority_tag[len(PRIORITY_TAG):]

	def get_priority_number_or_default(self):
		if self.priority_tag:
			if self.priority_tag == PRIORITY_TAG:
				return self.get_default_subchannel_priority()
			return self.priority_tag[len(PRIORITY_TAG):]

	def get_assigned_user(self):
		if self.user_tags:
			return self.user_tags[0]

	def get_followed_users(self):
		return self.user_tags[1:]

	def get_all_users(self):
		assigned_user = self.get_assigned_user()
		if not assigned_user:
			return
		user_tags = [assigned_user]
		user_tags += self.get_followed_users()
		return user_tags

	def get_hashtag_list(self):
		hashtags = [self.scheduled_tag, self.status_tag]
		hashtags += self.user_tags
		hashtags.append(self.priority_tag)
		return hashtags

	def get_hashtags_for_insertion(self):
		hashtags = []
		hashtags.append(self.scheduled_tag)
		hashtags.append(self.status_tag)
		hashtags += self.user_tags
		hashtags.append(self.priority_tag)
		return hashtags

	def set_status_tag(self, state: typing.Union[bool, None]):
		if state is None:
			self.status_tag = None
		else:
			self.status_tag = OPENED_TAG if state else CLOSED_TAG

	def assign_to_user(self, user: str):
		if user in self.user_tags:
			self.user_tags.remove(user)
		self.user_tags.insert(0, user)

	def set_priority(self, priority: str):
		self.priority_tag = PRIORITY_TAG + priority

	def remove_from_followers(self, user: str):
		self.user_tags.remove(user)

	def add_to_followers(self, user: str):
		if user not in self.user_tags:
			self.user_tags.append(user)

	def set_scheduled_tag(self, date):
		if date:
			self.scheduled_tag = SCHEDULED_TAG + " " + date
		else:
			self.scheduled_tag = None

	def insert_default_user_and_priority(self):
		main_channel_id_str = str(self.main_channel_id)
		if main_channel_id_str in DEFAULT_USER_DATA:
			self.status_tag = OPENED_TAG if self.is_status_missing() else self.status_tag
			user, priority = DEFAULT_USER_DATA[main_channel_id_str].split(" ")
			if not self.get_assigned_user():
				self.assign_to_user(user)
			if self.get_priority_number() is None:
				self.set_priority("")

	def check_priority_tag(self, tag, priority_tag):
		if not tag.startswith(priority_tag):
			return False
		return tag == priority_tag or tag[len(priority_tag):] in POSSIBLE_PRIORITIES

	def check_scheduled_tag(self, tag, scheduled_tag):
		if tag == scheduled_tag or tag.startswith(scheduled_tag + " "):
			return True
		return False

	def find_hashtag_indexes(self, text: str, entities: List[telebot.types.MessageEntity], main_channel_id: int):
		scheduled_tag_index = None
		status_tag_index = None
		user_tag_indexes = []
		priority_tag_index = None

		if entities is None:
			return None, None, [], None

		for entity_index in reversed(range(len(entities))):
			entity = entities[entity_index]
			if entity.type == "hashtag":
				tag = text[entity.offset + 1:entity.offset + entity.length]
				if config_utils.HASHTAGS_BEFORE_UPDATE and self.check_old_scheduled_tag(tag):
					scheduled_tag_index = entity_index
					continue

				if self.check_scheduled_tag(tag, SCHEDULED_TAG):
					scheduled_tag_index = entity_index
					continue

				if config_utils.HASHTAGS_BEFORE_UPDATE and self.check_old_status_tag(tag):
					status_tag_index = entity_index
					continue

				if tag == OPENED_TAG or tag == CLOSED_TAG:
					status_tag_index = entity_index
					continue

				if db_utils.is_user_tag_exists(main_channel_id, tag):
					user_tag_indexes.insert(0, entity_index)
					continue

				if config_utils.HASHTAGS_BEFORE_UPDATE and self.check_old_priority_tag(tag):
					priority_tag_index = entity_index
					continue

				if self.check_priority_tag(tag, PRIORITY_TAG):
					priority_tag_index = entity_index

		return scheduled_tag_index, status_tag_index, user_tag_indexes, priority_tag_index

	def extract_hashtags(self, post_data: telebot.types.Message, main_channel_id: int):
		text, entities = utils.get_post_content(post_data)

		self.hashtag_indexes = self.find_hashtag_indexes(text, entities, main_channel_id)
		scheduled_tag_index, status_tag_index, user_tag_indexes, priority_tag_index = self.hashtag_indexes

		scheduled_tag = None
		if scheduled_tag_index is not None:
			if config_utils.HASHTAGS_BEFORE_UPDATE:
				result = self.replace_old_scheduled_tag(text, entities, scheduled_tag_index)
				text = result if result else text
			self.update_scheduled_tag(text, entities, scheduled_tag_index)
			scheduled_tag = self.get_tag_from_entity(entities[scheduled_tag_index], text)

		status_tag = None
		if status_tag_index is not None:
			if config_utils.HASHTAGS_BEFORE_UPDATE:
				result = self.replace_old_status_tag(text, entities, status_tag_index)
				text = result if result else text
			status_tag = self.get_tag_from_entity(entities[status_tag_index], text)

		user_tags = []
		if user_tag_indexes:
			for user_tag_index in user_tag_indexes:
				user_tag = self.get_tag_from_entity(entities[user_tag_index], text)
				user_tags.append(user_tag)

		priority_tag = None
		if priority_tag_index is not None:
			if config_utils.HASHTAGS_BEFORE_UPDATE:
				result = self.replace_old_priority_tag(text, entities, priority_tag_index)
				text = result if result else text
			priority_tag = self.get_tag_from_entity(entities[priority_tag_index], text)

		return scheduled_tag, status_tag, user_tags, priority_tag

	def extract_other_hashtags(self, post_data: telebot.types.Message):
		text, entities = utils.get_post_content(post_data)
		if not entities:
			return []
		hashtags = []
		scheduled_tag_index, status_tag_index, user_tag_indexes, priority_tag_index = self.hashtag_indexes
		ignored_indexes = [scheduled_tag_index, status_tag_index, priority_tag_index]
		ignored_indexes += user_tag_indexes

		for entity_index in range(len(entities)):
			if entity_index in ignored_indexes or entities[entity_index].type != "hashtag":
				continue

			entity_text = self.get_tag_from_entity(entities[entity_index], text)
			hashtags.append("#" + entity_text)
		return hashtags
	
	def get_present_hashtag_indices(self):
		scheduled_tag_index, status_tag_index, user_tag_indexes, priority_tag_index = self.hashtag_indexes

		hashtags = [scheduled_tag_index, status_tag_index, priority_tag_index]
		if user_tag_indexes:
			hashtags += user_tag_indexes
		return list(filter(lambda elem: elem is not None, hashtags))

	def get_post_data_without_hashtags(self):
		text, entities = utils.get_post_content(self.post_data)
		
		entities_to_remove = self.get_present_hashtag_indices()
		entities_to_remove.sort(reverse=True)

		if not len(entities_to_remove):
			return self.post_data

		for entity_index in entities_to_remove:
			text, entities = utils.cut_entity_from_post(text, entities, entity_index)

		if text.endswith('\n'):
			text = text[:-1]

		utils.set_post_content(self.post_data, text, entities)
		return self.post_data

	def get_tag_from_entity(self, entity: telebot.types.MessageEntity, text: str):
		return text[entity.offset + 1:entity.offset + entity.length]

	def update_scheduled_tag(self, text: str, entities: List[telebot.types.MessageEntity], tag_index: int):
		scheduled_tag_offset = entities[tag_index].offset
		if text[scheduled_tag_offset + 1:].startswith(SCHEDULED_TAG):
			text_after_tag = text[scheduled_tag_offset + 1 + len(SCHEDULED_TAG) + 1:]
			result = re.search(self.SCHEDULED_DATE_FORMAT_REGEX, text_after_tag)
			if result is None:
				return False
			entities[tag_index].length += 1 + result.end()
			return True
		return False

	def check_old_status_tag(self, tag: str):
		old_opened_tag = config_utils.HASHTAGS_BEFORE_UPDATE["OPENED"]
		old_closed_tag = config_utils.HASHTAGS_BEFORE_UPDATE["CLOSED"]
		if tag == old_opened_tag or tag == old_closed_tag:
			return True
		return False

	def check_old_scheduled_tag(self, tag: str):
		old_scheduled_tag = config_utils.HASHTAGS_BEFORE_UPDATE["SCHEDULED"]
		if self.check_scheduled_tag(tag, old_scheduled_tag):
			return True
		return False

	def check_old_priority_tag(self, tag: str):
		if self.check_priority_tag(tag, config_utils.HASHTAGS_BEFORE_UPDATE["PRIORITY"]):
			return True
		return False

	def replace_old_status_tag(self, text: str, entities: List[telebot.types.MessageEntity], entity_index: int):
		tag = text[entities[entity_index].offset + 1:entities[entity_index].offset + entities[entity_index].length]
		old_opened_tag = config_utils.HASHTAGS_BEFORE_UPDATE["OPENED"]
		old_closed_tag = config_utils.HASHTAGS_BEFORE_UPDATE["CLOSED"]
		if tag == old_opened_tag or tag == old_closed_tag:
			position = entities[entity_index].offset
			text, entities = utils.cut_entity_from_post(text, entities, entity_index)
			if tag == old_opened_tag:
				new_hashtag = OPENED_TAG
			else:
				new_hashtag = CLOSED_TAG
			text, entities = hashtag_utils.insert_hashtag_in_post(text, entities, "#" + new_hashtag, position)
			return text

	def replace_old_scheduled_tag(self, text: str, entities: List[telebot.types.MessageEntity], entity_index: int):
		tag = text[entities[entity_index].offset + 1:entities[entity_index].offset + entities[entity_index].length]
		old_scheduled_tag = config_utils.HASHTAGS_BEFORE_UPDATE["SCHEDULED"]
		if tag.startswith(old_scheduled_tag):
			position = entities[entity_index].offset
			text, entities = utils.cut_entity_from_post(text, entities, entity_index)
			new_hashtag = SCHEDULED_TAG
			text, entities = hashtag_utils.insert_hashtag_in_post(text, entities, "#" + new_hashtag, position)
			return text

	def replace_old_priority_tag(self, text: str, entities: List[telebot.types.MessageEntity], entity_index: int):
		tag = text[entities[entity_index].offset + 1:entities[entity_index].offset + entities[entity_index].length]
		old_priority_tag = config_utils.HASHTAGS_BEFORE_UPDATE["PRIORITY"]
		if tag.startswith(old_priority_tag):
			position = entities[entity_index].offset
			text, entities = utils.cut_entity_from_post(text, entities, entity_index)
			new_hashtag = PRIORITY_TAG + tag[len(old_priority_tag):]
			text, entities = hashtag_utils.insert_hashtag_in_post(text, entities, "#" + new_hashtag, position)
			return text

	def get_default_subchannel_priority(self):
		main_channel_id_str = str(self.main_channel_id)
		if main_channel_id_str in DEFAULT_USER_DATA:
			user, priority = DEFAULT_USER_DATA[main_channel_id_str].split()
			return priority
