from unittest import TestCase, main
from unittest.mock import patch, Mock

import pytz
import datetime
from telebot import TeleBot
from telebot.types import CallbackQuery

import channel_manager
from tests import test_helper
from hashtag_data import HashtagData
import scheduled_messages_utils


@patch("config_utils.TIMEZONE_NAME", "UTC")
class UpdateStatusFromTagsTest(TestCase):
	def setUp(self):
		self.scheduled_message_dispatcher = scheduled_messages_utils.ScheduledMessageDispatcher()

	@patch("time.time", return_value=1700000000)
	@patch("db_utils.is_message_scheduled", return_value=False)
	@patch("utils.add_comment_to_ticket")
	@patch("db_utils.insert_scheduled_message")
	@patch("scheduled_messages_utils.ScheduledMessageDispatcher.insert_scheduled_message_info")
	def test_add_ticket_to_scheduled(self, mock_insert_scheduled_message_info, mock_insert_scheduled_message, mock_add_comment_to_ticket, *args):
		mock_bot = Mock(spec=TeleBot)

		main_message_id = 33
		main_channel_id = 1111

		mock_msg_data = test_helper.create_mock_message("", [])
		mock_msg_data.message_id = main_message_id
		mock_msg_data.chat = Mock(id=main_channel_id)

		mock_hashtag_data = Mock(spec=HashtagData)
		mock_hashtag_data.ignore_comments = False
		mock_hashtag_data.get_scheduled_datetime = Mock(return_value="2024-08-01 13:00")
		mock_hashtag_data.is_scheduled = Mock(return_value=True)

		self.scheduled_message_dispatcher.update_status_from_tags(mock_bot, mock_msg_data, mock_hashtag_data)
		mock_insert_scheduled_message_info.assert_called_once()
		mock_insert_scheduled_message.assert_called_once()
		mock_add_comment_to_ticket.assert_called_once()

	@patch("time.time", return_value=1700000000)
	@patch("db_utils.is_message_scheduled", return_value=False)
	@patch("utils.add_comment_to_ticket")
	@patch("db_utils.insert_scheduled_message")
	@patch("scheduled_messages_utils.ScheduledMessageDispatcher.insert_scheduled_message_info")
	def test_add_ticket_to_scheduled_and_ignore_comments(self, mock_insert_scheduled_message_info, mock_insert_scheduled_message, mock_add_comment_to_ticket, *args):
		mock_bot = Mock(spec=TeleBot)

		main_message_id = 33
		main_channel_id = 1111

		mock_msg_data = test_helper.create_mock_message("", [])
		mock_msg_data.message_id = main_message_id
		mock_msg_data.chat = Mock(id=main_channel_id)

		mock_hashtag_data = Mock(spec=HashtagData)
		mock_hashtag_data.ignore_comments = True
		mock_hashtag_data.get_scheduled_datetime = Mock(return_value="2024-08-01 13:00")
		mock_hashtag_data.is_scheduled = Mock(return_value=True)

		self.scheduled_message_dispatcher.update_status_from_tags(mock_bot, mock_msg_data, mock_hashtag_data)
		mock_add_comment_to_ticket.assert_not_called()
		mock_insert_scheduled_message_info.assert_called_once()
		mock_insert_scheduled_message.assert_called_once()


	@patch("db_utils.delete_scheduled_message_main")
	@patch("scheduled_messages_utils.ScheduledMessageDispatcher.remove_scheduled_message")
	def test_remove_ticket_from_scheduled(self, mock_remove_scheduled_message, mock_delete_scheduled_message_main, *args):
		mock_bot = Mock(spec=TeleBot)

		main_message_id = 33
		main_channel_id = 1111

		mock_msg_data = test_helper.create_mock_message("", [])
		mock_msg_data.message_id = main_message_id
		mock_msg_data.chat = Mock(id=main_channel_id)

		mock_hashtag_data = Mock(spec=HashtagData)
		mock_hashtag_data.is_scheduled = Mock(return_value=False)

		self.scheduled_message_dispatcher.update_status_from_tags(mock_bot, mock_msg_data, mock_hashtag_data)
		mock_remove_scheduled_message.assert_called_once()
		mock_delete_scheduled_message_main.assert_called_once()

	@patch("db_utils.is_message_scheduled", return_value=True)
	@patch("db_utils.get_scheduled_message_send_time", return_value=1722517200)
	@patch("db_utils.update_scheduled_message")
	def test_no_rescheduling(self, mock_update_scheduled_message, *args):
		mock_bot = Mock(spec=TeleBot)

		main_message_id = 33
		main_channel_id = 1111

		mock_msg_data = test_helper.create_mock_message("", [])
		mock_msg_data.message_id = main_message_id
		mock_msg_data.chat = Mock(id=main_channel_id)

		mock_hashtag_data = Mock(spec=HashtagData)
		mock_hashtag_data.get_scheduled_datetime = Mock(return_value="2024-08-01 13:00")
		mock_hashtag_data.is_scheduled = Mock(return_value=True)

		self.scheduled_message_dispatcher.update_status_from_tags(mock_bot, mock_msg_data, mock_hashtag_data)
		mock_update_scheduled_message.assert_not_called()

	@patch("db_utils.is_message_scheduled", return_value=True)
	@patch("db_utils.get_scheduled_message_send_time", return_value=1800000000)
	@patch("utils.add_comment_to_ticket")
	@patch("scheduled_messages_utils.ScheduledMessageDispatcher.update_scheduled_time")
	def test_reschedule_ticket(self, mock_update_scheduled_time, mock_add_comment_to_ticket, *args):
		mock_bot = Mock(spec=TeleBot)

		main_message_id = 33
		main_channel_id = 1111

		mock_msg_data = test_helper.create_mock_message("", [])
		mock_msg_data.message_id = main_message_id
		mock_msg_data.chat = Mock(id=main_channel_id)

		mock_hashtag_data = Mock(spec=HashtagData)
		mock_hashtag_data.ignore_comments = False
		mock_hashtag_data.get_scheduled_datetime = Mock(return_value="2024-08-01 13:00")
		mock_hashtag_data.is_scheduled = Mock(return_value=True)

		self.scheduled_message_dispatcher.update_status_from_tags(mock_bot, mock_msg_data, mock_hashtag_data)
		mock_update_scheduled_time.assert_called_once_with(main_message_id, main_channel_id, 1722517200)
		mock_add_comment_to_ticket.assert_called_once_with(mock_bot, mock_msg_data, "Ticket was deferred again to 2024-08-01 13:00.")

	@patch("db_utils.is_message_scheduled", return_value=True)
	@patch("db_utils.get_scheduled_message_send_time", return_value=1800000000)
	@patch("utils.add_comment_to_ticket")
	@patch("scheduled_messages_utils.ScheduledMessageDispatcher.update_scheduled_time")
	def test_reschedule_ticket_and_ignore_comments(self, mock_update_scheduled_time, mock_add_comment_to_ticket, *args):
		mock_bot = Mock(spec=TeleBot)

		main_message_id = 33
		main_channel_id = 1111

		mock_msg_data = test_helper.create_mock_message("", [])
		mock_msg_data.message_id = main_message_id
		mock_msg_data.chat = Mock(id=main_channel_id)

		mock_hashtag_data = Mock(spec=HashtagData)
		mock_hashtag_data.ignore_comments = True
		mock_hashtag_data.get_scheduled_datetime = Mock(return_value="2024-08-01 13:00")
		mock_hashtag_data.is_scheduled = Mock(return_value=True)

		self.scheduled_message_dispatcher.update_status_from_tags(mock_bot, mock_msg_data, mock_hashtag_data)
		mock_update_scheduled_time.assert_called_once_with(main_message_id, main_channel_id, 1722517200)
		mock_add_comment_to_ticket.assert_not_called()


