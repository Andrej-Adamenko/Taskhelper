import copy
import json
import logging
import threading
import time
from typing import List, Callable

import telebot
from telebot.apihelper import ApiTelegramException
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, User

import channel_manager
import core_api
from comment_utils import comment_dispatcher
import config_utils
import daily_reminder
import db_utils
from scheduled_messages_utils import scheduled_message_dispatcher
import user_utils
import utils
import hashtag_data as hashtag_data_utils

from hashtag_data import HashtagData
from config_utils import DISCUSSION_CHAT_DATA

CALLBACK_PREFIX = "FWRD"

_FORWARDING_LOCK = threading.RLock()

CHANNEL_TICKET_KEYBOARD_TYPE = {}

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


def get_unchanged_posts(bot: telebot.TeleBot, post_data: telebot.types.Message, subchannel_ids: List[int]):
	main_channel_id = post_data.chat.id
	message_id = post_data.message_id

	forwarded_messages = db_utils.get_copied_message_data(message_id, main_channel_id)
	unchanged_posts = {}
	for forwarded_message in forwarded_messages:
		forwarded_msg_id, forwarded_channel_id = forwarded_message
		forwarded_msg_data = utils.get_message_content_by_id(bot, forwarded_channel_id, forwarded_msg_id)

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


def forwarding_thread_lock(func):
	def inner_function(*args, **kwargs):
		with _FORWARDING_LOCK:
			try:
				return func(*args, **kwargs)
			except Exception as E:
				logging.exception(f"Error in {func.__name__} forwarding function, error: {E}")
	return inner_function


@forwarding_thread_lock
def forward_to_subchannel(bot: telebot.TeleBot, post_data: telebot.types.Message, hashtag_data: HashtagData):
	main_channel_id = post_data.chat.id
	main_message_id = post_data.message_id
	copied_message = None
	subchannel_ids = []

	daily_reminder.update_ticket_data(main_message_id, main_channel_id, hashtag_data)

	if not hashtag_data.is_closed():
		utils.add_channel_id_to_post_data(post_data)
		subchannel_ids = get_subchannel_ids_from_hashtags(main_channel_id, main_message_id, hashtag_data)
		subchannel_ids = filter_subchannels_by_members(main_channel_id, subchannel_ids)

	unchanged_posts = get_unchanged_posts(bot, post_data, list(subchannel_ids))

	if not subchannel_ids and not hashtag_data.is_closed():
		logging.warning(f"Subchannels not found {hashtag_data.get_hashtag_list()}, {main_channel_id}")
		return

	for subchannel_id in subchannel_ids:
		if subchannel_id in unchanged_posts:
			call = CallbackQuery(0, User(0, True, "Bot"), "", "", "", message=post_data)
			keyboard_markup = get_keyboard(call, subchannel_id, unchanged_posts[subchannel_id])
			utils.edit_message_keyboard(bot, post_data, keyboard_markup, chat_id=subchannel_id, message_id=unchanged_posts[subchannel_id])
			continue

		newest_message_id = db_utils.get_newest_copied_message(subchannel_id)
		keyboard_markup = utils.merge_keyboard_markup(
			generate_control_buttons(hashtag_data, post_data),
			channel_manager.get_ticket_settings_buttons(subchannel_id)
		)

		try:
			text, entities = utils.get_post_content(post_data)
			copied_message = bot.send_message(chat_id=subchannel_id, text=text, entities=entities, reply_markup=keyboard_markup)
			logging.info(f"Successfully forwarded post [{main_message_id}, {main_channel_id}] to {subchannel_id} subchannel by tags: {hashtag_data.get_hashtag_list()}")
			db_utils.insert_copied_message(main_message_id, main_channel_id, copied_message.message_id, subchannel_id)
			db_utils.insert_or_update_last_msg_id(copied_message.message_id, subchannel_id)
		except ApiTelegramException as E:
			if not copied_message is None:
				delete_forwarded_message(bot, subchannel_id, copied_message.message_id)

			if E.error_code == 429:
				raise E
			if E.error_code == 403 and E.description.endswith(utils.KICKED_FROM_CHANNEL_ERROR):
				db_utils.delete_individual_channel(subchannel_id)
			logging.warning(f"Exception during forwarding post to subchannel {hashtag_data.get_hashtag_list()} - {E}")
			continue

		# add to the newest settings button and remove it from previous message
		keyboard_markup = generate_control_buttons(hashtag_data, post_data)
		utils.edit_message_keyboard(bot, post_data, keyboard_markup, chat_id=subchannel_id, message_id=copied_message.message_id)
		update_copied_message(bot, subchannel_id, newest_message_id)


