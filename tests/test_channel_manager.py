import unittest
from unittest import TestCase, main
from unittest.mock import patch, Mock, call, ANY

from pyrogram.filters import reply_keyboard
from telebot import TeleBot
from telebot.types import Message, InlineKeyboardButton, CallbackQuery, User, InlineKeyboardMarkup

from tests import test_helper
import channel_manager


@patch("channel_manager.NEW_USER_TYPE", "+")
class AddNewUserTagToChannelsTest(TestCase):
	@patch("channel_manager.update_settings_message")
	@patch("db_utils.update_individual_channel_settings")
	@patch("db_utils.get_all_individual_channels")
	def test_add_new_user(self, mock_get_all_individual_channels, mock_update_individual_channel_settings, *args):
		channel_settings = '{"assigned": ["FF", "+"], "cc": ["FF"]}'
		channel_id = -10012345678
		main_channel_id = -100987654321
		mock_get_all_individual_channels.return_value = [[channel_id, channel_settings]]
		mock_bot = Mock(spec=TeleBot)
		new_user_tag = "NN"

		channel_manager.add_new_user_tag_to_channels(mock_bot, main_channel_id, new_user_tag)

		mock_update_individual_channel_settings.assert_called_once_with(channel_id, '{"assigned": ["FF", "+", "NN"], "cc": ["FF"]}')

	@patch("db_utils.update_individual_channel_settings")
	@patch("channel_manager.update_settings_message")
	@patch("db_utils.get_all_individual_channels")
	def test_update_settings_message(self, mock_get_all_individual_channels, mock_update_settings_message, *args):
		channel_settings = '{"assigned": ["FF", "+"], "cc": ["FF"], "settings_message_id": 3079}'
		channel_id = -10012345678
		main_channel_id = -100987654321
		mock_get_all_individual_channels.return_value = [[channel_id, channel_settings]]
		mock_bot = Mock(spec=TeleBot)
		new_user_tag = "NN"

		channel_manager.add_new_user_tag_to_channels(mock_bot, main_channel_id, new_user_tag)

		mock_update_settings_message.assert_called_once_with(mock_bot, channel_id, 3079)


class RemoveUserTagFromChannelsTest(TestCase):
	@patch("channel_manager.update_settings_message")
	@patch("db_utils.update_individual_channel_settings")
	@patch("db_utils.get_all_individual_channels")
	def test_remove_user(self, mock_get_all_individual_channels, mock_update_individual_channel_settings, *args):
		channel_settings = '{"assigned": ["FF", "NN"], "cc": ["NN"]}'
		channel_id = -10012345678
		main_channel_id = -100987654321
		mock_get_all_individual_channels.return_value = [[channel_id, channel_settings]]
		mock_bot = Mock(spec=TeleBot)
		user_tag = "NN"

		channel_manager.remove_user_tag_from_channels(mock_bot, main_channel_id, user_tag)

		mock_update_individual_channel_settings.assert_called_once_with(channel_id, '{"assigned": ["FF"], "cc": []}')

	@patch("db_utils.update_individual_channel_settings")
	@patch("channel_manager.update_settings_message")
	@patch("db_utils.get_all_individual_channels")
	def test_update_settings_message(self, mock_get_all_individual_channels, mock_update_settings_message, *args):
		channel_settings = '{"assigned": ["FF", "NN"], "cc": ["NN"], "settings_message_id": 3079}'
		channel_id = -10012345678
		main_channel_id = -100987654321
		mock_get_all_individual_channels.return_value = [[channel_id, channel_settings]]
		mock_bot = Mock(spec=TeleBot)
		user_tag = "NN"

		channel_manager.remove_user_tag_from_channels(mock_bot, main_channel_id, user_tag)

		mock_update_settings_message.assert_called_once_with(mock_bot, channel_id, 3079)

