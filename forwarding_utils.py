import logging
import copy
from typing import List

import telebot
from telebot.apihelper import ApiTelegramException
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

import channel_manager
import comment_utils
import config_utils
import daily_reminder
import db_utils
import hashtag_utils
import scheduled_messages_utils
import user_utils
import utils
import hashtag_data as hashtag_data_utils

from hashtag_data import HashtagData
from config_utils import DISCUSSION_CHAT_DATA

CALLBACK_PREFIX = "FWRD"


class CB_TYPES:
	CHANGE_SUBCHANNEL = "SUB"
	CHANGE_PRIORITY = "PR"
	CLOSE = "X"
	OPEN = "O"
	SAVE = "S"
	SHOW_SUBCHANNELS = "R"
	SHOW_PRIORITIES = "P"
	SHOW_CC = "CC"
	TOGGLE_CC = "TCC"


def get_message_content_by_id(bot: telebot.TeleBot, chat_id: int, message_id: int):
	try:
		forwarded_message = bot.forward_message(chat_id=config_utils.DUMP_CHAT_ID, from_chat_id=chat_id,
												message_id=message_id)
		bot.delete_message(chat_id=config_utils.DUMP_CHAT_ID, message_id=forwarded_message.message_id)
	except ApiTelegramException as E:
		if E.error_code == 429:
			raise E
		return

	return forwarded_message


def get_unchanged_posts(bot: telebot.TeleBot, post_data: telebot.types.Message, subchannel_ids: List[int]):
	main_channel_id = post_data.chat.id
	message_id = post_data.message_id

	forwarded_messages = db_utils.get_copied_message_data(message_id, main_channel_id)
	unchanged_posts = {}
	for forwarded_message in forwarded_messages:
		forwarded_msg_id, forwarded_channel_id = forwarded_message
		forwarded_msg_data = get_message_content_by_id(bot, forwarded_channel_id, forwarded_msg_id)

		in_subchannels = forwarded_channel_id in subchannel_ids
		if forwarded_msg_data and utils.is_post_data_equal(forwarded_msg_data, post_data) and in_subchannels:
			unchanged_posts[forwarded_channel_id] = forwarded_msg_id  # ignore unchanged posts
			continue
		try:
			delete_forwarded_message(bot, forwarded_channel_id, forwarded_msg_id)
		except ApiTelegramException as E:
			if E.error_code == 429:
				raise E
			elif E.description.endswith("message to delete not found"):
				db_utils.delete_copied_message(forwarded_msg_id, forwarded_channel_id)
			logging.info(f"Exception during delete_message [{forwarded_msg_id}, {forwarded_channel_id}] - {E}")
	return unchanged_posts


def forward_to_subchannel(bot: telebot.TeleBot, post_data: telebot.types.Message, hashtag_data: HashtagData):
	main_channel_id = post_data.chat.id
	main_message_id = post_data.message_id

	comment_utils.update_comment(bot, post_data, hashtag_data)
	daily_reminder.update_ticket_data(main_message_id, main_channel_id, hashtag_data)

	subchannel_ids = get_subchannel_ids_from_hashtags(main_channel_id, main_message_id, hashtag_data)

	unchanged_posts = get_unchanged_posts(bot, post_data, list(subchannel_ids))

	if hashtag_data.is_closed():
		return

	if not subchannel_ids:
		logging.warning(f"Subchannels not found {hashtag_data.get_hashtag_list()}, {main_channel_id}")
		return

	for subchannel_id in subchannel_ids:
		if subchannel_id in unchanged_posts:
			keyboard_markup = generate_control_buttons(hashtag_data, post_data)
			utils.edit_message_keyboard(bot, post_data, keyboard_markup, chat_id=subchannel_id, message_id=unchanged_posts[subchannel_id])
			continue

		try:
			copied_message = bot.copy_message(chat_id=subchannel_id, message_id=main_message_id, from_chat_id=main_channel_id)
			logging.info(f"Successfully forwarded post [{main_message_id}, {main_channel_id}] to {subchannel_id} subchannel by tags: {hashtag_data.get_hashtag_list()}")
		except ApiTelegramException as E:
			if E.error_code == 429:
				raise E
			if E.error_code == 403 and E.description.endswith(utils.KICKED_FROM_CHANNEL_ERROR):
				db_utils.delete_individual_channel(subchannel_id)
			logging.warning(f"Exception during forwarding post to subchannel {hashtag_data.get_hashtag_list()} - {E}")
			continue

		keyboard_markup = generate_control_buttons(hashtag_data, post_data)
		utils.edit_message_keyboard(bot, post_data, keyboard_markup, chat_id=subchannel_id, message_id=copied_message.message_id)

		db_utils.insert_copied_message(main_message_id, main_channel_id, copied_message.message_id, subchannel_id)