def update_copied_message(bot: telebot.TeleBot, copied_channel_id: int, copied_message_id: int):
	post_data = utils.get_message_content_by_id(bot, copied_channel_id, copied_message_id)
	if not post_data:
		return
	main_message_id, main_channel_id = db_utils.get_main_message_from_copied(copied_message_id, copied_channel_id)

	post_data.message_id = main_message_id
	post_data.chat.id = main_channel_id

	hashtag_data = HashtagData(post_data, main_channel_id)
	keyboard = generate_control_buttons(hashtag_data, post_data)
	utils.edit_message_keyboard(bot, post_data, keyboard, chat_id=copied_channel_id, message_id=copied_message_id)


def delete_all_forwarded_messages(bot: telebot.TeleBot, main_channel_id: int, main_message_id: int):
	copied_messages = db_utils.get_all_copied_messages(main_channel_id, main_message_id)
	for copied_message in copied_messages:
		copied_channel_id, copied_message_id = copied_message
		try:
			utils.delete_message(bot, copied_channel_id, copied_message_id)
		except ApiTelegramException:
			utils.remove_keyboard(bot, copied_channel_id, copied_message_id)
		db_utils.delete_copied_message(copied_message_id, copied_channel_id)
		logging.info(f"Deleted message {[copied_message_id, copied_channel_id]} with not supported content type, deleted from db")


def delete_forwarded_message(bot: telebot.TeleBot, chat_id: int, message_id: int):
	is_update_needed = False
	if db_utils.get_newest_copied_message(chat_id) == message_id:
		is_update_needed = True

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

				oldest_message_data = utils.get_message_content_by_id(bot, chat_id, oldest_message_id)
				if oldest_message_data is None:
					db_utils.delete_copied_message(oldest_message_id, chat_id)
					logging.info(f"Message {[oldest_message_id, chat_id]} doesn't exists, deleted from db")
					continue
				if oldest_message_data.content_type not in config_utils.SUPPORTED_CONTENT_TYPES_TICKET:
					db_utils.delete_copied_message(oldest_message_id, chat_id)
					logging.info(f"Deleted message {[oldest_message_id, chat_id]} with not supported content type, deleted from db")
					oldest_message_data = None
					continue

			msg_to_delete_data = utils.get_message_content_by_id(bot, chat_id, message_id)
			if not utils.check_content_type(bot, msg_to_delete_data):
				db_utils.delete_copied_message(message_id, chat_id)
				logging.info(f"Deleted message {[message_id, chat_id]} with not supported content type, deleted from db")
				return

			oldest_message_main_data = db_utils.get_main_message_from_copied(oldest_message_id, chat_id)
			if oldest_message_main_data is None:
				# if oldest message not found in main channel then just replace current message text with delete message
				utils.edit_message_content(bot, msg_to_delete_data, text=config_utils.TO_DELETE_MSG_TEXT, chat_id=chat_id,
				                           message_id=message_id, entities=[])
				return
			main_message_id, main_channel_id = oldest_message_main_data
			new_settings_message_id = message_id

			if oldest_message_data:
				if oldest_message_id < message_id:
					oldest_message_data.message_id = main_message_id
					oldest_message_data.chat.id = main_channel_id

					hashtag_data = HashtagData(oldest_message_data, main_channel_id)
					keyboard = generate_control_buttons(hashtag_data, oldest_message_data)
					text, entities = utils.get_post_content(oldest_message_data)

					utils.edit_message_content(bot, msg_to_delete_data, chat_id=chat_id, message_id=message_id,
					                           reply_markup=keyboard, text=text, entities=entities)
					new_settings_message_id = oldest_message_id
					db_utils.delete_copied_message(message_id, chat_id)
					db_utils.update_copied_message_id(oldest_message_id, chat_id, message_id)
				else:
					# if oldest message is the message that needs to be deleted than just delete it from db
					db_utils.delete_copied_message(message_id, chat_id)

				current_settings_message_id = channel_manager.get_settings_message_id(chat_id)
				if not current_settings_message_id or current_settings_message_id < new_settings_message_id:
					if current_settings_message_id:
						utils.mark_message_for_deletion(bot, chat_id, current_settings_message_id)
					channel_manager.update_settings_message(bot, chat_id, new_settings_message_id)
					is_update_needed = True

					channel_manager.set_settings_message_id(chat_id, new_settings_message_id)
				else:
					utils.edit_message_content(bot, msg_to_delete_data, chat_id=chat_id, message_id=new_settings_message_id,
											   text=config_utils.TO_DELETE_MSG_TEXT, entities=None)
			else:
				# if no oldest message was found then just replace current ticket text with delete message
				db_utils.delete_copied_message(message_id, chat_id)
				utils.edit_message_content(bot, msg_to_delete_data, chat_id=chat_id, message_id=message_id,
				                           text=config_utils.TO_DELETE_MSG_TEXT, entities=None)
		elif E.description.endswith(utils.KICKED_FROM_CHANNEL_ERROR):
			db_utils.delete_copied_message(message_id, chat_id)

	if is_update_needed:
		newest_message_id = db_utils.get_newest_copied_message(chat_id)
		update_copied_message(bot, chat_id, newest_message_id)


