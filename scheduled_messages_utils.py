import calendar
import datetime
import logging
import threading
import time

import pytz
import telebot
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

import db_utils
import forwarding_utils
import hashtag_utils
import utils
from config_utils import SCHEDULED_STORAGE_CHAT_IDS, TIMEZONE_NAME

CALLBACK_PREFIX = "SCH"

CURRENT_DATE_SYMBOL = "✅"

SCHEDULED_MESSAGES_LIST: list = []

DATE_FORMAT = "%Y-%m-%d %H:%M"

class CB_TYPES:
	MONTH_CALENDAR = "CALENDAR"
	SELECT_DAY = "DAY"
	NEXT_MONTH = "NEXT"
	PREVIOUS_MONTH = "PREV"
	SELECT_HOUR = "HOUR"
	SELECT_MINUTE = "MIN"
	SCHEDULE_MESSAGE = "SCHEDULE"


def schedule_message(bot: telebot.TeleBot, message: telebot.types.Message, send_time: int, dt: datetime.datetime):
	main_message_id = message.message_id
	main_channel_id = message.chat.id

	main_channel_id_str = str(main_channel_id)
	if main_channel_id_str not in SCHEDULED_STORAGE_CHAT_IDS:
		return

	scheduled_messages = db_utils.get_scheduled_messages(main_message_id, main_channel_id)
	if scheduled_messages:
		db_utils.update_scheduled_message(main_message_id, main_channel_id, send_time)

		for msg in SCHEDULED_MESSAGES_LIST:
			message_id, channel_id, _ = msg
			if message_id == main_message_id and channel_id == main_channel_id:
				msg[2] = send_time

		hashtags, message = hashtag_utils.extract_hashtags(message, main_channel_id, True)
		hashtags[0] = hashtag_utils.SCHEDULED_TAG + " " + dt.strftime(DATE_FORMAT)
		forwarding_utils.rearrange_hashtags(bot, message, hashtags)

		forwarding_utils.add_control_buttons(bot, message, hashtags)
		forwarding_utils.forward_to_subchannel(bot, message, hashtags)
		return

	if send_time <= 0:
		return

	hashtags, message = hashtag_utils.extract_hashtags(message, main_channel_id, True)
	hashtags[0] = hashtag_utils.SCHEDULED_TAG + " " + dt.strftime(DATE_FORMAT)
	forwarding_utils.rearrange_hashtags(bot, message, hashtags)

	for user_tag in hashtags[1:-1]:
		if user_tag not in SCHEDULED_STORAGE_CHAT_IDS[main_channel_id_str]:
			continue
		scheduled_storage_id = SCHEDULED_STORAGE_CHAT_IDS[main_channel_id_str][user_tag]
		copied_message = bot.copy_message(chat_id=scheduled_storage_id, from_chat_id=main_channel_id, message_id=main_message_id)
		scheduled_message_id = copied_message.message_id
		db_utils.insert_scheduled_message(main_message_id, main_channel_id, scheduled_message_id, scheduled_storage_id, send_time)

	forwarding_utils.add_control_buttons(bot, message, hashtags)
	forwarding_utils.forward_to_subchannel(bot, message, hashtags)

	scheduled_info = [main_message_id, main_channel_id, send_time]
	insert_schedule_message_info(scheduled_info)


def insert_schedule_message_info(scheduled_info):
	send_time = scheduled_info[2]
	for i in range(len(SCHEDULED_MESSAGES_LIST)):
		current_send_time = SCHEDULED_MESSAGES_LIST[i][2]
		if send_time < current_send_time:
			SCHEDULED_MESSAGES_LIST.insert(i, scheduled_info)
			return
	SCHEDULED_MESSAGES_LIST.append(scheduled_info)


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


def schedule_message_event(bot: telebot.TeleBot, post_data: telebot.types.Message, args: list):
	date, hour, minute = args
	format_str = "%d.%m.%Y %H:%M"
	dt = datetime.datetime.strptime(f"{date} {hour}:{minute}", format_str)
	timezone = pytz.timezone(TIMEZONE_NAME)
	dt = timezone.localize(dt)
	send_time = int(dt.astimezone(pytz.UTC).timestamp())

	schedule_message(bot, post_data, send_time, dt)


def generate_schedule_button():
	callback_data = utils.create_callback_str(CALLBACK_PREFIX, CB_TYPES.MONTH_CALENDAR)
	schedule_button = InlineKeyboardButton(f"🕒", callback_data=callback_data)
	return schedule_button


def generate_days_buttons(date_info=None):
	timezone = pytz.timezone(TIMEZONE_NAME)
	now = datetime.datetime.now(tz=timezone)

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

	back_button_callback = utils.create_callback_str(forwarding_utils.CALLBACK_PREFIX, forwarding_utils.CB_TYPES.SAVE)
	back_button = InlineKeyboardButton("Back", callback_data=back_button_callback)

	keyboard_rows = [[back_button]]
	keyboard_rows += [[left_arrow_button, current_month_button, right_arrow_button]]

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
	back_button_callback = utils.create_callback_str(CALLBACK_PREFIX, CB_TYPES.MONTH_CALENDAR)
	back_button = InlineKeyboardButton("Back", callback_data=back_button_callback)

	keyboard_rows = [[back_button]]
	width = 4
	height = 6

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
	back_button_callback = utils.create_callback_str(CALLBACK_PREFIX, CB_TYPES.SELECT_DAY, current_date)
	back_button = InlineKeyboardButton("Back", callback_data=back_button_callback)

	keyboard_rows = [[back_button]]
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