class UpdateTimezoneTest(TestCase):
	def setUp(self):
		self.scheduled_message_dispatcher = scheduled_messages_utils.ScheduledMessageDispatcher()

	@patch("scheduled_messages_utils.ScheduledMessageDispatcher.update_scheduled_time")
	@patch("db_utils.get_all_scheduled_messages")
	def test_regular_update(self, mock_get_all_scheduled_messages, mock_update_scheduled_time, *args):
		current_timezone = pytz.timezone("Europe/Kiev")
		new_timezone = pytz.timezone("Europe/London")

		send_date = "2024-04-15 14:00"
		send_datetime = datetime.datetime.strptime(send_date, "%Y-%m-%d %H:%M")
		send_time = current_timezone.localize(send_datetime).timestamp()

		mock_get_all_scheduled_messages.return_value = [
			[78, -10012345678, send_time],
		]

		self.scheduled_message_dispatcher.update_timezone(current_timezone, new_timezone)
		expected_send_time = new_timezone.localize(send_datetime).timestamp()
		mock_update_scheduled_time.assert_called_once_with(78, -10012345678, expected_send_time)

	@patch("scheduled_messages_utils.ScheduledMessageDispatcher.update_scheduled_time")
	@patch("db_utils.get_all_scheduled_messages")
	def test_dst_time(self, mock_get_all_scheduled_messages, mock_update_scheduled_time, *args):
		current_timezone = pytz.timezone("Asia/Hong_Kong")
		new_timezone = pytz.timezone("Europe/Kiev")

		send_date = "2024-10-27 02:00"
		send_datetime = datetime.datetime.strptime(send_date, "%Y-%m-%d %H:%M")
		send_time = current_timezone.localize(send_datetime).timestamp()

		mock_get_all_scheduled_messages.return_value = [
			[78, -10012345678, send_time],
		]

		self.scheduled_message_dispatcher.update_timezone(current_timezone, new_timezone)
		expected_send_time = new_timezone.localize(send_datetime).timestamp()
		mock_update_scheduled_time.assert_called_once_with(78, -10012345678, expected_send_time)