def delete_main_message(bot: telebot.TeleBot, main_channel_id: int, main_message_id: int):
	messages = db_utils.get_copied_messages_from_main(main_message_id, main_channel_id)
	for msg in messages:
		copied_message_id, copied_channel_id = msg
		delete_forwarded_message(bot, copied_channel_id, copied_message_id)
		db_utils.delete_copied_message(copied_message_id, copied_channel_id)
		logging.info(f"Removed forwarded message {msg} after it was deleted from main channel {main_message_id, main_channel_id}")
	db_utils.delete_scheduled_message_main(main_message_id, main_channel_id)

	ticket_data = db_utils.get_ticket_data(main_message_id, main_channel_id)
	if ticket_data:
		discussion_chat_id = config_utils.DISCUSSION_CHAT_DATA.get(str(main_channel_id))
		if discussion_chat_id:
			bot.send_message(chat_id=discussion_chat_id, text=f"A user manually deleted ticket {main_message_id}")
		db_utils.delete_ticket_data(main_message_id, main_channel_id)
		logging.info(f"Deleted ticket {main_message_id, main_channel_id} that doesn't exists in main channel anymore")


def deferred_filter(channel):
	channel_id, settings = channel
	if not settings:
		return False
	if channel_manager.SETTING_TYPES.DEFERRED not in settings:
		return False
	return settings[channel_manager.SETTING_TYPES.DEFERRED]


def due_filter(channel):
	channel_id, settings = channel
	if not settings:
		return False
	if channel_manager.SETTING_TYPES.DUE not in settings:
		return False
	return settings[channel_manager.SETTING_TYPES.DUE]


def filter_due_deferred_tickets(main_channel_id: int, main_message_id: int, hashtag_data: HashtagData, channel_data: List):
	if hashtag_data.is_scheduled():
		send_time = db_utils.get_scheduled_message_send_time(main_message_id, main_channel_id)
		if send_time and send_time > time.time():
			return list(filter(deferred_filter, channel_data))

	return list(filter(due_filter, channel_data))


def get_subchannel_ids_from_hashtags(main_channel_id: int, main_message_id: int, hashtag_data: HashtagData) -> set:
	subchannel_ids = set()
	priority = hashtag_data.get_priority_number_or_default()
	channel_data = db_utils.get_individual_channels_by_priority(priority)
	channel_data = [[channel_id, json.loads(settings)] for channel_id, settings in channel_data]

	channel_data = filter_due_deferred_tickets(main_channel_id, main_message_id, hashtag_data, channel_data)

	assigned_user_subchannels = filter_assigned_user_channels(channel_data, hashtag_data)
	if assigned_user_subchannels:
		subchannel_ids.update(assigned_user_subchannels)

	followed_user_subchannels = filter_followed_user_channels(channel_data, hashtag_data)
	if followed_user_subchannels:
		subchannel_ids.update(followed_user_subchannels)

	creator_subchannels = filter_creator_channels(channel_data, main_channel_id, main_message_id)
	if creator_subchannels:
		subchannel_ids.update(creator_subchannels)

	result_subchannel_ids = set()

	for subchannel_id in subchannel_ids:
		custom_hashtag = db_utils.get_custom_hashtag(subchannel_id)
		if custom_hashtag and custom_hashtag not in hashtag_data.other_hashtags:
			continue
		result_subchannel_ids.add(subchannel_id)

	return result_subchannel_ids


