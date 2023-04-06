import logging
from typing import List

import telebot.types
from telebot.apihelper import ApiTelegramException

from config_utils import MAX_BUTTONS_IN_ROW

SAME_MSG_CONTENT_ERROR = "Bad Request: message is not modified: specified new message content and reply markup are exactly the same as a current content and reply markup of the message"


def create_callback_str(callback_prefix, callback_type, *args):
	arguments_str = ",".join([str(arg) for arg in args])
	components = [callback_prefix, callback_type]
	if arguments_str:
		components.append(arguments_str)
	callback_str = ",".join(components)
	return callback_str


def offset_entities(entities, offset):
	if not entities:
		return []

	for entity in entities:
		entity.offset += offset

	return entities


def get_forwarded_from_id(message_data):
	if message_data.forward_from_chat:
		return message_data.forward_from_chat.id
	if message_data.forward_from:
		return message_data.forward_from.id

	return None


def get_post_content(post_data: telebot.types.Message):
	if post_data.text is not None:
		return post_data.text, post_data.entities
	elif post_data.caption is not None:
		return post_data.caption, post_data.caption_entities

	return "", []


def set_post_content(post_data: telebot.types.Message, text: str, entities: telebot.types.MessageEntity):
	if post_data.text is not None:
		post_data.text = text
		post_data.entities = entities
	else:
		post_data.caption = text
		post_data.caption_entities = entities


def edit_message_content(bot: telebot.TeleBot, post_data: telebot.types.Message, **kwargs):
	try:
		if post_data.text is not None:
			bot.edit_message_text(chat_id=post_data.chat.id, message_id=post_data.message_id, **kwargs)
		else:
			kwargs["caption"] = kwargs.pop("text")
			kwargs["caption_entities"] = kwargs.pop("entities")
			bot.edit_message_caption(chat_id=post_data.chat.id, message_id=post_data.message_id, **kwargs)
	except ApiTelegramException as E:
		if E.error_code == 429:
			raise E
		if E.description == SAME_MSG_CONTENT_ERROR:
			return


def is_post_data_equal(post_data1: telebot.types.Message, post_data2: telebot.types.Message):
	text1, entities1 = get_post_content(post_data1)
	text2, entities2 = get_post_content(post_data2)

	if text1 != text2:
		return False

	if entities1 is None and entities2 is None:
		return True

	if len(entities1) != len(entities2):
		return False

	for entity_i in range(len(entities1)):
		e1 = entities1[entity_i]
		e2 = entities2[entity_i]
		if e1.type != e2.type or e1.offset != e2.offset or e1.url != e2.url or e1.length != e2.length:
			return False

	return True


def place_buttons_in_rows(buttons: List[telebot.types.InlineKeyboardButton]):
	rows = [[]]
	current_row = button_counter = 0
	for button in buttons:
		if button_counter < MAX_BUTTONS_IN_ROW:
			rows[current_row].append(button)
			button_counter += 1
		else:
			button_counter = 1
			current_row += 1
			rows.append([button])

	return rows


def edit_message_keyboard(bot: telebot.TeleBot, post_data: telebot.types.Message, keyboard: telebot.types.InlineKeyboardMarkup):
	chat_id = post_data.chat.id
	message_id = post_data.message_id
	try:
		bot.edit_message_reply_markup(chat_id=chat_id, message_id=message_id, reply_markup=keyboard)
	except ApiTelegramException as E:
		if E.error_code == 429:
			raise E
		if E.description == SAME_MSG_CONTENT_ERROR:
			return
		logging.info(f"Exception during adding keyboard - {E}")