def delete_forwarded_message(bot: telebot.TeleBot, chat_id: int, message_id: int):
	try:
		utils.delete_message(bot, chat_id=chat_id, message_id=message_id)
		db_utils.delete_copied_message(message_id, chat_id)
	except ApiTelegramException as E:
		if E.description.endswith(utils.MSG_CANT_BE_DELETED_ERROR):
			oldest_message_data = None
			oldest_message_id = None
			while oldest_message_data is None:
				oldest_message_id = db_utils.get_oldest_copied_message(chat_id)
				if oldest_message_id is None:
					break

				oldest_message_data = get_message_content_by_id(bot, chat_id, oldest_message_id)
				if oldest_message_data is None:
					db_utils.delete_copied_message(oldest_message_id, chat_id)
					logging.info(f"Message {[oldest_message_id, chat_id]} doesn't exists, deleted from db")
					continue

			main_data = db_utils.get_main_message_from_copied(oldest_message_id, chat_id)
			if main_data is None:
				bot.edit_message_text(text=config_utils.TO_DELETE_MSG_TEXT, chat_id=chat_id, message_id=message_id)
				return
			main_message_id, main_channel_id = main_data

			msg_to_delete_data = get_message_content_by_id(bot, chat_id, message_id)

			if oldest_message_data:
				if oldest_message_id != message_id:
					oldest_message_data.message_id = main_message_id
					oldest_message_data.chat.id = main_channel_id

					hashtag_data = HashtagData(oldest_message_data, main_channel_id)
					keyboard = generate_control_buttons(hashtag_data, oldest_message_data)
					text, entities = utils.get_post_content(oldest_message_data)

					utils.edit_message_content(bot, msg_to_delete_data, chat_id=chat_id, message_id=message_id,
					                           reply_markup=keyboard, text=text, entities=entities)
					db_utils.delete_copied_message(message_id, chat_id)
					db_utils.update_copied_message_id(oldest_message_id, chat_id, message_id)
				else:
					db_utils.delete_copied_message(message_id, chat_id)

				utils.edit_message_content(bot, oldest_message_data, chat_id=chat_id, message_id=oldest_message_id,
				                           text=config_utils.TO_DELETE_MSG_TEXT, entities=None)
			else:
				db_utils.delete_copied_message(oldest_message_id, chat_id)
				utils.edit_message_content(bot, msg_to_delete_data, chat_id=chat_id, message_id=message_id,
				                           text=config_utils.TO_DELETE_MSG_TEXT, entities=None)
		elif E.description.endswith(utils.KICKED_FROM_CHANNEL_ERROR):
			db_utils.delete_copied_message(message_id, chat_id)