def filter_assigned_user_channels(channel_data: List, hashtag_data: HashtagData):
	user_tag = hashtag_data.get_assigned_user()
	if not user_tag:
		return

	result_channels = []
	for channel in channel_data:
		channel_id, settings = channel
		assigned_users = settings.get(channel_manager.SETTING_TYPES.ASSIGNED) or []
		if user_tag in assigned_users:
			result_channels.append(channel_id)

	return result_channels


def filter_followed_user_channels(channel_data: List, hashtag_data: HashtagData):
	user_tags = hashtag_data.get_followed_users()
	if not user_tags:
		return

	result_channels = []
	for channel in channel_data:
		channel_id, settings = channel
		followed_users = settings.get(channel_manager.SETTING_TYPES.FOLLOWED) or []
		for followed_user_tag in user_tags:
			if followed_user_tag in followed_users:
				result_channels.append(channel_id)

	return result_channels


def filter_creator_channels(channel_data: List, main_channel_id: int, main_message_id: int):
	sender_id = db_utils.get_main_message_sender(main_channel_id, main_message_id)
	user_tags = utils.get_keys_by_value(user_utils.get_user_tags(main_channel_id), sender_id) or []

	result_channels = []
	for channel in channel_data:
		channel_id, settings = channel
		creator_users = settings.get(channel_manager.SETTING_TYPES.REPORTED) or []
		for creator_user_tag in user_tags:
			if creator_user_tag in creator_users:
				result_channels.append(channel_id)

	return result_channels


def filter_subchannels_by_members(main_channel_id: int, subchannel_ids: set) -> list:
	result_subchannels = []
	all_members = user_utils.get_member_ids_channels([main_channel_id] + list(subchannel_ids))
	main_members = all_members[main_channel_id]

	for subchannel_id in subchannel_ids:
		members = all_members[subchannel_id]
		if not len([a for a in members if a not in main_members]):
			result_subchannels.append(subchannel_id)

	return result_subchannels


def generate_control_buttons(hashtag_data: HashtagData, post_data: telebot.types.Message):
	main_channel_id = post_data.chat.id
	main_message_id = post_data.message_id

	if hashtag_data.is_opened():
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

	schedule_button = scheduled_message_dispatcher.generate_schedule_button()

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
	current_subchannel_name = f"{current_subchannel} {current_priority}"

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

	main_channel_user_tags = user_utils.get_user_tags(main_channel_id).keys()

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


def get_subchannels_forwarding_data(channel_id: int) -> list:
	user_tags = user_utils.get_user_tags(channel_id).keys()
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

	if callback_type not in [CB_TYPES.CLOSE, CB_TYPES.OPEN]:
		newest_message_id = db_utils.get_newest_copied_message(current_channel_id)
		if newest_message_id == current_message_id:
			channel_manager.clear_channel_ticket_settings_state(call, channel_manager.TICKET_MENU_TYPE, current_channel_id)

	if callback_type in [CB_TYPES.SHOW_SUBCHANNELS, CB_TYPES.SHOW_PRIORITIES, CB_TYPES.SHOW_CC]:
		set_channel_ticket_keyboard_state(current_channel_id, current_message_id, call.from_user.id, callback_type)
	elif callback_type == CB_TYPES.TOGGLE_CC:
		set_channel_ticket_keyboard_state(current_channel_id, current_message_id, call.from_user.id, CB_TYPES.SHOW_CC)
	else:
		set_channel_ticket_keyboard_state(current_channel_id, current_message_id, call.from_user.id, None)

	if callback_type == CB_TYPES.CHANGE_SUBCHANNEL:
		subchannel_name = other_data[0]
		change_subchannel_button_event(bot, call, subchannel_name)
	elif callback_type == CB_TYPES.CLOSE:
		change_state_button_event(bot, call, False)
	elif callback_type == CB_TYPES.OPEN:
		change_state_button_event(bot, call, True)
	elif callback_type == CB_TYPES.SAVE:
		forward_and_add_inline_keyboard(bot, call.message)
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


