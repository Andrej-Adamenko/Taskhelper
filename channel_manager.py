import copy
import json
import logging
from typing import List, Dict

import telebot
from telebot.apihelper import ApiTelegramException
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, ChatMemberOwner, Message

import config_utils
import core_api
import db_utils
import forwarding_utils
import hashtag_data
import interval_updating_utils
import user_utils
import utils

CALLBACK_PREFIX = "CHNN"
NEW_USER_TYPE = "+"

DEFERRED_INTERVAL_CHECK_TIMER = None

SETTINGS_TITLE = "CURRENT SETTINGS"
CHANNEL_TICKET_SETTINGS_BUTTONS = {}
TICKET_MENU_TYPE = "ticket"
INFO_MENU_TYPE = "info"
ALL_MENU_TYPE = "all"

class CB_TYPES:
	ASSIGNED_SELECTED = "AS"
	REPORTED_SELECTED = "CR"
	FOLLOWED_SELECTED = "FL"
	REMIND_SELECTED = "RMN"
	PRIORITY_SELECTED = "PR"
	DEFERRED_SELECTED = "DFR"
	DUE_SELECTED = "DUE"
	SAVE_AND_HIDE_SETTINGS_MENU = "SVHS"
	TOGGLE_USER = "USR"
	TOGGLE_REMIND_SETTING = "TRM"
	SAVE_SELECTED_USERS = "SVU"
	SAVE_REMIND_SETTINGS = "SVR"
	BACK_TO_MAIN_MENU = "BMM"
	OPEN_CHANNEL_SETTINGS = "OCS"
	CREATE_CHANNEL_SETTINGS = "CCS"
	NOP = "NOP"  # No operation


class SETTING_TYPES:
	ASSIGNED = "assigned"
	REPORTED = "reported"
	FOLLOWED = "cc"
	DUE = "due"
	DEFERRED = "deferred"
	REMIND = "remind"
	SETTINGS_MESSAGE_ID = "settings_message_id"

CB_TYPES_TO_SETTINGS = {
	CB_TYPES.DUE_SELECTED: SETTING_TYPES.DUE,
	CB_TYPES.DEFERRED_SELECTED: SETTING_TYPES.DEFERRED,
	CB_TYPES.TOGGLE_REMIND_SETTING: SETTING_TYPES.REMIND
}

MENU_TITLES = {
	SETTING_TYPES.ASSIGNED: "Assigned to:",
	SETTING_TYPES.REPORTED: "Reported by:",
	SETTING_TYPES.FOLLOWED: "CCed to:",
	SETTING_TYPES.REMIND: "Remind me when:",
}


class REMIND_TYPES:
	ASSIGNED = "assigned"
	REPORTED = "reported"
	FOLLOWED = "cced"

	TYPES_ORDER = [ASSIGNED, REPORTED, FOLLOWED]
	TYPES_TITLE = {
		ASSIGNED: "Assigned to me",
		REPORTED: "Reported by me",
		FOLLOWED: "CCed to me"
	}


_TOGGLE_CALLBACKS = [
	CB_TYPES.DUE_SELECTED,
	CB_TYPES.DEFERRED_SELECTED,
	CB_TYPES.PRIORITY_SELECTED,
	CB_TYPES.TOGGLE_USER,
	CB_TYPES.TOGGLE_REMIND_SETTING,
]

_TYPE_SEPARATOR = ","
_DEFAULT_SETTINGS = {
	SETTING_TYPES.DUE: True,
	SETTING_TYPES.DEFERRED: True,
	SETTING_TYPES.REMIND: [REMIND_TYPES.ASSIGNED],
}


def get_individual_channel_settings(channel_id: int):
	settings_str, priorities_str = db_utils.get_individual_channel_settings(channel_id)
	settings = json.loads(settings_str) if settings_str else {}
	priorities = priorities_str.split(",") if priorities_str else []
	return settings, priorities

def update_individual_channel(channel_id: int, settings: dict, priorities: dict):
	priorities_str = _TYPE_SEPARATOR.join(priorities)
	settings_str = json.dumps(settings)
	db_utils.update_individual_channel(channel_id, settings_str, priorities_str)

def get_selected_users_from_settings(settings: Dict, channel_type: str):
	if channel_type not in settings:
		return []

	return settings[channel_type]


def add_user_tags_to_button_text(button: InlineKeyboardButton, channel_type: str, settings: Dict):
	user_tags = get_selected_users_from_settings(settings, channel_type)
	if len(user_tags) < 1:
		return

	if NEW_USER_TYPE in user_tags:
		user_tags.remove(NEW_USER_TYPE)
		user_tags.append("<new users>")

	button.text += f" {user_tags[0]}"
	for user_tag in user_tags[1:]:
		button.text += f", {user_tag}"


