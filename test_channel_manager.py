from unittest import TestCase, main
from unittest.mock import patch, Mock, call
from telebot import TeleBot
from telebot.types import Message


import channel_manager
import test_helper


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

		mock_message = Mock(spec=Message)
		mock_message.id = message_id
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

		mock_message = Mock(spec=Message)
		mock_message.id = message_id
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

		mock_message = Mock(spec=Message)
		mock_message.id = message_id
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

		mock_message = Mock(spec=Message)
		mock_message.id = message_id
		mock_bot.send_message.return_value = mock_message

		mock_get_exist_settings_message.return_value = True

		channel_manager.create_settings_message(mock_bot, channel_id)
		mock_get_exist_settings_message.assert_called_once_with(mock_bot, channel_id)
		mock_set_settings_message_id.assert_not_called()

	@patch("utils.get_last_message")
	@patch("utils.get_main_message_content_by_id")
	@patch("channel_manager.get_text_information_text")
	@patch("channel_manager.update_settings_message")
	@patch("db_utils.get_newest_copied_message")
	@patch("channel_manager.set_settings_message_id")
	@patch("forwarding_utils.generate_control_buttons")
	@patch("utils.edit_message_keyboard")
	def test_get_exist_settings_message(self, mock_edit_message_keyboard, mock_generate_control_buttons,
										mock_set_settings_message_id, mock_get_newest_copied_message,
										mock_update_settings_message, mock_get_text_information_text,
										mock_get_main_message_content_by_id, mock_get_last_message,
										mock_get_oldest_copied_message, *args):
		mock_bot = Mock(spec=TeleBot)
		channel_id = -10012345678
		last_message_id = 5
		message_id = 1
		expected_calls = [
			call.a(mock_bot, channel_id, 1),
			call.a(mock_bot, channel_id, 5)
		]

		mock_get_text_information_text.return_value = f"{message_id}"

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
		mock_get_text_information_text.assert_called_once_with()
		mock_update_settings_message.assert_called_once_with(mock_bot, channel_id, message_id)
		mock_set_settings_message_id.assert_called_once_with(channel_id, message_id)

		# Test update settings button
		mock_generate_control_buttons.assert_called_once()
		mock_edit_message_keyboard.assert_called_once_with(mock_bot, mock_message, mock_generate_control_buttons.return_value,
														   channel_id, last_message_id)


		self.assertTrue(result)

	@patch("utils.get_last_message")
	@patch("utils.get_main_message_content_by_id")
	@patch("channel_manager.get_text_information_text")
	@patch("channel_manager.set_settings_message_id")
	def test_get_exist_settings_message_with_empty_message(self, mock_set_settings_message_id, mock_get_text_information_text,
										mock_get_main_message_content_by_id, mock_get_last_message, *args):
		mock_bot = Mock(spec=TeleBot)
		channel_id = -10012345678
		last_message_id = 5
		message_id = 1
		expected_calls = []
		mock_get_text_information_text.return_value = f"{message_id}"
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
		mock_get_text_information_text.assert_called_once_with()
		mock_set_settings_message_id.assert_not_called()
		self.assertFalse(result)

	@patch("utils.get_last_message")
	@patch("utils.get_main_message_content_by_id")
	@patch("channel_manager.get_text_information_text")
	@patch("channel_manager.set_settings_message_id")
	def test_get_exist_information_message_without_information_message(self, mock_set_settings_message_id, mock_get_text_information_text,
										mock_get_main_message_content_by_id, mock_get_last_message, *args):
		mock_bot = Mock(spec=TeleBot)
		channel_id = -10012345678
		last_message_id = 5
		message_id = 3
		expected_calls = []
		mock_get_text_information_text.return_value = f"{message_id}"
		mock_message = test_helper.create_mock_message("", [])
		mock_get_main_message_content_by_id.return_value = mock_message
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
		mock_get_text_information_text.assert_called_once_with()
		mock_set_settings_message_id.assert_not_called()
		self.assertFalse(result)

	@patch("utils.get_last_message")
	@patch("utils.get_main_message_content_by_id")
	@patch("channel_manager.get_text_information_text")
	@patch("channel_manager.set_settings_message_id")
	def test_get_exist_information_message_without_information_message_with_copied_messages(self,
										mock_set_settings_message_id, mock_get_text_information_text,
										mock_get_main_message_content_by_id, mock_get_last_message,
										mock_get_oldest_copied_message, *args):
		mock_bot = Mock(spec=TeleBot)
		channel_id = -10012345678
		last_message_id = 5
		last_copied_id = 3
		message_id = 3
		expected_calls = []
		mock_get_text_information_text.return_value = f"{message_id}"
		mock_message = test_helper.create_mock_message("", [])
		mock_get_main_message_content_by_id.return_value = mock_message
		manager = Mock()
		manager.attach_mock(mock_get_main_message_content_by_id, 'a')

		for i in range(1, last_copied_id + 1):
			expected_calls.append(call.a(mock_bot, channel_id, i))

		mock_get_last_message.return_value = last_message_id
		mock_get_oldest_copied_message.return_value = last_copied_id
		result = channel_manager.get_exist_settings_message(mock_bot, channel_id)
		# Test get last message
		mock_get_oldest_copied_message.assert_called_once_with(channel_id)
		mock_get_last_message.assert_not_called()
		# Test get content in all messages
		self.assertEqual(manager.mock_calls, expected_calls)
		# Test find settings message
		mock_get_text_information_text.assert_called_once_with()
		mock_set_settings_message_id.assert_not_called()
		self.assertFalse(result)


if __name__ == "__main__":
	main()