def get_subchannel_ids_from_hashtags(main_channel_id: int, main_message_id: int, hashtag_data: HashtagData):
	subchannel_ids = set()
	if hashtag_data.is_scheduled():
		scheduled_users_subchannels = get_scheduled_subchannels_from_hashtags(main_channel_id, hashtag_data)
		if scheduled_users_subchannels:
			subchannel_ids.update(scheduled_users_subchannels)
	elif hashtag_data.is_opened():
		assigned_user_subchannels = get_assigned_user_channel_from_hashtags(main_channel_id, hashtag_data)
		if assigned_user_subchannels:
			subchannel_ids.update(assigned_user_subchannels)

		followed_users_subchannels = get_followed_user_channels_from_hashtags(main_channel_id, hashtag_data)
		if followed_users_subchannels:
			subchannel_ids.update(followed_users_subchannels)

	creator_subchannels = get_creator_channel_id(main_channel_id, main_message_id, hashtag_data)
	if creator_subchannels:
		subchannel_ids.update(creator_subchannels)

	return subchannel_ids


def get_assigned_user_channel_from_hashtags(main_channel_id: int, hashtag_data: HashtagData):
	user_tag = hashtag_data.get_assigned_user()
	priority = hashtag_data.get_priority_number_or_default()
	if not user_tag or not priority:
		return

	return db_utils.get_individual_channel_id_by_tag(
		main_channel_id, user_tag, priority, channel_manager.CHANNEL_TYPES.ASSIGNED
	)


def get_followed_user_channels_from_hashtags(main_channel_id: int, hashtag_data: HashtagData):
	user_tags = hashtag_data.get_followed_users()
	priority = hashtag_data.get_priority_number_or_default()
	if not user_tags or not priority:
		return

	channel_ids = []
	for user_tag in user_tags:
		user_channel_ids = db_utils.get_individual_channel_id_by_tag(
			main_channel_id, user_tag, priority, channel_manager.CHANNEL_TYPES.FOLLOWED
		)

		if user_channel_ids:
			channel_ids += user_channel_ids

	return channel_ids


def get_creator_channel_id(main_channel_id: int, main_message_id: int, hashtag_data: HashtagData):
	priority = hashtag_data.get_priority_number_or_default()
	user_id = db_utils.get_main_message_sender(main_channel_id, main_message_id)
	if not user_id:
		return

	return db_utils.get_individual_channel_id_by_user_id(
		main_channel_id, user_id, priority, channel_manager.CHANNEL_TYPES.CREATED
	)


def get_scheduled_subchannels_from_hashtags(main_channel_id: int, hashtag_data: HashtagData):
	user_tags = hashtag_data.get_all_users()
	priority = hashtag_data.get_priority_number_or_default()
	if not user_tags or not priority:
		return

	channel_ids = []
	for user_tag in user_tags:
		user_channel_ids = db_utils.get_individual_channel_id_by_tag(
			main_channel_id, user_tag, priority, channel_manager.CHANNEL_TYPES.SCHEDULED
		)

		if user_channel_ids:
			channel_ids += user_channel_ids

	return channel_ids