def generate_settings_keyboard(channel_id: int, add_help=False):
	settings, priorities = get_individual_channel_settings(channel_id)

	assigned_to_btn = InlineKeyboardButton(MENU_TITLES[SETTING_TYPES.ASSIGNED])
	assigned_to_btn.callback_data = utils.create_callback_str(CALLBACK_PREFIX, CB_TYPES.ASSIGNED_SELECTED)
	add_user_tags_to_button_text(assigned_to_btn, SETTING_TYPES.ASSIGNED, settings)

	reported_by_btn = InlineKeyboardButton(MENU_TITLES[SETTING_TYPES.REPORTED])
	reported_by_btn.callback_data = utils.create_callback_str(CALLBACK_PREFIX, CB_TYPES.REPORTED_SELECTED)
	add_user_tags_to_button_text(reported_by_btn, SETTING_TYPES.REPORTED, settings)

	followed_by_btn = InlineKeyboardButton(MENU_TITLES[SETTING_TYPES.FOLLOWED])
	followed_by_btn.callback_data = utils.create_callback_str(CALLBACK_PREFIX, CB_TYPES.FOLLOWED_SELECTED)
	add_user_tags_to_button_text(followed_by_btn, SETTING_TYPES.FOLLOWED, settings)

	remind_btn = InlineKeyboardButton(MENU_TITLES[SETTING_TYPES.REMIND])
	remind_settings = settings.get(SETTING_TYPES.REMIND)
	if remind_settings:
		settings_str = ",".join([f" {s}" for s in remind_settings])
		remind_btn.text += settings_str
	remind_btn.callback_data = utils.create_callback_str(CALLBACK_PREFIX, CB_TYPES.REMIND_SELECTED)

	due_btn = InlineKeyboardButton("Due")
	due_btn.callback_data = utils.create_callback_str(CALLBACK_PREFIX, CB_TYPES.DUE_SELECTED)
	is_due = settings[SETTING_TYPES.DUE] if SETTING_TYPES.DUE in settings else False
	due_btn.text += config_utils.BUTTON_TEXTS["CHECK"] if is_due else ""

	deferred_btn = InlineKeyboardButton("Deferred")
	deferred_btn.callback_data = utils.create_callback_str(CALLBACK_PREFIX, CB_TYPES.DEFERRED_SELECTED)
	is_deferred = settings[SETTING_TYPES.DEFERRED] if SETTING_TYPES.DEFERRED in settings else False
	deferred_btn.text += config_utils.BUTTON_TEXTS["CHECK"] if is_deferred else ""

	buttons = [
		assigned_to_btn,
		reported_by_btn,
		followed_by_btn,
		remind_btn,
		due_btn,
		deferred_btn,
	]

	for priority in hashtag_data.POSSIBLE_PRIORITIES:
		priority_btn = InlineKeyboardButton(f"Priority {priority}")
		if priority in priorities:
			priority_btn.text += config_utils.BUTTON_TEXTS["CHECK"]
		priority_btn.callback_data = utils.create_callback_str(CALLBACK_PREFIX, CB_TYPES.PRIORITY_SELECTED, priority)
		buttons.append(priority_btn)

	save_btn = InlineKeyboardButton(f"Close & Update")
	save_btn.callback_data = utils.create_callback_str(CALLBACK_PREFIX, CB_TYPES.SAVE_AND_HIDE_SETTINGS_MENU)
	buttons.append(save_btn)

	if add_help:
		buttons.append(add_help_button(channel_id))

	rows = [[btn] for btn in buttons]
	return InlineKeyboardMarkup(rows)

def add_help_button(channel_id):
	settings_button = telebot.types.InlineKeyboardButton("Help")
	settings_message_id = get_settings_message_id(channel_id)
	if settings_message_id:
		chat_id_str = str(channel_id)
		chat_id_str = chat_id_str[4:] if chat_id_str[:4] == "-100" else chat_id_str
		settings_button.url = f"https://t.me/c/{chat_id_str}/{settings_message_id}"
		settings_button.callback_data = config_utils.EMPTY_CALLBACK_DATA_BUTTON
	else:
		settings_button.callback_data = utils.create_callback_str(
			CALLBACK_PREFIX,
			CB_TYPES.CREATE_CHANNEL_SETTINGS
		)

	return settings_button

