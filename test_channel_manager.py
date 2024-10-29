from unittest import TestCase, main
from unittest.mock import patch, Mock
from telebot import TeleBot

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


if __name__ == "__main__":
	main()