@patch("db_utils.get_oldest_copied_message", return_value=False)
class TestChannelSettingsMessage(TestCase):
	@patch("db_utils.get_individual_channel_settings")
	def test_generate_current_settings_text(self, mock_get_individual_channel_settings, *args):
		channel_settings = '{"due": true, "deferred": false, "assigned": ["FF", "NN"], "reported": ["+"], "cc": ["NN"]}'
		priorities = '1,2'
		channel_id = -10012345678
		mock_get_individual_channel_settings.return_value = [channel_settings, priorities]

		text = channel_manager.generate_current_settings_text(channel_id)
		self.assertIn("\"/settings\"", text)

		self.assertIn("Assigned to -", text)
		self.assertIn("Reported by -", text)
		self.assertIn("CCed to -", text)
		self.assertIn("Remind me when -", text)
		self.assertIn("Due -", text)
		self.assertIn("Deferred -", text)
		self.assertIn("Priority 1/2/3 -", text)

		self.assertIn("CURRENT SETTINGS", text)
		self.assertIn("Assigned to: #FF, #NN", text)
		self.assertIn("Reported by: <new users>", text)
		self.assertIn("CCed to: #NN", text)
		self.assertIn("Include due tickets: yes", text)
		self.assertIn("Include deferred tickets: no", text)
		self.assertIn("Priorities: #п1, #п2", text)

	@patch("db_utils.get_individual_channel_settings")
	@patch("channel_manager.get_exist_settings_message")
	@patch("db_utils.insert_or_update_last_msg_id")
	@patch("channel_manager.set_settings_message_id")
	def test_create_settings_message(self, mock_set_settings_message_id, mock_insert_or_update_last_msg_id,
									 mock_get_exist_settings_message, mock_get_individual_channel_settings,
									 mock_get_oldest_copied_message, *args):
		mock_bot = Mock(spec=TeleBot)
		channel_id = -10012345678
		message_id = 123

		channel_settings = '{"due": true, "deferred": false, "assigned": ["FF", "NN"], "reported": ["+"], "cc": ["NN"]}'
		priorities = '1,2'
		mock_get_individual_channel_settings.return_value = [channel_settings, priorities]

		mock_message = test_helper.create_mock_message("", [], None, message_id)
		mock_bot.send_message.return_value = mock_message

		mock_get_exist_settings_message.return_value = False
		channel_manager.create_settings_message(mock_bot, channel_id)
		mock_get_exist_settings_message.assert_called_once_with(mock_bot, channel_id)
		mock_get_oldest_copied_message.assert_called_once_with(channel_id)
		mock_set_settings_message_id.assert_called_once_with(channel_id, message_id)
		mock_insert_or_update_last_msg_id.assert_called_once_with(message_id, channel_id)

	@patch("db_utils.get_individual_channel_settings")
	@patch("channel_manager.get_exist_settings_message")
	@patch("db_utils.get_main_message_from_copied")
	@patch("db_utils.insert_or_update_last_msg_id")
	@patch("channel_manager.set_settings_message_id")
	def test_create_settings_message_with_oldest_message(self, mock_set_settings_message_id, mock_insert_or_update_last_msg_id,
									 mock_get_main_message_from_copied,
									 mock_get_exist_settings_message, mock_get_individual_channel_settings,
									 mock_get_oldest_copied_message, *args):
		mock_bot = Mock(spec=TeleBot)
		channel_id = -10012345678
		message_id = 123
		oldest_message_id = 5
		main_channel_id = -10012345638
		main_message_id = 3

		channel_settings = '{"due": true, "deferred": false, "assigned": ["FF", "NN"], "reported": ["+"], "cc": ["NN"]}'
		priorities = '1,2'
		mock_get_individual_channel_settings.return_value = [channel_settings, priorities]

		mock_message = test_helper.create_mock_message("", [], None, message_id)
		mock_bot.send_message.return_value = mock_message

		mock_get_exist_settings_message.return_value = False
		mock_get_oldest_copied_message.return_value = oldest_message_id
		mock_get_main_message_from_copied.return_value = [main_message_id, main_channel_id]

		channel_manager.create_settings_message(mock_bot, channel_id)
		mock_get_exist_settings_message.assert_called_once_with(mock_bot, channel_id)
		mock_get_oldest_copied_message.assert_called_once_with(channel_id)
		mock_get_main_message_from_copied.assert_called_once_with(oldest_message_id, channel_id)
		mock_set_settings_message_id.assert_called_once_with(channel_id, oldest_message_id)
		mock_insert_or_update_last_msg_id.assert_not_called()

	@patch("db_utils.get_individual_channel_settings")
	@patch("channel_manager.get_exist_settings_message")
	@patch("channel_manager.set_settings_message_id")
	def test_create_settings_message_with_settings(self, mock_set_settings_message_id, mock_get_exist_settings_message,
									 mock_get_individual_channel_settings, *args):
		mock_bot = Mock(spec=TeleBot)
		channel_id = -10012345678
		message_id = 123

		channel_settings = '{"due": true, "deferred": false, "assigned": ["FF", "NN"], "reported": ["+"], "cc": ["NN"], "settings_message_id": 122}'
		priorities = '1,2'
		mock_get_individual_channel_settings.return_value = [channel_settings, priorities]

		mock_message = test_helper.create_mock_message("", [], None, message_id)
		mock_bot.send_message.return_value = mock_message


		channel_manager.create_settings_message(mock_bot, channel_id)
		mock_get_exist_settings_message.assert_not_called()
		mock_set_settings_message_id.assert_not_called()

	@patch("db_utils.get_individual_channel_settings")
	@patch("channel_manager.get_exist_settings_message")
	@patch("channel_manager.set_settings_message_id")
	def test_create_settings_message_with_exist_settings_message(self, mock_set_settings_message_id, mock_get_exist_settings_message,
									 mock_get_individual_channel_settings, *args):
		mock_bot = Mock(spec=TeleBot)
		channel_id = -10012345678
		message_id = 123

		channel_settings = '{"due": true, "deferred": false, "assigned": ["FF", "NN"], "reported": ["+"], "cc": ["NN"]}'
		priorities = '1,2'
		mock_get_individual_channel_settings.return_value = [channel_settings, priorities]

		mock_message = test_helper.create_mock_message("", [], None, message_id)
		mock_bot.send_message.return_value = mock_message

		mock_get_exist_settings_message.return_value = True

		channel_manager.create_settings_message(mock_bot, channel_id)
		mock_get_exist_settings_message.assert_called_once_with(mock_bot, channel_id)
		mock_set_settings_message_id.assert_not_called()

	@patch("utils.get_last_message")
	@patch("channel_manager.is_settings_message")
	@patch("utils.get_main_message_content_by_id")
	@patch("channel_manager.update_settings_message")
	@patch("db_utils.get_newest_copied_message")
	@patch("channel_manager.set_settings_message_id")
	@patch("forwarding_utils.generate_control_buttons")
	@patch("utils.edit_message_keyboard")
	def test_get_exist_settings_message(self, mock_edit_message_keyboard, mock_generate_control_buttons,
										mock_set_settings_message_id, mock_get_newest_copied_message,
										mock_update_settings_message, mock_get_main_message_content_by_id,
										mock_is_settings_message, mock_get_last_message,
										mock_get_oldest_copied_message, *args):
		mock_bot = Mock(spec=TeleBot)
		channel_id = -10012345678
		last_message_id = 5
		message_id = 1
		expected_calls = [
			call.a(mock_bot, channel_id, 1),
			call.a(mock_bot, channel_id, 5)
		]

		mock_is_settings_message.return_value = True

		mock_message = test_helper.create_mock_message(f"{message_id} 12345", [], channel_id, last_message_id)
		mock_get_main_message_content_by_id.return_value = mock_message

		manager = Mock()
		manager.attach_mock(mock_get_main_message_content_by_id, 'a')

		mock_get_last_message.return_value = last_message_id
		mock_get_newest_copied_message.return_value = last_message_id

		result = channel_manager.get_exist_settings_message(mock_bot, channel_id)
		# Test get last message
		mock_get_oldest_copied_message.assert_called_once_with(channel_id)
		mock_get_last_message.assert_called_once_with(mock_bot, channel_id)
		# Test get content in all messages
		self.assertEqual(manager.mock_calls, expected_calls)
		# Test update settings message
		mock_is_settings_message.assert_called_once_with(mock_message)
		mock_update_settings_message.assert_called_once_with(mock_bot, channel_id, message_id)
		mock_set_settings_message_id.assert_called_once_with(channel_id, message_id)

		# Test update settings button
		mock_generate_control_buttons.assert_called_once()
		mock_edit_message_keyboard.assert_called_once_with(mock_bot, mock_message, mock_generate_control_buttons.return_value,
														   channel_id, last_message_id)


		self.assertTrue(result)

	@patch("utils.get_last_message")
	@patch("channel_manager.is_settings_message")
	@patch("utils.get_main_message_content_by_id")
	@patch("channel_manager.set_settings_message_id")
	def test_get_exist_settings_message_with_empty_message(self, mock_set_settings_message_id, mock_get_main_message_content_by_id,
														   mock_is_settings_message, mock_get_last_message, *args):
		mock_bot = Mock(spec=TeleBot)
		channel_id = -10012345678
		last_message_id = 5
		expected_calls = []
		mock_is_settings_message.return_value = True
		mock_get_main_message_content_by_id.return_value = None
		manager = Mock()
		manager.attach_mock(mock_get_main_message_content_by_id, 'a')

		for i in range(1, last_message_id + 1):
			expected_calls.append(call.a(mock_bot, channel_id, i))

		mock_get_last_message.return_value = last_message_id
		result = channel_manager.get_exist_settings_message(mock_bot, channel_id)
		# Test get last message
		mock_get_last_message.assert_called_once_with(mock_bot, channel_id)
		# Test get content in all messages
		self.assertEqual(manager.mock_calls, expected_calls)
		# Test find settings message
		mock_is_settings_message.assert_not_called()
		mock_set_settings_message_id.assert_not_called()
		self.assertFalse(result)

	@patch("utils.get_last_message")
	@patch("channel_manager.is_settings_message")
	@patch("utils.get_main_message_content_by_id")
	@patch("channel_manager.set_settings_message_id")
	def test_get_exist_information_message_without_information_message(self, mock_set_settings_message_id,
														mock_get_main_message_content_by_id, mock_is_settings_message,
														mock_get_last_message, *args):
		mock_bot = Mock(spec=TeleBot)
		channel_id = -10012345678
		last_message_id = 5
		expected_calls = []
		mock_is_settings_message.return_value = False
		mock_message = test_helper.create_mock_message("", [])
		mock_get_main_message_content_by_id.return_value = mock_message
		manager = Mock()
		manager.attach_mock(mock_get_main_message_content_by_id, 'a')
		manager.attach_mock(mock_is_settings_message, 'b')

		for i in range(1, last_message_id + 1):
			expected_calls.append(call.a(mock_bot, channel_id, i))
			expected_calls.append(call.b(mock_message))

		mock_get_last_message.return_value = last_message_id
		result = channel_manager.get_exist_settings_message(mock_bot, channel_id)
		# Test get last message
		mock_get_last_message.assert_called_once_with(mock_bot, channel_id)
		# Test get content in all messages
		self.assertEqual(manager.mock_calls, expected_calls)
		# Test find settings message
		mock_set_settings_message_id.assert_not_called()
		self.assertFalse(result)

	@patch("utils.get_last_message")
	@patch("channel_manager.is_settings_message")
	@patch("utils.get_main_message_content_by_id")
	@patch("channel_manager.set_settings_message_id")
	def test_get_exist_information_message_without_information_message_with_copied_messages(self,
										mock_set_settings_message_id, mock_get_main_message_content_by_id,
										mock_is_settings_message, mock_get_last_message,
										mock_get_oldest_copied_message, *args):
		mock_bot = Mock(spec=TeleBot)
		channel_id = -10012345678
		last_message_id = 5
		last_copied_id = 3
		expected_calls = []
		mock_is_settings_message.return_value = False
		mock_message = test_helper.create_mock_message("", [])
		mock_get_main_message_content_by_id.return_value = mock_message
		manager = Mock()
		manager.attach_mock(mock_get_main_message_content_by_id, 'a')
		manager.attach_mock(mock_is_settings_message, 'b')

		for i in range(1, last_copied_id + 1):
			expected_calls.append(call.a(mock_bot, channel_id, i))
			expected_calls.append(call.b(mock_message))

		mock_get_last_message.return_value = last_message_id
		mock_get_oldest_copied_message.return_value = last_copied_id
		result = channel_manager.get_exist_settings_message(mock_bot, channel_id)
		# Test get last message
		mock_get_oldest_copied_message.assert_called_once_with(channel_id)
		mock_get_last_message.assert_not_called()
		# Test get content in all messages
		self.assertEqual(manager.mock_calls, expected_calls)
		# Test find settings message
		mock_set_settings_message_id.assert_not_called()
		self.assertFalse(result)

	@patch("channel_manager.get_text_information_text")
	def test_is_settings_message(self, mock_get_text_information_text, *args):
		mock_get_text_information_text.return_value = "123"
		result = channel_manager.is_settings_message(test_helper.create_mock_message("", []))
		self.assertFalse(result)

		result = channel_manager.is_settings_message(test_helper.create_mock_message("12345 5678", []))
		self.assertTrue(result)

		result = channel_manager.is_settings_message(test_helper.create_mock_message("2345 1235678", []))
		self.assertTrue(result)

	@patch("db_utils.get_main_channel_from_user")
	@patch("channel_manager.generate_user_keyboard")
	def test_get_user_selection_keyboard(self, mock_generate_user_keyboard, mock_get_main_channel_from_user, *args):
		main_channel_id = -10087654321
		channel_id = -10012345678
		message_id = 123
		user_id = 8536472

		mock_call = Mock(spec=CallbackQuery)
		mock_call.message = test_helper.create_mock_message("", [], channel_id, message_id)
		mock_call.from_user = Mock(spec=User)
		mock_call.from_user.id = user_id
		mock_get_main_channel_from_user.return_value = main_channel_id
		settings_type = channel_manager.SETTING_TYPES.ASSIGNED

		channel_manager.get_user_selection_keyboard(mock_call, settings_type)
		mock_get_main_channel_from_user.assert_called_once_with(user_id)
		mock_generate_user_keyboard.assert_called_once_with(main_channel_id, channel_id, settings_type)

	@patch("channel_manager.get_user_selection_keyboard")
	@patch("channel_manager.call_function_settings_button")
	@patch("channel_manager.update_settings_keyboard")
	def test_open_user_selection(self, mock_update_settings_keyboard, mock_call_function_settings_button,
								 mock_get_user_selection_keyboard, *args):
		mock_bot = Mock(spec=TeleBot)
		mock_call = Mock(spec=CallbackQuery)
		mock_call.message = test_helper.create_mock_message("", [], -10012345678, 123)
		settings_type = channel_manager.SETTING_TYPES.REPORTED
		mock_keyboard = Mock(spec=InlineKeyboardMarkup)
		mock_get_user_selection_keyboard.return_value = mock_keyboard
		settings_args = mock_bot, mock_call.message, mock_keyboard

		channel_manager.open_user_selection(mock_bot, mock_call, settings_type)
		mock_get_user_selection_keyboard.assert_called_once_with(mock_call, settings_type)
		mock_call_function_settings_button.assert_called_once_with(mock_bot, mock_call.message,
																   mock_update_settings_keyboard, settings_args,
																   mock_keyboard)

	@patch("db_utils.get_individual_channel_settings",
		   return_value=['{"due": true, "deferred": false, "assigned": ["FF", "NN"], "reported": ["+"], "cc": ["NN"]}',
						 '1,2'])
	@patch("channel_manager.is_settings_message", return_value=True)
	@patch("channel_manager.update_settings_keyboard")
	@patch("channel_manager.get_settings_message_id")
	@patch("channel_manager.update_settings_message")
	@patch("db_utils.get_newest_copied_message")
	@patch("forwarding_utils.generate_control_buttons_from_subchannel")
	@patch("utils.merge_keyboard_markup")
	def test_call_function_settings_button(self, mock_merge_keyboard_markup, mock_generate_control_buttons_from_subchannel,
								 mock_get_newest_copied_message, mock_update_settings_message,
								 mock_get_settings_message_id, mock_update_settings_keyboard,
								 mock_is_settings_message, *args):

		mock_bot = Mock(spec=TeleBot)
		mock_message = test_helper.create_mock_message("", [], -10012345678, 123)
		mock_get_settings_message_id.return_value = 123
		mock_newest_message_id = 321
		mock_get_newest_copied_message.return_value = mock_newest_message_id
		mock_keyboard = Mock(spec=InlineKeyboardMarkup)
		args = mock_bot, mock_message, mock_keyboard

		channel_manager.call_function_settings_button(mock_bot, mock_message, mock_update_settings_keyboard, args, mock_keyboard)
		mock_is_settings_message.assert_called_once_with(mock_message)
		mock_update_settings_keyboard.assert_called_once_with(*args)
		mock_get_settings_message_id.assert_called_once_with(mock_message.chat.id)
		mock_update_settings_message.assert_not_called()
		mock_get_newest_copied_message.assert_called_once_with(mock_message.chat.id)
		mock_generate_control_buttons_from_subchannel.assert_not_called()
		mock_merge_keyboard_markup.assert_not_called()
		mock_bot.edit_message_reply_markup.assert_not_called()

	@patch("db_utils.get_individual_channel_settings",
		   return_value=['{"due": true, "deferred": false, "assigned": ["FF", "NN"], "reported": ["+"], "cc": ["NN"]}',
						 '1,2'])
	@patch("channel_manager.is_settings_message", return_value=True)
	@patch("channel_manager.update_settings_keyboard")
	@patch("channel_manager.get_settings_message_id")
	@patch("channel_manager.update_settings_message")
	@patch("db_utils.get_newest_copied_message")
	@patch("forwarding_utils.generate_control_buttons_from_subchannel")
	@patch("utils.merge_keyboard_markup")
	def test_call_function_settings_button_another_settings_message(self, mock_merge_keyboard_markup, mock_generate_control_buttons_from_subchannel,
								 mock_get_newest_copied_message, mock_update_settings_message,
								 mock_get_settings_message_id, mock_update_settings_keyboard,
								 mock_is_settings_message, *args):
		mock_bot = Mock(spec=TeleBot)
		mock_message = test_helper.create_mock_message("", [], -10012345678, 125)
		mock_get_settings_message_id.return_value = 123
		mock_newest_message_id = 321
		mock_get_newest_copied_message.return_value = mock_newest_message_id
		mock_keyboard = Mock(spec=InlineKeyboardMarkup)
		args = mock_bot, mock_message, mock_keyboard

		channel_manager.call_function_settings_button(mock_bot, mock_message, mock_update_settings_keyboard, args, mock_keyboard)
		mock_is_settings_message.assert_called_once_with(mock_message)
		mock_update_settings_keyboard.assert_called_once_with(*args)
		mock_get_settings_message_id.assert_called_once_with(mock_message.chat.id)
		mock_update_settings_message.assert_called_once_with(mock_bot, mock_message.chat.id,
															 mock_get_settings_message_id.return_value)
		mock_get_newest_copied_message.assert_called_once_with(mock_message.chat.id)
		mock_generate_control_buttons_from_subchannel.assert_not_called()
		mock_merge_keyboard_markup.assert_not_called()
		mock_bot.edit_message_reply_markup.assert_not_called()

	@patch("db_utils.get_individual_channel_settings",
		   return_value=['{"due": true, "deferred": false, "assigned": ["FF", "NN"], "reported": ["+"], "cc": ["NN"]}',
						 '1,2'])
	@patch("channel_manager.is_settings_message", return_value=False)
	@patch("channel_manager.update_settings_keyboard")
	@patch("channel_manager.get_settings_message_id")
	@patch("channel_manager.update_settings_message")
	@patch("db_utils.get_newest_copied_message")
	@patch("forwarding_utils.generate_control_buttons_from_subchannel")
	@patch("utils.merge_keyboard_markup")
	def test_call_function_settings_button_last_ticket(self, mock_merge_keyboard_markup, mock_generate_control_buttons_from_subchannel,
								 mock_get_newest_copied_message, mock_update_settings_message,
								 mock_get_settings_message_id, mock_update_settings_keyboard,
								 mock_is_settings_message, *args):
		mock_bot = Mock(spec=TeleBot)
		mock_message = test_helper.create_mock_message("", [], -10012345678, 321)
		mock_get_settings_message_id.return_value = 123
		mock_newest_message_id = 321
		mock_get_newest_copied_message.return_value = mock_newest_message_id
		mock_keyboard = Mock(spec=InlineKeyboardMarkup)
		args = mock_bot, mock_message, mock_keyboard

		channel_manager.call_function_settings_button(mock_bot, mock_message, mock_update_settings_keyboard, args, mock_keyboard)
		mock_is_settings_message.assert_called_once_with(mock_message)
		mock_update_settings_keyboard.assert_not_called()
		mock_get_settings_message_id.assert_called_once_with(mock_message.chat.id)
		mock_update_settings_message.assert_called_once_with(mock_bot, mock_message.chat.id,
															 mock_get_settings_message_id.return_value)
		mock_get_newest_copied_message.assert_called_once_with(mock_message.chat.id)
		mock_generate_control_buttons_from_subchannel.assert_called_once_with(mock_message)
		mock_merge_keyboard_markup.assert_called_once_with(mock_generate_control_buttons_from_subchannel.return_value,
														   mock_keyboard)
		mock_bot.edit_message_reply_markup.assert_called_once_with(chat_id=mock_message.chat.id,
																   message_id=mock_newest_message_id,
																   reply_markup=mock_merge_keyboard_markup.return_value)