def show_settings_keyboard(bot: telebot.TeleBot, call: telebot.types.CallbackQuery,
						   force_update_info: bool = False, force_update_ticket: bool = False):
	message = call.message
	channel_id = message.chat.id
	ticket_keyboard = get_settings_menu(channel_id, TICKET_MENU_TYPE)
	keyboard = get_settings_menu(channel_id, INFO_MENU_TYPE)
	try:
		_call_settings_button(bot, call, keyboard, ticket_keyboard, force_update_info, force_update_ticket)
	except ApiTelegramException as E:
		if "message is not modified:" in E.description:
			logging.error(f"Error during channel settings message update - {E}")

def get_settings_message_id(channel_id):
	settings, priorities = get_individual_channel_settings(channel_id)
	return settings.get(SETTING_TYPES.SETTINGS_MESSAGE_ID)


def set_settings_message_id(channel_id, message_id):
	settings, priorities = get_individual_channel_settings(channel_id)
	settings[SETTING_TYPES.SETTINGS_MESSAGE_ID] = message_id
	settings_str = json.dumps(settings)
	db_utils.update_individual_channel_settings(channel_id, settings_str)


def is_settings_message(message: telebot.types.Message):
	not_settings = message.reply_markup is None
	not_settings = not_settings or f"\n{SETTINGS_TITLE}\n" not in message.text
	not_settings = not_settings or db_utils.is_copied_message_exists(message.id, message.chat.id)
	not_settings = not_settings or db_utils.is_main_message_exists(message.chat.id, message.id)
	return not not_settings


def get_exist_settings_message(bot: telebot.TeleBot, channel_id):
	last_message = db_utils.get_oldest_copied_message(channel_id)

	if not last_message:
		last_message = utils.get_last_message(bot, channel_id)

	if last_message and last_message > 0:
		messages = core_api.get_messages(channel_id, last_message, 50)
		if not messages:
			return False

		for forwarded_message in messages:
			if forwarded_message.empty or forwarded_message.service:
				continue
			current_msg_id = forwarded_message.id
			if is_settings_message(forwarded_message):
				update_settings_message(bot, channel_id, current_msg_id)
				set_settings_message_id(channel_id, current_msg_id)

				newest_message_id = db_utils.get_newest_copied_message(channel_id)
				if newest_message_id is not None:
					post_data = utils.get_main_message_content_by_id(bot, channel_id, newest_message_id)
					hashtag = hashtag_data.HashtagData(post_data, channel_id)
					keyboard_markup = forwarding_utils.generate_control_buttons(hashtag, post_data)
					utils.edit_message_keyboard(bot, post_data, keyboard_markup, channel_id, newest_message_id)

				return True

	return False


def initialize_channel(bot: telebot.TeleBot, channel_id: int, user_id: int = None):
	if db_utils.is_main_channel_exists(channel_id):
		return

	if not db_utils.is_individual_channel_exists(channel_id):
		try:
			channel_admins = bot.get_chat_administrators(channel_id)
			channel_owner = next((user for user in channel_admins if type(user) == ChatMemberOwner), None)
			user_id = channel_owner.user.id
		except Exception as E:
			logging.warning(f"Can't get owner_id from channel, use user #{user_id} in channel #{channel_id}. Error - {E}")
			if user_id is None:
				raise E

		settings_str = json.dumps(_DEFAULT_SETTINGS)
		db_utils.insert_individual_channel(channel_id, settings_str, user_id)

	create_settings_message(bot, channel_id)


def create_settings_message(bot: telebot.TeleBot, channel_id: int):
	settings_message_id = get_settings_message_id(channel_id)
	if settings_message_id:
		settings_message = utils.get_message_content_by_id(bot, channel_id, settings_message_id)
		if settings_message:
			return

	if get_exist_settings_message(bot, channel_id):
		return

	oldest_message_id = db_utils.get_oldest_copied_message(channel_id)
	if oldest_message_id:
		main_message_id, main_channel_id = db_utils.get_main_message_from_copied(oldest_message_id, channel_id)
		db_utils.delete_copied_message(oldest_message_id, channel_id)
		update_settings_message(bot, channel_id, oldest_message_id)
		set_settings_message_id(channel_id, oldest_message_id)
		interval_updating_utils.update_older_message(bot, main_channel_id, main_message_id)
	else:
		keyboard = generate_settings_keyboard(channel_id)
		text = generate_current_settings_text(channel_id)
		msg = bot.send_message(chat_id=channel_id, reply_markup=keyboard, text=text)
		set_settings_message_id(channel_id, msg.id)
		db_utils.insert_or_update_last_msg_id(msg.id, channel_id)


