import logging
import copy

from telebot.apihelper import ApiTelegramException
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, MessageEntity

import post_link_utils
import utils

PRIORITY_TAG = "п"
OPENED_TAG = "о"
CLOSED_TAG = "х"

CALLBACK_PREFIX = "FWRD"

CHECK_MARK_CHARACTER = "\U00002705"

MAX_BUTTONS_IN_ROW = 3


def forward_to_subchannel(bot, post_data, subchannel_data, hashtags):
	if OPENED_TAG not in hashtags:
		return

	main_channel_id = post_data.chat.id
	message_id = post_data.message_id

	subchannel_id = get_subchannel_id_from_hashtags(main_channel_id, subchannel_data, hashtags)
	if not subchannel_id:
		logging.warning("Subchannel not found in config file")
		return

	try:
		copied_message = bot.copy_message(chat_id=subchannel_id, message_id=message_id, from_chat_id=main_channel_id)
		logging.info("Successfully forwarded post to subchannel by tags: " + str(hashtags))
	except ApiTelegramException as E:
		if E.error_code == 429:
			raise E
		logging.warning("Exception during forwarding post to subchannel {0} - {1}".format(hashtags, E))
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
		if hashtag.startswith(PRIORITY_TAG):
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


def generate_control_buttons(previous_subchannel_id, previous_message_id, hashtags):
	close_ticket_callback_data = utils.create_callback_str(CALLBACK_PREFIX, "X", previous_subchannel_id, previous_message_id)
	close_ticket_button = InlineKeyboardButton("#x", callback_data=close_ticket_callback_data)

	open_ticket_callback_data = utils.create_callback_str(CALLBACK_PREFIX, "O", previous_subchannel_id, previous_message_id)
	open_ticket_button = InlineKeyboardButton("#o", callback_data=open_ticket_callback_data)

	if OPENED_TAG not in hashtags:
		close_ticket_button.text += CHECK_MARK_CHARACTER
		close_ticket_button.callback_data = "_"
	else:
		open_ticket_button.text += CHECK_MARK_CHARACTER
		open_ticket_button.callback_data = "_"

	reassign_callback_data = utils.create_callback_str(CALLBACK_PREFIX, "R", previous_subchannel_id, previous_message_id)
	reassign_button = InlineKeyboardButton("Reassign", callback_data=reassign_callback_data)

	save_callback_data = utils.create_callback_str(CALLBACK_PREFIX, "S", previous_subchannel_id, previous_message_id)
	save_button = InlineKeyboardButton("Save", callback_data=save_callback_data)

	buttons = [
		reassign_button,
		close_ticket_button,
		open_ticket_button,
		save_button
	]

	keyboard_markup = InlineKeyboardMarkup([buttons])
	return keyboard_markup


def generate_subchannel_buttons(main_channel_id, subchannel_data, post_data, previous_subchannel_id, previous_message_id):
	forwarding_data = get_subchannels_forwarding_data(subchannel_data, main_channel_id)

	_, user_hashtag_index, priority_hashtag_index = find_hashtag_indexes(post_data, subchannel_data, main_channel_id)
	current_subchannel_name = ""

	if user_hashtag_index is not None:
		entity = post_data.entities[user_hashtag_index]
		current_subchannel_name += post_data.text[entity.offset + 1:entity.offset + entity.length]
		if priority_hashtag_index is not None:
			entity = post_data.entities[priority_hashtag_index]
			priority = post_data.text[entity.offset + 1 + len(PRIORITY_TAG):entity.offset + entity.length]
			current_subchannel_name += " " + priority

	subchannel_buttons = []
	for subchannel_name in forwarding_data:
		callback_str = utils.create_callback_str(CALLBACK_PREFIX, "SUB", previous_subchannel_id, previous_message_id, subchannel_name)
		btn = InlineKeyboardButton("#" + subchannel_name, callback_data=callback_str)
		if subchannel_name == current_subchannel_name:
			btn.text += CHECK_MARK_CHARACTER
			btn.callback_data = utils.create_callback_str(CALLBACK_PREFIX, "S", previous_subchannel_id, previous_message_id)
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


