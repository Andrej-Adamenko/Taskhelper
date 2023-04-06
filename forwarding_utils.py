import logging
import copy
from typing import List

import telebot
from telebot.apihelper import ApiTelegramException
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, MessageEntity

import db_utils
import post_link_utils
import utils

from config_utils import SUBCHANNEL_DATA, DISCUSSION_CHAT_DATA, DEFAULT_USER_DATA, DUMP_CHAT_ID, AUTO_FORWARDING_ENABLED

PRIORITY_TAG = "п"
OPENED_TAG = "о"
CLOSED_TAG = "х"

CALLBACK_PREFIX = "FWRD"

CHECK_MARK_CHARACTER = "\U00002705"
COMMENTS_CHARACTER = "\U0001F4AC"


def get_message_content_by_id(bot: telebot.TeleBot, chat_id: int, message_id: int):
	try:
		forwarded_message = bot.forward_message(chat_id=DUMP_CHAT_ID, from_chat_id=chat_id,
												message_id=message_id)
		bot.delete_message(chat_id=DUMP_CHAT_ID, message_id=forwarded_message.message_id)
	except ApiTelegramException as E:
		if E.error_code == 429:
			raise E
		return

	return forwarded_message


def forward_to_subchannel(bot: telebot.TeleBot, post_data: telebot.types.Message, hashtags: List[str]):
	main_channel_id = post_data.chat.id
	message_id = post_data.message_id

	forwarded_message_data = db_utils.get_copied_message_data(message_id, main_channel_id)
	if forwarded_message_data:
		forwarded_msg_id, forwarded_channel_id = forwarded_message_data
		forwarded_msg_data = get_message_content_by_id(bot, forwarded_channel_id, forwarded_msg_id)
		if forwarded_msg_data and utils.is_post_data_equal(forwarded_msg_data, post_data):
			return

		try:
			bot.delete_message(chat_id=forwarded_channel_id, message_id=forwarded_msg_id)
		except ApiTelegramException as E:
			if E.error_code == 429:
				raise E
			logging.info(f"Exception during delete_message [{forwarded_msg_id}, {forwarded_channel_id}] - {E}")

	if OPENED_TAG not in hashtags:
		return

	subchannel_id = get_subchannel_id_from_hashtags(main_channel_id, hashtags)
	if not subchannel_id:
		logging.warning(f"Subchannel not found in config file {hashtags}, {main_channel_id}")
		return

	try:
		copied_message = bot.copy_message(chat_id=subchannel_id, message_id=message_id, from_chat_id=main_channel_id)
		logging.info(f"Successfully forwarded post [{message_id}, {main_channel_id}] to {subchannel_id} subchannel by tags: {hashtags}")
	except ApiTelegramException as E:
		if E.error_code == 429:
			raise E
		logging.warning(f"Exception during forwarding post to subchannel {hashtags} - {E}")
		return

	db_utils.insert_or_update_copied_message(message_id, main_channel_id, copied_message.message_id, subchannel_id)
	return subchannel_id, copied_message.message_id


def get_subchannel_id_from_hashtags(main_channel_id: int, hashtags: List[str]):
	main_channel_id_str = str(main_channel_id)
	if main_channel_id_str not in SUBCHANNEL_DATA:
		return

	priority = None
	user_priority_list = None
	found_user = None

	subchannel_users = SUBCHANNEL_DATA[main_channel_id_str]
	for user in subchannel_users:
		if user in hashtags:
			user_priority_list = subchannel_users[user]
			found_user = user

	if not user_priority_list:
		return

	for hashtag in hashtags:
		if hashtag and hashtag.startswith(PRIORITY_TAG):
			priority = hashtag[len(PRIORITY_TAG):]

	if priority == "" and main_channel_id_str in DEFAULT_USER_DATA:
		default_user, default_priority = DEFAULT_USER_DATA[main_channel_id_str].split()
		if default_user == found_user:
			return user_priority_list[default_priority]

	if priority not in user_priority_list or priority is None:
		return

	return user_priority_list[priority]


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


def get_all_discussion_chat_ids():
	discussion_chat_ids = []
	for discussion_chat_id in DISCUSSION_CHAT_DATA.values():
		discussion_chat_ids.append(discussion_chat_id)
	return discussion_chat_ids