def get_text_information_text():
	return '''
Please select this channel's settings, click on buttons to select/deselect filtering parameters. When all needed parameters are selected press "Save" button. If this message with settings was deleted you can call "/settings" command to create it. If "New users" parameter is selected than new users will be automatically added to the list. Descriptions of each parameter:
   1) Assigned to - include tickets that is assigned to the selected users
   2) Reported by - include tickets that is created by the selected users
   3) CCed to - include tickets where the selected users in CC
   4) Remind me when - regulates what tickets can be reminded in this channel
   5) Due - if this option is enabled, regular (NOT deferred) tickets and also tickets deferred until a date, but that date is in the past now, will all be included in this channel
   6) Deferred - if this option is enabled, tickets, deferred until now will be included in this channel
   7) Priority 1/2/3 - here you should specify which tickets with priority 1, 2 and 3 will be forwarded to this channel
'''


def generate_current_settings_text(channel_id: int):
	text = get_text_information_text()

	text += f"\n{SETTINGS_TITLE}"

	settings, priorities = get_individual_channel_settings(channel_id)

	for setting_type in [SETTING_TYPES.ASSIGNED, SETTING_TYPES.REPORTED, SETTING_TYPES.FOLLOWED]:
		text += "\n" + MENU_TITLES[setting_type] + " "
		selected_users = get_selected_users_from_settings(settings, setting_type)
		if len(selected_users) < 1:
			continue

		user_tags = [f"#{user_tag}" for user_tag in selected_users if user_tag != NEW_USER_TYPE]
		if NEW_USER_TYPE in selected_users:
			user_tags.append("<new users>")
		text += ", ".join(user_tags)

	text += "\n" + MENU_TITLES[SETTING_TYPES.REMIND] + " "
	selected_options = get_selected_users_from_settings(settings, SETTING_TYPES.REMIND)
	text += ", ".join(selected_options)

	due_flag = bool(get_selected_users_from_settings(settings, SETTING_TYPES.DUE))
	text += "\nInclude due tickets: " + ("yes" if due_flag else "no")

	deferred_flag = bool(get_selected_users_from_settings(settings, SETTING_TYPES.DEFERRED))
	text += "\nInclude deferred tickets: " + ("yes" if deferred_flag else "no")

	priority_tags = [f"#{hashtag_data.PRIORITY_TAG}{p}" for p in priorities]
	text += "\nPriorities: " + ", ".join(priority_tags)

	return text


def generate_user_keyboard(channel_id: int, setting_type: str):
	settings, priorities = get_individual_channel_settings(channel_id)
	active_user_tags = []
	if setting_type in settings:
		active_user_tags = settings[setting_type]

	nop_callback = utils.create_callback_str(CALLBACK_PREFIX, CB_TYPES.NOP)
	text_button = InlineKeyboardButton(MENU_TITLES[setting_type], callback_data=nop_callback)
	buttons = [text_button]
	for user_tag in user_utils.get_user_tags():
		callback = utils.create_callback_str(CALLBACK_PREFIX, CB_TYPES.TOGGLE_USER, setting_type, user_tag)
		button_text = f"#{user_tag}" if user_tag != NEW_USER_TYPE else "New users"
		user_button = InlineKeyboardButton(button_text, callback_data=callback)
		if user_tag in active_user_tags:
			user_button.text += config_utils.BUTTON_TEXTS["CHECK"]
		buttons.append(user_button)

	callback = utils.create_callback_str(CALLBACK_PREFIX, CB_TYPES.TOGGLE_USER, setting_type, NEW_USER_TYPE)
	new_user_button = InlineKeyboardButton(f"New users", callback_data=callback)
	if NEW_USER_TYPE in active_user_tags:
		new_user_button.text += config_utils.BUTTON_TEXTS["CHECK"]
	buttons.append(new_user_button)

	callback = utils.create_callback_str(CALLBACK_PREFIX, CB_TYPES.BACK_TO_MAIN_MENU)
	save_button = InlineKeyboardButton(f"← Back", callback_data=callback)
	buttons.append(save_button)

	rows = [[btn] for btn in buttons]
	return InlineKeyboardMarkup(rows)


