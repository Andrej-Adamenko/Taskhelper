import telebot
from telebot.apihelper import ApiTelegramException
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

import config_utils
import db_utils
import forwarding_utils
import interval_updating_utils
import utils

CALLBACK_PREFIX = "CHNN"


class CB_TYPES:
	ASSIGNED_SELECTED = "AS"
	CREATED_SELECTED = "CR"
	FOLLOWED_SELECTED = "FL"
	SCHEDULED_SELECTED = "SCH"
	PRIORITY_SELECTED = "PR"
	SAVE = "SV"


class CHANNEL_TYPES:
	ASSIGNED = "1"
	CREATED = "2"
	FOLLOWED = "3"
	SCHEDULED = "4"


_TOGGLE_CALLBACKS = [
	CB_TYPES.ASSIGNED_SELECTED,
	CB_TYPES.CREATED_SELECTED,
	CB_TYPES.FOLLOWED_SELECTED,
	CB_TYPES.SCHEDULED_SELECTED,
	CB_TYPES.PRIORITY_SELECTED,
]

_TYPE_SEPARATOR = ","


def get_individual_channel_info(channel_id: int):
	channel_info = db_utils.get_individual_channel(channel_id)
	if not channel_info:
		return [], []

	main_channel_id, user_tag, priorities, types = channel_info
	priorities_list = priorities.split(_TYPE_SEPARATOR)
	types_list = types.split(_TYPE_SEPARATOR)

	return priorities_list, types_list


def generate_settings_keyboard(channel_id: int):
	priorities, types = get_individual_channel_info(channel_id)

	rows = []

	assigned_to_btn = InlineKeyboardButton("Assigned to this user")
	if CHANNEL_TYPES.ASSIGNED in types:
		assigned_to_btn.text += config_utils.BUTTON_TEXTS["CHECK"]
	assigned_to_btn.callback_data = utils.create_callback_str(CALLBACK_PREFIX, CB_TYPES.ASSIGNED_SELECTED)

	created_by_btn = InlineKeyboardButton("Reported by this user")
	if CHANNEL_TYPES.CREATED in types:
		created_by_btn.text += config_utils.BUTTON_TEXTS["CHECK"]
	created_by_btn.callback_data = utils.create_callback_str(CALLBACK_PREFIX, CB_TYPES.CREATED_SELECTED)

	followed_by_btn = InlineKeyboardButton("CCed to this user")
	if CHANNEL_TYPES.FOLLOWED in types:
		followed_by_btn.text += config_utils.BUTTON_TEXTS["CHECK"]
	followed_by_btn.callback_data = utils.create_callback_str(CALLBACK_PREFIX, CB_TYPES.FOLLOWED_SELECTED)

	scheduled_to_btn = InlineKeyboardButton("Scheduled to this user")
	if CHANNEL_TYPES.SCHEDULED in types:
		scheduled_to_btn.text += config_utils.BUTTON_TEXTS["CHECK"]
	scheduled_to_btn.callback_data = utils.create_callback_str(CALLBACK_PREFIX, CB_TYPES.SCHEDULED_SELECTED)

	rows.append([assigned_to_btn])
	rows.append([created_by_btn])
	rows.append([followed_by_btn])
	rows.append([scheduled_to_btn])

	for priority in ["1", "2", "3"]:
		priority_btn = InlineKeyboardButton(f"Priority {priority}")
		if priority in priorities:
			priority_btn.text += config_utils.BUTTON_TEXTS["CHECK"]
		priority_btn.callback_data = utils.create_callback_str(CALLBACK_PREFIX, CB_TYPES.PRIORITY_SELECTED, priority)
		rows.append([priority_btn])

	save_btn = InlineKeyboardButton(f"Save")
	save_btn.callback_data = utils.create_callback_str(CALLBACK_PREFIX, CB_TYPES.SAVE)
	rows.append([save_btn])

	return InlineKeyboardMarkup(rows)