def generate_control_buttons(hashtags: List[str], post_data: telebot.types.Message):
	main_channel_id = post_data.chat.id
	message_id = post_data.message_id

	if hashtags[0] == OPENED_TAG:
		ticket_state_switch_callback_data = utils.create_callback_str(CALLBACK_PREFIX, "X")
		ticket_state_switch_button = InlineKeyboardButton("☑️", callback_data=ticket_state_switch_callback_data)
	else:
		ticket_state_switch_callback_data = utils.create_callback_str(CALLBACK_PREFIX, "O")
		ticket_state_switch_button = InlineKeyboardButton("✖", callback_data=ticket_state_switch_callback_data)

	reassign_callback_data = utils.create_callback_str(CALLBACK_PREFIX, "R")
	current_user = hashtags[1] if hashtags[1] is not None else "-"
	reassign_button = InlineKeyboardButton(f"к:{current_user}", callback_data=reassign_callback_data)

	priority_callback_data = utils.create_callback_str(CALLBACK_PREFIX, "P")
	current_priority = "-"
	if hashtags[2] is not None and hashtags[2] != PRIORITY_TAG:
		current_priority = hashtags[2]
		current_priority = current_priority[len(PRIORITY_TAG):]

	priority_button = InlineKeyboardButton(current_priority, callback_data=priority_callback_data)

	buttons = [
		ticket_state_switch_button,
		reassign_button,
		priority_button
	]

	main_channel_id_str = str(main_channel_id)
	if main_channel_id_str in DISCUSSION_CHAT_DATA and DISCUSSION_CHAT_DATA[main_channel_id_str] is not None:
		discussion_chat_id = DISCUSSION_CHAT_DATA[main_channel_id_str]
		discussion_message_id = db_utils.get_discussion_message_id(message_id, main_channel_id)
		if discussion_message_id:
			discussion_chat_id = str(discussion_chat_id)[4:]
			comments_url = f"tg://privatepost?channel={discussion_chat_id}&post={discussion_message_id}&thread={discussion_message_id}"
			comments_button = InlineKeyboardButton(COMMENTS_CHARACTER, url=comments_url)
			buttons.append(comments_button)

	keyboard_markup = InlineKeyboardMarkup([buttons])
	return keyboard_markup


def generate_subchannel_buttons(post_data):
	main_channel_id = post_data.chat.id

	forwarding_data = get_subchannels_forwarding_data(main_channel_id)

	text, entities = utils.get_post_content(post_data)

	_, user_hashtag_index, priority_hashtag_index = find_hashtag_indexes(text, entities, main_channel_id)
	current_subchannel_name = ""

	if user_hashtag_index is not None:
		entity = entities[user_hashtag_index]
		current_subchannel_name += text[entity.offset + 1:entity.offset + entity.length]
		if priority_hashtag_index is not None:
			entity = entities[priority_hashtag_index]
			priority = text[entity.offset + 1 + len(PRIORITY_TAG):entity.offset + entity.length]
			current_subchannel_name += " " + priority

	subchannel_buttons = []
	for subchannel_name in forwarding_data:
		callback_str = utils.create_callback_str(CALLBACK_PREFIX, "SUB", subchannel_name)
		btn = InlineKeyboardButton("#" + subchannel_name, callback_data=callback_str)
		if subchannel_name == current_subchannel_name:
			btn.text += CHECK_MARK_CHARACTER
			btn.callback_data = utils.create_callback_str(CALLBACK_PREFIX, "S")
		subchannel_buttons.append(btn)

	rows = utils.place_buttons_in_rows(subchannel_buttons)

	keyboard_markup = InlineKeyboardMarkup(rows)
	return keyboard_markup