def generate_remind_keyboard(channel_id):
	settings, priorities = get_individual_channel_settings(channel_id)
	active_settings = []
	buttons = []
	if SETTING_TYPES.REMIND in settings:
		active_settings = settings[SETTING_TYPES.REMIND]
	for item in REMIND_TYPES.TYPES_ORDER:
		callback = utils.create_callback_str(CALLBACK_PREFIX, CB_TYPES.TOGGLE_REMIND_SETTING, item)
		button = InlineKeyboardButton(REMIND_TYPES.TYPES_TITLE[item], callback_data=callback)
		if item in active_settings:
			button.text += config_utils.BUTTON_TEXTS["CHECK"]
		buttons.append(button)

	callback = utils.create_callback_str(CALLBACK_PREFIX, CB_TYPES.BACK_TO_MAIN_MENU)
	buttons.append(InlineKeyboardButton(f"← Back", callback_data=callback))

	nop_callback = utils.create_callback_str(CALLBACK_PREFIX, CB_TYPES.NOP)
	buttons.insert(0, InlineKeyboardButton(MENU_TITLES[SETTING_TYPES.REMIND], callback_data=nop_callback))

	rows = [[btn] for btn in buttons]
	return InlineKeyboardMarkup(rows)


def _call_settings_button(bot: telebot.TeleBot, call: CallbackQuery,
								  keyboard: InlineKeyboardMarkup, ticket_keyboard: InlineKeyboardMarkup,
								  force_update_info_keyboard:bool = False, force_update_ticket_keyboard:bool = False):
	post_data = call.message
	message_id = get_settings_message_id(post_data.chat.id)

	if is_settings_message(post_data):
		update_settings_message(bot, post_data.chat.id, post_data.id, keyboard)

	if message_id != post_data.id and force_update_info_keyboard:
		update_settings_message(bot, post_data.chat.id, message_id, keyboard)

	newest_message_id = db_utils.get_newest_copied_message(post_data.chat.id)
	if newest_message_id == post_data.id or force_update_ticket_keyboard:
		ticket_keyboard = utils.merge_keyboard_markup(
			forwarding_utils.get_keyboard_from_channel_message(bot, call, newest_message_id),
			ticket_keyboard
		)
		bot.edit_message_reply_markup(chat_id=post_data.chat.id, message_id=newest_message_id,
									  reply_markup=ticket_keyboard)


def update_settings_keyboard(bot: telebot.TeleBot, message: Message, keyboard: InlineKeyboardMarkup = None):
	channel_id = message.chat.id
	message_id = message.id
	if keyboard is None:
		keyboard = generate_settings_keyboard(channel_id)
	text = generate_current_settings_text(channel_id)
	bot.edit_message_text(chat_id=channel_id, message_id=message_id, reply_markup=keyboard, text=text)


def update_settings_message(bot: telebot.TeleBot, channel_id: int, message_id: int,
							keyboard: InlineKeyboardMarkup = None):
	text = generate_current_settings_text(channel_id)
	if keyboard is None:
		keyboard = get_button_settings_keyboard()

	try:
		bot.edit_message_text(text=text, reply_markup=keyboard, chat_id=channel_id, message_id=message_id)
	except ApiTelegramException as E:
		logging.error(f"Error during channel settings message update - {E}")


def get_button_settings_keyboard(text: str = "Edit channel settings ⚙️"):
	settings_button = telebot.types.InlineKeyboardButton(text)
	settings_button.callback_data = utils.create_callback_str(CALLBACK_PREFIX, CB_TYPES.OPEN_CHANNEL_SETTINGS)

	return telebot.types.InlineKeyboardMarkup([[settings_button]])


def get_ticket_settings_buttons(channel_id: int) -> (InlineKeyboardMarkup, InlineKeyboardMarkup):
	keyboard = get_settings_menu(channel_id, TICKET_MENU_TYPE)

	return keyboard


def get_settings_menu(channel_id: int, menu_type: str = None) -> (InlineKeyboardMarkup, InlineKeyboardMarkup):
	channel_menu = None
	if channel_id in CHANNEL_TICKET_SETTINGS_BUTTONS:
		if menu_type in CHANNEL_TICKET_SETTINGS_BUTTONS[channel_id]:
			channel_menu = CHANNEL_TICKET_SETTINGS_BUTTONS[channel_id][menu_type]['state']

	return _get_settings_menu_by_type(channel_id, channel_menu, menu_type == TICKET_MENU_TYPE)


def _get_settings_menu_by_type(channel_id: int, state: str = None, is_ticket: bool = False) \
																-> (InlineKeyboardMarkup, InlineKeyboardMarkup):
	if is_ticket:
		keyboard = get_button_settings_keyboard("Settings ⚙️")
	else:
		keyboard = get_button_settings_keyboard()

	if state is not None:
		if state == CB_TYPES.OPEN_CHANNEL_SETTINGS:
			keyboard = generate_settings_keyboard(channel_id, is_ticket)
		elif state == CB_TYPES.ASSIGNED_SELECTED:
			keyboard = generate_user_keyboard(channel_id, SETTING_TYPES.ASSIGNED)
		elif state == CB_TYPES.FOLLOWED_SELECTED:
			keyboard = generate_user_keyboard(channel_id, SETTING_TYPES.FOLLOWED)
		elif state == CB_TYPES.REPORTED_SELECTED:
			keyboard = generate_user_keyboard(channel_id, SETTING_TYPES.REPORTED)
		elif state == CB_TYPES.REMIND_SELECTED:
			keyboard = generate_remind_keyboard(channel_id)

	return keyboard