def add_control_buttons(bot, post_data, subchannel_id, copied_message_id, hashtags):
	main_channel_id = post_data.chat.id

	keyboard_markup = generate_control_buttons(subchannel_id, copied_message_id, hashtags)
	try:
		bot.edit_message_text(chat_id=main_channel_id, message_id=post_data.message_id, text=post_data.text, entities=post_data.entities, reply_markup=keyboard_markup)
	except ApiTelegramException as E:
		if E.error_code == 429:
			raise E
		logging.info("Exception during adding control buttons - " + str(E))


def extract_hashtags(post_data, subchannel_data, main_channel_id):
	status_tag_index, user_tag_index, priority_tag_index = find_hashtag_indexes(post_data, subchannel_data, main_channel_id)

	if status_tag_index is None or user_tag_index is None or priority_tag_index is None:
		return [None, None]

	extracted_hashtags = [
		post_data.entities[status_tag_index],
		post_data.entities[user_tag_index],
		post_data.entities[priority_tag_index]
	]

	for i in range(len(extracted_hashtags)):
		entity_offset = extracted_hashtags[i].offset
		entity_length = extracted_hashtags[i].length
		extracted_hashtags[i] = post_data.text[entity_offset + 1:entity_offset + entity_length]

	entities_to_remove = [status_tag_index, user_tag_index, priority_tag_index]
	entities_to_remove.sort(reverse=True)

	for entity_index in entities_to_remove:
		post_data = cut_entity_from_post(post_data, entity_index)

	return extracted_hashtags, post_data


def find_hashtag_indexes(post_data, subchannel_data, main_channel_id):
	status_tag_index = None
	user_tag_index = None
	priority_tag_index = None

	for entity_index in reversed(range(len(post_data.entities))):
		entity = post_data.entities[entity_index]
		if entity.type == "hashtag":
			tag = post_data.text[entity.offset + 1:entity.offset + entity.length]
			if tag == OPENED_TAG or tag == CLOSED_TAG:
				status_tag_index = entity_index
				continue

			main_channel_users = subchannel_data[str(main_channel_id)]
			if tag in main_channel_users:
				user_tag_index = entity_index
				continue

			if tag.startswith(PRIORITY_TAG):
				priority_tag_index = entity_index

	return status_tag_index, user_tag_index, priority_tag_index


def handle_callback(bot, call, subchannel_data):
	callback_data = call.data[len(CALLBACK_PREFIX) + 1:]
	callback_data_list = callback_data.split(",")
	callback_type, subchannel_id, message_id = callback_data_list[:3]
	other_data = callback_data_list[3:]

	if callback_type != "R" and subchannel_id != "None" and message_id != "None":
		try:
			bot.delete_message(chat_id=subchannel_id, message_id=message_id)
		except ApiTelegramException as E:
			if E.error_code == 429:
				raise E
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
	elif callback_type == "R":
		show_subchannel_buttons(bot, subchannel_data, call.message, subchannel_id, message_id)


def show_subchannel_buttons(bot, subchannel_data, post_data, subchannel_id, message_id):
	main_channel_id = post_data.chat.id

	keyboard_markup = generate_subchannel_buttons(main_channel_id, subchannel_data, post_data, subchannel_id, message_id)
	try:
		bot.edit_message_text(chat_id=main_channel_id, message_id=post_data.message_id, text=post_data.text, entities=post_data.entities, reply_markup=keyboard_markup)
	except ApiTelegramException as E:
		if E.error_code == 429:
			raise E
		logging.info("Exception during adding subchannel buttons - " + str(E))


def change_state_button_event(bot, subchannel_data, post_data, new_state):
	main_channel_id = post_data.chat.id

	hashtags, post_data = extract_hashtags(post_data, subchannel_data, main_channel_id)
	if hashtags:
		hashtags[0] = OPENED_TAG if new_state else CLOSED_TAG

		rearrange_hashtags(bot, post_data, hashtags, main_channel_id)
		forwarded_data = forward_to_subchannel(bot, post_data, subchannel_data, hashtags)
		forwarded_to, copied_message_id = forwarded_data if forwarded_data else [None, None]
		add_control_buttons(bot, post_data, forwarded_to, copied_message_id, hashtags)