def set_channel_ticket_keyboard_state(channel_id: int, message_id: int, user: int, state: str|None, data: str = None):
	if channel_id is None or message_id is None:
		return

	key = f"{channel_id}_{message_id}"
	if key not in CHANNEL_TICKET_KEYBOARD_TYPE:
		CHANNEL_TICKET_KEYBOARD_TYPE[key] = {}

	if state is not None:
		CHANNEL_TICKET_KEYBOARD_TYPE[key] = { "state": state, "data": data, "user": user }
	else:
		del CHANNEL_TICKET_KEYBOARD_TYPE[key]

def clear_channel_ticket_keyboard_by_user(channel_id: int, message_id: int, user: int):
	if channel_id is None or message_id is None:
		return

	key = f"{channel_id}_{message_id}"
	if (key in CHANNEL_TICKET_KEYBOARD_TYPE and
			("user" not in CHANNEL_TICKET_KEYBOARD_TYPE[key] or CHANNEL_TICKET_KEYBOARD_TYPE[key]["user"] == user)):
		del CHANNEL_TICKET_KEYBOARD_TYPE[key]


def _get_channel_ticket_keyboard(channel_id: int, message_id: int) -> dict|None:
	key = f"{channel_id}_{message_id}"
	if key in CHANNEL_TICKET_KEYBOARD_TYPE:
			return CHANNEL_TICKET_KEYBOARD_TYPE[key]

	return None

def _get_channel_ticket_keyboard_state(channel_id: int, message_id: int) -> str|None:
	settings = _get_channel_ticket_keyboard(channel_id, message_id)
	if settings is not None:
		settings = settings["state"]

	return settings

def get_keyboard_from_channel_message(bot: telebot.TeleBot, call: telebot.types.CallbackQuery, message_id: int):
	call1 = copy.deepcopy(call)
	if call1.message.id != message_id:
		call1.message = utils.get_message_content_by_id(bot, call.message.chat.id, message_id)
	main_message_id, main_channel_id = db_utils.get_main_message_from_copied(message_id, call.message.chat.id)
	call1.message.chat.id = main_channel_id
	call1.message.id = call1.message.message_id = main_message_id
	call1.message.reply_markup = call1.message.reply_markup if call1.message.reply_markup else InlineKeyboardMarkup()

	return get_keyboard(call1, call.message.chat.id, message_id)


def get_keyboard(call: telebot.types.CallbackQuery, current_channel_id: int = None, current_message_id: int = None):
	message = call.message
	state = _get_channel_ticket_keyboard_state(current_channel_id, current_message_id)
	keyboard_markup = None
	update_show_buttons(message, state)

	if state == CB_TYPES.SHOW_SUBCHANNELS:
		keyboard_markup = generate_subchannel_buttons(message)
	elif state == CB_TYPES.SHOW_PRIORITIES:
		keyboard_markup = generate_priority_buttons(message)
	elif state == CB_TYPES.SHOW_CC:
		keyboard_markup = generate_cc_buttons(message)
	elif state == scheduled_message_dispatcher.CALLBACK_PREFIX:
		keyboard_settings = _get_channel_ticket_keyboard(current_channel_id, current_message_id)
		call.data = f"{state},{keyboard_settings['data']}"
		keyboard, data = scheduled_message_dispatcher.generate_keyboard(call)
		message.reply_markup = keyboard

	if keyboard_markup is not None and keyboard_markup:
		message.reply_markup.keyboard += keyboard_markup.keyboard

	return message.reply_markup

def show_keyboard(bot: telebot.TeleBot, call: telebot.types.CallbackQuery,
						   current_channel_id: int = None, current_message_id: int = None):
	get_keyboard(call, current_channel_id, current_message_id)
	utils.edit_message_keyboard(bot, call.message, chat_id=current_channel_id, message_id=current_message_id)


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

	post_data.reply_markup = generate_control_buttons(hashtag_data, post_data)

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
	is_opened_tag_in_other_tags = hashtag_data.is_tag_in_other_hashtags(hashtag_data_utils.OPENED_TAG)
	if not is_ticket_opened and is_opened_tag_in_other_tags:
		bot.answer_callback_query(call.id, "This ticket cannot be closed due to an opened tag in the text")
		return

	state_str = "opened" if is_ticket_opened else "closed"
	utils.add_comment_to_ticket(bot, post_data, f"{call.from_user.first_name} {state_str} the ticket.")

	hashtag_data.set_status_tag(is_ticket_opened)

	update_message_and_forward_to_subchannels(bot, hashtag_data, post_data, keyboard_function=_update_stat_button)

