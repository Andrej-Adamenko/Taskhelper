from unittest import TestCase, main
from unittest.mock import patch, Mock, call, ANY

from telebot import TeleBot
from telebot.types import CallbackQuery, User, InlineKeyboardMarkup, InlineKeyboardButton, ChatMemberOwner

import config_utils
from tests import test_helper
import channel_manager


@patch("telebot.types.CallbackQuery.__init__", return_value=None)
@patch("channel_manager.NEW_USER_TYPE", "+")
@patch("channel_manager._update_user_tags_in_settings_menu_ticket")
@patch("db_utils.update_individual_channel_settings")
@patch("channel_manager.update_settings_message")
@patch("db_utils.get_all_individual_channels")
class AddNewUserTagToChannelsTest(TestCase):
	def test_add_new_user(self, mock_get_all_individual_channels, mock_update_settings_message,
						  mock_update_individual_channel_settings, mock__update_user_tags_in_settings_menu_ticket, *args):
		channel_settings = '{"assigned": ["FF", "+"], "cc": ["FF"]}'
		channel_id = -10012345678
		mock_get_all_individual_channels.return_value = [[channel_id, channel_settings]]
		mock_bot = Mock(spec=TeleBot)
		new_user_tag = "NN"

		channel_manager.add_new_user_tag_to_channels(mock_bot, new_user_tag)
		mock_get_all_individual_channels.assert_called_once_with()
		mock_update_individual_channel_settings.assert_called_once_with(channel_id, '{"assigned": ["FF", "+", "NN"], "cc": ["FF"]}')
		mock_update_settings_message.assert_not_called()
		mock__update_user_tags_in_settings_menu_ticket.assert_called_once_with(mock_bot, channel_id)

	def test_update_settings_message(self, mock_get_all_individual_channels, mock_update_settings_message,
									 mock_update_individual_channel_settings, mock__update_user_tags_in_settings_menu_ticket, *args):
		channel_settings = '{"assigned": ["FF", "+"], "cc": ["FF"], "settings_message_id": 3079}'
		channel_id = -10012345678
		mock_get_all_individual_channels.return_value = [[channel_id, channel_settings]]
		mock_bot = Mock(spec=TeleBot)
		new_user_tag = "NN"

		channel_manager.add_new_user_tag_to_channels(mock_bot, new_user_tag)
		mock_get_all_individual_channels.assert_called_once_with()
		mock_update_individual_channel_settings.assert_called_once_with(channel_id, '{"assigned": ["FF", "+", "NN"], "cc": ["FF"], "settings_message_id": 3079}')
		mock_update_settings_message.assert_called_once_with(mock_bot, channel_id, 3079)
		mock__update_user_tags_in_settings_menu_ticket.assert_called_once_with(mock_bot, channel_id)


@patch("telebot.types.CallbackQuery.__init__", return_value=None)
@patch("channel_manager._update_user_tags_in_settings_menu_ticket")
@patch("db_utils.update_individual_channel_settings")
@patch("channel_manager.update_settings_message")
@patch("db_utils.get_all_individual_channels")
class RemoveUserTagFromChannelsTest(TestCase):
	def test_remove_user(self, mock_get_all_individual_channels, mock_update_settings_message,
						 mock_update_individual_channel_settings, mock__update_user_tags_in_settings_menu_ticket, *args):
		channel_settings = '{"assigned": ["FF", "NN"], "cc": ["NN"]}'
		channel_id = -10012345678
		mock_get_all_individual_channels.return_value = [[channel_id, channel_settings]]
		mock_bot = Mock(spec=TeleBot)
		user_tag = "NN"

		channel_manager.remove_user_tag_from_channels(mock_bot, user_tag)
		mock_get_all_individual_channels.assert_called_once_with()
		mock_update_individual_channel_settings.assert_called_once_with(channel_id, '{"assigned": ["FF"], "cc": []}')
		mock_update_settings_message.assert_not_called()
		mock__update_user_tags_in_settings_menu_ticket.assert_called_once_with(mock_bot, channel_id)

	def test_update_settings_message(self, mock_get_all_individual_channels, mock_update_settings_message,
									 mock_update_individual_channel_settings, mock__update_user_tags_in_settings_menu_ticket, *args):
		channel_settings = '{"assigned": ["FF", "NN"], "cc": ["NN"], "settings_message_id": 3079}'
		channel_id = -10012345678
		mock_get_all_individual_channels.return_value = [[channel_id, channel_settings]]
		mock_bot = Mock(spec=TeleBot)
		user_tag = "NN"

		channel_manager.remove_user_tag_from_channels(mock_bot, user_tag)
		mock_get_all_individual_channels.assert_called_once_with()
		mock_update_individual_channel_settings.assert_called_once_with(channel_id, '{"assigned": ["FF"], "cc": [], "settings_message_id": 3079}')
		mock_update_settings_message.assert_called_once_with(mock_bot, channel_id, 3079)
		mock__update_user_tags_in_settings_menu_ticket.assert_called_once_with(mock_bot, channel_id)


