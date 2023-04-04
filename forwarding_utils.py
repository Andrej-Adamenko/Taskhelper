import logging
import copy
from typing import List

import telebot
from telebot.apihelper import ApiTelegramException
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, MessageEntity

import db_utils
import post_link_utils
import utils

from config_utils import SUBCHANNEL_DATA, DISCUSSION_CHAT_DATA, DEFAULT_USER_DATA, DUMP_CHAT_ID

PRIORITY_TAG = "п"
OPENED_TAG = "о"
CLOSED_TAG = "х"

CALLBACK_PREFIX = "FWRD"

CHECK_MARK_CHARACTER = "\U00002705"
COMMENTS_CHARACTER = "\U0001F4AC"

MAX_BUTTONS_IN_ROW = 3

SAME_MSG_CONTENT_ERROR = "Bad Request: message is not modified: specified new message content and reply markup are exactly the same as a current content and reply markup of the message"


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
		if forwarded_msg_data and is_post_data_equal(forwarded_msg_data, post_data):
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


def generate_control_buttons(hashtags, main_channel_id, message_id):
	close_ticket_callback_data = utils.create_callback_str(CALLBACK_PREFIX, "X")
	close_ticket_button = InlineKeyboardButton("#x", callback_data=close_ticket_callback_data)

	open_ticket_callback_data = utils.create_callback_str(CALLBACK_PREFIX, "O")
	open_ticket_button = InlineKeyboardButton("#o", callback_data=open_ticket_callback_data)

	if hashtags[0] == CLOSED_TAG:
		close_ticket_button.text += CHECK_MARK_CHARACTER
		close_ticket_button.callback_data = "_"
	elif hashtags[0] == OPENED_TAG:
		open_ticket_button.text += CHECK_MARK_CHARACTER
		open_ticket_button.callback_data = "_"

	reassign_callback_data = utils.create_callback_str(CALLBACK_PREFIX, "R")
	reassign_button = InlineKeyboardButton("Reassign", callback_data=reassign_callback_data)

	buttons = [
		reassign_button,
		close_ticket_button,
		open_ticket_button
	]

	main_channel_id_str = str(main_channel_id)
	if main_channel_id_str in DISCUSSION_CHAT_DATA:
		discussion_chat_id = DISCUSSION_CHAT_DATA[main_channel_id_str]
		discussion_message_id = db_utils.get_discussion_message_id(message_id, main_channel_id)
		if discussion_message_id:
			discussion_chat_id = str(discussion_chat_id)[4:]
			comments_url = f"tg://privatepost?channel={discussion_chat_id}&post={discussion_message_id}&thread={discussion_message_id}"
			comments_button = InlineKeyboardButton(COMMENTS_CHARACTER, url=comments_url)
			buttons.append(comments_button)

	keyboard_markup = InlineKeyboardMarkup([buttons])
	return keyboard_markup


def generate_subchannel_buttons(main_channel_id, post_data):
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

	rows = [[]]
	current_row = button_counter = 0
	for button in subchannel_buttons:
		if button_counter < MAX_BUTTONS_IN_ROW:
			rows[current_row].append(button)
			button_counter += 1
		else:
			button_counter = 1
			current_row += 1
			rows.append([button])

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
	main_channel_id = post_data.chat.id
	message_id = post_data.message_id

	text, entities = utils.get_post_content(post_data)

	keyboard_markup = generate_control_buttons(hashtags, main_channel_id, message_id)
	try:
		utils.edit_message_content(bot, post_data, text=text, entities=entities, reply_markup=keyboard_markup)
	except ApiTelegramException as E:
		if E.error_code == 429:
			raise E
		if E.description == SAME_MSG_CONTENT_ERROR:
			return
		logging.info(f"Exception during adding control buttons - {E}")


def extract_hashtags(post_data, main_channel_id):
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
		update_post_button_event(bot, call.message)
	elif callback_type == "R":
		show_subchannel_buttons(bot, call.message)


def show_subchannel_buttons(bot: telebot.TeleBot, post_data: telebot.types.Message):
	main_channel_id = post_data.chat.id

	keyboard_markup = generate_subchannel_buttons(main_channel_id, post_data)
	try:
		text, entities = utils.get_post_content(post_data)
		utils.edit_message_content(bot, post_data, text=text, entities=entities, reply_markup=keyboard_markup)
	except ApiTelegramException as E:
		if E.error_code == 429:
			raise E
		logging.info(f"Exception during adding subchannel buttons - {E}")


def change_state_button_event(bot: telebot.TeleBot, post_data: telebot.types.Message, new_state: bool):
	main_channel_id = post_data.chat.id

	hashtags, post_data = extract_hashtags(post_data, main_channel_id)
	if hashtags:
		hashtags[0] = OPENED_TAG if new_state else CLOSED_TAG

		rearrange_hashtags(bot, post_data, hashtags, main_channel_id)
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

		rearrange_hashtags(bot, post_data, hashtags, main_channel_id, original_post_data)
		forward_to_subchannel(bot, post_data, hashtags)
		add_control_buttons(bot, post_data, hashtags)


def update_post_button_event(bot: telebot.TeleBot, post_data: telebot.types.Message):
	forward_and_add_inline_keyboard(bot, post_data)


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


def forward_and_add_inline_keyboard(bot: telebot.TeleBot, post_data: telebot.types.Message, use_default_user: bool = False):
	main_channel_id = post_data.chat.id

	original_post_data = copy.deepcopy(post_data)

	hashtags, post_data = extract_hashtags(post_data, main_channel_id)
	if hashtags:
		if hashtags[1] is None and hashtags[2] is None and use_default_user:
			hashtags = insert_default_user_hashtags(main_channel_id, hashtags)

		rearrange_hashtags(bot, post_data, hashtags, main_channel_id, original_post_data)
		forward_to_subchannel(bot, post_data, hashtags)
		add_control_buttons(bot, post_data, hashtags)


def rearrange_hashtags(bot: telebot.TeleBot, post_data: telebot.types.Message, hashtags: List[str], main_channel_id: int,
					   original_post_data: telebot.types.Message = None):
	post_data = insert_hashtags(post_data, hashtags)

	if original_post_data and is_post_data_equal(post_data, original_post_data):
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

	for hashtag in hashtags[::-1]:
		if hashtag is None:
			continue
		text, entities = insert_hashtag_in_post(text, entities, "#" + hashtag, hashtags_start_position)

	utils.set_post_content(post_data, text, entities)

	return post_data


def is_post_data_equal(post_data1: telebot.types.Message, post_data2: telebot.types.Message):
	text1, entities1 = utils.get_post_content(post_data1)
	text2, entities2 = utils.get_post_content(post_data2)

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