def generate_priority_buttons(post_data: telebot.types.Message):
	main_channel_id = post_data.chat.id

	text, entities = utils.get_post_content(post_data)

	available_priorities = ["1", "2", "3"]

	_, user_hashtag_index, priority_hashtag_index = find_hashtag_indexes(text, entities, main_channel_id)
	current_user = ""
	current_priority = ""
	if user_hashtag_index is not None:
		entity = entities[user_hashtag_index]
		current_user = text[entity.offset + 1:entity.offset + entity.length]
		if priority_hashtag_index is not None:
			entity = entities[priority_hashtag_index]
			current_priority = text[entity.offset + 1 + len(PRIORITY_TAG):entity.offset + entity.length]

	main_channel_id_str = str(main_channel_id)
	if main_channel_id_str in SUBCHANNEL_DATA:
		users = SUBCHANNEL_DATA[main_channel_id_str]
		if current_user in users:
			available_priorities = list(users[current_user].keys())

	priority_buttons = []

	for priority in available_priorities:
		callback_str = utils.create_callback_str(CALLBACK_PREFIX, "PR", priority)
		btn = InlineKeyboardButton(priority, callback_data=callback_str)
		if priority == current_priority:
			btn.text += CHECK_MARK_CHARACTER
			btn.callback_data = utils.create_callback_str(CALLBACK_PREFIX, "S")
		priority_buttons.append(btn)

	rows = utils.place_buttons_in_rows(priority_buttons)

	keyboard_markup = InlineKeyboardMarkup(rows)
	return keyboard_markup


def get_subchannels_forwarding_data(main_channel_id):
	main_channel_id_str = str(main_channel_id)
	if main_channel_id_str not in SUBCHANNEL_DATA:
		return {}

	forwarding_data = {}

	channel_users = SUBCHANNEL_DATA[main_channel_id_str]
	for user in channel_users:
		user_priorities = channel_users[user]
		for priority in user_priorities:
			subchannel_id = user_priorities[priority]
			forwarding_data[user + " " + priority] = subchannel_id

	return forwarding_data


def add_control_buttons(bot: telebot.TeleBot, post_data: telebot.types.Message, hashtags: List[str]):
	keyboard_markup = generate_control_buttons(hashtags, post_data)
	utils.edit_message_keyboard(bot, post_data, keyboard_markup)


def extract_hashtags(post_data: telebot.types.Message, main_channel_id: int):
	text, entities = utils.get_post_content(post_data)

	status_tag_index, user_tag_index, priority_tag_index = find_hashtag_indexes(text, entities, main_channel_id)

	extracted_hashtags = []
	if status_tag_index is None:
		extracted_hashtags.append(None)
	else:
		extracted_hashtags.append(entities[status_tag_index])

	if user_tag_index is None:
		extracted_hashtags.append(None)
	else:
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

	entities_to_remove = [status_tag_index, user_tag_index, priority_tag_index]
	entities_to_remove = list(filter(lambda elem: elem is not None, entities_to_remove))
	entities_to_remove.sort(reverse=True)

	for entity_index in entities_to_remove:
		text, entities = cut_entity_from_post(text, entities, entity_index)

	utils.set_post_content(post_data, text, entities)

	return extracted_hashtags, post_data


def find_hashtag_indexes(text: str, entities: List[telebot.types.MessageEntity], main_channel_id: int):
	status_tag_index = None
	user_tag_index = None
	priority_tag_index = None

	if entities is None:
		return None, None, None

	main_channel_id_str = str(main_channel_id)

	for entity_index in reversed(range(len(entities))):
		entity = entities[entity_index]
		if entity.type == "hashtag":
			tag = text[entity.offset + 1:entity.offset + entity.length]
			if tag == OPENED_TAG or tag == CLOSED_TAG:
				status_tag_index = entity_index
				continue

			if main_channel_id_str in SUBCHANNEL_DATA:
				main_channel_users = SUBCHANNEL_DATA[main_channel_id_str]
				if tag in main_channel_users:
					user_tag_index = entity_index
					continue

			if tag.startswith(PRIORITY_TAG):
				priority_tag_index = entity_index

	return status_tag_index, user_tag_index, priority_tag_index


def handle_callback(bot: telebot.TeleBot, call: telebot.types.CallbackQuery):
	callback_data = call.data[len(CALLBACK_PREFIX) + 1:]
	callback_data_list = callback_data.split(",")
	callback_type = callback_data_list[0]
	other_data = callback_data_list[1:]

	if callback_type == "SUB":
		subchannel_name = other_data[0]
		change_subchannel_button_event(bot, call.message, subchannel_name)
	elif callback_type == "X":
		change_state_button_event(bot, call.message, False)
	elif callback_type == "O":
		change_state_button_event(bot, call.message, True)
	elif callback_type == "S":
		forward_and_add_inline_keyboard(bot, call.message, force_forward=True)
	elif callback_type == "R":
		show_subchannel_buttons(bot, call.message)
	elif callback_type == "P":
		show_priority_buttons(bot, call.message)
	elif callback_type == "PR":
		priority = other_data[0]
		change_priority_button_event(bot, call.message, priority)


