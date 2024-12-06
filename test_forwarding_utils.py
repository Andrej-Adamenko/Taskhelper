import unittest
from unittest import TestCase, main
from unittest.mock import patch, Mock, ANY, call

from telebot import TeleBot
from telebot.types import Message, Chat, InlineKeyboardMarkup, InlineKeyboardButton

import test_helper
from hashtag_data import HashtagData

import scheduled_messages_utils
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

@patch("hashtag_data.HashtagData.__init__", return_value=None)
@patch("daily_reminder.update_ticket_data")
@patch("forwarding_utils.get_unchanged_posts", return_value=[])
@patch("hashtag_data.HashtagData.is_closed", return_value=False)
@patch("hashtag_data.HashtagData.get_assigned_user", return_value="NN")
@patch("hashtag_data.HashtagData.get_priority_number", return_value="2")
@patch("hashtag_data.HashtagData.is_scheduled", return_value=False)
@patch("hashtag_data.HashtagData.set_scheduled_tag", return_value=False)
@patch("hashtag_data.HashtagData.is_opened", return_value=True)
@patch("hashtag_data.HashtagData.get_hashtag_list", return_value=[None, "", "NN", ""])
@patch("db_utils.get_newest_copied_message", return_value=166)
class ForwardForSubchannelTest(TestCase):
	@patch("forwarding_utils.generate_control_buttons")
	@patch("forwarding_utils.get_subchannel_ids_from_hashtags")
	@patch("utils.copy_message")
	@patch("db_utils.insert_copied_message")
	@patch("forwarding_utils.update_copied_message")
	@patch("utils.edit_message_keyboard")
	def test_order_add_remove_settings_button(self, mock_edit_message_keyboard, mock_update_copied_message, mock_insert_copied_message,
									mock_copy_message, mock_get_subchannel_ids_from_hashtags,
									mock_generate_control_buttons, *args):
		main_chat_id = 12345678
		main_message_id = 157
		test = "test item"
		mock_bot = Mock(spec=TeleBot)

		mock_message = test_helper.create_mock_message(test, [], main_chat_id, main_message_id)

		sub_chat_id = 87654321
		sub_message_id = 167

		mock_copied_message = test_helper.create_mock_message(test, [], sub_chat_id, sub_message_id)
		mock_copy_message.return_value = mock_copied_message
		mock_get_subchannel_ids_from_hashtags.return_value = [sub_chat_id]

		hashtag_data = HashtagData()

		manager = Mock()
		manager.attach_mock(mock_insert_copied_message, 'a')
		manager.attach_mock(mock_edit_message_keyboard, 'b')
		manager.attach_mock(mock_update_copied_message, 'c')

		keyboard_markup = mock_generate_control_buttons(hashtag_data, mock_message)
		forwarding_utils.forward_to_subchannel(mock_bot, mock_message, hashtag_data)

		expected_calls = [
			call.a(main_message_id, main_chat_id, sub_message_id, sub_chat_id),
			call.b(mock_bot, mock_message, keyboard_markup, chat_id=sub_chat_id, message_id=sub_message_id),
			call.c(mock_bot, sub_chat_id, 166),
		]
		self.assertEqual(manager.mock_calls, expected_calls)

	@patch("forwarding_utils.generate_control_buttons")
	@patch("forwarding_utils.get_subchannel_ids_from_hashtags")
	@patch("utils.copy_message")
	def test_create_message_with_keyboard(self, mock_copy_message, mock_get_subchannel_ids_from_hashtags,
										  mock_generate_control_buttons, *args):
		main_chat_id = 12345678
		main_message_id = 157
		test = "test item"
		mock_bot = Mock(spec=TeleBot)

		mock_message = test_helper.create_mock_message(test, [], main_chat_id, main_message_id)

		sub_chat_id = 87654321
		sub_message_id = 167

		mock_copied_message = test_helper.create_mock_message(test, [], sub_chat_id, sub_message_id)
		mock_copy_message.return_value = mock_copied_message
		mock_get_subchannel_ids_from_hashtags.return_value = [sub_chat_id]

		hashtag_data = HashtagData()
		keyboard_markup = mock_generate_control_buttons(hashtag_data, mock_message, newest=True, subchannel_id=sub_chat_id)
		forwarding_utils.forward_to_subchannel(mock_bot, mock_message, hashtag_data)

		mock_generate_control_buttons.assert_has_calls([unittest.mock.call(hashtag_data, mock_message, newest=True, subchannel_id=sub_chat_id),
														unittest.mock.call(hashtag_data, mock_message)])
		mock_copy_message.assert_called_once_with(mock_bot, chat_id=sub_chat_id, message_id=main_message_id, from_chat_id=main_chat_id, reply_markup=keyboard_markup)

if __name__ == "__main__":
	main()

