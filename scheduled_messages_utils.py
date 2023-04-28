import calendar
import datetime

import telebot
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

import db_utils
import forwarding_utils
import utils
from config_utils import SCHEDULED_STORAGE_CHAT_IDS

CALLBACK_PREFIX = "SCH"

CURRENT_DATE_SYMBOL = "✅"

class CB_TYPES:
	MONTH_CALENDAR = "CALENDAR"
	SELECT_DAY = "DAY"
	NEXT_MONTH = "NEXT"
	PREVIOUS_MONTH = "PREV"
	SELECT_HOUR = "HOUR"
	SELECT_MINUTE = "MIN"
	SCHEDULE_MESSAGE = "SCHEDULE"


def schedule_message(bot: telebot.TeleBot, message: telebot.types.Message, send_time: int):
	main_message_id = message.message_id
	main_channel_id = message.chat.id

	main_channel_id_str = str(main_channel_id)
	if main_channel_id_str not in SCHEDULED_STORAGE_CHAT_IDS:
		return

	scheduled_message = db_utils.get_scheduled_message(main_message_id, main_channel_id)
	if scheduled_message:
		scheduled_message_id, scheduled_chat_id, _ = scheduled_message
		db_utils.update_scheduled_message(scheduled_message_id, scheduled_chat_id, send_time)
		forwarding_utils.forward_and_add_inline_keyboard(bot, message, force_forward=True)
		return

	scheduled_storage_chat_id = SCHEDULED_STORAGE_CHAT_IDS[main_channel_id_str]
	copied_message = bot.copy_message(chat_id=scheduled_storage_chat_id, from_chat_id=main_channel_id, message_id=main_message_id)
	scheduled_message_id = copied_message.message_id
	db_utils.insert_scheduled_message(main_message_id, main_channel_id, scheduled_message_id, scheduled_storage_chat_id, send_time)


def handle_callback(bot: telebot.TeleBot, call: telebot.types.CallbackQuery):
	callback_type, other_data = utils.parse_callback_str(call.data)

	if callback_type == CB_TYPES.MONTH_CALENDAR:
		keyboard = generate_days_buttons()
		utils.edit_message_keyboard(bot, call.message, keyboard)
	elif callback_type == CB_TYPES.SCHEDULE_MESSAGE:
		schedule_message_event(bot, call.message, other_data)
	elif callback_type == CB_TYPES.NEXT_MONTH:
		change_month_event(bot, call.message, other_data, True)
	elif callback_type == CB_TYPES.PREVIOUS_MONTH:
		change_month_event(bot, call.message, other_data, False)
	elif callback_type == CB_TYPES.SELECT_DAY:
		select_day_event(bot, call.message, other_data)
	elif callback_type == CB_TYPES.SELECT_HOUR:
		select_hour_event(bot, call.message, other_data)


def change_month_event(bot: telebot.TeleBot, msg_data: telebot.types.Message, args: list, forward: bool):
	date_str = args[0]
	current_month, current_year = [int(num) for num in date_str.split(".")]
	current_month += 1 if forward else -1

	if current_month > 12:
		current_year += 1
		current_month = 1
	elif current_month < 1:
		current_year -= 1
		current_month = 12

	keyboard = generate_days_buttons([current_month, current_year])
	utils.edit_message_keyboard(bot, msg_data, keyboard)


def select_day_event(bot: telebot.TeleBot, msg_data: telebot.types.Message, args: list):
	current_date = args[0]
	keyboard = generate_hours_buttons(current_date)
	utils.edit_message_keyboard(bot, msg_data, keyboard)


def select_hour_event(bot: telebot.TeleBot, msg_data: telebot.types.Message, args: list):
	current_date, current_hour = args
	keyboard = generate_minutes_buttons(current_date, current_hour)
	utils.edit_message_keyboard(bot, msg_data, keyboard)


def schedule_message_event(bot: telebot.TeleBot, msg_data: telebot.types.Message, args: list):
	date, hour, minute = args
	format_str = "%d.%m.%Y %H:%M"
	dt = datetime.datetime.strptime(f"{date} {hour}:{minute}", format_str)
	send_time = int(dt.timestamp())

	forwarding_utils.forward_and_add_inline_keyboard(bot, msg_data)
	schedule_message(bot, msg_data, send_time)


def generate_schedule_button():
	callback_data = utils.create_callback_str(CALLBACK_PREFIX, CB_TYPES.MONTH_CALENDAR)
	schedule_button = InlineKeyboardButton(f"🕒", callback_data=callback_data)
	return schedule_button


def generate_days_buttons(date_info=None):
	now = datetime.datetime.now()

	if date_info:
		current_month, current_year = date_info
	else:
		current_year = now.year
		current_month = now.month

	current_date_str = f"{current_month}.{current_year}"

	left_arrow_cb = utils.create_callback_str(CALLBACK_PREFIX, CB_TYPES.PREVIOUS_MONTH, current_date_str)
	left_arrow_button = InlineKeyboardButton("<", callback_data=left_arrow_cb)

	right_arrow_cb = utils.create_callback_str(CALLBACK_PREFIX, CB_TYPES.NEXT_MONTH, current_date_str)
	right_arrow_button = InlineKeyboardButton(">", callback_data=right_arrow_cb)

	current_month_button = InlineKeyboardButton(f"{current_year} {calendar.month_name[current_month]}", callback_data="_")

	keyboard_rows = [[left_arrow_button, current_month_button, right_arrow_button]]

	month_list = calendar.monthcalendar(current_year, current_month)
	for week in month_list:
		week_buttons = []
		for day in week:
			button_text = str(day) if day > 0 else " "
			if now.day == day and now.month == current_month and now.year == current_year:
				button_text = CURRENT_DATE_SYMBOL + button_text
			callback = "_"
			if day > 0:
				callback = utils.create_callback_str(CALLBACK_PREFIX, CB_TYPES.SELECT_DAY, f"{day}.{current_date_str}")

			day_button = InlineKeyboardButton(button_text, callback_data=callback)
			week_buttons.append(day_button)
		keyboard_rows.append(week_buttons)

	return InlineKeyboardMarkup(keyboard_rows)


def generate_hours_buttons(current_date):
	keyboard_rows = []
	width = 6
	height = 4

	for i in range(height):
		buttons_row = []
		for j in range(width):
			hour = i * width + j
			hour = str(hour).zfill(2)
			callback = utils.create_callback_str(CALLBACK_PREFIX, CB_TYPES.SELECT_HOUR, current_date, hour)
			button = InlineKeyboardButton(f"{hour}:00", callback_data=callback)
			buttons_row.append(button)

		keyboard_rows.append(buttons_row)

	return InlineKeyboardMarkup(keyboard_rows)


def generate_minutes_buttons(current_date, current_hour):
	keyboard_rows = []
	width = 2
	height = 6

	for i in range(height):
		buttons_row = []
		for j in range(width):
			minute = (i * width + j) * 5
			minute = str(minute).zfill(2)
			callback = utils.create_callback_str(CALLBACK_PREFIX, CB_TYPES.SCHEDULE_MESSAGE, current_date, current_hour, minute)
			button = InlineKeyboardButton(f"{current_hour}:{minute}", callback_data=callback)
			buttons_row.append(button)

		keyboard_rows.append(buttons_row)

	return InlineKeyboardMarkup(keyboard_rows)