def show_subchannel_buttons(bot: telebot.TeleBot, post_data: telebot.types.Message):
	keyboard_markup = generate_subchannel_buttons(post_data)
	utils.edit_message_keyboard(bot, post_data, keyboard_markup)


def show_priority_buttons(bot: telebot.TeleBot, post_data: telebot.types.Message):
	keyboard_markup = generate_priority_buttons(post_data)
	utils.edit_message_keyboard(bot, post_data, keyboard_markup)


def change_state_button_event(bot: telebot.TeleBot, post_data: telebot.types.Message, new_state: bool):
	main_channel_id = post_data.chat.id

	hashtags, post_data = extract_hashtags(post_data, main_channel_id)
	if hashtags:
		hashtags[0] = OPENED_TAG if new_state else CLOSED_TAG

		rearrange_hashtags(bot, post_data, hashtags)
		forward_to_subchannel(bot, post_data, hashtags)
		add_control_buttons(bot, post_data, hashtags)


def change_subchannel_button_event(bot: telebot.TeleBot, post_data: telebot.types.Message, new_subchannel_name: str):
	main_channel_id = post_data.chat.id

	subchannel_user, subchannel_priority = new_subchannel_name.split(" ")

	original_post_data = copy.deepcopy(post_data)
	hashtags, post_data = extract_hashtags(post_data, main_channel_id)

	if hashtags:
		hashtags[1] = subchannel_user
		hashtags[2] = PRIORITY_TAG + subchannel_priority

		rearrange_hashtags(bot, post_data, hashtags, original_post_data)
		forward_to_subchannel(bot, post_data, hashtags)
		add_control_buttons(bot, post_data, hashtags)


def change_priority_button_event(bot: telebot.TeleBot, post_data: telebot.types.Message, new_priority: str):
	main_channel_id = post_data.chat.id

	original_post_data = copy.deepcopy(post_data)
	hashtags, post_data = extract_hashtags(post_data, main_channel_id)

	if hashtags:
		hashtags[2] = PRIORITY_TAG + new_priority

		rearrange_hashtags(bot, post_data, hashtags, original_post_data)
		forward_to_subchannel(bot, post_data, hashtags)
		add_control_buttons(bot, post_data, hashtags)


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
	offsetted_entities = utils.offset_entities(entities[entity_index + 1:], -entity_to_cut.length + 1)
	entities[entity_index:] = offsetted_entities

	return text, entities


def insert_default_user_hashtags(main_channel_id: int, hashtags: List[str]):
	main_channel_id_str = str(main_channel_id)
	if main_channel_id_str in DEFAULT_USER_DATA:
		hashtags[0] = OPENED_TAG if hashtags[0] is None else hashtags[0]
		user, priority = DEFAULT_USER_DATA[main_channel_id_str].split(" ")
		hashtags[1] = user
		hashtags[2] = PRIORITY_TAG

	return hashtags


def forward_and_add_inline_keyboard(bot: telebot.TeleBot, post_data: telebot.types.Message,
									use_default_user: bool = False, force_forward: bool = False):
	main_channel_id = post_data.chat.id

	original_post_data = copy.deepcopy(post_data)

	hashtags, post_data = extract_hashtags(post_data, main_channel_id)
	if hashtags:
		if hashtags[1] is None and hashtags[2] is None and use_default_user:
			hashtags = insert_default_user_hashtags(main_channel_id, hashtags)

		rearrange_hashtags(bot, post_data, hashtags, original_post_data)
		if AUTO_FORWARDING_ENABLED or force_forward:
			forward_to_subchannel(bot, post_data, hashtags)
		add_control_buttons(bot, post_data, hashtags)


def rearrange_hashtags(bot: telebot.TeleBot, post_data: telebot.types.Message, hashtags: List[str],
					   original_post_data: telebot.types.Message = None):
	post_data = insert_hashtags(post_data, hashtags)

	if original_post_data and utils.is_post_data_equal(post_data, original_post_data):
		return

	try:
		text, entities = utils.get_post_content(post_data)
		utils.edit_message_content(bot, post_data, text=text, entities=entities, reply_markup=post_data.reply_markup)
	except ApiTelegramException as E:
		if E.error_code == 429:
			raise E
		logging.info(f"Exception during rearranging hashtags - {E}")
		return


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