def generate_control_buttons(hashtag_data: HashtagData, post_data: telebot.types.Message):
	main_channel_id = post_data.chat.id
	main_message_id = post_data.message_id

	if hashtag_data.is_opened():
		state_switch_callback_data = utils.create_callback_str(CALLBACK_PREFIX, CB_TYPES.CLOSE)
		state_btn_text = config_utils.BUTTON_TEXTS["OPENED_TICKET"]
		state_switch_button = InlineKeyboardButton(state_btn_text, callback_data=state_switch_callback_data)
	elif hashtag_data.is_scheduled():
		state_switch_callback_data = utils.create_callback_str(CALLBACK_PREFIX, CB_TYPES.CLOSE)
		state_btn_text = config_utils.BUTTON_TEXTS["OPENED_TICKET"]
		state_switch_button = InlineKeyboardButton(state_btn_text, callback_data=state_switch_callback_data)
	else:
		state_switch_callback_data = utils.create_callback_str(CALLBACK_PREFIX, CB_TYPES.OPEN)
		state_btn_text = config_utils.BUTTON_TEXTS["CLOSED_TICKET"]
		state_switch_button = InlineKeyboardButton(state_btn_text, callback_data=state_switch_callback_data)

	reassign_callback_data = utils.create_callback_str(CALLBACK_PREFIX, CB_TYPES.SHOW_SUBCHANNELS)
	current_user = hashtag_data.get_assigned_user() or "-"
	reassign_button_text = config_utils.BUTTON_TEXTS["ASSIGNED_USER_PREFIX"] + " " + current_user
	reassign_button = InlineKeyboardButton(reassign_button_text, callback_data=reassign_callback_data)

	priority_callback_data = utils.create_callback_str(CALLBACK_PREFIX, CB_TYPES.SHOW_PRIORITIES)
	current_priority = hashtag_data.get_priority_number() or "-"

	priority_text = current_priority
	if current_priority in config_utils.BUTTON_TEXTS["PRIORITIES"]:
		priority_text = config_utils.BUTTON_TEXTS["PRIORITIES"][current_priority]
	priority_button = InlineKeyboardButton(priority_text, callback_data=priority_callback_data)

	cc_callback_data = utils.create_callback_str(CALLBACK_PREFIX, CB_TYPES.SHOW_CC)
	cc_button = InlineKeyboardButton(config_utils.BUTTON_TEXTS["CC"], callback_data=cc_callback_data)

	schedule_button = scheduled_messages_utils.generate_schedule_button()

	buttons = [
		state_switch_button,
		reassign_button,
		cc_button,
		priority_button,
		schedule_button
	]

	main_channel_id_str = str(main_channel_id)
	if main_channel_id_str in DISCUSSION_CHAT_DATA and DISCUSSION_CHAT_DATA[main_channel_id_str] is not None:
		discussion_chat_id = DISCUSSION_CHAT_DATA[main_channel_id_str]
		discussion_message_id = db_utils.get_discussion_message_id(main_message_id, main_channel_id)
		if discussion_message_id:
			discussion_chat_id_str = str(discussion_chat_id)[4:]
			comments_url = f"tg://privatepost?channel={discussion_chat_id_str}&post={discussion_message_id}&thread={discussion_message_id}"
			comments_amount_text = f"({db_utils.get_comments_count(discussion_message_id, discussion_chat_id)})"
			comments_button = InlineKeyboardButton(comments_amount_text, url=comments_url)
			buttons.append(comments_button)

	keyboard_markup = InlineKeyboardMarkup([buttons])
	return keyboard_markup


def generate_subchannel_buttons(post_data: telebot.types.Message):
	main_channel_id = post_data.chat.id

	forwarding_data = get_subchannels_forwarding_data(main_channel_id)

	hashtag_data = HashtagData(post_data, main_channel_id)
	current_subchannel = hashtag_data.get_assigned_user() or ""
	current_priority = hashtag_data.get_priority_number() or ""
	current_subchannel_name = current_subchannel + " " + current_priority

	subchannel_buttons = []
	for subchannel_name in forwarding_data:
		callback_str = utils.create_callback_str(CALLBACK_PREFIX, CB_TYPES.CHANGE_SUBCHANNEL, subchannel_name)
		btn = InlineKeyboardButton("#" + subchannel_name, callback_data=callback_str)
		if subchannel_name == current_subchannel_name:
			btn.text += config_utils.BUTTON_TEXTS["CHECK"]
			btn.callback_data = utils.create_callback_str(CALLBACK_PREFIX, CB_TYPES.SAVE)
		subchannel_buttons.append(btn)

	rows = utils.place_buttons_in_rows(subchannel_buttons)

	keyboard_markup = InlineKeyboardMarkup(rows)
	return keyboard_markup


def generate_priority_buttons(post_data: telebot.types.Message):
	main_channel_id = post_data.chat.id

	hashtag_data = HashtagData(post_data, main_channel_id)
	current_priority = hashtag_data.get_priority_number()

	priority_buttons = []

	for priority in hashtag_data_utils.POSSIBLE_PRIORITIES:
		callback_str = utils.create_callback_str(CALLBACK_PREFIX, CB_TYPES.CHANGE_PRIORITY, priority)
		btn = InlineKeyboardButton(priority, callback_data=callback_str)
		if priority == current_priority:
			btn.text += config_utils.BUTTON_TEXTS["CHECK"]
			btn.callback_data = utils.create_callback_str(CALLBACK_PREFIX, CB_TYPES.SAVE)
		priority_buttons.append(btn)

	rows = utils.place_buttons_in_rows(priority_buttons)

	keyboard_markup = InlineKeyboardMarkup(rows)
	return keyboard_markup


