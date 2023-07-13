import logging
import threading
import time

import telebot.types

import db_utils
import config_utils
import forwarding_utils
import interval_updating_utils
from hashtag_data import HashtagData

_DAILY_CHECK_INTERVAL = 60 * 60 * 24


def update_ticket_data(main_message_id: int, main_channel_id: int, hashtag_data: HashtagData):
	user_tags = hashtag_data.get_all_users()
	user_tags = ",".join(user_tags) if user_tags else None
	priority = hashtag_data.get_priority_number()
	is_ticket_opened = hashtag_data.is_opened()
	db_utils.insert_or_update_ticket_data(main_message_id, main_channel_id, is_ticket_opened, user_tags, priority)


def set_ticket_update_time(main_message_id: int, main_channel_id: int):
	db_utils.set_ticket_update_time(main_message_id, main_channel_id, int(time.time()))


def update_user_last_interaction(main_message_id: int, main_channel_id: int, msg_data: telebot.types.Message):
	user_tags = db_utils.get_tags_from_user_id(msg_data.from_user.id)
	if not user_tags and msg_data.from_user.username:
		user_tags = db_utils.get_tags_from_user_id(msg_data.from_user.username)

	if not user_tags:
		return

	for user_tag in user_tags:
		highest_priority = db_utils.get_user_highest_priority(main_channel_id, user_tag)
		_, priority, _ = db_utils.get_ticket_data(main_message_id, main_channel_id)
		if priority == highest_priority:
			db_utils.insert_or_update_last_user_interaction(main_channel_id, user_tag, int(time.time()))
			logging.info(f"Updated {msg_data.from_user.id, user_tag} user last interaction.")


def ticket_update_time_comparator(ticket):
	main_channel_id, main_message_id, update_time, remind_time = ticket
	return max(update_time or 0, remind_time or 0)


def get_message_for_reminding(main_channel_id: int, user_tag: str, priority: str):
	ticket_data = db_utils.get_tickets_for_reminding(main_channel_id, user_tag, priority)
	if not ticket_data:
		logging.info(f"No tickets for reminding were found in {user_tag, priority, main_channel_id}")
		return

	filtered_ticket_data = []
	for ticket in ticket_data:
		main_channel_id, main_message_id, update_time, remind_time = ticket
		copied_data = db_utils.find_copied_message_from_main(main_message_id, main_channel_id, user_tag, priority)
		if copied_data:
			filtered_ticket_data.append(ticket)

	if not filtered_ticket_data:
		logging.info(f"No forwarded tickets for reminding were found in {user_tag, priority, main_channel_id}")
		return

	filtered_ticket_data.sort(key=ticket_update_time_comparator)
	main_channel_id, main_message_id, update_time, remind_time = filtered_ticket_data[0]
	return main_message_id


def send_daily_reminders(bot: telebot.TeleBot):
	user_data = db_utils.get_all_users()
	for user in user_data:
		main_channel_id, user_id, user_tag = user
		if not db_utils.is_user_reminder_data_exists(main_channel_id, user_tag):
			db_utils.insert_or_update_last_user_interaction(main_channel_id, user_tag, None)

		last_interaction_time = db_utils.get_last_interaction_time(main_channel_id, user_tag) or 0
		seconds_since_last_interaction = time.time() - last_interaction_time
		if seconds_since_last_interaction < config_utils.REMINDER_TIME_WITHOUT_INTERACTION * 60:
			continue
		highest_priority = db_utils.get_user_highest_priority(main_channel_id, user_tag)
		message_to_remind = get_message_for_reminding(main_channel_id, user_tag, highest_priority)
		if not message_to_remind:
			continue

		copied_message_data = db_utils.find_copied_message_from_main(message_to_remind, main_channel_id, user_tag, highest_priority)
		if not copied_message_data:
			logging.warning(f"Not found forwarded message for reminding {main_channel_id, user_tag, message_to_remind}")
			continue
		copied_message_id, copied_channel_id = copied_message_data

		forwarding_utils.delete_forwarded_message(bot, copied_channel_id, copied_message_id)
		interval_updating_utils.update_older_message(bot, main_channel_id, message_to_remind)

		db_utils.insert_or_update_remind_time(message_to_remind, main_channel_id, user_tag, int(time.time()))
		logging.info(f"Sent reminder to {user_id, user_tag}, message: {message_to_remind, main_channel_id}.")


def start_reminder_thread(bot: telebot.TeleBot):
	threading.Thread(target=reminder_thread, args=(bot,)).start()


def reminder_thread(bot: telebot.TeleBot):
	while 1:
		if time.time() - config_utils.LAST_DAILY_REMINDER_TIME > _DAILY_CHECK_INTERVAL:
			send_daily_reminders(bot)
			config_utils.LAST_DAILY_REMINDER_TIME = int(time.time())
			config_utils.update_config({"LAST_DAILY_REMINDER_TIME": config_utils.LAST_DAILY_REMINDER_TIME})
		time.sleep(1)