def _update_stat_button(bot: telebot.TeleBot, updated_post_data: telebot.types.Message, hashtag: HashtagData):
	is_ticket_opened = hashtag.is_opened()
	for button in updated_post_data.reply_markup.keyboard[0]:
		cb_type, _ = utils.parse_callback_str(button.callback_data)
		if cb_type == CB_TYPES.OPEN or cb_type == CB_TYPES.CLOSE:
			callback_type = CB_TYPES.CLOSE if is_ticket_opened else CB_TYPES.OPEN
			button.callback_data = utils.create_callback_str(CALLBACK_PREFIX, callback_type)
			state_btn_text = config_utils.BUTTON_TEXTS["OPENED_TICKET" if is_ticket_opened else "CLOSED_TICKET"]
			button.text = state_btn_text
			break
	add_control_buttons(bot, updated_post_data, hashtag)

def change_subchannel_button_event(bot: telebot.TeleBot, call: telebot.types.CallbackQuery, new_subchannel_name: str):
	post_data = call.message
	main_channel_id = post_data.chat.id

	subchannel_user, subchannel_priority = new_subchannel_name.split(" ")

	hashtag_data = HashtagData(post_data, main_channel_id)

	is_user_tag_changed = hashtag_data.get_assigned_user() != subchannel_user
	is_priority_tag_changed = hashtag_data.get_priority_number() != subchannel_priority

	priorities = hashtag_data.find_priorities_in_other_hashtags()
	if priorities and int(subchannel_priority) > min(priorities):
		bot.answer_callback_query(call.id, "Can't change priority because of a tag with higher priority in the text")
		return

	comment_text = f"{call.from_user.first_name} "
	if is_user_tag_changed and is_priority_tag_changed:
		comment_text += f"reassigned the ticket to {{USER}}, and changed its priority to {subchannel_priority}."
	elif is_user_tag_changed:
		comment_text += f"reassigned the ticket to {{USER}}."
	elif is_priority_tag_changed:
		comment_text += f"changed ticket's priority to {subchannel_priority}."

	if comment_text:
		text, entities = user_utils.insert_user_reference(subchannel_user, comment_text)
		utils.add_comment_to_ticket(bot, post_data, text, entities)

	hashtag_data.assign_to_user(subchannel_user)

	hashtag_data.set_priority(subchannel_priority)

	update_message_and_forward_to_subchannels(bot, hashtag_data, post_data)



def change_priority_button_event(bot: telebot.TeleBot, call: telebot.types.CallbackQuery, new_priority: str):
	post_data = call.message
	main_channel_id = post_data.chat.id

	hashtag_data = HashtagData(post_data, main_channel_id)

	priorities = hashtag_data.find_priorities_in_other_hashtags()
	if priorities and int(new_priority) > min(priorities):
		bot.answer_callback_query(call.id, "Can't change priority because of a tag with higher priority in the text")
		return

	utils.add_comment_to_ticket(bot, post_data, f"{call.from_user.first_name} changed ticket's priority to {new_priority}. ")
	hashtag_data.set_priority(new_priority)

	update_message_and_forward_to_subchannels(bot, hashtag_data, post_data)


def toggle_cc_button_event(bot: telebot.TeleBot, call: telebot.types.CallbackQuery, selected_user: str):
	post_data = call.message
	main_channel_id = post_data.chat.id

	hashtag_data = HashtagData(post_data, main_channel_id)

	if selected_user in hashtag_data.get_followed_users():
		if not hashtag_data.can_remove_user_from_followers(selected_user):
			bot.answer_callback_query(call.id, "Can't remove this user because he's mentioned in the text")
			return
		hashtag_data.remove_from_followers(selected_user)
		comment_text = f"{call.from_user.first_name} removed {{USER}} from ticket's followers."
	else:
		hashtag_data.add_user(selected_user)
		comment_text = f"{call.from_user.first_name} added {{USER}} to ticket's followers."

	text, entities = user_utils.insert_user_reference(selected_user, comment_text)
	utils.add_comment_to_ticket(bot, post_data, text, entities)

	update_message_and_forward_to_subchannels(bot, hashtag_data, post_data,
			keyboard_function=lambda bot_item, updated_post_data, hashtag: show_cc_buttons(bot_item, updated_post_data))