def generate_cc_buttons(post_data: telebot.types.Message):
	main_channel_id = post_data.chat.id

	hashtag_data = HashtagData(post_data, main_channel_id)
	current_subchannel_user = hashtag_data.get_assigned_user()
	followed_users = hashtag_data.get_followed_users()

	main_channel_user_tags = db_utils.get_main_channel_user_tags(main_channel_id)

	if not main_channel_user_tags:
		return

	subchannel_buttons = []
	for user_tag in main_channel_user_tags:
		if user_tag == current_subchannel_user:
			continue
		callback_str = utils.create_callback_str(CALLBACK_PREFIX, CB_TYPES.TOGGLE_CC, user_tag)
		btn = InlineKeyboardButton("#" + user_tag, callback_data=callback_str)
		if user_tag in followed_users:
			btn.text += config_utils.BUTTON_TEXTS["CHECK"]

		subchannel_buttons.append(btn)

	rows = utils.place_buttons_in_rows(subchannel_buttons)

	keyboard_markup = InlineKeyboardMarkup(rows)
	return keyboard_markup


def get_subchannels_forwarding_data(main_channel_id):
	user_tags = db_utils.get_main_channel_user_tags(main_channel_id)
	if not user_tags:
		return []

	forwarding_data = []
	for user_tag in user_tags:
		for priority in hashtag_data_utils.POSSIBLE_PRIORITIES:
			forwarding_data.append(f"{user_tag} {priority}")

	return forwarding_data


def add_control_buttons(bot: telebot.TeleBot, post_data: telebot.types.Message, hashtag_data: HashtagData):
	keyboard_markup = generate_control_buttons(hashtag_data, post_data)
	utils.edit_message_keyboard(bot, post_data, keyboard_markup)


def handle_callback(bot: telebot.TeleBot, call: telebot.types.CallbackQuery, current_channel_id: int = None, current_message_id: int = None):
	callback_type, other_data = utils.parse_callback_str(call.data)

	if callback_type == CB_TYPES.CHANGE_SUBCHANNEL:
		subchannel_name = other_data[0]
		change_subchannel_button_event(bot, call, subchannel_name)
	elif callback_type == CB_TYPES.CLOSE:
		change_state_button_event(bot, call, False)
	elif callback_type == CB_TYPES.OPEN:
		change_state_button_event(bot, call, True)
	elif callback_type == CB_TYPES.SAVE:
		forward_and_add_inline_keyboard(bot, call.message, force_forward=True)
	elif callback_type == CB_TYPES.SHOW_SUBCHANNELS:
		show_subchannel_buttons(bot, call.message, current_channel_id, current_message_id)
	elif callback_type == CB_TYPES.SHOW_PRIORITIES:
		show_priority_buttons(bot, call.message, current_channel_id, current_message_id)
	elif callback_type == CB_TYPES.CHANGE_PRIORITY:
		priority = other_data[0]
		change_priority_button_event(bot, call, priority)
	elif callback_type == CB_TYPES.SHOW_CC:
		show_cc_buttons(bot, call.message, current_channel_id, current_message_id)
	elif callback_type == CB_TYPES.TOGGLE_CC:
		user = other_data[0]
		toggle_cc_button_event(bot, call, user)


def show_subchannel_buttons(bot: telebot.TeleBot, post_data: telebot.types.Message, current_channel_id: int = None, current_message_id: int = None):
	subchannel_keyboard_markup = generate_subchannel_buttons(post_data)
	update_show_buttons(post_data, CB_TYPES.SHOW_SUBCHANNELS)
	post_data.reply_markup.keyboard += subchannel_keyboard_markup.keyboard

	utils.edit_message_keyboard(bot, post_data, chat_id=current_channel_id, message_id=current_message_id)


