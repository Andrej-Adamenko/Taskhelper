import logging

from telebot.apihelper import ApiTelegramException
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, MessageEntity

import utils

PRIORITY_TAG = "п"
OPENED_TAG = "о"
CLOSED_TAG = "х"

CALLBACK_PREFIX = "FWRD"

CHECK_MARK_CHARACTER = "\U00002705"


def parse_hashtags(post_data):
	if not post_data.entities:
		return []

	hashtags = []

	for entity in post_data.entities:
		if entity.type != "hashtag":
			continue
		hashtag_name = post_data.text[entity.offset + 1:entity.offset + entity.length]
		hashtags.append(hashtag_name)

	return hashtags


def forward_to_subchannel(bot, post_data, subchannel_data, hashtags):
	if OPENED_TAG not in hashtags:
		return

	main_channel_id = post_data.chat.id
	message_id = post_data.message_id

	subchannel_id = get_subchannel_id_from_hashtags(main_channel_id, subchannel_data, hashtags)
	if subchannel_id:
		try:
			copied_message = bot.copy_message(chat_id=subchannel_id, message_id=message_id, from_chat_id=main_channel_id)
		except ApiTelegramException:
			return
		return [subchannel_id, copied_message.message_id]


def get_subchannel_id_from_hashtags(main_channel_id, subchannel_data, hashtags):
	main_channel_id_str = str(main_channel_id)
	if main_channel_id_str not in subchannel_data:
		return

	priority = None
	user_priority_list = None

	subchannel_users = subchannel_data[main_channel_id_str]
	for user in subchannel_users:
		if user in hashtags:
			user_priority_list = subchannel_users[user]

	if not user_priority_list:
		return

	for hashtag in hashtags:
		if hashtag.startswith(PRIORITY_TAG) and len(hashtag) == 2:
			priority = hashtag[len(PRIORITY_TAG):]

	if priority not in user_priority_list:
		return

	return user_priority_list[priority]


def get_all_subchannel_ids(subchannel_data):
	subchannel_ids = []
	for main_channel_id in subchannel_data:
		channel_users = subchannel_data[main_channel_id]
		for user in channel_users:
			user_priorities = channel_users[user]
			for priority in user_priorities:
				subchannel_id = user_priorities[priority]
				subchannel_ids.append(subchannel_id)

	return subchannel_ids


def generate_control_buttons(main_channel_id, subchannel_data, subchannel_id, copied_message_id, hashtags):
	buttons = []

	forwarding_data = get_subchannels_forwarding_data(subchannel_data, main_channel_id)

	subchannel_buttons_row = []
	for subchannel_name in forwarding_data:
		callback_str = utils.create_callback_str(CALLBACK_PREFIX, "SUB", subchannel_id, copied_message_id, subchannel_name)
		btn = InlineKeyboardButton("#" + subchannel_name, callback_data=callback_str)
		hashtag_subchannel_id = get_subchannel_id_from_hashtags(main_channel_id, subchannel_data, hashtags)
		if forwarding_data[subchannel_name] == hashtag_subchannel_id:
			btn.text += CHECK_MARK_CHARACTER
			btn.callback_data = "_"  # no callback because this subchannel already selected
		subchannel_buttons_row.append(btn)

	status_buttons_row = [
		InlineKeyboardButton("#x", callback_data=utils.create_callback_str(CALLBACK_PREFIX,"X", subchannel_id, copied_message_id)),
		InlineKeyboardButton("#o", callback_data=utils.create_callback_str(CALLBACK_PREFIX,"O", subchannel_id, copied_message_id)),
		InlineKeyboardButton("Save", callback_data=utils.create_callback_str(CALLBACK_PREFIX,"S", subchannel_id, copied_message_id))
	]

	if OPENED_TAG not in hashtags:
		status_buttons_row[0].text += CHECK_MARK_CHARACTER
		status_buttons_row[0].callback_data = "_"
	else:
		status_buttons_row[1].text += CHECK_MARK_CHARACTER
		status_buttons_row[1].callback_data = "_"

	buttons.append(subchannel_buttons_row)
	buttons.append(status_buttons_row)

	keyboard_markup = InlineKeyboardMarkup(buttons)
	return keyboard_markup


def get_subchannels_forwarding_data(subchannel_data, main_channel_id):
	main_channel_id_str = str(main_channel_id)
	if main_channel_id_str not in subchannel_data:
		return {}

	forwarding_data = {}

	channel_users = subchannel_data[main_channel_id_str]
	for user in channel_users:
		user_priorities = channel_users[user]
		for priority in user_priorities:
			subchannel_id = user_priorities[priority]
			forwarding_data[user + " " + priority] = subchannel_id

	return forwarding_data


def add_control_buttons(bot, post_data, subchannel_data, subchannel_id, copied_message_id, hashtags):
	main_channel_id = post_data.chat.id
	if not is_hashtags_correct(hashtags, subchannel_data, main_channel_id):
		return
	keyboard_markup = generate_control_buttons(main_channel_id, subchannel_data, subchannel_id, copied_message_id, hashtags)
	try:
		bot.edit_message_text(chat_id=main_channel_id, message_id=post_data.message_id, text=post_data.text, entities=post_data.entities, reply_markup=keyboard_markup)
	except ApiTelegramException as E:
		logging.info("Exception during adding control buttons - " + str(E))


