from unittest import TestCase, main
from unittest.mock import patch, Mock, ANY
from telebot import TeleBot

import forwarding_utils


class DeleteMainMessageTest(TestCase):
	@patch("config_utils.DISCUSSION_CHAT_DATA", {"12345678": None})
	@patch("db_utils.get_copied_messages_from_main", return_value=[(34, 12345678),])
	@patch("db_utils.delete_copied_message")
	@patch("db_utils.delete_scheduled_message_main")
	@patch("db_utils.get_ticket_data", return_value=Mock())
	@patch("db_utils.delete_ticket_data")
	@patch("forwarding_utils.delete_forwarded_message")
	def test_without_discussion_chat(self, mock_delete_forwarded_message, mock_delete_ticket_data, *args):
		main_message_id = 157
		main_channel_id = 12345678
		mock_bot = Mock(spec=TeleBot)

		forwarding_utils.delete_main_message(mock_bot, main_channel_id, main_message_id)
		mock_delete_forwarded_message.assert_called_once_with(mock_bot, 12345678, 34)
		mock_delete_ticket_data.assert_called_once_with(main_message_id, main_channel_id)

	@patch("config_utils.DISCUSSION_CHAT_DATA", {})
	@patch("db_utils.get_copied_messages_from_main", return_value=[(34, 12345678),])
	@patch("db_utils.delete_copied_message")
	@patch("db_utils.delete_scheduled_message_main")
	@patch("db_utils.get_ticket_data", return_value=Mock())
	@patch("db_utils.delete_ticket_data")
	@patch("forwarding_utils.delete_forwarded_message")
	def test_main_channel_not_found_in_discussion_chat_dict(self, mock_delete_forwarded_message, mock_delete_ticket_data, *args):
		main_message_id = 157
		main_channel_id = 12345678
		mock_bot = Mock(spec=TeleBot)

		forwarding_utils.delete_main_message(mock_bot, main_channel_id, main_message_id)
		mock_delete_forwarded_message.assert_called_once_with(mock_bot, 12345678, 34)
		mock_delete_ticket_data.assert_called_once_with(main_message_id, main_channel_id)

	@patch("config_utils.DISCUSSION_CHAT_DATA", {"12345678": 87654321})
	@patch("db_utils.get_copied_messages_from_main", return_value=[(34, 12345678),])
	@patch("db_utils.delete_copied_message")
	@patch("db_utils.delete_scheduled_message_main")
	@patch("db_utils.get_ticket_data", return_value=Mock())
	@patch("db_utils.delete_ticket_data")
	@patch("forwarding_utils.delete_forwarded_message")
	def test_with_discussion_chat(self, mock_delete_forwarded_message, mock_delete_ticket_data, *args):
		main_message_id = 157
		main_channel_id = 12345678
		mock_bot = Mock(spec=TeleBot)

		forwarding_utils.delete_main_message(mock_bot, main_channel_id, main_message_id)
		mock_delete_forwarded_message.assert_called_once_with(mock_bot, 12345678, 34)
		mock_delete_ticket_data.assert_called_once_with(main_message_id, main_channel_id)
		mock_bot.send_message.assert_called_once()


if __name__ == "__main__":
	main()