def forward_and_add_inline_keyboard(bot: telebot.TeleBot, post_data: telebot.types.Message, new_ticket: bool = False,
									check_ticket: bool = False):
	main_channel_id = post_data.chat.id
	main_message_id = post_data.message_id

	hashtag_data = HashtagData(post_data, main_channel_id, True, check_ticket)

	if new_ticket:
		sender_id = db_utils.get_main_message_sender(main_channel_id, main_message_id)
		if sender_id:
			user_tags = utils.get_keys_by_value(user_utils.get_user_tags(main_channel_id), sender_id)
			for user_tag in user_tags:
				hashtag_data.add_user(user_tag)

	update_message_and_forward_to_subchannels(bot, hashtag_data, post_data, True)


def update_message_and_forward_to_subchannels(bot: telebot.TeleBot, hashtag_data: HashtagData, post_data: telebot.types.Message = None,
											  add_next_action_comment: bool = False,
											  keyboard_function: Callable[[telebot.TeleBot, telebot.types.Message, HashtagData], None] = add_control_buttons):
	updated_message = hashtag_data.get_updated_post_data()
	update_main_message_content(bot, hashtag_data, updated_message, post_data)
	if add_next_action_comment:
		comment_dispatcher.add_next_action_comment(bot, updated_message)
	keyboard_function(bot, updated_message, hashtag_data)
	forward_to_subchannel(bot, updated_message, hashtag_data)


def update_main_message_content(bot: telebot.TeleBot, hashtag_data: HashtagData, post_data: telebot.types.Message,
					   original_post_data: telebot.types.Message = None):
	scheduled_message_dispatcher.update_status_from_tags(bot, post_data, hashtag_data)

	if original_post_data and utils.is_post_data_equal(post_data, original_post_data):
		return

	try:
		text, entities = utils.get_post_content(post_data)
		utils.edit_message_content(bot, post_data, text=text, entities=entities, reply_markup=post_data.reply_markup)
		if hashtag_data.comment:
			comment_text, comment_entities = hashtag_data.comment
			utils.add_comment_to_ticket(bot, post_data, comment_text, comment_entities)
	except ApiTelegramException as E:
		if E.error_code == 429:
			raise E
		logging.info(f"Exception during rearranging hashtags - {E}")
		return


def get_invalid_ticket_ids(bot: telebot.TeleBot):
	logging.info("Deleting invalid ticket ids")
	db_utils.delete_invalid_ticket_data()
	channels_data = db_utils.get_all_individual_channels()
	for channel_data in channels_data:
		count_invalid = 0
		channel_id, settings = channel_data
		settings = json.loads(settings)
		last_msg_id = utils.get_last_message(bot, channel_id)
		if not last_msg_id:
			logging.info(f"Can't get last message in channel {channel_id}, scanning of invalid tickets is skipped")
			continue

		logging.info(f"Checking channel {channel_id}")
		copied_messages = db_utils.get_copied_messages_existing_main_from_copied_channel(channel_id)
		main_messages = db_utils.get_main_message_ids(channel_id)
		message_ids = [i for i in range(1, last_msg_id + 1) if i not in copied_messages and i not in main_messages and
					   i != settings.get(channel_manager.SETTING_TYPES.SETTINGS_MESSAGE_ID)]
		messages = core_api.get_messages(channel_id, 0, 50, message_ids=message_ids)
		if not messages:
			logging.info(f"Can't get messages in channel {channel_id}, scanning of invalid tickets is skipped")
			continue

		for message in messages:
			if message.empty or message.service or not message.reply_markup or utils.get_forwarded_from_id(message):
				continue

			utils.update_forwarded_fields(message)
			delete_forwarded_message(bot, channel_id, message.id)
			count_invalid += 1
			logging.info(f"Deleted invalid ticket {message.id} in channel {channel_id}")
			time.sleep(config_utils.DELAY_AFTER_ONE_SCAN)

		logging.info(f"Count deleted invalid tickets in channel {channel_id} is {count_invalid}")