@patch("db_utils.get_oldest_copied_message", return_value=False)
@patch("db_utils.get_individual_channel_settings",
	   return_value=['{"due": true, "deferred": false, "assigned": ["FF", "NN"], "reported": ["+"], "cc": ["NN"]}',
					 '1,2'])
class TestAddSettingsKeyboard(TestCase):
	@patch("channel_manager.add_help_button")
	def test_generate_settings_keyboard(self, mock_add_help_button, *args):
		channel_id = -10012345678

		channel_manager.generate_settings_keyboard(channel_id)
		mock_add_help_button.assert_not_called()

	@patch("channel_manager.add_help_button")
	def test_add_help_button(self, mock_add_help_button, *args):
		channel_id = -10012345678

		channel_manager.generate_settings_keyboard(channel_id, True)
		mock_add_help_button.assert_called_once_with(channel_id)

	@patch("channel_manager.generate_settings_keyboard")
	def test_show_settings_keyboard(self, mock_generate_settings_keyboard, *args):
		mock_bot = Mock(spec=TeleBot)
		mock_message = test_helper.create_mock_message("", [], -10012345678, 123)

		text = channel_manager.generate_current_settings_text(mock_message.chat.id)
		channel_manager.show_settings_keyboard(mock_bot, mock_message)
		mock_bot.edit_message_text.assert_called_once_with(chat_id=mock_message.chat.id, message_id=mock_message.id,
														   text=text, reply_markup=mock_generate_settings_keyboard.return_value)

	@patch("db_utils.get_main_message_from_copied")
	@patch("forwarding_utils.generate_control_buttons_from_subchannel")
	@patch("channel_manager.generate_settings_keyboard")
	@patch("utils.merge_keyboard_markup")
	def test_show_settings_keyboard_for_button(self, mock_merge_keyboard_markup, mock_generate_settings_keyboard,
											   mock_generate_control_buttons_from_subchannel, mock_get_main_message_from_copied, *args):
		mock_bot = Mock(spec=TeleBot)
		mock_message_id = 123
		mock_main_message_id = 102
		mock_channel_id = -10012345678
		mock_main_channel_id = -10087654321
		mock_message = test_helper.create_mock_message("", [], mock_channel_id, mock_message_id)

		mock_get_main_message_from_copied.return_value = [mock_main_message_id, mock_main_channel_id]

		channel_manager.show_settings_keyboard_for_button(mock_bot, mock_message)
		mock_generate_control_buttons_from_subchannel.assert_called_once_with(mock_message)
		mock_generate_settings_keyboard.assert_called_once_with(mock_channel_id, add_help=True)
		mock_merge_keyboard_markup.assert_called_once_with(
			mock_generate_control_buttons_from_subchannel.return_value,
			mock_generate_settings_keyboard.return_value
		)
		mock_bot.edit_message_reply_markup.assert_called_once_with(chat_id=mock_channel_id, message_id=mock_message_id,
														   reply_markup=mock_merge_keyboard_markup.return_value)

	@patch("channel_manager.generate_settings_keyboard")
	@patch("channel_manager.generate_current_settings_text")
	def test_update_settings_keyboard(self, mock_generate_current_settings_text, mock_generate_settings_keyboard, *args):
		channel_id = -10012345678
		message_id = 123
		mock_bot = Mock(spec=TeleBot)
		mock_message = test_helper.create_mock_message("", [], channel_id, message_id)

		channel_manager.update_settings_keyboard(mock_bot, mock_message)
		mock_generate_settings_keyboard.assert_called_once_with(channel_id)
		mock_generate_current_settings_text.assert_called_once_with(channel_id)
		mock_bot.edit_message_text.assert_called_once_with(chat_id=channel_id, message_id=message_id,
									reply_markup=mock_generate_settings_keyboard.return_value,
									text=mock_generate_current_settings_text.return_value)

	@patch("channel_manager.generate_settings_keyboard")
	@patch("channel_manager.generate_current_settings_text")
	def test_update_settings_keyboard_with_another_keyboard(self, mock_generate_current_settings_text, mock_generate_settings_keyboard, *args):
		channel_id = -10012345678
		message_id = 123
		mock_bot = Mock(spec=TeleBot)
		mock_message = test_helper.create_mock_message("", [], channel_id, message_id)
		keyboard = Mock(spec=InlineKeyboardMarkup)

		channel_manager.update_settings_keyboard(mock_bot, mock_message, keyboard)
		mock_generate_settings_keyboard.assert_not_called()
		mock_generate_current_settings_text.assert_called_once_with(channel_id)
		mock_bot.edit_message_text.assert_called_once_with(chat_id=channel_id, message_id=message_id,
									reply_markup=keyboard,
									text=mock_generate_current_settings_text.return_value)