def is_hashtags_correct(hashtags, subchannel_data, main_channel_id):
	if hashtags[0] != OPENED_TAG and hashtags[0] != CLOSED_TAG:
		return False

	subchannel_id_by_tags = get_subchannel_id_from_hashtags(main_channel_id, subchannel_data, hashtags[1:3])
	if subchannel_id_by_tags is None:
		return False

	return True


def handle_callback(bot, call, subchannel_data):
	callback_data = call.data[len(CALLBACK_PREFIX) + 1:]
	callback_data_list = callback_data.split(",")
	callback_type, subchannel_id, message_id = callback_data_list[:3]
	other_data = callback_data_list[3:]

	if subchannel_id != "None" and message_id != "None":
		try:
			bot.delete_message(chat_id=subchannel_id, message_id=message_id)
		except ApiTelegramException as E:
			logging.info("Exception during delete_message - " + str(E))

	if callback_type == "SUB":
		subchannel_name = other_data[0]
		change_subchannel_button_event(bot, subchannel_data, call.message, subchannel_name)
	elif callback_type == "X":
		change_state_button_event(bot, subchannel_data, call.message, False)
	elif callback_type == "O":
		change_state_button_event(bot, subchannel_data, call.message, True)
	elif callback_type == "S":
		update_post_button_event(bot, subchannel_data, call.message)


def change_state_button_event(bot, subchannel_data, post_data, new_state):
	main_channel_id = post_data.chat.id

	hashtag_indexes = []
	i = 0
	for entity in post_data.entities:
		if entity.type == "hashtag":
			hashtag_indexes.append(i)
		i += 1

	first_hashtag_offset = post_data.entities[hashtag_indexes[0]].offset

	post_data = cut_entity_from_post(post_data, hashtag_indexes[0])

	state_tag = OPENED_TAG if new_state else CLOSED_TAG
	post_data = insert_hashtag_in_post(post_data, "#" + state_tag, first_hashtag_offset)

	hashtags = parse_hashtags(post_data)
	forwarded_to = copied_message_id = None
	if new_state:
		forwarded_data = forward_to_subchannel(bot, post_data, subchannel_data, hashtags)
		if forwarded_data:
			forwarded_to, copied_message_id = forwarded_data

	keyboard_markup = generate_control_buttons(main_channel_id, subchannel_data, forwarded_to, copied_message_id, hashtags)

	bot.edit_message_text(chat_id=main_channel_id, message_id=post_data.message_id, text=post_data.text,
						  entities=post_data.entities, reply_markup=keyboard_markup)


def change_subchannel_button_event(bot, subchannel_data, post_data, new_subchannel_name):
	main_channel_id = post_data.chat.id

	subchannel_user, subchannel_priority = new_subchannel_name.split(" ")

	hashtag_indexes = []
	i = 0
	for entity in post_data.entities:
		if entity.type == "hashtag":
			hashtag_indexes.append(i)
		i += 1

	second_hashtag_offset = post_data.entities[hashtag_indexes[1]].offset

	post_data = cut_entity_from_post(post_data, hashtag_indexes[1])
	post_data = cut_entity_from_post(post_data, hashtag_indexes[2] - 1)

	priority_str = "#" + PRIORITY_TAG + subchannel_priority
	post_data = insert_hashtag_in_post(post_data, priority_str, second_hashtag_offset + 1)

	post_data = insert_hashtag_in_post(post_data, "#" + subchannel_user, second_hashtag_offset)

	hashtags = parse_hashtags(post_data)
	forwarded_data = forward_to_subchannel(bot, post_data, subchannel_data, hashtags)
	forwarded_to, copied_message_id = forwarded_data if forwarded_data else [None, None]
	keyboard_markup = generate_control_buttons(main_channel_id, subchannel_data, forwarded_to, copied_message_id, hashtags)

	bot.edit_message_text(chat_id=main_channel_id, message_id=post_data.message_id, text=post_data.text,
						  entities=post_data.entities, reply_markup=keyboard_markup)


def update_post_button_event(bot, subchannel_data, post_data):
	hashtags = parse_hashtags(post_data)
	forwarded_data = forward_to_subchannel(bot, post_data, subchannel_data, hashtags)
	forwarded_to, copied_message_id = forwarded_data if forwarded_data else [None, None]
	add_control_buttons(bot, post_data, subchannel_data, forwarded_to, copied_message_id, hashtags)


def insert_hashtag_in_post(post_data, hashtag, position):
	post_data.text = post_data.text[:position] + hashtag + post_data.text[position:]

	for entity in post_data.entities:
		if entity.offset > position:
			entity.offset += len(hashtag)

	hashtag_entity = MessageEntity(type="hashtag", offset=position, length=len(hashtag))
	post_data.entities.append(hashtag_entity)

	return post_data


def cut_entity_from_post(post_data, entity_index):
	entity_to_cut = post_data.entities[entity_index]
	text = post_data.text
	post_data.text = text[:entity_to_cut.offset] + text[entity_to_cut.offset + entity_to_cut.length:]
	offsetted_entities = utils.offset_entities(post_data.entities[entity_index + 1:], -entity_to_cut.length)
	post_data.entities[entity_index:] = offsetted_entities

	return post_data