@patch("config_utils.TIMEZONE_NAME", "UTC")
class ScheduleMessageTest(TestCase):
	def setUp(self):
		self.scheduled_message_dispatcher = scheduled_messages_utils.ScheduledMessageDispatcher()

	@patch("db_utils.is_main_channel_exists", return_value=True)
	@patch("hashtag_data.HashtagData.find_scheduled_tag_in_other_hashtags", return_value=None)
	@patch("hashtag_data.HashtagData.__init__", return_value=None)
	@patch("db_utils.is_message_scheduled", return_value=False)
	@patch("db_utils.insert_scheduled_message")
	@patch("utils.add_comment_to_ticket")
	@patch("forwarding_utils.update_message_and_forward_to_subchannels")
	@patch("scheduled_messages_utils.ScheduledMessageDispatcher.insert_scheduled_message_info")
	def test_not_scheduled_message(self, mock_insert_scheduled_message_info, *args):
		mock_bot = Mock(spec=TeleBot)
		mock_call = Mock(spec=CallbackQuery)

		mock_call.message = test_helper.create_mock_message("", [])
		mock_call.message.message_id = 152
		mock_call.message.chat = Mock(id=12345678)
		mock_call.from_user = Mock(first_name="Name")

		send_time = 1722517200

		self.scheduled_message_dispatcher.schedule_message(mock_bot, mock_call, send_time)
		mock_insert_scheduled_message_info.assert_called_once()

	@patch("db_utils.is_main_channel_exists", return_value=True)
	@patch("hashtag_data.HashtagData.find_scheduled_tag_in_other_hashtags", return_value=None)
	@patch("hashtag_data.HashtagData.__init__", return_value=None)
	@patch("db_utils.is_message_scheduled", return_value=True)
	@patch("forwarding_utils.update_message_and_forward_to_subchannels")
	@patch("utils.add_comment_to_ticket")
	@patch("scheduled_messages_utils.ScheduledMessageDispatcher.update_scheduled_time")
	def test_already_scheduled_message(self, mock_update_scheduled_time, mock_add_comment_to_ticket, *args):
		mock_bot = Mock(spec=TeleBot)
		mock_call = Mock(spec=CallbackQuery)

		mock_call.message = test_helper.create_mock_message("", [])
		mock_call.message.message_id = 152
		mock_call.message.chat = Mock(id=12345678)
		mock_call.from_user = Mock(first_name="Name")

		send_time = 1722517200

		self.scheduled_message_dispatcher.schedule_message(mock_bot, mock_call, send_time)
		mock_update_scheduled_time.assert_called_once()
		mock_add_comment_to_ticket.assert_called_once_with(mock_bot, mock_call.message,
										"Name deferred again the ticket to be sent on 2024-08-01 13:00.")


