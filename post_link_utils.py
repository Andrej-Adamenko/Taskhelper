import telebot.types
from telebot.types import MessageEntity, InlineKeyboardMarkup, InlineKeyboardButton
from typing import List

import utils
import interval_updating_utils

LINK_ENDING = ". "

CALLBACK_PREFIX = "LNK"

START_UPDATE_QUESTION = "Do you want to start updating older posts? (This can take some time, bot can respond with delay until updating is complete)"


def get_post_url(post_data: telebot.types.Message):
	channel_url = str(post_data.chat.id)[4:]
	return f"https://t.me/c/{channel_url}/{post_data.message_id}"


def get_previous_link(entities: List[MessageEntity], post_url: str):
	if entities:
		for entity in entities:
			if entity.offset == 0 and entity.type == "text_link" and entity.url == post_url:
				return entity
	return None


def insert_link_into_post(post_data: telebot.types.Message, link_text: str, post_url: str, additional_offset: int = 0):
	text, entities = utils.get_post_content(post_data)

	updated_entities = utils.offset_entities(entities, len(link_text) + len(LINK_ENDING) + additional_offset)
	updated_entities.append(MessageEntity(type="text_link", offset=0, length=len(link_text), url=post_url))
	updated_entities.sort(key=lambda e: e.offset)

	text = link_text + LINK_ENDING + text
	entities = updated_entities

	utils.set_post_content(post_data, text, entities)

	return post_data


def get_link_text(post_data: telebot.types.Message):
	return str(post_data.message_id)


def add_link_to_new_post(post_data: telebot.types.Message):
	post_url = get_post_url(post_data)
	link_text = get_link_text(post_data)

	return insert_link_into_post(post_data, link_text, post_url)


def update_post_link(bot: telebot.TeleBot, post_data: telebot.types.Message):
	text, entities = utils.get_post_content(post_data)

	post_url = get_post_url(post_data)
	link_text = get_link_text(post_data)

	previous_link = get_previous_link(entities, post_url)
	if previous_link:
		if len(link_text) == previous_link.length and text.startswith(link_text + LINK_ENDING):
			return  # return if link is correct
		text, entities = remove_previous_link(text, entities, previous_link, link_text)

	utils.set_post_content(post_data, text, entities)

	post_with_link = insert_link_into_post(post_data, link_text, post_url)
	utils.edit_message_content(bot, post_data, reply_markup=post_data.reply_markup)

	return post_with_link


def remove_previous_link(text: str, entities: List[MessageEntity], previous_link: MessageEntity, new_link_text: str):
	entity_offset = 0

	if text.startswith(new_link_text + LINK_ENDING):
		previous_length = len(new_link_text + LINK_ENDING)
		text = text[previous_length:]
		entity_offset -= previous_length
	else:
		text = text[previous_link.length:]
		entity_offset -= previous_link.length
		first_line = text.split("\n")[0]

		if len(LINK_ENDING) > len(first_line) and first_line.startswith(LINK_ENDING[:len(first_line)]):
			# remove remaining part of previous link from the first line
			text = text[len(first_line):]
			entity_offset -= len(first_line)
		elif text.startswith(LINK_ENDING[:len(text)]):
			# remove LINE_ENDING that's placed after the link
			text = text[len(LINK_ENDING):]
			entity_offset -= len(LINK_ENDING)
		elif text.startswith(" "):
			# remove a space character that's placed after the link because it will be added anyway by LINK_ENDING
			text = text[1:]
			entity_offset -= 1

	entities.remove(previous_link)
	entities = utils.offset_entities(entities, entity_offset)

	return text, entities


def handle_callback(bot, call):
	pass