@patch("db_utils.is_individual_channel_exists", return_value=True)
class TestHandleCallback(TestCase):
	@patch("channel_manager.save_channel_settings")
	@patch("channel_manager.call_function_settings_button")
	@patch("channel_manager.update_settings_message")
	@patch("channel_manager.get_button_settings_keyboard")
	@patch("channel_manager.start_deferred_interval_check")
	def test_save_and_hide_settings_menu(self, mock_start_deferred_interval_check, mock_get_button_settings_keyboard,
										 mock_update_settings_message, mock_call_function_settings_button,
										 mock_save_channel_settings, *args):
		channel_id = -10012345678
		message_id = 123
		mock_bot = Mock(spec=TeleBot)
		mock_call = Mock(spec=CallbackQuery)
		mock_call.data = f"{channel_manager.CALLBACK_PREFIX},{channel_manager.CB_TYPES.SAVE_AND_HIDE_SETTINGS_MENU},"
		mock_call.message = test_helper.create_mock_message("", [], channel_id, message_id)
		setting_args = mock_bot, channel_id, message_id

		channel_manager.handle_callback(mock_bot, mock_call)
		mock_save_channel_settings.assert_called_once_with(mock_bot, mock_call)
		mock_call_function_settings_button.assert_called_once_with(mock_bot, mock_call.message,
																   mock_update_settings_message, setting_args,
																   mock_get_button_settings_keyboard.return_value)
		mock_get_button_settings_keyboard.assert_called_once_with()
		mock_start_deferred_interval_check.assert_called_once_with(mock_bot, 0)

	@patch("channel_manager.save_channel_settings")
	@patch("channel_manager.open_user_selection")
	@patch("channel_manager.start_deferred_interval_check")
	def test_assigned_selected(self, mock_start_deferred_interval_check, mock_open_user_selection,
							   mock_save_channel_settings, *args):
		channel_id = -10012345678
		message_id = 123
		mock_bot = Mock(spec=TeleBot)
		mock_call = Mock(spec=CallbackQuery)
		mock_call.data = f"{channel_manager.CALLBACK_PREFIX},{channel_manager.CB_TYPES.ASSIGNED_SELECTED},"
		mock_call.message = test_helper.create_mock_message("", [], channel_id, message_id)

		channel_manager.handle_callback(mock_bot, mock_call)
		mock_save_channel_settings.assert_called_once_with(mock_bot, mock_call)
		mock_open_user_selection.assert_called_once_with(mock_bot, mock_call, channel_manager.SETTING_TYPES.ASSIGNED)
		mock_start_deferred_interval_check.assert_not_called()

	@patch("channel_manager.save_channel_settings")
	@patch("channel_manager.open_user_selection")
	@patch("channel_manager.start_deferred_interval_check")
	def test_reported_selected(self, mock_start_deferred_interval_check, mock_open_user_selection,
							   mock_save_channel_settings, *args):
		channel_id = -10012345678
		message_id = 123
		mock_bot = Mock(spec=TeleBot)
		mock_call = Mock(spec=CallbackQuery)
		mock_call.data = f"{channel_manager.CALLBACK_PREFIX},{channel_manager.CB_TYPES.REPORTED_SELECTED},"
		mock_call.message = test_helper.create_mock_message("", [], channel_id, message_id)

		channel_manager.handle_callback(mock_bot, mock_call)
		mock_save_channel_settings.assert_called_once_with(mock_bot, mock_call)
		mock_open_user_selection.assert_called_once_with(mock_bot, mock_call, channel_manager.SETTING_TYPES.REPORTED)
		mock_start_deferred_interval_check.assert_not_called()

	@patch("channel_manager.save_channel_settings")
	@patch("channel_manager.open_user_selection")
	@patch("channel_manager.start_deferred_interval_check")
	def test_followed_selected(self, mock_start_deferred_interval_check, mock_open_user_selection,
							   mock_save_channel_settings, *args):
		channel_id = -10012345678
		message_id = 123
		mock_bot = Mock(spec=TeleBot)
		mock_call = Mock(spec=CallbackQuery)
		mock_call.data = f"{channel_manager.CALLBACK_PREFIX},{channel_manager.CB_TYPES.FOLLOWED_SELECTED},"
		mock_call.message = test_helper.create_mock_message("", [], channel_id, message_id)

		channel_manager.handle_callback(mock_bot, mock_call)
		mock_save_channel_settings.assert_called_once_with(mock_bot, mock_call)
		mock_open_user_selection.assert_called_once_with(mock_bot, mock_call, channel_manager.SETTING_TYPES.FOLLOWED)
		mock_start_deferred_interval_check.assert_not_called()



if __name__ == "__main__":
	main()