def send_settings_keyboard(bot: telebot.TeleBot, channel_id: int):
	keyboard = generate_settings_keyboard(channel_id)
	text = '''
		Please select this channel's settings, click on buttons to select/deselect filtering parameters. When all needed parameters were selected press "Save" button. You can call this settings menu using "/show_settings" command.
	'''
	bot.send_message(chat_id=channel_id, text=text, reply_markup=keyboard)


def handle_callback(bot: telebot.TeleBot, call: telebot.types.CallbackQuery):
	callback_type, other_data = utils.parse_callback_str(call.data)

	if callback_type in _TOGGLE_CALLBACKS:
		toggle_button(bot, call, callback_type, other_data)
	elif callback_type == CB_TYPES.SAVE:
		save_channel_settings(bot, call)


def toggle_button(bot: telebot.TeleBot, call: CallbackQuery, cb_type: str, cb_data: str):
	reply_markup = call.message.reply_markup
	buttons = [btn for row in reply_markup.keyboard for btn in row]
	for btn in buttons:
		callback_str = btn.callback_data
		btn_cb_type, btn_cb_data = utils.parse_callback_str(callback_str)
		if btn_cb_type == cb_type and btn_cb_data == cb_data:
			if btn.text.endswith(config_utils.BUTTON_TEXTS["CHECK"]):
				btn.text = btn.text[:-len(config_utils.BUTTON_TEXTS["CHECK"])]
			else:
				btn.text += config_utils.BUTTON_TEXTS["CHECK"]

	bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.id, reply_markup=reply_markup)


def save_channel_settings(bot: telebot.TeleBot, call: CallbackQuery):
	main_channel_id = db_utils.get_main_channel_from_user(call.from_user.id)
	if not main_channel_id and call.from_user.username:
		main_channel_id = db_utils.get_main_channel_from_user("@" + call.from_user.username)

	if not main_channel_id:
		bot.answer_callback_query(callback_query_id=call.id, text="User not found.")
		return

	reply_markup = call.message.reply_markup
	buttons = [btn for row in reply_markup.keyboard for btn in row]

	priorities = []
	types = []

	for btn in buttons:
		callback_str = btn.callback_data
		btn_cb_type, btn_cb_data = utils.parse_callback_str(callback_str)
		if not btn.text.endswith(config_utils.BUTTON_TEXTS["CHECK"]) or btn_cb_type not in _TOGGLE_CALLBACKS:
			continue

		if btn_cb_type == CB_TYPES.PRIORITY_SELECTED:
			priority = btn_cb_data[0]
			priorities.append(priority)
		elif btn_cb_type == CB_TYPES.ASSIGNED_SELECTED:
			types.append(CHANNEL_TYPES.ASSIGNED)
		elif btn_cb_type == CB_TYPES.FOLLOWED_SELECTED:
			types.append(CHANNEL_TYPES.FOLLOWED)
		elif btn_cb_type == CB_TYPES.CREATED_SELECTED:
			types.append(CHANNEL_TYPES.CREATED)
		elif btn_cb_type == CB_TYPES.SCHEDULED_SELECTED:
			types.append(CHANNEL_TYPES.SCHEDULED)

	channel_id = call.message.chat.id
	priorities = _TYPE_SEPARATOR.join(priorities)
	types = _TYPE_SEPARATOR.join(types)
	db_utils.insert_or_update_individual_channel(main_channel_id, channel_id, priorities, types)

	user_tag = db_utils.get_individual_channel_user_tag(channel_id)
	forwarding_utils.delete_forwarded_message(bot, call.message.chat.id, call.message.id)
	if not user_tag:
		bot.send_message(
			chat_id=call.message.chat.id,
			text="Now you need to set user tag for this channel using command \"/set_user_tag {user_tag}\". Also you can change user tag for this channel using same command. After setting user tag bot will automatically start forwarding tickets to this channel according to the selected parameters.",
		)

	interval_updating_utils.start_interval_updating(bot)