@patch("utils.edit_message_keyboard")
@patch("forwarding_utils.get_keyboard_from_channel_message")
@patch("utils.get_message_content_by_id")
@patch("db_utils.get_newest_copied_message")
class UpdateUserTagsInSettingsMenuTicket(TestCase):
	@patch("channel_manager.CHANNEL_TICKET_SETTINGS_BUTTONS", {-10012345678: {channel_manager.TICKET_MENU_TYPE: {
							"user": 1, "state": channel_manager.CB_TYPES.ASSIGNED_SELECTED}}})
	def test_update_last_ticket_keyboard_assigned(self, mock_get_newest_copied_message, mock_get_message_content_by_id,
										  mock_get_keyboard_from_channel_message, mock_edit_message_keyboard, *args):
		channel_id = -10012345678
		newest_message_id = 156
		mock_bot = Mock(spec=TeleBot)
		mock_message = test_helper.create_mock_message("", [], channel_id, newest_message_id)
		mock_message.from_user = Mock(id=15345)
		mock_keyboard = Mock(spec=InlineKeyboardMarkup)
		mock_get_newest_copied_message.return_value = newest_message_id
		mock_get_message_content_by_id.return_value = mock_message
		mock_get_keyboard_from_channel_message.return_value = mock_keyboard

		channel_manager._update_user_tags_in_settings_menu_ticket(mock_bot, channel_id)
		mock_get_newest_copied_message.assert_called_once_with(channel_id)
		mock_get_message_content_by_id(mock_bot, channel_id, newest_message_id)
		mock_get_keyboard_from_channel_message.assert_called_once_with(mock_bot, ANY, newest_message_id)
		mock_edit_message_keyboard.assert_called_once_with(mock_bot, mock_message, keyboard_markup=mock_keyboard,
														   chat_id=channel_id, message_id=newest_message_id)

	@patch("channel_manager.CHANNEL_TICKET_SETTINGS_BUTTONS", {-10012345678: {channel_manager.TICKET_MENU_TYPE: {
							"user": 1, "state": channel_manager.CB_TYPES.REPORTED_SELECTED}}})
	def test_update_last_ticket_keyboard_reported(self, mock_get_newest_copied_message, mock_get_message_content_by_id,
										  mock_get_keyboard_from_channel_message, mock_edit_message_keyboard, *args):
		channel_id = -10012345678
		newest_message_id = 156
		mock_bot = Mock(spec=TeleBot)
		mock_message = test_helper.create_mock_message("", [], channel_id, newest_message_id)
		mock_message.from_user = Mock(id=15345)
		mock_keyboard = Mock(spec=InlineKeyboardMarkup)
		mock_get_newest_copied_message.return_value = newest_message_id
		mock_get_message_content_by_id.return_value = mock_message
		mock_get_keyboard_from_channel_message.return_value = mock_keyboard

		channel_manager._update_user_tags_in_settings_menu_ticket(mock_bot, channel_id)
		mock_get_newest_copied_message.assert_called_once_with(channel_id)
		mock_get_message_content_by_id(mock_bot, channel_id, newest_message_id)
		mock_get_keyboard_from_channel_message.assert_called_once_with(mock_bot, ANY, newest_message_id)
		mock_edit_message_keyboard.assert_called_once_with(mock_bot, mock_message, keyboard_markup=mock_keyboard,
														   chat_id=channel_id, message_id=newest_message_id)

	@patch("channel_manager.CHANNEL_TICKET_SETTINGS_BUTTONS", {-10012345678: {channel_manager.TICKET_MENU_TYPE: {
							"user": 1, "state": channel_manager.CB_TYPES.FOLLOWED_SELECTED}}})
	def test_update_last_ticket_keyboard_followed(self, mock_get_newest_copied_message, mock_get_message_content_by_id,
										  mock_get_keyboard_from_channel_message, mock_edit_message_keyboard, *args):
		channel_id = -10012345678
		newest_message_id = 156
		mock_bot = Mock(spec=TeleBot)
		mock_message = test_helper.create_mock_message("", [], channel_id, newest_message_id)
		mock_message.from_user = Mock(id=15345)
		mock_keyboard = Mock(spec=InlineKeyboardMarkup)
		mock_get_newest_copied_message.return_value = newest_message_id
		mock_get_message_content_by_id.return_value = mock_message
		mock_get_keyboard_from_channel_message.return_value = mock_keyboard

		channel_manager._update_user_tags_in_settings_menu_ticket(mock_bot, channel_id)
		mock_get_newest_copied_message.assert_called_once_with(channel_id)
		mock_get_message_content_by_id(mock_bot, channel_id, newest_message_id)
		mock_get_keyboard_from_channel_message.assert_called_once_with(mock_bot, ANY, newest_message_id)
		mock_edit_message_keyboard.assert_called_once_with(mock_bot, mock_message, keyboard_markup=mock_keyboard,
														   chat_id=channel_id, message_id=newest_message_id)

	@patch("channel_manager.CHANNEL_TICKET_SETTINGS_BUTTONS", {-10012345678: {channel_manager.TICKET_MENU_TYPE: {
							"user": 1, "state": channel_manager.CB_TYPES.OPEN_CHANNEL_SETTINGS}}})
	def test_update_last_ticket_keyboard_open_channel(self, mock_get_newest_copied_message, mock_get_message_content_by_id,
										  mock_get_keyboard_from_channel_message, mock_edit_message_keyboard, *args):
		channel_id = -10012345678
		newest_message_id = 156
		mock_bot = Mock(spec=TeleBot)
		mock_message = test_helper.create_mock_message("", [], channel_id, newest_message_id)
		mock_message.from_user = Mock(id=15345)
		mock_keyboard = Mock(spec=InlineKeyboardMarkup)
		mock_get_newest_copied_message.return_value = newest_message_id
		mock_get_message_content_by_id.return_value = mock_message
		mock_get_keyboard_from_channel_message.return_value = mock_keyboard

		channel_manager._update_user_tags_in_settings_menu_ticket(mock_bot, channel_id)
		mock_get_newest_copied_message.assert_called_once_with(channel_id)
		mock_get_message_content_by_id.assert_called_once_with(mock_bot, channel_id, newest_message_id)
		mock_get_keyboard_from_channel_message.assert_called_once_with(mock_bot, ANY, newest_message_id)
		mock_edit_message_keyboard.assert_called_once_with(mock_bot, mock_message, keyboard_markup=mock_keyboard,
														   chat_id=channel_id, message_id=newest_message_id)

	@patch("channel_manager.CHANNEL_TICKET_SETTINGS_BUTTONS", {-10012345678: {channel_manager.TICKET_MENU_TYPE: {
							"user": 1, "state": channel_manager.CB_TYPES.REMIND_SELECTED}}})
	def test_update_last_ticket_keyboard_remind(self, mock_get_newest_copied_message, mock_get_message_content_by_id,
										  mock_get_keyboard_from_channel_message, mock_edit_message_keyboard, *args):
		channel_id = -10012345678
		newest_message_id = 156
		mock_bot = Mock(spec=TeleBot)
		mock_message = test_helper.create_mock_message("", [], channel_id, newest_message_id)
		mock_message.from_user = Mock(id=15345)
		mock_keyboard = Mock(spec=InlineKeyboardMarkup)
		mock_get_newest_copied_message.return_value = newest_message_id
		mock_get_message_content_by_id.return_value = mock_message
		mock_get_keyboard_from_channel_message.return_value = mock_keyboard

		channel_manager._update_user_tags_in_settings_menu_ticket(mock_bot, channel_id)
		mock_get_newest_copied_message.assert_not_called()
		mock_get_message_content_by_id.assert_not_called()
		mock_get_keyboard_from_channel_message.assert_not_called()
		mock_edit_message_keyboard.assert_not_called()

	@patch("channel_manager.CHANNEL_TICKET_SETTINGS_BUTTONS", {})
	def test_update_last_ticket_keyboard_empty(self, mock_get_newest_copied_message, mock_get_message_content_by_id,
										  mock_get_keyboard_from_channel_message, mock_edit_message_keyboard, *args):
		channel_id = -10012345678
		newest_message_id = 156
		mock_bot = Mock(spec=TeleBot)
		mock_message = test_helper.create_mock_message("", [], channel_id, newest_message_id)
		mock_message.from_user = Mock(id=15345)
		mock_keyboard = Mock(spec=InlineKeyboardMarkup)
		mock_get_newest_copied_message.return_value = newest_message_id
		mock_get_message_content_by_id.return_value = mock_message
		mock_get_keyboard_from_channel_message.return_value = mock_keyboard

		channel_manager._update_user_tags_in_settings_menu_ticket(mock_bot, channel_id)
		mock_get_newest_copied_message.assert_not_called()
		mock_get_message_content_by_id.assert_not_called()
		mock_get_keyboard_from_channel_message.assert_not_called()
		mock_edit_message_keyboard.assert_not_called()


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
		self.assertIn("If this message with settings was deleted you can call \"/settings\" command to create it", text)

		self.assertIn("Assigned to - include tickets that is assigned to the selected users", text)
		self.assertIn("Reported by - include tickets that is created by the selected users", text)
		self.assertIn("CCed to - include tickets where the selected users in CC", text)
		self.assertIn("Remind me when - regulates what tickets can be reminded in this channel", text)
		self.assertIn("Due - if this option is enabled, regular (NOT deferred) tickets and also tickets deferred until a date, but that date is in the past now, will all be included in this channel", text)
		self.assertIn("Deferred - if this option is enabled, tickets, deferred until now will be included in this channel", text)
		self.assertIn("Priority 1/2/3 - here you should specify which tickets with priority 1, 2 and 3 will be forwarded to this channel", text)

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

	@patch("db_utils.delete_copied_message")
	@patch("db_utils.get_individual_channel_settings")
	@patch("channel_manager.get_exist_settings_message")
	@patch("db_utils.get_main_message_from_copied")
	@patch("db_utils.insert_or_update_last_msg_id")
	@patch("channel_manager.set_settings_message_id")
	def test_create_settings_message_with_oldest_message(self, mock_set_settings_message_id, mock_insert_or_update_last_msg_id,
									 mock_get_main_message_from_copied,
									 mock_get_exist_settings_message, mock_get_individual_channel_settings,
									 mock_delete_copied_message, mock_get_oldest_copied_message, *args):
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
		mock_delete_copied_message.assert_called_once_with(oldest_message_id, channel_id)
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
	@patch("channel_manager.update_settings_message")
	@patch("db_utils.get_newest_copied_message")
	@patch("channel_manager.set_settings_message_id")
	@patch("forwarding_utils.generate_control_buttons")
	@patch("utils.edit_message_keyboard")
	def test_get_exist_settings_message_without_last_message(self, mock_edit_message_keyboard, mock_generate_control_buttons,
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

		mock_get_last_message.return_value = None
		mock_get_newest_copied_message.return_value = last_message_id

		result = channel_manager.get_exist_settings_message(mock_bot, channel_id)
		# Test get last message
		mock_get_oldest_copied_message.assert_called_once_with(channel_id)
		mock_get_last_message.assert_called_once_with(mock_bot, channel_id)
		mock_get_main_message_content_by_id.assert_not_called()
		# Test update settings message
		mock_is_settings_message.assert_not_called()
		mock_update_settings_message.assert_not_called()
		mock_set_settings_message_id.assert_not_called()

		# Test update settings button
		mock_generate_control_buttons.assert_not_called()
		mock_edit_message_keyboard.assert_not_called()
		self.assertFalse(result)

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

	@patch("db_utils.is_copied_message_exists")
	@patch("db_utils.is_main_message_exists")
	def test_is_settings_message(self, mock_is_main_message_exists, mock_is_copied_message_exists, *args):
		mock_is_copied_message_exists.return_value = True
		mock_is_main_message_exists.return_value = False
		result = channel_manager.is_settings_message(test_helper.create_mock_message("", [], -10012345, 123))
		self.assertFalse(result)

		mock_is_copied_message_exists.return_value = False
		mock_is_main_message_exists.return_value = True
		result = channel_manager.is_settings_message(test_helper.create_mock_message("", [], -10012345, 123))
		self.assertFalse(result)

		mock_is_copied_message_exists.return_value = True
		mock_is_main_message_exists.return_value = True
		result = channel_manager.is_settings_message(test_helper.create_mock_message("", [], -10012345, 123))
		self.assertFalse(result)

		mock_is_copied_message_exists.return_value = False
		mock_is_main_message_exists.return_value = False
		result = channel_manager.is_settings_message(test_helper.create_mock_message("", [], -10012345, 123))
		self.assertTrue(result)

	@patch("channel_manager.is_button_checked", return_value=False)
	@patch("utils.parse_callback_str", return_value=[channel_manager.CB_TYPES.DUE_SELECTED, [""]])
	@patch("channel_manager.save_toggle_button")
	def test_toggle_button_error_due(self, mock_save_toggle_button, *args):
		channel_id = -10012345678
		message_id = 123
		mock_bot = Mock(spec=TeleBot)
		mock_call = Mock(spec=CallbackQuery)
		mock_call.id = 12234
		mock_button = Mock(spec=InlineKeyboardButton)
		mock_button.text = f"Due{config_utils.BUTTON_TEXTS['CHECK']}"
		mock_button.callback_data = f"{channel_manager.CALLBACK_PREFIX},{channel_manager.CB_TYPES.DUE_SELECTED},"
		mock_keyboard = Mock(spec=InlineKeyboardMarkup)
		mock_keyboard.keyboard = [[mock_button]]
		mock_call.message = test_helper.create_mock_message("", [], channel_id, message_id)
		mock_call.message.reply_markup = mock_keyboard

		channel_manager.toggle_button(mock_bot, mock_call, channel_manager.CB_TYPES.DUE_SELECTED, [""])
		mock_bot.answer_callback_query.assert_called_once_with(callback_query_id=mock_call.id, text="At least one of the Due and Deferred buttons should be selected")
		mock_save_toggle_button.assert_not_called()
		mock_bot.edit_message_reply_markup.assert_not_called()
		self.assertEqual(f"Due{config_utils.BUTTON_TEXTS['CHECK']}", mock_keyboard.keyboard[0][0].text)

	@patch("channel_manager.is_button_checked", return_value=True)
	@patch("utils.parse_callback_str", return_value=[channel_manager.CB_TYPES.DUE_SELECTED, [""]])
	@patch("channel_manager.save_toggle_button")
	def test_toggle_button(self, mock_save_toggle_button, *args):
		channel_id = -10012345678
		message_id = 123
		mock_bot = Mock(spec=TeleBot)
		mock_call = Mock(spec=CallbackQuery)
		mock_call.id = 12234
		mock_button = Mock(spec=InlineKeyboardButton)
		mock_button.text = f"Due{config_utils.BUTTON_TEXTS['CHECK']}"
		mock_button.callback_data = f"{channel_manager.CALLBACK_PREFIX},{channel_manager.CB_TYPES.DUE_SELECTED},"
		mock_keyboard = Mock(spec=InlineKeyboardMarkup)
		mock_keyboard.keyboard = [[mock_button]]
		mock_call.message = test_helper.create_mock_message("", [], channel_id, message_id)
		mock_call.message.reply_markup = mock_keyboard

		channel_manager.toggle_button(mock_bot, mock_call, channel_manager.CB_TYPES.DUE_SELECTED, [""])
		mock_bot.answer_callback_query.assert_not_called()
		mock_save_toggle_button.assert_called_once_with(mock_bot, mock_call, channel_manager.SETTING_TYPES.DUE, "", False)
		mock_bot.edit_message_reply_markup.assert_not_called()
		self.assertEqual("Due", mock_keyboard.keyboard[0][0].text)

	@patch("channel_manager.is_button_checked", return_value=True)
	@patch("channel_manager.save_toggle_button")
	def test_toggle_button_user(self, mock_save_toggle_button, *args):
		channel_id = -10012345678
		message_id = 123
		mock_bot = Mock(spec=TeleBot)
		mock_call = Mock(spec=CallbackQuery)
		mock_call.id = 12234
		mock_button = Mock(spec=InlineKeyboardButton)
		mock_button.text = f"Due{config_utils.BUTTON_TEXTS['CHECK']}"
		mock_button.callback_data = f"{channel_manager.CALLBACK_PREFIX},{channel_manager.CB_TYPES.TOGGLE_USER},{channel_manager.SETTING_TYPES.ASSIGNED},cc"
		mock_keyboard = Mock(spec=InlineKeyboardMarkup)
		mock_keyboard.keyboard = [[mock_button]]
		mock_call.message = test_helper.create_mock_message("", [], channel_id, message_id)
		mock_call.message.reply_markup = mock_keyboard

		channel_manager.toggle_button(mock_bot, mock_call, channel_manager.CB_TYPES.TOGGLE_USER,
									  [channel_manager.SETTING_TYPES.ASSIGNED, "cc"])
		mock_bot.answer_callback_query.assert_not_called()
		mock_save_toggle_button.assert_called_once_with(mock_bot, mock_call, channel_manager.SETTING_TYPES.ASSIGNED, "cc", False)
		mock_bot.edit_message_reply_markup.assert_not_called()
		self.assertEqual("Due", mock_keyboard.keyboard[0][0].text)

	@patch("channel_manager.is_button_checked", return_value=True)
	@patch("utils.parse_callback_str", return_value=[channel_manager.CB_TYPES.DUE_SELECTED, [""]])
	@patch("channel_manager.save_toggle_button")
	def test_toggle_button_empty(self, mock_save_toggle_button, *args):
		channel_id = -10012345678
		message_id = 123
		mock_bot = Mock(spec=TeleBot)
		mock_call = Mock(spec=CallbackQuery)
		mock_call.id = 12234
		mock_keyboard = Mock(spec=InlineKeyboardMarkup)
		mock_keyboard.keyboard = [[]]
		mock_call.message = test_helper.create_mock_message("", [], channel_id, message_id)
		mock_call.message.reply_markup = mock_keyboard

		channel_manager.toggle_button(mock_bot, mock_call, channel_manager.CB_TYPES.DUE_SELECTED, [""])
		mock_bot.answer_callback_query.assert_not_called()
		mock_save_toggle_button.assert_not_called()
		mock_bot.edit_message_reply_markup.assert_not_called()


@patch("config_utils.USER_TAGS", {"AA": 1, "BB": 2, "CC": 3, "FF": 4, "NN": 5})
class SortArraySettingsTest(TestCase):
	def test_assigned(self, *args):
		result = channel_manager._sort_array_settings(["CC", "AA", "NN"], channel_manager.SETTING_TYPES.ASSIGNED)
		self.assertEqual(result, ["AA", "CC", "NN"])

	def test_assigned_no_tags(self, *args):
		config_utils.USER_TAGS = {}

		result = channel_manager._sort_array_settings(["CC", "AA", "NN"], channel_manager.SETTING_TYPES.ASSIGNED)
		self.assertEqual(result, [])

	def test_reported(self, *args):
		result = channel_manager._sort_array_settings(["NN", "BB", "FF"], channel_manager.SETTING_TYPES.REPORTED)
		self.assertEqual(result, ["BB", "FF", "NN"])

	def test_followed(self, *args):
		result = channel_manager._sort_array_settings(["GG", "BB", "FF"], channel_manager.SETTING_TYPES.REPORTED)
		self.assertEqual(result, ["BB", "FF"])

	def test_remind(self, *args):
		result = channel_manager._sort_array_settings(["cced", "assigned", "CC", "reported"], channel_manager.SETTING_TYPES.REMIND)
		self.assertEqual(result, ["assigned", "reported", "cced"])


@patch("channel_manager.CHANNEL_TICKET_SETTINGS_BUTTONS", {-10012345678: {"ticket": {"state": channel_manager.CB_TYPES.OPEN_CHANNEL_SETTINGS, "user": 85241367}}})
@patch("config_utils.USER_TAGS", {"FF": 1, "CC": 2, "NN": 3})
@patch("db_utils.get_individual_channel_settings",
		return_value=['{"due": true, "assigned": ["FF", "NN"], "reported": ["+"]}',
					  '1,2'])
@patch("db_utils.update_individual_channel")
@patch("channel_manager.show_settings_keyboard")
class TestSaveToggleButton(TestCase):
	def test_save_toggle_button_set(self, mock_show_settings_keyboard, mock_update_individual_channel,
									mock_get_individual_channel_settings, *args):
		channel_id = -10012345678
		message_id = 123
		mock_bot = Mock(spec=TeleBot)
		mock_call = Mock(spec=CallbackQuery)
		mock_call.id = 12234
		mock_keyboard = Mock(spec=InlineKeyboardMarkup)
		mock_keyboard.keyboard = [[]]
		mock_call.message = test_helper.create_mock_message("", [], channel_id, message_id)
		mock_call.message.reply_markup = mock_keyboard
		setting_type = channel_manager.SETTING_TYPES.DUE
		cb_data = ""
		is_enabled = True

		channel_manager.save_toggle_button(mock_bot, mock_call, setting_type, cb_data, is_enabled)
		mock_get_individual_channel_settings.assert_called_once_with(channel_id)
		mock_update_individual_channel.assert_called_once_with(channel_id, '{"due": true, "deferred": false, "assigned": ["FF", "NN"], "reported": ["+"]}',  '1,2')
		mock_show_settings_keyboard.assert_called_once_with(mock_bot, mock_call, True, True)

	def test_save_toggle_button_add(self, mock_show_settings_keyboard, mock_update_individual_channel,
									mock_get_individual_channel_settings, *args):
		channel_id = -10012345678
		message_id = 123
		mock_bot = Mock(spec=TeleBot)
		mock_call = Mock(spec=CallbackQuery)
		mock_call.id = 12234
		mock_keyboard = Mock(spec=InlineKeyboardMarkup)
		mock_keyboard.keyboard = [[]]
		mock_call.message = test_helper.create_mock_message("", [], channel_id, message_id)
		mock_call.message.reply_markup = mock_keyboard
		setting_type = channel_manager.SETTING_TYPES.DEFERRED
		cb_data = ""
		is_enabled = True

		channel_manager.save_toggle_button(mock_bot, mock_call, setting_type, cb_data, is_enabled)
		mock_get_individual_channel_settings.assert_called_once_with(channel_id)
		mock_update_individual_channel.assert_called_once_with(channel_id, '{"due": true, "deferred": true, "assigned": ["FF", "NN"], "reported": ["+"]}',  '1,2')
		mock_show_settings_keyboard.assert_called_once_with(mock_bot, mock_call, True, True)

	def test_save_toggle_button_remove_due_and_deferred(self, mock_show_settings_keyboard, mock_update_individual_channel,
									mock_get_individual_channel_settings, *args):
		channel_id = -10012345678
		message_id = 123
		mock_bot = Mock(spec=TeleBot)
		mock_call = Mock(spec=CallbackQuery)
		mock_call.id = 12234
		mock_keyboard = Mock(spec=InlineKeyboardMarkup)
		mock_keyboard.keyboard = [[]]
		mock_call.message = test_helper.create_mock_message("", [], channel_id, message_id)
		mock_call.message.reply_markup = mock_keyboard
		setting_type = channel_manager.SETTING_TYPES.DUE
		cb_data = ""
		is_enabled = False

		channel_manager.save_toggle_button(mock_bot, mock_call, setting_type, cb_data, is_enabled)
		mock_get_individual_channel_settings.assert_called_once_with(channel_id)
		mock_update_individual_channel.assert_not_called()
		mock_show_settings_keyboard.assert_called_once_with(mock_bot, mock_call, True, True)

	def test_save_toggle_button_priority_remove(self, mock_show_settings_keyboard, mock_update_individual_channel,
									mock_get_individual_channel_settings, *args):
		channel_id = -10012345678
		message_id = 123
		mock_bot = Mock(spec=TeleBot)
		mock_call = Mock(spec=CallbackQuery)
		mock_call.id = 12234
		mock_keyboard = Mock(spec=InlineKeyboardMarkup)
		mock_keyboard.keyboard = [[]]
		mock_call.message = test_helper.create_mock_message("", [], channel_id, message_id)
		mock_call.message.reply_markup = mock_keyboard
		setting_type = channel_manager.CB_TYPES.PRIORITY_SELECTED
		cb_data = "2"
		is_enabled = False

		channel_manager.save_toggle_button(mock_bot, mock_call, setting_type, cb_data, is_enabled)
		mock_get_individual_channel_settings.assert_called_once_with(channel_id)
		mock_update_individual_channel.assert_called_once_with(channel_id, '{"due": true, "deferred": false, "assigned": ["FF", "NN"], "reported": ["+"]}',  '1')
		mock_show_settings_keyboard.assert_called_once_with(mock_bot, mock_call, True, True)

	def test_save_toggle_button_priority_add(self, mock_show_settings_keyboard, mock_update_individual_channel,
									mock_get_individual_channel_settings, *args):
		channel_id = -10012345678
		message_id = 123
		mock_bot = Mock(spec=TeleBot)
		mock_call = Mock(spec=CallbackQuery)
		mock_call.id = 12234
		mock_keyboard = Mock(spec=InlineKeyboardMarkup)
		mock_keyboard.keyboard = [[]]
		mock_call.message = test_helper.create_mock_message("", [], channel_id, message_id)
		mock_call.message.reply_markup = mock_keyboard
		setting_type = channel_manager.CB_TYPES.PRIORITY_SELECTED
		cb_data = "3"
		is_enabled = True

		channel_manager.save_toggle_button(mock_bot, mock_call, setting_type, cb_data, is_enabled)
		mock_get_individual_channel_settings.assert_called_once_with(channel_id)
		mock_update_individual_channel.assert_called_once_with(channel_id, '{"due": true, "deferred": false, "assigned": ["FF", "NN"], "reported": ["+"]}',  '1,2,3')
		mock_show_settings_keyboard.assert_called_once_with(mock_bot, mock_call, True, True)

	def test_save_toggle_button_add_array(self, mock_show_settings_keyboard, mock_update_individual_channel,
									mock_get_individual_channel_settings, *args):
		channel_id = -10012345678
		message_id = 123
		user_id = 85241367
		mock_bot = Mock(spec=TeleBot)
		mock_call = Mock(spec=CallbackQuery)
		mock_call.id = 12234
		mock_keyboard = Mock(spec=InlineKeyboardMarkup)
		mock_keyboard.keyboard = [[]]
		mock_call.message = test_helper.create_mock_message("", [], channel_id, message_id)
		mock_call.message.reply_markup = mock_keyboard
		mock_call.from_user = Mock(spec=User)
		mock_call.from_user.id = user_id
		setting_type = channel_manager.SETTING_TYPES.FOLLOWED
		cb_data = "NN"
		is_enabled = True

		channel_manager.save_toggle_button(mock_bot, mock_call, setting_type, cb_data, is_enabled)
		mock_get_individual_channel_settings.assert_called_once_with(channel_id)
		mock_update_individual_channel.assert_called_once_with(channel_id, '{"due": true, "deferred": false, "assigned": ["FF", "NN"], "reported": ["+"], "cc": ["NN"]}',  '1,2')
		mock_show_settings_keyboard.assert_called_once_with(mock_bot, mock_call, True, True)

	def test_save_toggle_button_add_array_element(self, mock_show_settings_keyboard, mock_update_individual_channel,
									mock_get_individual_channel_settings, *args):
		channel_id = -10012345678
		message_id = 123
		user_id = 85241367
		mock_bot = Mock(spec=TeleBot)
		mock_call = Mock(spec=CallbackQuery)
		mock_call.id = 12234
		mock_keyboard = Mock(spec=InlineKeyboardMarkup)
		mock_keyboard.keyboard = [[]]
		mock_call.message = test_helper.create_mock_message("", [], channel_id, message_id)
		mock_call.message.reply_markup = mock_keyboard
		mock_call.from_user = Mock(spec=User)
		mock_call.from_user.id = user_id
		setting_type = channel_manager.SETTING_TYPES.ASSIGNED
		cb_data = "CC"
		is_enabled = True

		channel_manager.save_toggle_button(mock_bot, mock_call, setting_type, cb_data, is_enabled)
		mock_get_individual_channel_settings.assert_called_once_with(channel_id)
		mock_update_individual_channel.assert_called_once_with(channel_id, '{"due": true, "deferred": false, "assigned": ["FF", "CC", "NN"], "reported": ["+"]}', '1,2')
		mock_show_settings_keyboard.assert_called_once_with(mock_bot, mock_call, True, True)

	def test_save_toggle_button_add_remind(self, mock_show_settings_keyboard, mock_update_individual_channel,
									mock_get_individual_channel_settings, *args):
		channel_id = -10012345678
		message_id = 123
		mock_bot = Mock(spec=TeleBot)
		mock_call = Mock(spec=CallbackQuery)
		mock_call.id = 12234
		mock_keyboard = Mock(spec=InlineKeyboardMarkup)
		mock_keyboard.keyboard = [[]]
		mock_call.message = test_helper.create_mock_message("", [], channel_id, message_id)
		mock_call.message.reply_markup = mock_keyboard
		setting_type = channel_manager.SETTING_TYPES.REMIND
		cb_data = channel_manager.REMIND_TYPES.REPORTED
		is_enabled = True
		mock_get_individual_channel_settings.return_value = ['{"due": true, "deferred": false, "assigned": ["FF", "NN"], "remind": ["cced"]}', '2,3']

		channel_manager.save_toggle_button(mock_bot, mock_call, setting_type, cb_data, is_enabled)
		mock_get_individual_channel_settings.assert_called_once_with(channel_id)
		mock_update_individual_channel.assert_called_once_with(channel_id, '{"due": true, "deferred": false, "assigned": ["FF", "NN"], "remind": ["reported", "cced"]}', '2,3')
		mock_show_settings_keyboard.assert_called_once_with(mock_bot, mock_call, True, True)

	def test_save_toggle_button_add_priority(self, mock_show_settings_keyboard, mock_update_individual_channel,
									mock_get_individual_channel_settings, *args):
		channel_id = -10012345678
		message_id = 123
		mock_bot = Mock(spec=TeleBot)
		mock_call = Mock(spec=CallbackQuery)
		mock_call.id = 12234
		mock_keyboard = Mock(spec=InlineKeyboardMarkup)
		mock_keyboard.keyboard = [[]]
		mock_call.message = test_helper.create_mock_message("", [], channel_id, message_id)
		mock_call.message.reply_markup = mock_keyboard
		setting_type = channel_manager.CB_TYPES.PRIORITY_SELECTED
		cb_data = '1'
		is_enabled = True
		mock_get_individual_channel_settings.return_value = ['{"due": true, "deferred": false, "assigned": ["FF", "NN"], "reported": ["+"]}', '2,3']

		channel_manager.save_toggle_button(mock_bot, mock_call, setting_type, cb_data, is_enabled)
		mock_get_individual_channel_settings.assert_called_once_with(channel_id)
		mock_update_individual_channel.assert_called_once_with(channel_id, '{"due": true, "deferred": false, "assigned": ["FF", "NN"], "reported": ["+"]}', '1,2,3')
		mock_show_settings_keyboard.assert_called_once_with(mock_bot, mock_call, True, True)

	def test_save_toggle_button_add_exists_array_element(self, mock_show_settings_keyboard, mock_update_individual_channel,
									mock_get_individual_channel_settings, *args):
		channel_id = -10012345678
		message_id = 123
		mock_bot = Mock(spec=TeleBot)
		mock_call = Mock(spec=CallbackQuery)
		mock_call.id = 12234
		mock_keyboard = Mock(spec=InlineKeyboardMarkup)
		mock_keyboard.keyboard = [[]]
		mock_call.message = test_helper.create_mock_message("", [], channel_id, message_id)
		mock_call.message.reply_markup = mock_keyboard
		setting_type = channel_manager.SETTING_TYPES.ASSIGNED
		cb_data = "NN"
		is_enabled = True

		channel_manager.save_toggle_button(mock_bot, mock_call, setting_type, cb_data, is_enabled)
		mock_get_individual_channel_settings.assert_called_once_with(channel_id)
		mock_update_individual_channel.assert_called_once_with(channel_id, '{"due": true, "deferred": false, "assigned": ["FF", "NN"], "reported": ["+"]}', '1,2')
		mock_show_settings_keyboard.assert_called_once_with(mock_bot, mock_call, True, True)

	def test_save_toggle_button_remove_array_element(self, mock_show_settings_keyboard, mock_update_individual_channel,
									mock_get_individual_channel_settings, *args):
		channel_id = -10012345678
		message_id = 123
		mock_bot = Mock(spec=TeleBot)
		mock_call = Mock(spec=CallbackQuery)
		mock_call.id = 12234
		mock_keyboard = Mock(spec=InlineKeyboardMarkup)
		mock_keyboard.keyboard = [[]]
		mock_call.message = test_helper.create_mock_message("", [], channel_id, message_id)
		mock_call.message.reply_markup = mock_keyboard
		setting_type = channel_manager.SETTING_TYPES.REPORTED
		cb_data = "+"
		is_enabled = False

		channel_manager.save_toggle_button(mock_bot, mock_call, setting_type, cb_data, is_enabled)
		mock_get_individual_channel_settings.assert_called_once_with(channel_id)
		mock_update_individual_channel.assert_called_once_with(channel_id, '{"due": true, "deferred": false, "assigned": ["FF", "NN"], "reported": []}',  '1,2')
		mock_show_settings_keyboard.assert_called_once_with(mock_bot, mock_call, True, True)


class TestChannelSettingsKeyboard(TestCase):
	@patch("db_utils.get_individual_channel_settings",
		   return_value=['{"due": true, "deferred": false, "assigned": ["FF", "NN"], "reported": ["+"], "cc": ["NN"]}',
						 '1,2'])
	@patch("channel_manager.is_settings_message", return_value=True)
	@patch("channel_manager.update_settings_keyboard")
	@patch("channel_manager.get_settings_message_id")
	@patch("channel_manager.update_settings_message")
	@patch("db_utils.get_newest_copied_message")
	@patch("forwarding_utils.get_keyboard_from_channel_message")
	@patch("utils.merge_keyboard_markup")
	def test__call_settings_button(self, mock_merge_keyboard_markup, mock_get_keyboard_from_channel_message,
								 mock_get_newest_copied_message, mock_update_settings_message,
								 mock_get_settings_message_id, mock_update_settings_keyboard,
								 mock_is_settings_message, *args):

		mock_bot = Mock(spec=TeleBot)
		channel_id = -10012345678
		message_id = 123
		mock_call = Mock(spec=CallbackQuery)
		mock_call.message = test_helper.create_mock_message("", [], channel_id, message_id)
		mock_get_settings_message_id.return_value = 123
		mock_newest_message_id = 321
		mock_get_newest_copied_message.return_value = mock_newest_message_id
		mock_keyboard = Mock(spec=InlineKeyboardMarkup)
		mock_keyboard1 = Mock(spec=InlineKeyboardMarkup)

		channel_manager._call_settings_button(mock_bot, mock_call, mock_keyboard, mock_keyboard1)
		mock_is_settings_message.assert_called_once_with(mock_call.message)
		mock_update_settings_keyboard.assert_not_called()
		mock_get_settings_message_id.assert_called_once_with(mock_call.message.chat.id)
		mock_update_settings_message.assert_called_once_with(mock_bot, channel_id, message_id, mock_keyboard)
		mock_get_newest_copied_message.assert_called_once_with(mock_call.message.chat.id)
		mock_get_keyboard_from_channel_message.assert_not_called()
		mock_merge_keyboard_markup.assert_not_called()
		mock_bot.edit_message_reply_markup.assert_not_called()

	@patch("db_utils.get_individual_channel_settings",
		   return_value=['{"due": true, "deferred": false, "assigned": ["FF", "NN"], "reported": ["+"], "cc": ["NN"]}',
						 '1,2'])
	@patch("channel_manager.is_settings_message", return_value=True)
	@patch("channel_manager.get_settings_message_id")
	@patch("channel_manager.update_settings_message")
	@patch("db_utils.get_newest_copied_message")
	@patch("copy.deepcopy")
	@patch("db_utils.get_main_message_from_copied")
	@patch("forwarding_utils.get_keyboard_from_channel_message")
	@patch("utils.merge_keyboard_markup")
	def test__call_settings_button_force_update_ticket_keyboard(self, mock_merge_keyboard_markup,
								mock_get_keyboard_from_channel_message, mock_get_main_message_from_copied, mock_deepcopy,
								mock_get_newest_copied_message, mock_update_settings_message,
								mock_get_settings_message_id, mock_is_settings_message, *args):

		mock_bot = Mock(spec=TeleBot)
		channel_id = -10012345678
		message_id = 123
		main_channel_id = -10087654321
		main_message_id = 121
		mock_call = Mock(spec=CallbackQuery)
		mock_call.message = test_helper.create_mock_message("", [], channel_id, message_id)
		mock_get_settings_message_id.return_value = message_id
		mock_newest_message_id = 321
		mock_get_newest_copied_message.return_value = mock_newest_message_id
		mock_keyboard = Mock(spec=InlineKeyboardMarkup)
		mock_keyboard1 = Mock(spec=InlineKeyboardMarkup)
		mock_get_main_message_from_copied.return_value = [main_message_id, main_channel_id]

		channel_manager._call_settings_button(mock_bot, mock_call,
													  mock_keyboard, mock_keyboard1, True, True)
		mock_is_settings_message.assert_called_once_with(mock_call.message)
		mock_get_settings_message_id.assert_called_once_with(mock_call.message.chat.id)
		mock_update_settings_message.assert_called_once_with(mock_bot, mock_call.message.chat.id, mock_call.message.id,mock_keyboard)
		mock_get_newest_copied_message.assert_called_once_with(mock_call.message.chat.id)
		mock_deepcopy.assert_not_called()
		mock_get_keyboard_from_channel_message.assert_called_once_with(mock_bot, mock_call, mock_newest_message_id)
		mock_merge_keyboard_markup.assert_called_once_with(mock_get_keyboard_from_channel_message.return_value,
														   mock_keyboard1)
		mock_bot.edit_message_reply_markup.assert_called_once_with(chat_id=mock_call.message.chat.id,
																   message_id=mock_newest_message_id,
																   reply_markup=mock_merge_keyboard_markup.return_value)

	@patch("db_utils.get_individual_channel_settings",
		   return_value=['{"due": true, "deferred": false, "assigned": ["FF", "NN"], "reported": ["+"], "cc": ["NN"]}',
						 '1,2'])
	@patch("channel_manager.is_settings_message", return_value=True)
	@patch("channel_manager.get_settings_message_id")
	@patch("channel_manager.update_settings_message")
	@patch("db_utils.get_newest_copied_message")
	@patch("forwarding_utils.get_keyboard_from_channel_message")
	@patch("utils.merge_keyboard_markup")
	def test__call_settings_button_another_settings_message(self, mock_merge_keyboard_markup,
								mock_get_keyboard_from_channel_message, mock_get_newest_copied_message,
								mock_update_settings_message, mock_get_settings_message_id,
								mock_is_settings_message, *args):
		mock_bot = Mock(spec=TeleBot)
		mock_call = Mock(spec=CallbackQuery)
		mock_call.message = test_helper.create_mock_message("", [], -10012345678, -10012345678)
		mock_get_settings_message_id.return_value = 123
		mock_newest_message_id = 321
		mock_get_newest_copied_message.return_value = mock_newest_message_id
		mock_keyboard = Mock(spec=InlineKeyboardMarkup)
		mock_keyboard1 = Mock(spec=InlineKeyboardMarkup)

		channel_manager._call_settings_button(mock_bot, mock_call, mock_keyboard, mock_keyboard1)
		mock_is_settings_message.assert_called_once_with(mock_call.message)
		mock_get_settings_message_id.assert_called_once_with(mock_call.message.chat.id)
		mock_update_settings_message.assert_called_once_with(mock_bot, mock_call.message.chat.id,
															 mock_call.message.id, mock_keyboard)
		mock_get_newest_copied_message.assert_called_once_with(mock_call.message.chat.id)
		mock_get_keyboard_from_channel_message.assert_not_called()
		mock_merge_keyboard_markup.assert_not_called()
		mock_bot.edit_message_reply_markup.assert_not_called()

	@patch("db_utils.get_individual_channel_settings",
		   return_value=['{"due": true, "deferred": false, "assigned": ["FF", "NN"], "reported": ["+"], "cc": ["NN"]}',
						 '1,2'])
	@patch("channel_manager.is_settings_message", return_value=True)
	@patch("channel_manager.get_settings_message_id")
	@patch("channel_manager.update_settings_message")
	@patch("db_utils.get_newest_copied_message")
	@patch("forwarding_utils.get_keyboard_from_channel_message")
	@patch("utils.merge_keyboard_markup")
	def test__call_settings_button_another_settings_message(self, mock_merge_keyboard_markup, mock_get_keyboard_from_channel_message,
								 mock_get_newest_copied_message, mock_update_settings_message,
								 mock_get_settings_message_id, mock_is_settings_message, *args):
		mock_bot = Mock(spec=TeleBot)
		mock_call = Mock(spec=CallbackQuery)
		mock_call.message = test_helper.create_mock_message("", [], -10012345678, 125)
		mock_get_settings_message_id.return_value = 123
		mock_newest_message_id = 321
		mock_get_newest_copied_message.return_value = mock_newest_message_id
		mock_keyboard = Mock(spec=InlineKeyboardMarkup)
		mock_keyboard1 = Mock(spec=InlineKeyboardMarkup)

		channel_manager._call_settings_button(mock_bot, mock_call, mock_keyboard, mock_keyboard1, True)
		mock_is_settings_message.assert_called_once_with(mock_call.message)
		mock_get_settings_message_id.assert_called_once_with(mock_call.message.chat.id)
		mock_update_settings_message.assert_has_calls([call(mock_bot, mock_call.message.chat.id, mock_call.message.id, mock_keyboard),
														call(mock_bot, mock_call.message.chat.id,
															 mock_get_settings_message_id.return_value, mock_keyboard)])
		mock_get_newest_copied_message.assert_called_once_with(mock_call.message.chat.id)
		mock_get_keyboard_from_channel_message.assert_not_called()
		mock_merge_keyboard_markup.assert_not_called()
		mock_bot.edit_message_reply_markup.assert_not_called()

	@patch("db_utils.get_individual_channel_settings",
		   return_value=['{"due": true, "deferred": false, "assigned": ["FF", "NN"], "reported": ["+"], "cc": ["NN"]}',
						 '1,2'])
	@patch("channel_manager.is_settings_message", return_value=False)
	@patch("channel_manager.get_settings_message_id")
	@patch("channel_manager.update_settings_message")
	@patch("db_utils.get_newest_copied_message")
	@patch("copy.deepcopy")
	@patch("db_utils.get_main_message_from_copied")
	@patch("forwarding_utils.get_keyboard_from_channel_message")
	@patch("utils.merge_keyboard_markup")
	def test__call_settings_button_last_ticket(self, mock_merge_keyboard_markup, mock_get_keyboard_from_channel_message,
								 mock_get_main_message_from_copied, mock_deepcopy,
								 mock_get_newest_copied_message, mock_update_settings_message,
								 mock_get_settings_message_id, mock_is_settings_message, *args):
		mock_bot = Mock(spec=TeleBot)
		channel_id = -10012345678
		message_id = 321
		main_channel_id = -10087654321
		main_message_id = 121
		mock_call = Mock(spec=CallbackQuery)
		mock_call.message = test_helper.create_mock_message("", [], channel_id, message_id)
		mock_get_settings_message_id.return_value = 123
		mock_newest_message_id = message_id
		mock_get_newest_copied_message.return_value = mock_newest_message_id
		mock_keyboard = Mock(spec=InlineKeyboardMarkup)
		mock_keyboard1 = Mock(spec=InlineKeyboardMarkup)
		mock_get_main_message_from_copied.return_value = [main_channel_id, main_message_id]

		channel_manager._call_settings_button(mock_bot, mock_call, mock_keyboard, mock_keyboard1)
		mock_is_settings_message.assert_called_once_with(mock_call.message)
		mock_get_settings_message_id.assert_called_once_with(mock_call.message.chat.id)
		mock_update_settings_message.assert_not_called()
		mock_get_newest_copied_message.assert_called_once_with(mock_call.message.chat.id)
		mock_deepcopy.assert_not_called()
		mock_get_keyboard_from_channel_message.assert_called_once_with(mock_bot, mock_call, mock_newest_message_id)
		mock_merge_keyboard_markup.assert_called_once_with(mock_get_keyboard_from_channel_message.return_value,
														   mock_keyboard1)
		mock_bot.edit_message_reply_markup.assert_called_once_with(chat_id=mock_call.message.chat.id,
																   message_id=mock_newest_message_id,
																   reply_markup=mock_merge_keyboard_markup.return_value)

	@patch("channel_manager.get_settings_menu")
	def test_get_ticket_settings_buttons(self, mock_get_settings_menu, *args):
		channel_id = -10012345678
		main_channel_id = -10087654231
		user_id = 85241367
		keyboard = Mock(spec=InlineKeyboardMarkup)
		mock_get_settings_menu.return_value = keyboard

		result = channel_manager.get_ticket_settings_buttons(channel_id)
		mock_get_settings_menu.assert_called_once_with(channel_id, channel_manager.TICKET_MENU_TYPE)
		self.assertEqual(result, keyboard)

	@patch("channel_manager.CHANNEL_TICKET_SETTINGS_BUTTONS", {})
	@patch("channel_manager.get_button_settings_keyboard")
	@patch("channel_manager.generate_settings_keyboard")
	@patch("channel_manager.generate_user_keyboard")
	@patch("channel_manager.generate_remind_keyboard")
	def test_get_settings_menu(self, mock_generate_remind_keyboard, mock_generate_user_keyboard,
										 mock_generate_settings_keyboard, mock_get_button_settings_keyboard, *args):
		channel_id = -10012345678

		keyboard = channel_manager.get_settings_menu(channel_id, menu_type=channel_manager.INFO_MENU_TYPE)
		mock_get_button_settings_keyboard.assert_called_once_with()
		mock_generate_settings_keyboard.assert_not_called()
		mock_generate_user_keyboard.assert_not_called()
		mock_generate_remind_keyboard.assert_not_called()
		self.assertEqual(keyboard, mock_get_button_settings_keyboard.return_value)

	@patch("channel_manager.CHANNEL_TICKET_SETTINGS_BUTTONS", {})
	@patch("channel_manager.get_button_settings_keyboard")
	@patch("channel_manager.generate_settings_keyboard")
	@patch("channel_manager.generate_user_keyboard")
	@patch("channel_manager.generate_remind_keyboard")
	def test_get_settings_menu_ticket(self, mock_generate_remind_keyboard, mock_generate_user_keyboard,
										 mock_generate_settings_keyboard, mock_get_button_settings_keyboard, *args):
		channel_id = -10012345678

		keyboard = channel_manager.get_settings_menu(channel_id, menu_type=channel_manager.TICKET_MENU_TYPE)
		mock_get_button_settings_keyboard.assert_called_once_with("Settings ⚙️")
		mock_generate_settings_keyboard.assert_not_called()
		mock_generate_user_keyboard.assert_not_called()
		mock_generate_remind_keyboard.assert_not_called()
		self.assertEqual(keyboard, mock_get_button_settings_keyboard.return_value)

	@patch("channel_manager.CHANNEL_TICKET_SETTINGS_BUTTONS", {-10012345678: {"info": {"state": channel_manager.CB_TYPES.OPEN_CHANNEL_SETTINGS, "user": 85241367}}})
	@patch("channel_manager.get_button_settings_keyboard")
	@patch("channel_manager.generate_settings_keyboard")
	@patch("channel_manager.generate_user_keyboard")
	@patch("channel_manager.generate_remind_keyboard")
	def test_get_settings_menu_settings_menu(self, mock_generate_remind_keyboard, mock_generate_user_keyboard,
										 mock_generate_settings_keyboard, mock_get_button_settings_keyboard, *args):
		channel_id = -10012345678

		keyboard = channel_manager.get_settings_menu(channel_id, menu_type=channel_manager.INFO_MENU_TYPE)
		mock_get_button_settings_keyboard.assert_called_once_with()
		mock_generate_settings_keyboard.assert_called_once_with(channel_id, False)
		mock_generate_user_keyboard.assert_not_called()
		mock_generate_remind_keyboard.assert_not_called()
		self.assertEqual(keyboard, mock_generate_settings_keyboard.return_value)

	@patch("channel_manager.CHANNEL_TICKET_SETTINGS_BUTTONS", {-10012345678: {"ticket": {"state": channel_manager.CB_TYPES.OPEN_CHANNEL_SETTINGS, "user": 85241367}}})
	@patch("channel_manager.get_button_settings_keyboard")
	@patch("channel_manager.generate_settings_keyboard")
	@patch("channel_manager.generate_user_keyboard")
	@patch("channel_manager.generate_remind_keyboard")
	def test_get_settings_menu_settings_menu_ticket(self, mock_generate_remind_keyboard, mock_generate_user_keyboard,
										 mock_generate_settings_keyboard, mock_get_button_settings_keyboard, *args):
		channel_id = -10012345678

		keyboard = channel_manager.get_settings_menu(channel_id, menu_type=channel_manager.TICKET_MENU_TYPE)
		mock_get_button_settings_keyboard.assert_called_once_with("Settings ⚙️")
		mock_generate_settings_keyboard.assert_called_once_with(channel_id, True)
		mock_generate_user_keyboard.assert_not_called()
		mock_generate_remind_keyboard.assert_not_called()
		self.assertEqual(keyboard, mock_generate_settings_keyboard.return_value)

	@patch("channel_manager.CHANNEL_TICKET_SETTINGS_BUTTONS", {-10012345678: {"info": {"state": channel_manager.CB_TYPES.ASSIGNED_SELECTED, "user": 85241367}}})
	@patch("channel_manager.get_button_settings_keyboard")
	@patch("channel_manager.generate_settings_keyboard")
	@patch("channel_manager.generate_user_keyboard")
	@patch("channel_manager.generate_remind_keyboard")
	def test_get_settings_menu_user_assigned_menu(self, mock_generate_remind_keyboard, mock_generate_user_keyboard,
										 mock_generate_settings_keyboard, mock_get_button_settings_keyboard, *args):
		channel_id = -10012345678

		keyboard = channel_manager.get_settings_menu(channel_id, menu_type=channel_manager.INFO_MENU_TYPE)
		mock_get_button_settings_keyboard.assert_called_once_with()
		mock_generate_settings_keyboard.assert_not_called()
		mock_generate_user_keyboard.assert_called_once_with(channel_id, channel_manager.SETTING_TYPES.ASSIGNED)
		mock_generate_remind_keyboard.assert_not_called()
		self.assertEqual(keyboard, mock_generate_user_keyboard.return_value)

	@patch("channel_manager.CHANNEL_TICKET_SETTINGS_BUTTONS", {-10012345678: {"info": {"state": channel_manager.CB_TYPES.FOLLOWED_SELECTED, "user": 85241367}}})
	@patch("channel_manager.get_button_settings_keyboard")
	@patch("channel_manager.generate_settings_keyboard")
	@patch("channel_manager.generate_user_keyboard")
	@patch("channel_manager.generate_remind_keyboard")
	def test_get_settings_menu_user_followed_menu(self, mock_generate_remind_keyboard, mock_generate_user_keyboard,
										 mock_generate_settings_keyboard, mock_get_button_settings_keyboard, *args):
		channel_id = -10012345678

		keyboard = channel_manager.get_settings_menu(channel_id, menu_type=channel_manager.INFO_MENU_TYPE)
		mock_get_button_settings_keyboard.assert_called_once_with()
		mock_generate_settings_keyboard.assert_not_called()
		mock_generate_user_keyboard.assert_called_once_with(channel_id, channel_manager.SETTING_TYPES.FOLLOWED)
		mock_generate_remind_keyboard.assert_not_called()
		self.assertEqual(keyboard, mock_generate_user_keyboard.return_value)

	@patch("channel_manager.CHANNEL_TICKET_SETTINGS_BUTTONS", {-10012345678: {"info": {"state": channel_manager.CB_TYPES.REPORTED_SELECTED, "user": 85241367}}})
	@patch("channel_manager.get_button_settings_keyboard")
	@patch("channel_manager.generate_settings_keyboard")
	@patch("channel_manager.generate_user_keyboard")
	@patch("channel_manager.generate_remind_keyboard")
	def test_get_settings_menu_user_reported_menu(self, mock_generate_remind_keyboard, mock_generate_user_keyboard,
										 mock_generate_settings_keyboard, mock_get_button_settings_keyboard, *args):
		channel_id = -10012345678

		keyboard = channel_manager.get_settings_menu(channel_id, menu_type=channel_manager.INFO_MENU_TYPE)
		mock_get_button_settings_keyboard.assert_called_once_with()
		mock_generate_settings_keyboard.assert_not_called()
		mock_generate_user_keyboard.assert_called_once_with(channel_id, channel_manager.SETTING_TYPES.REPORTED)
		mock_generate_remind_keyboard.assert_not_called()
		self.assertEqual(keyboard, mock_generate_user_keyboard.return_value)

	@patch("channel_manager.CHANNEL_TICKET_SETTINGS_BUTTONS", {-10012345678: {"info": {"state": channel_manager.CB_TYPES.REMIND_SELECTED, "user": 85241367}}})
	@patch("channel_manager.get_button_settings_keyboard")
	@patch("channel_manager.generate_settings_keyboard")
	@patch("channel_manager.generate_user_keyboard")
	@patch("channel_manager.generate_remind_keyboard")
	def test_get_settings_menu_remind_menu(self, mock_generate_remind_keyboard, mock_generate_user_keyboard,
										 mock_generate_settings_keyboard, mock_get_button_settings_keyboard, *args):
		channel_id = -10012345678

		keyboard = channel_manager.get_settings_menu(channel_id, menu_type=channel_manager.INFO_MENU_TYPE)
		mock_get_button_settings_keyboard.assert_called_once_with()
		mock_generate_settings_keyboard.assert_not_called()
		mock_generate_user_keyboard.assert_not_called()
		mock_generate_remind_keyboard.assert_called_once_with(channel_id)
		self.assertEqual(keyboard, mock_generate_remind_keyboard.return_value)


@patch("db_utils.get_individual_channel_settings",
	   return_value=['{"due": true, "deferred": false, "assigned": ["FF", "NN"], "reported": ["+"], "cc": ["NN"]}',
					 '1,2'])
@patch("utils.create_callback_str")
class GenerateUserKeyboardTest(TestCase):
	def test_default(self, mock_create_callback_str, *args):
		main_channel_id = -10012345678
		channel_id = -10087654321
		setting_type = "assigned"
		config_utils.USER_TAGS = {"AA": 1, "BB": 2, "FF": 4, "NN": 5, "DD": 3}

		manager = Mock()
		manager.attach_mock(mock_create_callback_str, "a")
		expected_calls = [
			call.a(channel_manager.CALLBACK_PREFIX, channel_manager.CB_TYPES.NOP),
			call.a(channel_manager.CALLBACK_PREFIX, channel_manager.CB_TYPES.TOGGLE_USER, setting_type, "AA"),
			call.a(channel_manager.CALLBACK_PREFIX, channel_manager.CB_TYPES.TOGGLE_USER, setting_type, "BB"),
			call.a(channel_manager.CALLBACK_PREFIX, channel_manager.CB_TYPES.TOGGLE_USER, setting_type, "FF"),
			call.a(channel_manager.CALLBACK_PREFIX, channel_manager.CB_TYPES.TOGGLE_USER, setting_type, "NN"),
			call.a(channel_manager.CALLBACK_PREFIX, channel_manager.CB_TYPES.TOGGLE_USER, setting_type, "DD"),
			call.a(channel_manager.CALLBACK_PREFIX, channel_manager.CB_TYPES.TOGGLE_USER, setting_type, channel_manager.NEW_USER_TYPE),
			call.a(channel_manager.CALLBACK_PREFIX, channel_manager.CB_TYPES.BACK_TO_MAIN_MENU)
		]

		result = channel_manager.generate_user_keyboard(channel_id, setting_type)
		self.assertEqual(manager.mock_calls, expected_calls)

		self.assertEqual(result.keyboard[0][0].text, channel_manager.MENU_TITLES[setting_type])
		self.assertEqual(result.keyboard[1][0].text, "#AA")
		self.assertEqual(result.keyboard[2][0].text, "#BB")
		self.assertEqual(result.keyboard[3][0].text, "#FF" + config_utils.BUTTON_TEXTS["CHECK"])
		self.assertEqual(result.keyboard[4][0].text, "#NN" + config_utils.BUTTON_TEXTS["CHECK"])
		self.assertEqual(result.keyboard[5][0].text, "#DD")
		self.assertEqual(result.keyboard[6][0].text, "New users")
		self.assertEqual(result.keyboard[7][0].text, "← Back")


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

	@patch("channel_manager.get_settings_menu")
	@patch("channel_manager._call_settings_button")
	def test_show_settings_keyboard(self, mock__call_settings_button, mock_get_settings_menu, *args):
		channel_id = -10012345678
		message_id = 123
		user_id = 8536472
		mock_bot = Mock(spec=TeleBot)
		mock_call = Mock(spec=CallbackQuery)
		mock_call.message = test_helper.create_mock_message("", [], channel_id, 123)
		mock_call.from_user = Mock(spec=User)
		mock_call.from_user.id = user_id
		mock_keyboard = Mock(spec=InlineKeyboardMarkup)
		mock_get_settings_menu.return_value = mock_keyboard

		channel_manager.show_settings_keyboard(mock_bot, mock_call)
		mock_get_settings_menu.assert_has_calls([
			call(channel_id, channel_manager.TICKET_MENU_TYPE),
			call(channel_id, channel_manager.INFO_MENU_TYPE)
		])
		mock__call_settings_button.assert_called_once_with(mock_bot, mock_call,
																   mock_keyboard, mock_keyboard, False, False)

	@patch("channel_manager.get_settings_menu")
	@patch("channel_manager._call_settings_button")
	def test_show_settings_keyboard_force(self, mock__call_settings_button, mock_get_settings_menu, *args):
		channel_id = -10012345678
		user_id = 8536472
		mock_bot = Mock(spec=TeleBot)
		mock_call = Mock(spec=CallbackQuery)
		mock_call.message = test_helper.create_mock_message("", [], channel_id, 123)
		mock_call.from_user = Mock(spec=User)
		mock_call.from_user.id = user_id
		mock_keyboard = Mock(spec=InlineKeyboardMarkup)
		mock_get_settings_menu.return_value = mock_keyboard

		channel_manager.show_settings_keyboard(mock_bot, mock_call, True, True)
		mock_get_settings_menu.assert_has_calls([
			call(channel_id, channel_manager.TICKET_MENU_TYPE),
			call(channel_id, channel_manager.INFO_MENU_TYPE)
		])
		mock__call_settings_button.assert_called_once_with(mock_bot, mock_call,
																   mock_keyboard, mock_keyboard, True, True)

	@patch("channel_manager.get_button_settings_keyboard")
	@patch("channel_manager.generate_current_settings_text")
	def test_update_settings_message(self, mock_generate_current_settings_text, mock_get_button_settings_keyboard, *args):
		channel_id = -10012345678
		message_id = 123
		mock_bot = Mock(spec=TeleBot)

		channel_manager.update_settings_message(mock_bot, channel_id, message_id)
		mock_get_button_settings_keyboard.assert_called_once_with()
		mock_generate_current_settings_text.assert_called_once_with(channel_id)
		mock_bot.edit_message_text.assert_called_once_with(text=mock_generate_current_settings_text.return_value,
									reply_markup=mock_get_button_settings_keyboard.return_value,
									chat_id=channel_id, message_id=message_id)

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


	@patch("utils.create_callback_str")
	def test_get_button_settings_keyboard(self, mock_create_callback_str, *args):
		channel_manager.get_button_settings_keyboard()
		mock_create_callback_str.assert_called_once_with(
			channel_manager.CALLBACK_PREFIX,
			channel_manager.CB_TYPES.OPEN_CHANNEL_SETTINGS
		)


@patch("db_utils.is_individual_channel_exists", return_value=True)
@patch("db_utils.get_individual_channel_settings",
		return_value=['{"due": true, "deferred": false, "assigned": ["FF", "NN"], "reported": ["+"], "cc": ["NN"]}',
					 '1,2'])
@patch("channel_manager._set_channel_ticket_settings_state")
@patch("forwarding_utils.clear_channel_ticket_keyboard_by_user")
class TestHandleCallback(TestCase):
	@patch("channel_manager.show_settings_keyboard")
	@patch("interval_updating_utils.start_interval_updating")
	def test_assigned_selected(self, mock_start_interval_updating, mock_show_settings_keyboard,
							   mock_clear_channel_ticket_keyboard_by_user, mock__set_channel_ticket_settings_state, *args):
		channel_id = -10012345678
		message_id = 123
		user_id = 8536472
		mock_bot = Mock(spec=TeleBot)
		mock_call = Mock(spec=CallbackQuery)
		mock_call.data = f"{channel_manager.CALLBACK_PREFIX},{channel_manager.CB_TYPES.ASSIGNED_SELECTED},"
		mock_call.message = test_helper.create_mock_message("", [], channel_id, message_id)
		mock_call.from_user = Mock(spec=User)
		mock_call.from_user.id = user_id

		channel_manager.handle_callback(mock_bot, mock_call)
		mock__set_channel_ticket_settings_state.assert_called_once_with(mock_call, channel_manager.CB_TYPES.ASSIGNED_SELECTED)
		mock_show_settings_keyboard.assert_called_once_with(mock_bot, mock_call)
		mock_start_interval_updating.assert_not_called()
		mock_clear_channel_ticket_keyboard_by_user.assert_called_once_with(channel_id, message_id, user_id)

	@patch("channel_manager.show_settings_keyboard")
	@patch("interval_updating_utils.start_interval_updating")
	def test_reported_selected(self, mock_start_interval_updating, mock_show_settings_keyboard,
							   mock_clear_channel_ticket_keyboard_by_user, mock__set_channel_ticket_settings_state, *args):
		channel_id = -10012345678
		message_id = 123
		user_id = 8536472
		mock_bot = Mock(spec=TeleBot)
		mock_call = Mock(spec=CallbackQuery)
		mock_call.data = f"{channel_manager.CALLBACK_PREFIX},{channel_manager.CB_TYPES.REPORTED_SELECTED},"
		mock_call.message = test_helper.create_mock_message("", [], channel_id, message_id)
		mock_call.from_user = Mock(spec=User)
		mock_call.from_user.id = user_id

		channel_manager.handle_callback(mock_bot, mock_call)
		mock__set_channel_ticket_settings_state.assert_called_once_with(mock_call, channel_manager.CB_TYPES.REPORTED_SELECTED)
		mock_show_settings_keyboard.assert_called_once_with(mock_bot, mock_call)
		mock_start_interval_updating.assert_not_called()
		mock_clear_channel_ticket_keyboard_by_user.assert_called_once_with(channel_id, message_id, user_id)

	@patch("channel_manager.show_settings_keyboard")
	@patch("interval_updating_utils.start_interval_updating")
	def test_followed_selected(self, mock_start_interval_updating, mock_show_settings_keyboard,
							   mock_clear_channel_ticket_keyboard_by_user, mock__set_channel_ticket_settings_state, *args):
		channel_id = -10012345678
		message_id = 123
		user_id = 8536472
		mock_bot = Mock(spec=TeleBot)
		mock_call = Mock(spec=CallbackQuery)
		mock_call.data = f"{channel_manager.CALLBACK_PREFIX},{channel_manager.CB_TYPES.FOLLOWED_SELECTED},"
		mock_call.message = test_helper.create_mock_message("", [], channel_id, message_id)
		mock_call.from_user = Mock(spec=User)
		mock_call.from_user.id = user_id

		channel_manager.handle_callback(mock_bot, mock_call)
		mock__set_channel_ticket_settings_state.assert_called_once_with(mock_call, channel_manager.CB_TYPES.FOLLOWED_SELECTED)
		mock_show_settings_keyboard.assert_called_once_with(mock_bot, mock_call)
		mock_start_interval_updating.assert_not_called()
		mock_clear_channel_ticket_keyboard_by_user.assert_called_once_with(channel_id, message_id, user_id)

	@patch("channel_manager.show_settings_keyboard")
	@patch("interval_updating_utils.start_interval_updating")
	def test_remind_selected(self, mock_start_interval_updating, mock_show_settings_keyboard,
							   mock_clear_channel_ticket_keyboard_by_user, mock__set_channel_ticket_settings_state, *args):
		channel_id = -10012345678
		message_id = 123
		user_id = 8536472
		mock_bot = Mock(spec=TeleBot)
		mock_call = Mock(spec=CallbackQuery)
		mock_call.data = f"{channel_manager.CALLBACK_PREFIX},{channel_manager.CB_TYPES.REMIND_SELECTED},"
		mock_call.message = test_helper.create_mock_message("", [], channel_id, message_id)
		mock_call.from_user = Mock(spec=User)
		mock_call.from_user.id = user_id

		channel_manager.handle_callback(mock_bot, mock_call)
		mock__set_channel_ticket_settings_state.assert_called_once_with(mock_call, channel_manager.CB_TYPES.REMIND_SELECTED)
		mock_show_settings_keyboard.assert_called_once_with(mock_bot, mock_call)
		mock_start_interval_updating.assert_not_called()
		mock_clear_channel_ticket_keyboard_by_user.assert_called_once_with(channel_id, message_id, user_id)

	@patch("channel_manager.show_settings_keyboard")
	@patch("interval_updating_utils.start_interval_updating")
	def test_save_selected_users(self, mock_start_interval_updating, mock_show_settings_keyboard,
								 mock_clear_channel_ticket_keyboard_by_user, mock__set_channel_ticket_settings_state, *args):
		channel_id = -10012345678
		message_id = 123
		user_id = 8536472
		settings_type = channel_manager.SETTING_TYPES.REPORTED
		mock_bot = Mock(spec=TeleBot)
		mock_call = Mock(spec=CallbackQuery)
		mock_call.data = f"{channel_manager.CALLBACK_PREFIX},{channel_manager.CB_TYPES.BACK_TO_MAIN_MENU},{settings_type}"
		mock_call.message = test_helper.create_mock_message("", [], channel_id, message_id)
		mock_call.from_user = Mock(spec=User)
		mock_call.from_user.id = user_id

		channel_manager.handle_callback(mock_bot, mock_call)
		mock__set_channel_ticket_settings_state.assert_called_once_with(mock_call, channel_manager.CB_TYPES.OPEN_CHANNEL_SETTINGS)
		mock_show_settings_keyboard.assert_called_once_with(mock_bot, mock_call)
		mock_start_interval_updating.assert_not_called()
		mock_clear_channel_ticket_keyboard_by_user.assert_called_once_with(channel_id, message_id, user_id)

	@patch("channel_manager.CHANNEL_TICKET_SETTINGS_BUTTONS", {-10012345678: {channel_manager.TICKET_MENU_TYPE: {"state": channel_manager.CB_TYPES.OPEN_CHANNEL_SETTINGS, "user": 8536472},
																			  channel_manager.INFO_MENU_TYPE: {"state": channel_manager.CB_TYPES.OPEN_CHANNEL_SETTINGS, "user": 8536472}}})
	@patch("db_utils.is_copied_message_exists")
	@patch("channel_manager._call_settings_button")
	@patch("channel_manager.get_button_settings_keyboard")
	@patch("interval_updating_utils.start_interval_updating")
	def test_save_and_hide_settings_menu(self, mock_start_interval_updating, mock_get_button_settings_keyboard,
										 mock__call_settings_button, mock_is_copied_message_exists,
										 mock_clear_channel_ticket_keyboard_by_user, *args):
		channel_id = -10012345678
		message_id = 123
		user_id = 8536472
		mock_bot = Mock(spec=TeleBot)
		mock_call = Mock(spec=CallbackQuery)
		mock_call.data = f"{channel_manager.CALLBACK_PREFIX},{channel_manager.CB_TYPES.SAVE_AND_HIDE_SETTINGS_MENU},"
		mock_call.message = test_helper.create_mock_message("", [], channel_id, message_id)
		mock_call.from_user = Mock(spec=User)
		mock_call.from_user.id = user_id
		mock_is_copied_message_exists.return_value = True

		channel_manager.handle_callback(mock_bot, mock_call)
		mock_is_copied_message_exists.assert_called_once_with(message_id, channel_id)
		mock__call_settings_button.assert_called_once_with(mock_bot, mock_call,
																   mock_get_button_settings_keyboard.return_value,
																   mock_get_button_settings_keyboard.return_value, True, True)
		mock_get_button_settings_keyboard.assert_has_calls([call("Settings ⚙️"), call()])
		mock_start_interval_updating.assert_called_once_with(mock_bot)
		mock_clear_channel_ticket_keyboard_by_user.assert_called_once_with(channel_id, message_id, user_id)

	@patch("channel_manager.CHANNEL_TICKET_SETTINGS_BUTTONS", {-10012345678: {channel_manager.TICKET_MENU_TYPE: {"state": channel_manager.CB_TYPES.OPEN_CHANNEL_SETTINGS, "user": 8536472},
																			  channel_manager.INFO_MENU_TYPE: {"state": channel_manager.CB_TYPES.OPEN_CHANNEL_SETTINGS, "user": 3546846}}})
	@patch("db_utils.is_copied_message_exists")
	@patch("channel_manager._call_settings_button")
	@patch("channel_manager.generate_settings_keyboard")
	@patch("channel_manager.get_button_settings_keyboard")
	@patch("interval_updating_utils.start_interval_updating")
	def test_save_and_hide_settings_menu_another_user(self, mock_start_interval_updating, mock_get_button_settings_keyboard,
													  mock_generate_settings_keyboard, mock__call_settings_button,
													  mock_is_copied_message_exists, mock_clear_channel_ticket_keyboard_by_user, *args):
		channel_id = -10012345678
		message_id = 123
		user_id = 8536472
		mock_bot = Mock(spec=TeleBot)
		mock_call = Mock(spec=CallbackQuery)
		mock_call.data = f"{channel_manager.CALLBACK_PREFIX},{channel_manager.CB_TYPES.SAVE_AND_HIDE_SETTINGS_MENU},"
		mock_call.message = test_helper.create_mock_message("", [], channel_id, message_id)
		mock_call.from_user = Mock(spec=User)
		mock_call.from_user.id = user_id
		mock_is_copied_message_exists.return_value = True

		channel_manager.handle_callback(mock_bot, mock_call)
		mock_is_copied_message_exists.assert_called_once_with(message_id, channel_id)
		mock__call_settings_button.assert_called_once_with(mock_bot, mock_call,
																   mock_generate_settings_keyboard.return_value,
																   mock_get_button_settings_keyboard.return_value, False, True)
		mock_get_button_settings_keyboard.assert_has_calls([call("Settings ⚙️"), call()])
		mock_generate_settings_keyboard.assert_called_once_with(channel_id, False)
		mock_start_interval_updating.assert_called_once_with(mock_bot)
		mock_clear_channel_ticket_keyboard_by_user.assert_called_once_with(channel_id, message_id, user_id)

	@patch("channel_manager.CHANNEL_TICKET_SETTINGS_BUTTONS", {-10012345678: {channel_manager.TICKET_MENU_TYPE: {"state": channel_manager.CB_TYPES.OPEN_CHANNEL_SETTINGS, "user": 8536472}}})
	@patch("db_utils.is_copied_message_exists")
	@patch("channel_manager._call_settings_button")
	@patch("channel_manager.get_button_settings_keyboard")
	@patch("interval_updating_utils.start_interval_updating")
	def test_save_and_hide_settings_empty_another(self, mock_start_interval_updating, mock_get_button_settings_keyboard,
												  mock__call_settings_button, mock_is_copied_message_exists,
												  mock_clear_channel_ticket_keyboard_by_user, *args):
		channel_id = -10012345678
		message_id = 123
		user_id = 8536472
		mock_bot = Mock(spec=TeleBot)
		mock_call = Mock(spec=CallbackQuery)
		mock_call.data = f"{channel_manager.CALLBACK_PREFIX},{channel_manager.CB_TYPES.SAVE_AND_HIDE_SETTINGS_MENU},"
		mock_call.message = test_helper.create_mock_message("", [], channel_id, message_id)
		mock_call.from_user = Mock(spec=User)
		mock_call.from_user.id = user_id
		mock_is_copied_message_exists.return_value = True

		channel_manager.handle_callback(mock_bot, mock_call)
		mock_is_copied_message_exists.assert_called_once_with(message_id, channel_id)
		mock__call_settings_button.assert_called_once_with(mock_bot, mock_call,
																   mock_get_button_settings_keyboard.return_value,
																   mock_get_button_settings_keyboard.return_value, False, True)
		mock_get_button_settings_keyboard.assert_has_calls([call("Settings ⚙️"), call()])
		mock_start_interval_updating.assert_called_once_with(mock_bot)
		mock_clear_channel_ticket_keyboard_by_user.assert_called_once_with(channel_id, message_id, user_id)

	@patch("channel_manager.toggle_button")
	def test_toggle_callbacks(self, mock_toggle_button, mock_clear_channel_ticket_keyboard_by_user,
							  mock__set_channel_ticket_settings_state, *args):
		channel_id = -10012345678
		message_id = 123
		user_id = 8536472
		mock_bot = Mock(spec=TeleBot)
		mock_call = Mock(spec=CallbackQuery)
		mock_call.data = f"{channel_manager.CALLBACK_PREFIX},{channel_manager.CB_TYPES.DUE_SELECTED},"
		mock_call.message = test_helper.create_mock_message("", [], channel_id, message_id)
		mock_call.from_user = Mock(spec=User)
		mock_call.from_user.id = user_id

		channel_manager.handle_callback(mock_bot, mock_call)
		mock__set_channel_ticket_settings_state.assert_not_called()
		mock_toggle_button.assert_called_once_with(mock_bot, mock_call, channel_manager.CB_TYPES.DUE_SELECTED, [''])
		mock_clear_channel_ticket_keyboard_by_user.assert_called_once_with(channel_id, message_id, user_id)

	@patch("channel_manager.toggle_button")
	def test_toggle_callbacks_user(self, mock_toggle_button, mock_clear_channel_ticket_keyboard_by_user,
								   mock__set_channel_ticket_settings_state, *args):
		channel_id = -10012345678
		message_id = 123
		user_id = 8536472
		mock_bot = Mock(spec=TeleBot)
		mock_call = Mock(spec=CallbackQuery)
		mock_call.data = f"{channel_manager.CALLBACK_PREFIX},{channel_manager.CB_TYPES.TOGGLE_USER},{channel_manager.SETTING_TYPES.FOLLOWED},NN"
		mock_call.message = test_helper.create_mock_message("", [], channel_id, message_id)
		mock_call.from_user = Mock(spec=User)
		mock_call.from_user.id = user_id

		channel_manager.handle_callback(mock_bot, mock_call)
		mock__set_channel_ticket_settings_state.assert_not_called()
		mock_toggle_button.assert_called_once_with(mock_bot, mock_call, channel_manager.CB_TYPES.TOGGLE_USER,
												   [channel_manager.SETTING_TYPES.FOLLOWED, 'NN'])
		mock_clear_channel_ticket_keyboard_by_user.assert_called_once_with(channel_id, message_id, user_id)

	@patch("channel_manager.toggle_button")
	def test_toggle_callbacks_remind(self, mock_toggle_button, mock_clear_channel_ticket_keyboard_by_user,
									 mock__set_channel_ticket_settings_state, *args):
		channel_id = -10012345678
		message_id = 123
		user_id = 8536472
		mock_bot = Mock(spec=TeleBot)
		mock_call = Mock(spec=CallbackQuery)
		mock_call.data = f"{channel_manager.CALLBACK_PREFIX},{channel_manager.CB_TYPES.TOGGLE_REMIND_SETTING},{channel_manager.REMIND_TYPES.ASSIGNED}"
		mock_call.message = test_helper.create_mock_message("", [], channel_id, message_id)
		mock_call.from_user = Mock(spec=User)
		mock_call.from_user.id = user_id

		channel_manager.handle_callback(mock_bot, mock_call)
		mock__set_channel_ticket_settings_state.assert_not_called()
		mock_toggle_button.assert_called_once_with(mock_bot, mock_call, channel_manager.CB_TYPES.TOGGLE_REMIND_SETTING,
											[channel_manager.REMIND_TYPES.ASSIGNED])
		mock_clear_channel_ticket_keyboard_by_user.assert_called_once_with(channel_id, message_id, user_id)

	@patch("channel_manager.show_settings_keyboard")
	def test_open_channel_settings(self, mock_show_settings_keyboard, mock_clear_channel_ticket_keyboard_by_user,
								   mock__set_channel_ticket_settings_state, *args):
		channel_id = -10012345678
		message_id = 123
		user_id = 8536472
		mock_bot = Mock(spec=TeleBot)
		mock_call = Mock(spec=CallbackQuery)
		mock_call.data = f"{channel_manager.CALLBACK_PREFIX},{channel_manager.CB_TYPES.OPEN_CHANNEL_SETTINGS},"
		mock_call.message = test_helper.create_mock_message("", [], channel_id, message_id)
		mock_call.from_user = Mock(spec=User)
		mock_call.from_user.id = user_id

		channel_manager.handle_callback(mock_bot, mock_call)
		mock__set_channel_ticket_settings_state.assert_called_once_with(mock_call, channel_manager.CB_TYPES.OPEN_CHANNEL_SETTINGS)
		mock_show_settings_keyboard.assert_called_once_with(mock_bot, mock_call)
		mock_clear_channel_ticket_keyboard_by_user.assert_called_once_with(channel_id, message_id, user_id)

	@patch("channel_manager.create_settings_message")
	def test_create_channel_settings(self, mock_create_settings_message, mock_clear_channel_ticket_keyboard_by_user,
									 mock__set_channel_ticket_settings_state, *args):
		channel_id = -10012345678
		message_id = 123
		user_id = 8536472
		mock_bot = Mock(spec=TeleBot)
		mock_call = Mock(spec=CallbackQuery)
		mock_call.data = f"{channel_manager.CALLBACK_PREFIX},{channel_manager.CB_TYPES.CREATE_CHANNEL_SETTINGS},"
		mock_call.message = test_helper.create_mock_message("", [], channel_id, message_id)
		mock_call.from_user = Mock(spec=User)
		mock_call.from_user.id = user_id

		channel_manager.handle_callback(mock_bot, mock_call)
		mock__set_channel_ticket_settings_state.assert_called_once_with(mock_call, channel_manager.CB_TYPES.OPEN_CHANNEL_SETTINGS)
		mock_create_settings_message.assert_called_once_with(mock_bot, channel_id)
		mock_clear_channel_ticket_keyboard_by_user.assert_called_once_with(channel_id, message_id, user_id)

	def test_set_channel_ticket_settings_state(self, *args):
		channel_id = -10012345678
		message_id = 123
		user_id = 8536472
		mock_call = Mock(spec=CallbackQuery)
		mock_call.data = f"{channel_manager.CALLBACK_PREFIX},{channel_manager.CB_TYPES.CREATE_CHANNEL_SETTINGS},"
		mock_call.message = test_helper.create_mock_message("", [], channel_id, message_id)
		mock_call.from_user = Mock(spec=User)
		mock_call.from_user.id = user_id
		state = channel_manager.CB_TYPES.FOLLOWED_SELECTED
		result = channel_manager._set_channel_ticket_settings_state(mock_call, state)


@patch("db_utils.is_main_channel_exists", return_value=False)
@patch("db_utils.is_individual_channel_exists", return_value=False)
@patch("logging.warning")
@patch("db_utils.insert_individual_channel")
@patch("channel_manager.create_settings_message")
class InitializeChannelTest(TestCase):
	def test_default(self, mock_create_settings_message, mock_insert_individual_channel,
					 mock_warning, mock_is_individual_channel_exists, mock_is_main_channel_exists, *args):
		mock_bot = Mock(spec=TeleBot)
		channel_id = -10087654321
		user_id = 852364
		settings_str = "{\"due\": true, \"deferred\": true, \"remind\": [\"assigned\"]}"
		mock_bot.get_chat_administrators.return_value = []

		channel_manager.initialize_channel(mock_bot, channel_id, user_id)
		mock_is_main_channel_exists.assert_called_once_with(channel_id)
		mock_is_individual_channel_exists.assert_called_once_with(channel_id)
		mock_bot.get_chat_administrators.assert_called_once_with(channel_id)
		mock_warning.assert_called_once_with(f"Can't get owner_id from channel, use user #{user_id} in channel #{channel_id}. Error - 'NoneType' object has no attribute 'user'")
		mock_insert_individual_channel.assert_called_once_with(channel_id, settings_str, user_id)
		mock_create_settings_message.assert_called_once_with(mock_bot, channel_id)

	def test_main_channel(self, mock_create_settings_message, mock_insert_individual_channel,
					 mock_warning, mock_is_individual_channel_exists, mock_is_main_channel_exists, *args):
		mock_bot = Mock(spec=TeleBot)
		channel_id = -10087654321
		user_id = 852364
		mock_bot.get_chat_administrators.return_value = []
		mock_is_main_channel_exists.return_value = True

		channel_manager.initialize_channel(mock_bot, channel_id, user_id)
		mock_is_main_channel_exists.assert_called_once_with(channel_id)
		mock_is_individual_channel_exists.assert_not_called()
		mock_bot.get_chat_administrators.assert_not_called()
		mock_warning.assert_not_called()
		mock_insert_individual_channel.assert_not_called()
		mock_create_settings_message.assert_not_called()

	def test_with_exists_settings(self, mock_create_settings_message, mock_insert_individual_channel,
								  mock_warning, mock_is_individual_channel_exists, mock_is_main_channel_exists, *args):
		mock_bot = Mock(spec=TeleBot)
		channel_id = -10087654321
		mock_is_individual_channel_exists.return_value = True

		channel_manager.initialize_channel(mock_bot, channel_id)
		mock_is_main_channel_exists.assert_called_once_with(channel_id)
		mock_is_individual_channel_exists.assert_called_once_with(channel_id)
		mock_bot.get_chat_administrators.assert_not_called()
		mock_warning.assert_not_called()
		mock_insert_individual_channel.assert_not_called()
		mock_create_settings_message.assert_called_once_with(mock_bot, channel_id)


@patch("forwarding_utils.delete_forwarded_message")
@patch("db_utils.delete_individual_channel")
@patch("db_utils.get_individual_channel_settings")
class DeleteIndividualSettingsForWorkspace(TestCase):
	def test_default(self, mock_get_individual_channel_settings, mock_delete_individual_channel,
					 mock_delete_forwarded_message, *args):
		mock_bot = Mock(spec=TeleBot)
		channel_id = -10012345678
		main_channel_id = -10087654321
		settings_id = 2
		mock_get_individual_channel_settings.return_value = ("{\"settings_message_id\": " + f"{settings_id}" + "}", "1,2")

		channel_manager.delete_individual_settings_for_workspace(mock_bot, main_channel_id)
		mock_get_individual_channel_settings.assert_called_once_with(main_channel_id)
		mock_delete_forwarded_message.assert_called_once_with(mock_bot, main_channel_id, settings_id)
		mock_delete_individual_channel.assert_called_once_with(main_channel_id)

	def test_not_exist_settings_message_id(self, mock_get_individual_channel_settings, mock_delete_individual_channel,
										   mock_delete_forwarded_message, *args):
		mock_bot = Mock(spec=TeleBot)
		channel_id = -10012345678
		main_channel_id = -10087654321
		mock_get_individual_channel_settings.return_value = ("{}", "1,2")

		channel_manager.delete_individual_settings_for_workspace(mock_bot, main_channel_id)
		mock_get_individual_channel_settings.assert_called_once_with(main_channel_id)
		mock_delete_forwarded_message.assert_not_called()
		mock_delete_individual_channel.assert_called_once_with(main_channel_id)

	def test_not_exist_individual_settings(self, mock_get_individual_channel_settings, mock_delete_individual_channel,
										   mock_delete_forwarded_message, *args):
		mock_bot = Mock(spec=TeleBot)
		channel_id = -10012345678
		main_channel_id = -10087654321
		mock_get_individual_channel_settings.return_value = None

		channel_manager.delete_individual_settings_for_workspace(mock_bot, main_channel_id)
		mock_get_individual_channel_settings.assert_called_once_with(main_channel_id)
		mock_delete_forwarded_message.assert_not_called()
		mock_delete_individual_channel.assert_not_called()


if __name__ == "__main__":
	main()
