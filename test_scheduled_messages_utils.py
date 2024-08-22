from unittest import TestCase, main
from unittest.mock import patch, Mock, ANY
from telebot import TeleBot

import test_helper
import forwarding_utils
import scheduled_messages_utils
from hashtag_data import HashtagData

scheduled_messages_utils.TIMEZONE_NAME = "UTC"


@patch("utils.SCHEDULED_DATETIME_FORMAT", "%Y-%m-%d %H:%M")
class UpdateStatusFromTagsTest(TestCase):
	def setUp(self):
		self.scheduled_message_dispatcher = scheduled_messages_utils.ScheduledMessageDispatcher()

	@patch("time.time", return_value=1700000000)
	@patch("db_utils.is_message_scheduled", return_value=False)
	@patch("utils.add_comment_to_ticket")
	@patch("db_utils.insert_scheduled_message")
	@patch("scheduled_messages_utils.ScheduledMessageDispatcher.insert_scheduled_message_info")
	def test_add_ticket_to_scheduled(self, mock_insert_scheduled_message_info, mock_insert_scheduled_message, *args):
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
	def test_reschedule_ticket(self, mock_update_scheduled_time, *args):
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
		mock_update_scheduled_time.assert_called_once_with(main_message_id, main_channel_id, 1722517200)


if __name__ == "__main__":
	main()