@patch("db_utils.get_newest_copied_message")
@patch("channel_manager.clear_channel_ticket_settings_state")
class TestHandleCallback(TestCase):
	def setUp(self):
		self.scheduled_message_dispatcher = scheduled_messages_utils.ScheduledMessageDispatcher()

	@patch("scheduled_messages_utils.ScheduledMessageDispatcher.generate_days_buttons")
	@patch("utils.edit_message_keyboard")
	def test_month_calendar(self, mock_edit_message_keyboard, mock_generate_days_buttons, *args):
		channel_id = -10012345678
		message_id = 123
		mock_bot = Mock(spec=TeleBot)
		mock_call = Mock(spec=CallbackQuery)
		mock_call.data = f"{self.scheduled_message_dispatcher.CALLBACK_PREFIX},{self.scheduled_message_dispatcher._MONTH_CALENDAR_CALLBACK}"
		mock_call.message = test_helper.create_mock_message("", [], channel_id, message_id)

		self.scheduled_message_dispatcher.handle_callback(mock_bot, mock_call, channel_id, message_id)
		mock_generate_days_buttons.assert_called_once_with()
		mock_edit_message_keyboard.assert_called_once_with(mock_bot, mock_call.message,
														   mock_generate_days_buttons.return_value,
														   chat_id=channel_id, message_id=message_id)

	@patch("scheduled_messages_utils.ScheduledMessageDispatcher.schedule_message_event")
	def test_schedule_message(self, mock_schedule_message_event, *args):
		channel_id = -10012345678
		message_id = 123
		mock_bot = Mock(spec=TeleBot)
		mock_call = Mock(spec=CallbackQuery)
		callback_data = ['02.10.2025', '12', '00']
		mock_call.data = f"{self.scheduled_message_dispatcher.CALLBACK_PREFIX},{self.scheduled_message_dispatcher._SCHEDULE_MESSAGE_CALLBACK}," + ','.join(callback_data)
		mock_call.message = test_helper.create_mock_message("", [], channel_id, message_id)

		self.scheduled_message_dispatcher.handle_callback(mock_bot, mock_call, channel_id, message_id)
		mock_schedule_message_event.assert_called_once_with(mock_bot, mock_call, callback_data)

	@patch("scheduled_messages_utils.ScheduledMessageDispatcher.change_month_event")
	def test_next_month(self, mock_change_month_event, *args):
		channel_id = -10012345678
		message_id = 123
		mock_bot = Mock(spec=TeleBot)
		mock_call = Mock(spec=CallbackQuery)
		callback_data = ['10.2025']
		mock_call.data = f"{self.scheduled_message_dispatcher.CALLBACK_PREFIX},{self.scheduled_message_dispatcher._NEXT_MONTH_CALLBACK}," + ','.join(callback_data)
		mock_call.message = test_helper.create_mock_message("", [], channel_id, message_id)

		self.scheduled_message_dispatcher.handle_callback(mock_bot, mock_call, channel_id, message_id)
		mock_change_month_event.assert_called_once_with(mock_bot, mock_call.message, callback_data, True, channel_id, message_id)

	@patch("scheduled_messages_utils.ScheduledMessageDispatcher.change_month_event")
	def test_previous_month(self, mock_change_month_event, *args):
		channel_id = -10012345678
		message_id = 123
		mock_bot = Mock(spec=TeleBot)
		mock_call = Mock(spec=CallbackQuery)
		callback_data = ['10.2025']
		mock_call.data = f"{self.scheduled_message_dispatcher.CALLBACK_PREFIX},{self.scheduled_message_dispatcher._PREVIOUS_MONTH_CALLBACK}," + ','.join(callback_data)
		mock_call.message = test_helper.create_mock_message("", [], channel_id, message_id)

		self.scheduled_message_dispatcher.handle_callback(mock_bot, mock_call, channel_id, message_id)
		mock_change_month_event.assert_called_once_with(mock_bot, mock_call.message, callback_data, False, channel_id, message_id)

	@patch("scheduled_messages_utils.ScheduledMessageDispatcher.select_day_event")
	def test_select_day(self, mock_select_day_event, *args):
		channel_id = -10012345678
		message_id = 123
		mock_bot = Mock(spec=TeleBot)
		mock_call = Mock(spec=CallbackQuery)
		callback_data = ['02.10.2025']
		mock_call.data = f"{self.scheduled_message_dispatcher.CALLBACK_PREFIX},{self.scheduled_message_dispatcher._SELECT_DAY_CALLBACK}," + ','.join(callback_data)
		mock_call.message = test_helper.create_mock_message("", [], channel_id, message_id)

		self.scheduled_message_dispatcher.handle_callback(mock_bot, mock_call, channel_id, message_id)
		mock_select_day_event.assert_called_once_with(mock_bot, mock_call.message, callback_data, channel_id, message_id)

	@patch("scheduled_messages_utils.ScheduledMessageDispatcher.select_hour_event")
	def test_select_hour(self, mock_select_hour_event, mock_clear_channel_ticket_settings_state,
						 mock_get_newest_copied_message, *args):
		channel_id = -10012345678
		message_id = 123
		mock_bot = Mock(spec=TeleBot)
		mock_call = Mock(spec=CallbackQuery)
		callback_data = ['02.10.2025', '09']
		mock_call.data = f"{self.scheduled_message_dispatcher.CALLBACK_PREFIX},{self.scheduled_message_dispatcher._SELECT_HOUR_CALLBACK}," + ','.join(callback_data)
		mock_call.message = test_helper.create_mock_message("", [], channel_id, message_id)
		mock_get_newest_copied_message.return_value = message_id

		self.scheduled_message_dispatcher.handle_callback(mock_bot, mock_call, channel_id, message_id)
		mock_select_hour_event.asssert_called_once_with(mock_bot, mock_call, callback_data, channel_id, message_id)
		mock_get_newest_copied_message.assert_called_once_with(channel_id)
		mock_clear_channel_ticket_settings_state.assert_called_once_with(mock_call, channel_manager.TICKET_MENU_TYPE, channel_id)

	@patch("scheduled_messages_utils.ScheduledMessageDispatcher.select_hour_event")
	def test_select_hour_no_newest(self, mock_select_hour_event, mock_clear_channel_ticket_settings_state,
						 mock_get_newest_copied_message, *args):
		channel_id = -10012345678
		message_id = 123
		newest_message = 125
		mock_bot = Mock(spec=TeleBot)
		mock_call = Mock(spec=CallbackQuery)
		callback_data = ['02.10.2025', '09']
		mock_call.data = f"{self.scheduled_message_dispatcher.CALLBACK_PREFIX},{self.scheduled_message_dispatcher._SELECT_HOUR_CALLBACK}," + ','.join(callback_data)
		mock_call.message = test_helper.create_mock_message("", [], channel_id, message_id)
		mock_get_newest_copied_message.return_value = newest_message

		self.scheduled_message_dispatcher.handle_callback(mock_bot, mock_call, channel_id, message_id)
		mock_select_hour_event.asssert_called_once_with(mock_bot, mock_call, callback_data, channel_id, message_id)
		mock_get_newest_copied_message.assert_called_once_with(channel_id)
		mock_clear_channel_ticket_settings_state.assert_not_called()


if __name__ == "__main__":
	main()