def change_subchannel_button_event(bot, subchannel_data, post_data, new_subchannel_name):
	main_channel_id = post_data.chat.id

	subchannel_user, subchannel_priority = new_subchannel_name.split(" ")

	original_post_data = copy.deepcopy(post_data)
	hashtags, post_data = extract_hashtags(post_data, subchannel_data, main_channel_id)

	if hashtags:
		hashtags[1] = subchannel_user
		hashtags[2] = PRIORITY_TAG + subchannel_priority

		rearrange_hashtags(bot, post_data, hashtags, main_channel_id, original_post_data)
		forwarded_data = forward_to_subchannel(bot, post_data, subchannel_data, hashtags)
		forwarded_to, copied_message_id = forwarded_data if forwarded_data else [None, None]
		add_control_buttons(bot, post_data, forwarded_to, copied_message_id, hashtags)


def update_post_button_event(bot, subchannel_data, post_data):
	forward_and_add_inline_keyboard(bot, post_data, subchannel_data)


def insert_hashtag_in_post(post_data, hashtag, position):
	post_data.text = post_data.text[:position] + hashtag + " " + post_data.text[position:]

	for entity in post_data.entities:
		if entity.offset >= position:
			entity.offset += len(hashtag) + 1  # +1 because of space

	hashtag_entity = MessageEntity(type="hashtag", offset=position, length=len(hashtag))
	post_data.entities.append(hashtag_entity)
	post_data.entities.sort(key=lambda e: e.offset)

	return post_data


def cut_entity_from_post(post_data, entity_index):
	entity_to_cut = post_data.entities[entity_index]
	if entity_to_cut.offset != 0 and post_data.text[entity_to_cut.offset - 1] == " ":
		entity_to_cut.offset -= 1
		entity_to_cut.length += 1
	if len(post_data.text) > entity_to_cut.offset + entity_to_cut.length:
		character_after_entity = post_data.text[entity_to_cut.offset + entity_to_cut.length]
		if character_after_entity == " ":
			entity_to_cut.length += 1

	text = post_data.text
	post_data.text = text[:entity_to_cut.offset] + " " + text[entity_to_cut.offset + entity_to_cut.length:]
	offsetted_entities = utils.offset_entities(post_data.entities[entity_index + 1:], -entity_to_cut.length + 1)
	post_data.entities[entity_index:] = offsetted_entities

	return post_data


def forward_and_add_inline_keyboard(bot, post_data, subchannel_data):
	main_channel_id = post_data.chat.id

	original_post_data = copy.deepcopy(post_data)

	hashtags, post_data = extract_hashtags(post_data, subchannel_data, main_channel_id)
	if hashtags:
		rearrange_hashtags(bot, post_data, hashtags, main_channel_id, original_post_data)
		forwarded_data = forward_to_subchannel(bot, post_data, subchannel_data, hashtags)
		forwarded_to, copied_message_id = forwarded_data if forwarded_data else [None, None]
		add_control_buttons(bot, post_data, forwarded_to, copied_message_id, hashtags)


def rearrange_hashtags(bot, post_data, hashtags, main_channel_id, original_post_data=None):
	post_data = insert_hashtags(post_data, hashtags)

	if original_post_data and is_post_data_equal(post_data, original_post_data):
		return

	try:
		bot.edit_message_text(chat_id=main_channel_id, message_id=post_data.message_id, text=post_data.text,
							  entities=post_data.entities, reply_markup=post_data.reply_markup)
	except ApiTelegramException as E:
		if E.error_code == 429:
			raise E
		logging.info("Exception during rearranging hashtags - " + str(E))
		return


def insert_hashtags(post_data, hashtags):
	hashtags_start_position = 0
	if post_data.entities[0].type == "text_link" and post_data.entities[0].offset == 0:
		hashtags_start_position += post_data.entities[0].length + len(post_link_utils.LINK_ENDING)

	for hashtag in hashtags[::-1]:
		post_data = insert_hashtag_in_post(post_data, "#" + hashtag, hashtags_start_position)

	return post_data


def is_post_data_equal(post_data1, post_data2):
	if post_data1.text != post_data2.text:
		return False

	if len(post_data1.entities) != len(post_data1.entities):
		return False

	for entity_i in range(len(post_data1.entities)):
		e1 = post_data1.entities[entity_i]
		e2 = post_data2.entities[entity_i]
		if e1.type != e2.type or e1.offset != e2.offset or e1.url != e2.url or e1.length != e2.length:
			return False

	return True