def handle_callback(bot: telebot.TeleBot, call: CallbackQuery):
	callback_type, other_data = utils.parse_callback_str(call.data)
	message = call.message

	if not db_utils.is_individual_channel_exists(message.chat.id):
		bot.answer_callback_query(call.id)
		return

	forwarding_utils.clear_channel_ticket_keyboard_by_user(message.chat.id, message.id, call.from_user.id)

	if callback_type in [CB_TYPES.ASSIGNED_SELECTED, CB_TYPES.REPORTED_SELECTED,
						 CB_TYPES.FOLLOWED_SELECTED, CB_TYPES.REMIND_SELECTED]:
		_set_channel_ticket_settings_state(call, callback_type)
		show_settings_keyboard(bot, call)
	elif callback_type in [CB_TYPES.BACK_TO_MAIN_MENU, CB_TYPES.OPEN_CHANNEL_SETTINGS,
						   CB_TYPES.SAVE_SELECTED_USERS, CB_TYPES.SAVE_REMIND_SETTINGS]:
		_set_channel_ticket_settings_state(call, CB_TYPES.OPEN_CHANNEL_SETTINGS)
		show_settings_keyboard(bot, call)
	elif callback_type == CB_TYPES.SAVE_AND_HIDE_SETTINGS_MENU:
		ticket_old_state = _get_channel_ticket_settings_state(message.chat.id, TICKET_MENU_TYPE)
		info_old_state = _get_channel_ticket_settings_state(message.chat.id, INFO_MENU_TYPE)
		clear_channel_ticket_settings_state(call)
		show_settings_keyboard(bot, call,
		   info_old_state is not None and _get_channel_ticket_settings_state(message.chat.id, INFO_MENU_TYPE) is None,
		   ticket_old_state is not None and _get_channel_ticket_settings_state(message.chat.id, TICKET_MENU_TYPE) is None)
		interval_updating_utils.start_interval_updating(bot)
	elif callback_type == CB_TYPES.NOP:
		bot.answer_callback_query(call.id)
	elif callback_type in _TOGGLE_CALLBACKS:
		toggle_button(bot, call, callback_type, other_data)
	elif callback_type == CB_TYPES.CREATE_CHANNEL_SETTINGS:
		_set_channel_ticket_settings_state(call, CB_TYPES.OPEN_CHANNEL_SETTINGS)
		create_settings_message(bot, message.chat.id)


def _set_channel_ticket_settings_state(call: CallbackQuery, state: str):
	menu_type = TICKET_MENU_TYPE
	if is_settings_message(call.message):
		menu_type = INFO_MENU_TYPE

	if call.message.chat.id not in CHANNEL_TICKET_SETTINGS_BUTTONS:
		CHANNEL_TICKET_SETTINGS_BUTTONS[call.message.chat.id] = {}

	CHANNEL_TICKET_SETTINGS_BUTTONS[call.message.chat.id][menu_type] = {
			"state": state,
			"user": call.from_user.id
	}


def _get_channel_ticket_settings(channel_id: int, menu_type: str) -> dict|None:
	if channel_id in CHANNEL_TICKET_SETTINGS_BUTTONS:
		if menu_type in CHANNEL_TICKET_SETTINGS_BUTTONS[channel_id]:
			return CHANNEL_TICKET_SETTINGS_BUTTONS[channel_id][menu_type]

	return None

def _get_channel_ticket_settings_state(channel_id: int, menu_type: str) -> str|None:
	settings = _get_channel_ticket_settings(channel_id, menu_type)
	if settings is not None:
		settings = settings["state"]

	return settings


def clear_channel_ticket_settings_state(call: CallbackQuery, state: str = ALL_MENU_TYPE, channel_id: str = None):
	menu_type = TICKET_MENU_TYPE
	if state == ALL_MENU_TYPE and is_settings_message(call.message):
		menu_type = INFO_MENU_TYPE

	if channel_id is None:
		channel_id = call.message.chat.id

	if channel_id in CHANNEL_TICKET_SETTINGS_BUTTONS:
		items = copy.deepcopy(CHANNEL_TICKET_SETTINGS_BUTTONS[channel_id]).items()
		for key, value in items:
			if (state == ALL_MENU_TYPE and (key == menu_type or value["user"] == call.from_user.id) or
					key == state and value["user"] == call.from_user.id):
				del CHANNEL_TICKET_SETTINGS_BUTTONS[channel_id][key]


