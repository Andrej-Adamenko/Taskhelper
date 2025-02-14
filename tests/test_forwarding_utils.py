import unittest
from unittest import TestCase, main
from unittest.mock import patch, Mock, ANY, call

from telebot import TeleBot

from tests import test_helper
from hashtag_data import HashtagData

import forwarding_utils


@patch("db_utils.get_copied_messages_from_main", return_value=[(34, 12345678),])
@patch("db_utils.delete_scheduled_message_main")
@patch("db_utils.get_ticket_data", return_value=Mock())
class DeleteMainMessageTest(TestCase):
	@patch("config_utils.DISCUSSION_CHAT_DATA", {"12345678": None})
	@patch("db_utils.delete_ticket_data")
	@patch("db_utils.delete_copied_message")
	@patch("forwarding_utils.delete_forwarded_message")
	def test_without_discussion_chat(self, mock_delete_forwarded_message, mock_delete_copied_message,
									 mock_delete_ticket_data, *args):
		main_message_id = 157
		main_channel_id = 12345678
		copied_message_id = 34
		copied_channel_id = 12345678
		mock_bot = Mock(spec=TeleBot)

		manager = Mock()
		manager.attach_mock(mock_delete_forwarded_message, 'a')
		manager.attach_mock(mock_delete_copied_message, 'b')
		manager.attach_mock(mock_delete_ticket_data, 'c')

		expected_calls = [
			call.a(mock_bot, copied_channel_id, copied_message_id),
			call.b(copied_message_id, copied_channel_id),
			call.c(main_message_id, main_channel_id),
		]

		forwarding_utils.delete_main_message(mock_bot, main_channel_id, main_message_id)
		self.assertEqual(manager.mock_calls, expected_calls)

	@patch("config_utils.DISCUSSION_CHAT_DATA", {})
	@patch("db_utils.delete_ticket_data")
	@patch("db_utils.delete_copied_message")
	@patch("forwarding_utils.delete_forwarded_message")
	def test_main_channel_not_found_in_discussion_chat_dict(self, mock_delete_forwarded_message, mock_delete_copied_message,
															mock_delete_ticket_data, *args):
		main_message_id = 157
		main_channel_id = 12345678
		copied_message_id = 34
		copied_channel_id = 12345678
		mock_bot = Mock(spec=TeleBot)

		manager = Mock()
		manager.attach_mock(mock_delete_forwarded_message, 'a')
		manager.attach_mock(mock_delete_copied_message, 'b')
		manager.attach_mock(mock_delete_ticket_data, 'c')

		expected_calls = [
			call.a(mock_bot, copied_channel_id, copied_message_id),
			call.b(copied_message_id, copied_channel_id),
			call.c(main_message_id, main_channel_id),
		]

		forwarding_utils.delete_main_message(mock_bot, main_channel_id, main_message_id)
		self.assertEqual(manager.mock_calls, expected_calls)

	@patch("config_utils.DISCUSSION_CHAT_DATA", {"12345678": 87654321})
	@patch("db_utils.delete_ticket_data")
	@patch("db_utils.delete_copied_message")
	@patch("forwarding_utils.delete_forwarded_message")
	def test_with_discussion_chat(self, mock_delete_forwarded_message, mock_delete_copied_message,
								  mock_delete_ticket_data, *args):
		main_message_id = 157
		main_channel_id = 12345678
		copied_message_id = 34
		copied_channel_id = 12345678
		mock_bot = Mock(spec=TeleBot)

		manager = Mock()
		manager.attach_mock(mock_delete_forwarded_message, 'a')
		manager.attach_mock(mock_delete_copied_message, 'b')
		manager.attach_mock(mock_delete_ticket_data, 'c')

		expected_calls = [
			call.a(mock_bot, copied_channel_id, copied_message_id),
			call.b(copied_message_id, copied_channel_id),
			call.c(main_message_id, main_channel_id),
		]

		forwarding_utils.delete_main_message(mock_bot, main_channel_id, main_message_id)
		mock_bot.send_message.assert_called_once_with(chat_id=87654321, text=ANY)
		self.assertEqual(manager.mock_calls, expected_calls)

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
	@patch("db_utils.insert_or_update_last_msg_id")
	@patch("forwarding_utils.update_copied_message")
	@patch("utils.edit_message_keyboard")
	def test_order_add_remove_settings_button(self, mock_edit_message_keyboard, mock_update_copied_message, mock_insert_or_update_last_msg_id,
											  mock_insert_copied_message, mock_copy_message, mock_get_subchannel_ids_from_hashtags,
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
		manager.attach_mock(mock_insert_or_update_last_msg_id, 'd')

		forwarding_utils.forward_to_subchannel(mock_bot, mock_message, hashtag_data)

		expected_calls = [
			call.a(main_message_id, main_chat_id, sub_message_id, sub_chat_id),
			call.d(sub_message_id, sub_chat_id),
			call.b(mock_bot, mock_message, mock_generate_control_buttons.return_value, chat_id=sub_chat_id, message_id=sub_message_id),
			call.c(mock_bot, sub_chat_id, 166),
		]
		self.assertEqual(manager.mock_calls, expected_calls)

	@patch("db_utils.get_main_message_from_copied")
	@patch("forwarding_utils.generate_control_buttons")
	@patch("forwarding_utils.get_subchannel_ids_from_hashtags")
	@patch("channel_manager.get_button_settings_keyboard")
	@patch("utils.merge_keyboard_markup")
	@patch("utils.copy_message")
	def test_create_message_with_keyboard(self, mock_copy_message, mock_merge_keyboard_markup,
										  mock_get_button_settings_keyboard, mock_get_subchannel_ids_from_hashtags,
										  mock_generate_control_buttons, mock_get_main_message_from_copied, *args):
		main_chat_id = 12345678
		main_message_id = 157
		test = "test item"
		mock_bot = Mock(spec=TeleBot)

		mock_message = test_helper.create_mock_message(test, [], main_chat_id, main_message_id)
		mock_get_main_message_from_copied.return_value = [main_message_id, main_chat_id]

		sub_chat_id = 87654321
		sub_message_id = 167

		mock_copied_message = test_helper.create_mock_message(test, [], sub_chat_id, sub_message_id)
		mock_copy_message.return_value = mock_copied_message
		mock_get_subchannel_ids_from_hashtags.return_value = [sub_chat_id]

		hashtag_data = HashtagData()
		forwarding_utils.forward_to_subchannel(mock_bot, mock_message, hashtag_data)

		mock_generate_control_buttons.assert_has_calls([unittest.mock.call(hashtag_data, mock_message),
														unittest.mock.call(hashtag_data, mock_message)])
		mock_get_button_settings_keyboard.assert_called_once_with("Settings ⚙️")
		mock_merge_keyboard_markup.assert_called_once_with(
			mock_generate_control_buttons.return_value,
			mock_get_button_settings_keyboard.return_value
		)

		mock_copy_message.assert_called_once_with(mock_bot, chat_id=sub_chat_id, message_id=main_message_id,
												  from_chat_id=main_chat_id, reply_markup=mock_merge_keyboard_markup.return_value)


if __name__ == "__main__":
	main()