def show_priority_buttons(bot: telebot.TeleBot, post_data: telebot.types.Message, current_channel_id: int = None, current_message_id: int = None):
	priority_keyboard_markup = generate_priority_buttons(post_data)
	update_show_buttons(post_data, CB_TYPES.SHOW_PRIORITIES)
	post_data.reply_markup.keyboard += priority_keyboard_markup.keyboard

	utils.edit_message_keyboard(bot, post_data, chat_id=current_channel_id, message_id=current_message_id)


def show_cc_buttons(bot: telebot.TeleBot, post_data: telebot.types.Message, current_channel_id: int = None, current_message_id: int = None):
	cc_keyboard_markup = generate_cc_buttons(post_data)
	update_show_buttons(post_data, CB_TYPES.SHOW_CC)
	if cc_keyboard_markup:
		post_data.reply_markup.keyboard += cc_keyboard_markup.keyboard

	utils.edit_message_keyboard(bot, post_data, chat_id=current_channel_id, message_id=current_message_id)


def update_show_buttons(post_data: telebot.types.Message, current_button_type: str):
	main_channel_id = post_data.chat.id
	hashtag_data = HashtagData(post_data, main_channel_id)

	control_buttons = generate_control_buttons(hashtag_data, post_data)
	post_data.reply_markup.keyboard = control_buttons.keyboard

	for button in post_data.reply_markup.keyboard[0]:
		if button.callback_data is None:
			continue
		cb_type, _ = utils.parse_callback_str(button.callback_data)
		if cb_type == current_button_type:
			button.callback_data = utils.create_callback_str(CALLBACK_PREFIX, CB_TYPES.SAVE)


def change_state_button_event(bot: telebot.TeleBot, call: telebot.types.CallbackQuery, is_ticket_opened: bool):
	post_data = call.message
	main_channel_id = post_data.chat.id

	hashtag_data = HashtagData(post_data, main_channel_id)
	post_data = hashtag_data.get_post_data_without_hashtags()

	state_str = "opened" if is_ticket_opened else "closed"
	utils.add_comment_to_ticket(bot, post_data, f"{call.from_user.first_name} {state_str} the ticket.")

	hashtag_data.set_status_tag(is_ticket_opened)
	hashtag_data.set_scheduled_tag(None)

	if not is_ticket_opened:
		scheduled_messages_utils.cancel_scheduled_message(main_channel_id, post_data.message_id)

	rearrange_hashtags(bot, post_data, hashtag_data)
	for button in post_data.reply_markup.keyboard[0]:
		cb_type, _ = utils.parse_callback_str(button.callback_data)
		if cb_type == CB_TYPES.OPEN or cb_type == CB_TYPES.CLOSE:
			callback_type = CB_TYPES.CLOSE if is_ticket_opened else CB_TYPES.OPEN
			button.callback_data = utils.create_callback_str(CALLBACK_PREFIX, callback_type)
			state_btn_text = config_utils.BUTTON_TEXTS["OPENED_TICKET" if is_ticket_opened else "CLOSED_TICKET"]
			button.text = state_btn_text
			break
	add_control_buttons(bot, post_data, hashtag_data)
	forward_to_subchannel(bot, post_data, hashtag_data)