def send_scheduled_message(bot: telebot.TeleBot, scheduled_message_info):
	main_message_id, main_channel_id, send_time = scheduled_message_info
	message = forwarding_utils.get_message_content_by_id(bot, main_channel_id, main_message_id)
	if message is None:
		return

	message.message_id = main_message_id
	message.chat.id = main_channel_id

	hashtags, post_data = hashtag_utils.extract_hashtags(message, main_channel_id)

	scheduled_messages = db_utils.get_scheduled_messages(main_message_id, main_channel_id)
	if not scheduled_messages:
		SCHEDULED_MESSAGES_LIST.remove(scheduled_message_info)
		forwarding_utils.add_control_buttons(bot, post_data, hashtags)
		forwarding_utils.forward_to_subchannel(bot, post_data, hashtags)
		return

	for msg in scheduled_messages:
		scheduled_message_id, scheduled_channel_id, send_time = msg
		bot.delete_message(chat_id=scheduled_channel_id, message_id=scheduled_message_id)

	hashtags[0] = hashtag_utils.OPENED_TAG

	db_utils.delete_scheduled_message_main(main_message_id, main_channel_id)

	forwarding_utils.rearrange_hashtags(bot, post_data, hashtags)
	forwarding_utils.add_control_buttons(bot, post_data, hashtags)
	forwarding_utils.forward_to_subchannel(bot, post_data, hashtags)

	SCHEDULED_MESSAGES_LIST.remove(scheduled_message_info)


def scheduled_message_comparison_func(msg):
	send_time = msg[2]
	return send_time


def get_scheduled_messages_for_send():
	filtered_messages = []
	current_time = time.time()
	for msg in SCHEDULED_MESSAGES_LIST:
		if msg[2] < current_time:
			filtered_messages.append(msg)
		else:
			break
	return filtered_messages


def start_scheduled_thread(bot: telebot.TeleBot):
	scheduled_messages = db_utils.get_all_scheduled_messages()
	for m in scheduled_messages:
		main_message_id, main_channel_id, scheduled_message_id, scheduled_storage_id, send_time = m
		SCHEDULED_MESSAGES_LIST.append([main_message_id, main_channel_id, send_time])
	SCHEDULED_MESSAGES_LIST.sort(key=scheduled_message_comparison_func)

	threading.Thread(target=schedule_loop_thread, args=(bot,)).start()


def schedule_loop_thread(bot: telebot.TeleBot):
	while 1:
		for_send = get_scheduled_messages_for_send()
		for msg_info in for_send:
			try:
				send_scheduled_message(bot, msg_info)
			except Exception as E:
				logging.error(f"Exception during sending scheduled message: {E}")
		time.sleep(1)


def update_scheduled_messages(bot: telebot.TeleBot, scheduled_messages_info: list, post_data: telebot.types.Message, hashtags: list):
	_, _, send_time = scheduled_messages_info[0]

	main_message_id = post_data.message_id
	main_channel_id = post_data.chat.id

	if hashtag_utils.CLOSED_TAG in hashtags:
		for msg in scheduled_messages_info:
			scheduled_message_id, scheduled_channel_id, _ = msg
			bot.delete_message(chat_id=scheduled_channel_id, message_id=scheduled_message_id)
		db_utils.delete_scheduled_message_main(main_message_id, main_channel_id)

		for msg in SCHEDULED_MESSAGES_LIST:
			message_id, channel_id, _ = msg
			if message_id == main_message_id and channel_id == main_channel_id:
				msg[2] = send_time
		return

	main_channel_id_str = str(main_channel_id)
	storage_channels = SCHEDULED_STORAGE_CHAT_IDS[main_channel_id_str]

	for msg in scheduled_messages_info:
		scheduled_message_id, scheduled_channel_id, _ = msg
		user_tag = utils.get_key_by_value(storage_channels, scheduled_channel_id)
		if user_tag not in hashtags:
			bot.delete_message(chat_id=scheduled_channel_id, message_id=scheduled_message_id)
			db_utils.delete_scheduled_message(scheduled_message_id, scheduled_channel_id)
			scheduled_messages_info.remove(msg)

	hashtag_scheduled_channels = [m[1] for m in scheduled_messages_info]
	for user_tag in hashtags[1:-1]:
		if user_tag not in storage_channels:
			continue
		scheduled_storage_id = storage_channels[user_tag]
		if scheduled_storage_id not in hashtag_scheduled_channels:
			copied_message = bot.copy_message(chat_id=scheduled_storage_id, from_chat_id=main_channel_id, message_id=main_message_id)
			scheduled_message_id = copied_message.message_id
			db_utils.insert_scheduled_message(main_message_id, main_channel_id, scheduled_message_id, scheduled_storage_id, send_time)

	for msg in scheduled_messages_info:
		scheduled_message_id, scheduled_channel_id, _ = msg
		post_data.message_id = scheduled_message_id
		post_data.chat.id = scheduled_channel_id
		utils.edit_message_content(bot, post_data, text=post_data.text, entities=post_data.entities)