def is_button_checked(buttons: List[InlineKeyboardButton], target_cb_type: str):
	for btn in buttons:
		btn_cb_type, btn_cb_data = utils.parse_callback_str(btn.callback_data)
		if btn_cb_type == target_cb_type:
			return btn.text.endswith(config_utils.BUTTON_TEXTS["CHECK"])
	return None


def toggle_button(bot: telebot.TeleBot, call: CallbackQuery, cb_type: str, cb_data: list):
	reply_markup = call.message.reply_markup
	buttons = [btn for row in reply_markup.keyboard for btn in row]
	is_deferred_checked = is_button_checked(buttons, CB_TYPES.DEFERRED_SELECTED)
	is_due_checked = is_button_checked(buttons, CB_TYPES.DUE_SELECTED)
	is_enabled = is_button_checked(buttons, cb_type)
	save_changes = False

	setting_type = ""
	if cb_type in CB_TYPES_TO_SETTINGS:
		setting_type = CB_TYPES_TO_SETTINGS[cb_type]
	elif cb_type == CB_TYPES.PRIORITY_SELECTED:
		setting_type = CB_TYPES.PRIORITY_SELECTED
	if len(cb_data) > 1:
		setting_type, other_data = cb_data
	else:
		other_data = cb_data[0] if len(cb_data) > 0 else ""

	for btn in buttons:
		callback_str = btn.callback_data
		btn_cb_type, btn_cb_data = utils.parse_callback_str(callback_str)

		if btn_cb_type != cb_type or btn_cb_data != cb_data:
			continue

		if btn.text.endswith(config_utils.BUTTON_TEXTS["CHECK"]):
			if (cb_type == CB_TYPES.DUE_SELECTED and not is_deferred_checked) or (
					cb_type == CB_TYPES.DEFERRED_SELECTED and not is_due_checked):
				bot.answer_callback_query(callback_query_id=call.id,
											text="At least one of the Due and Deferred buttons should be selected")
				return
			btn.text = btn.text[:-len(config_utils.BUTTON_TEXTS["CHECK"])]
			is_enabled = False
			save_changes = True
		else:
			btn.text += config_utils.BUTTON_TEXTS["CHECK"]
			is_enabled = True
			save_changes = True

	if save_changes:
		save_toggle_button(bot, call, setting_type, other_data, is_enabled)


def save_toggle_button(bot: telebot.TeleBot, call:CallbackQuery, setting_type:str,
					   cb_data:str, is_enable:bool):
	channel_id = call.message.chat.id
	settings, priorities = get_individual_channel_settings(channel_id)
	settings[CB_TYPES.PRIORITY_SELECTED] = priorities
	update_settings = True
	array_settings = [SETTING_TYPES.ASSIGNED, SETTING_TYPES.REPORTED, SETTING_TYPES.FOLLOWED,
					  SETTING_TYPES.REMIND, CB_TYPES.PRIORITY_SELECTED]
	default_settings = {
		SETTING_TYPES.DUE: False,
		SETTING_TYPES.DEFERRED: False
	}
	settings = {**default_settings, **settings}

	if setting_type in array_settings:
		if is_enable:
			settings[setting_type] = settings[setting_type] if setting_type in settings else []
			if cb_data not in settings[setting_type]:
				settings[setting_type].append(cb_data)
				settings[setting_type] = _sort_array_settings(settings[setting_type], setting_type)
		elif cb_data in settings[setting_type]:
			settings[setting_type].remove(cb_data)
	elif not is_enable and (setting_type == SETTING_TYPES.DUE and not settings[SETTING_TYPES.DEFERRED] or
							setting_type == SETTING_TYPES.DEFERRED and not settings[SETTING_TYPES.DUE]):
		update_settings = False
	else:
		settings[setting_type] = is_enable

	priorities = settings[CB_TYPES.PRIORITY_SELECTED]
	del settings[CB_TYPES.PRIORITY_SELECTED]

	if update_settings:
		update_individual_channel(channel_id, settings, priorities)

	ticket_keyboard_state = _get_channel_ticket_settings_state(channel_id, TICKET_MENU_TYPE)
	info_keyboard_state = _get_channel_ticket_settings_state(channel_id, INFO_MENU_TYPE)
	force_update_ticket = (ticket_keyboard_state is not None and
			(ticket_keyboard_state == CB_TYPES.OPEN_CHANNEL_SETTINGS or ticket_keyboard_state == info_keyboard_state))
	show_settings_keyboard(bot, call, True, force_update_ticket)