def change_subchannel_button_event(bot: telebot.TeleBot, call: telebot.types.CallbackQuery, new_subchannel_name: str):
	post_data = call.message
	main_channel_id = post_data.chat.id

	subchannel_user, subchannel_priority = new_subchannel_name.split(" ")

	original_post_data = copy.deepcopy(post_data)
	hashtag_data = HashtagData(post_data, main_channel_id)
	post_data = hashtag_data.get_post_data_without_hashtags()

	is_user_tag_changed = hashtag_data.get_assigned_user() != subchannel_user
	is_priority_tag_changed = hashtag_data.get_priority_number != subchannel_priority

	comment_text = f"{call.from_user.first_name} "
	if is_user_tag_changed and is_priority_tag_changed:
		comment_text += f"reassigned the ticket to {{USER}}, and changed its priority to {subchannel_priority}."
	elif is_user_tag_changed:
		comment_text += f"reassigned the ticket to {{USER}}."
	elif is_priority_tag_changed:
		comment_text += f"changed ticket's priority to {subchannel_priority}."

	if comment_text:
		text, entities = user_utils.insert_user_reference(main_channel_id, subchannel_user, comment_text)
		utils.add_comment_to_ticket(bot, post_data, text, entities)

	hashtag_data.assign_to_user(subchannel_user)

	hashtag_data.set_priority(subchannel_priority)

	rearrange_hashtags(bot, post_data, hashtag_data, original_post_data)
	add_control_buttons(bot, post_data, hashtag_data)
	forward_to_subchannel(bot, post_data, hashtag_data)


def change_priority_button_event(bot: telebot.TeleBot, call: telebot.types.CallbackQuery, new_priority: str):
	post_data = call.message
	main_channel_id = post_data.chat.id

	original_post_data = copy.deepcopy(post_data)
	hashtag_data = HashtagData(post_data, main_channel_id)
	post_data = hashtag_data.get_post_data_without_hashtags()

	utils.add_comment_to_ticket(bot, post_data, f"{call.from_user.first_name} changed ticket's priority to {new_priority}. ")
	hashtag_data.set_priority(new_priority)

	rearrange_hashtags(bot, post_data, hashtag_data, original_post_data)
	add_control_buttons(bot, post_data, hashtag_data)
	forward_to_subchannel(bot, post_data, hashtag_data)


def toggle_cc_button_event(bot: telebot.TeleBot, call: telebot.types.CallbackQuery, selected_user: str):
	post_data = call.message
	main_channel_id = post_data.chat.id

	original_post_data = copy.deepcopy(post_data)
	hashtag_data = HashtagData(post_data, main_channel_id)
	post_data = hashtag_data.get_post_data_without_hashtags()

	if selected_user in hashtag_data.get_followed_users():
		hashtag_data.remove_from_followers(selected_user)
		comment_text = f"{call.from_user.first_name} removed {{USER}} from ticket's followers."
	else:
		hashtag_data.add_to_followers(selected_user)
		comment_text = f"{call.from_user.first_name} added {{USER}} to ticket's followers."

	text, entities = user_utils.insert_user_reference(main_channel_id, selected_user, comment_text)
	utils.add_comment_to_ticket(bot, post_data, text, entities)

	rearrange_hashtags(bot, post_data, hashtag_data, original_post_data)
	show_cc_buttons(bot, post_data)
	forward_to_subchannel(bot, post_data, hashtag_data)


def forward_and_add_inline_keyboard(bot: telebot.TeleBot, post_data: telebot.types.Message,
									use_default_user: bool = False, force_forward: bool = False):
	main_channel_id = post_data.chat.id

	original_post_data = copy.deepcopy(post_data)

	hashtag_data = HashtagData(post_data, main_channel_id)
	post_data = hashtag_data.get_post_data_without_hashtags()
	assigned_user = hashtag_data.get_assigned_user()
	priority = hashtag_data.get_priority_number()
	if assigned_user is None and priority is None and use_default_user:
		hashtag_data.insert_default_user_and_priority()

	rearrange_hashtags(bot, post_data, hashtag_data, original_post_data)
	add_control_buttons(bot, post_data, hashtag_data)
	if config_utils.AUTO_FORWARDING_ENABLED or force_forward:
		forward_to_subchannel(bot, post_data, hashtag_data)


def rearrange_hashtags(bot: telebot.TeleBot, post_data: telebot.types.Message, hashtag_data: HashtagData,
					   original_post_data: telebot.types.Message = None):
	hashtags = hashtag_data.get_hashtags_for_insertion()
	post_data = hashtag_utils.insert_hashtags(post_data, hashtags)

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
