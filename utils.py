import logging
from typing import List

import telebot.types
from telebot.apihelper import ApiTelegramException

import config_utils
from config_utils import MAX_BUTTONS_IN_ROW, DISCUSSION_CHAT_DATA, SUBCHANNEL_DATA, SCHEDULED_STORAGE_CHAT_IDS, USER_DATA

SAME_MSG_CONTENT_ERROR = "Bad Request: message is not modified: specified new message content and reply markup are exactly the same as a current content and reply markup of the message"


def create_callback_str(callback_prefix, callback_type, *args):
	arguments_str = ",".join([str(arg) for arg in args])
	components = [callback_prefix, callback_type]
	if arguments_str:
		components.append(arguments_str)
	callback_str = ",".join(components)
	return callback_str


def parse_callback_str(callback_str: str):
	components = callback_str.split(",")
	callback_type = components[1]
	arguments = components[2:]
	return callback_type, arguments


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
	if "chat_id" not in kwargs:
		kwargs["chat_id"] = post_data.chat.id
	if "message_id" not in kwargs:
		kwargs["message_id"] = post_data.message_id

	try:
		if post_data.text is not None:
			bot.edit_message_text(**kwargs)
		else:
			kwargs["caption"] = kwargs.pop("text")
			kwargs["caption_entities"] = kwargs.pop("entities")
			bot.edit_message_caption(**kwargs)
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


def edit_message_keyboard(bot: telebot.TeleBot, post_data: telebot.types.Message,
                          keyboard: telebot.types.InlineKeyboardMarkup = None, chat_id: int = None, message_id: int = None):
	if chat_id is None and message_id is None:
		chat_id = post_data.chat.id
		message_id = post_data.message_id

	if keyboard is None:
		keyboard = post_data.reply_markup

	try:
		bot.edit_message_reply_markup(chat_id=chat_id, message_id=message_id, reply_markup=keyboard)
	except ApiTelegramException as E:
		if E.error_code == 429:
			raise E
		if E.description == SAME_MSG_CONTENT_ERROR:
			return
		logging.info(f"Exception during adding keyboard - {E}")


def cut_entity_from_post(text: str, entities: List[telebot.types.MessageEntity], entity_index: int):
	entity_to_cut = entities[entity_index]
	if entity_to_cut.offset != 0 and text[entity_to_cut.offset - 1] == " ":
		entity_to_cut.offset -= 1
		entity_to_cut.length += 1
	if len(text) > entity_to_cut.offset + entity_to_cut.length:
		character_after_entity = text[entity_to_cut.offset + entity_to_cut.length]
		if character_after_entity == " ":
			entity_to_cut.length += 1

	text = text[:entity_to_cut.offset] + " " + text[entity_to_cut.offset + entity_to_cut.length:]
	offsetted_entities = offset_entities(entities[entity_index + 1:], -entity_to_cut.length + 1)
	entities[entity_index:] = offsetted_entities

	return text, entities


def get_all_subchannel_ids():
	subchannel_ids = []
	for main_channel_id in SUBCHANNEL_DATA:
		channel_users = SUBCHANNEL_DATA[main_channel_id]
		for user in channel_users:
			user_priorities = channel_users[user]
			for priority in user_priorities:
				subchannel_id = user_priorities[priority]
				subchannel_ids.append(subchannel_id)

	return subchannel_ids


def get_all_scheduled_storage_ids():
	storage_ids = []
	for main_channel_id in SCHEDULED_STORAGE_CHAT_IDS:
		channel_users = SCHEDULED_STORAGE_CHAT_IDS[main_channel_id]
		for user in channel_users:
			storage_ids.append(channel_users[user])
	return storage_ids


def get_ignored_chat_ids():
	ignored_chat_ids = [config_utils.DUMP_CHAT_ID]
	ignored_chat_ids += list(DISCUSSION_CHAT_DATA.values())
	for main_channel_id in SCHEDULED_STORAGE_CHAT_IDS:
		for tag in SCHEDULED_STORAGE_CHAT_IDS[main_channel_id]:
			ignored_chat_ids.append(SCHEDULED_STORAGE_CHAT_IDS[main_channel_id][tag])
	ignored_chat_ids += get_all_subchannel_ids()

	return ignored_chat_ids


def get_key_by_value(d: dict, value: object):
	key_list = list(d.keys())
	val_list = list(d.values())

	try:
		position = val_list.index(value)
	except ValueError:
		return

	return key_list[position]


def insert_user_reference(main_channel_id: int, user_tag: str, text: str):
	placeholder_text = "{USER}"
	placeholder_position = text.find(placeholder_text)
	if placeholder_position < 0:
		return text, None

	text = text[:placeholder_position] + text[placeholder_position + len(placeholder_text):]

	main_channel_id_str = str(main_channel_id)
	if main_channel_id_str not in USER_DATA:
		text = text[:placeholder_position] + user_tag + text[placeholder_position:]
		return text, None
	user_tags = USER_DATA[main_channel_id_str]
	if user_tag not in user_tags:
		text = text[:placeholder_position] + user_tag + text[placeholder_position:]
		return text, None

	user = user_tags[user_tag]
	if type(user) == str:
		text = text[:placeholder_position] + user + text[placeholder_position:]
		return text, None
	elif user.username:
		user_reference_text = f"@{user.username}"
		text = text[:placeholder_position] + user_reference_text + text[placeholder_position:]
		return text, None
	else:
		user_reference_text = user.first_name
		text = text[:placeholder_position] + user_reference_text + text[placeholder_position:]
		mentioned_user = {"id": user.id, "first_name": user.first_name, "last_name": user.last_name}
		entity = telebot.types.MessageEntity(offset=placeholder_position, length=len(user_reference_text),
		                                     type="text_mention", user=mentioned_user)
		return text, [entity]


def is_main_channel_exists(main_channel_id):
	main_channel_id = int(main_channel_id)
	return main_channel_id in config_utils.CHANNEL_IDS