def _sort_array_settings(array: list, setting_type: str):
	array.sort()
	update_sort_array = False
	sorted_array = []

	if setting_type in [SETTING_TYPES.ASSIGNED, SETTING_TYPES.REPORTED, SETTING_TYPES.FOLLOWED]:
		update_sort_array = True
		for user_tag in user_utils.get_user_tags():
			if user_tag in array:
				sorted_array.append(user_tag)
		if NEW_USER_TYPE in array:
			sorted_array.append(NEW_USER_TYPE)
	elif setting_type == SETTING_TYPES.REMIND:
		update_sort_array = True
		for item in REMIND_TYPES.TYPES_ORDER:
			if item in array:
				sorted_array.append(item)

	if update_sort_array:
		array = sorted_array

	return array


def add_new_user_tag_to_channels(bot: telebot.TeleBot, user_tag: str):
	channel_data = db_utils.get_all_individual_channels()
	for channel in channel_data:
		channel_id, settings = channel
		settings = json.loads(settings)
		assigned = settings.get(SETTING_TYPES.ASSIGNED) or []
		reported = settings.get(SETTING_TYPES.REPORTED) or []
		followed = settings.get(SETTING_TYPES.FOLLOWED) or []

		if not NEW_USER_TYPE in (assigned + reported + followed):
			continue

		if NEW_USER_TYPE in assigned:
			settings[SETTING_TYPES.ASSIGNED].append(user_tag)
		if NEW_USER_TYPE in reported:
			settings[SETTING_TYPES.REPORTED].append(user_tag)
		if NEW_USER_TYPE in followed:
			settings[SETTING_TYPES.FOLLOWED].append(user_tag)

		settings_str = json.dumps(settings)
		db_utils.update_individual_channel_settings(channel_id, settings_str)

		settings_message_id = settings.get(SETTING_TYPES.SETTINGS_MESSAGE_ID)
		if settings_message_id:
			update_settings_message(bot, channel_id, settings_message_id)

		_update_user_tags_in_settings_menu_ticket(bot, channel_id)


def remove_user_tag_from_channels(bot: telebot.TeleBot, user_tag: str):
	channel_data = db_utils.get_all_individual_channels()
	for channel in channel_data:
		channel_id, settings = channel
		settings = json.loads(settings)

		tag_filter = lambda t: t != user_tag
		update_needed = False
		for setting_type in [SETTING_TYPES.ASSIGNED, SETTING_TYPES.REPORTED, SETTING_TYPES.FOLLOWED]:
			if setting_type not in settings:
				continue

			if user_tag in settings[setting_type]:
				update_needed = True
			settings[setting_type] = list(filter(tag_filter, settings[setting_type]))

		if not update_needed:
			continue

		settings_str = json.dumps(settings)
		db_utils.update_individual_channel_settings(channel_id, settings_str)

		settings_message_id = settings.get(SETTING_TYPES.SETTINGS_MESSAGE_ID)
		if settings_message_id:
			update_settings_message(bot, channel_id, settings_message_id)

		_update_user_tags_in_settings_menu_ticket(bot, channel_id)


def _update_user_tags_in_settings_menu_ticket(bot, channel_id):
	if _get_channel_ticket_settings_state(channel_id, TICKET_MENU_TYPE) in [CB_TYPES.ASSIGNED_SELECTED, CB_TYPES.REPORTED_SELECTED,
					 CB_TYPES.FOLLOWED_SELECTED, CB_TYPES.OPEN_CHANNEL_SETTINGS]:
		newest_message_id = db_utils.get_newest_copied_message(channel_id)
		post_data = utils.get_message_content_by_id(bot, channel_id, newest_message_id)
		call = CallbackQuery(0, post_data.from_user, "", "", "", message=post_data)
		keyboard = forwarding_utils.get_keyboard_from_channel_message(bot, call, newest_message_id)
		utils.edit_message_keyboard(bot, post_data, keyboard_markup=keyboard, chat_id=channel_id,
									message_id=newest_message_id)


def delete_individual_settings_for_workspace(bot, channel_id):
	settings = db_utils.get_individual_channel_settings(channel_id)
	if settings:
		settings, _ = settings
		settings = json.loads(settings)
		settings_message_id = settings.get(SETTING_TYPES.SETTINGS_MESSAGE_ID)
		if settings_message_id:
			forwarding_utils.delete_forwarded_message(bot, channel_id, settings_message_id)
		db_utils.delete_individual_channel(channel_id)
