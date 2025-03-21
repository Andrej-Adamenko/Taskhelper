from unittest import TestCase, main
from unittest.mock import patch, Mock, ANY, call

from telebot import TeleBot
from telebot.types import CallbackQuery, User, InlineKeyboardMarkup

import channel_manager
import scheduled_messages_utils
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
@patch("hashtag_data.HashtagData.__init__", return_value=None)
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
	@patch("channel_manager.get_ticket_settings_buttons")
	@patch("utils.merge_keyboard_markup")
	@patch("utils.copy_message")
	@patch("forwarding_utils.update_copied_message")
	def test_create_message_with_keyboard(self, mock_update_copied_message, mock_copy_message, mock_merge_keyboard_markup,
										  mock_get_ticket_settings_buttons, mock_get_subchannel_ids_from_hashtags,
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

		mock_generate_control_buttons.assert_has_calls([call(hashtag_data, mock_message),
														call(hashtag_data, mock_message)])
		mock_get_ticket_settings_buttons.assert_called_once_with(sub_chat_id, main_chat_id)
		mock_merge_keyboard_markup.assert_called_once_with(
			mock_generate_control_buttons.return_value,
			mock_get_ticket_settings_buttons.return_value
		)

		mock_copy_message.assert_called_once_with(mock_bot, chat_id=sub_chat_id, message_id=main_message_id,
												  from_chat_id=main_chat_id, reply_markup=mock_merge_keyboard_markup.return_value)
		mock_update_copied_message.assert_called_once_with(mock_bot, sub_chat_id, 166)

@patch("scheduled_messages_utils.ScheduledMessageDispatcher.handle_callback")
@patch("forwarding_utils._get_channel_ticket_keyboard")
@patch("forwarding_utils._get_channel_ticket_keyboard_state")
@patch("forwarding_utils.update_show_buttons")
@patch("forwarding_utils.generate_subchannel_buttons")
@patch("forwarding_utils.generate_priority_buttons")
@patch("forwarding_utils.generate_cc_buttons")
@patch("scheduled_messages_utils.ScheduledMessageDispatcher.generate_keyboard")
class TestShowKeyboard(TestCase):
	@patch("forwarding_utils.get_keyboard")
	@patch("utils.edit_message_keyboard")
	def test_show_keyboard(self, mock_edit_message_keyboard, mock_get_keyboard, *args):
		channel_id = -100865467
		message_id = 323
		user_id = 867345
		mock_bot = Mock(spec=TeleBot)
		mock_call = Mock(spec=CallbackQuery)
		mock_call.message = test_helper.create_mock_message("", [], -1001234567, 125)
		mock_call.message.reply_markup = Mock(spec=InlineKeyboardMarkup)
		mock_call.message.reply_markup.keyboard = []
		forwarding_utils.CHANNEL_TICKET_KEYBOARD_TYPE = {f"{channel_id}_{message_id}": {"state": forwarding_utils.CB_TYPES.SHOW_PRIORITIES, "user": user_id}}

		forwarding_utils.show_keyboard(mock_bot, mock_call, channel_id, message_id)
		mock_get_keyboard.assert_called_once_with(mock_call, channel_id, message_id)
		mock_edit_message_keyboard.assert_called_once_with(mock_bot, mock_call.message, chat_id=channel_id, message_id=message_id)

	def test_get_keyboard_empty(self, mock_generate_keyboard, mock_generate_cc_buttons, mock_generate_priority_buttons,
								mock_generate_subchannel_buttons, mock_update_show_buttons,
								mock__get_channel_ticket_keyboard_state, mock__get_channel_ticket_keyboard, *args):
		channel_id = -100865467
		message_id = 323
		mock_call = Mock(spec=CallbackQuery)
		mock_call.message = test_helper.create_mock_message("", [], -1001234567, 125)
		mock_call.message.reply_markup = Mock(spec=InlineKeyboardMarkup)
		mock_call.message.reply_markup.keyboard = []
		mock__get_channel_ticket_keyboard_state.return_value = None

		forwarding_utils.get_keyboard(mock_call, channel_id, message_id)
		mock__get_channel_ticket_keyboard_state.assert_called_once_with(channel_id, message_id)
		mock__get_channel_ticket_keyboard.assert_not_called()
		mock_update_show_buttons.assert_called_once_with(mock_call.message, None)
		mock_generate_subchannel_buttons.assert_not_called()
		mock_generate_priority_buttons.assert_not_called()
		mock_generate_cc_buttons.assert_not_called()
		mock_generate_keyboard.assert_not_called()

	def test_get_keyboard_show_subchannels(self, mock_generate_keyboard, mock_generate_cc_buttons,
										   mock_generate_priority_buttons, mock_generate_subchannel_buttons,
										   mock_update_show_buttons, mock__get_channel_ticket_keyboard_state,
										   mock__get_channel_ticket_keyboard, *args):
		channel_id = -100865467
		message_id = 323
		state = forwarding_utils.CB_TYPES.SHOW_SUBCHANNELS
		mock_call = Mock(spec=CallbackQuery)
		mock_call.message = test_helper.create_mock_message("", [], -1001234567, 125)
		mock_call.message.reply_markup = Mock(spec=InlineKeyboardMarkup)
		mock_call.message.reply_markup.keyboard = []
		mock__get_channel_ticket_keyboard_state.return_value = state

		forwarding_utils.get_keyboard(mock_call, channel_id, message_id)
		mock__get_channel_ticket_keyboard_state.assert_called_once_with(channel_id, message_id)
		mock__get_channel_ticket_keyboard.assert_not_called()
		mock_update_show_buttons.assert_called_once_with(mock_call.message, state)
		mock_generate_subchannel_buttons.assert_called_once_with(mock_call.message)
		mock_generate_priority_buttons.assert_not_called()
		mock_generate_cc_buttons.assert_not_called()
		mock_generate_keyboard.assert_not_called()

	def test_get_keyboard_show_priorities(self, mock_generate_keyboard, mock_generate_cc_buttons,
										  mock_generate_priority_buttons, mock_generate_subchannel_buttons,
										  mock_update_show_buttons, mock__get_channel_ticket_keyboard_state,
										  mock__get_channel_ticket_keyboard, *args):
		channel_id = -100865467
		message_id = 323
		state = forwarding_utils.CB_TYPES.SHOW_PRIORITIES
		mock_call = Mock(spec=CallbackQuery)
		mock_call.message = test_helper.create_mock_message("", [], -1001234567, 125)
		mock_call.message.reply_markup = Mock(spec=InlineKeyboardMarkup)
		mock_call.message.reply_markup.keyboard = []
		mock__get_channel_ticket_keyboard_state.return_value = state

		forwarding_utils.get_keyboard(mock_call, channel_id, message_id)
		mock__get_channel_ticket_keyboard_state.assert_called_once_with(channel_id, message_id)
		mock__get_channel_ticket_keyboard.assert_not_called()
		mock_update_show_buttons.assert_called_once_with(mock_call.message, state)
		mock_generate_subchannel_buttons.assert_not_called()
		mock_generate_priority_buttons.assert_called_once_with(mock_call.message)
		mock_generate_cc_buttons.assert_not_called()
		mock_generate_keyboard.assert_not_called()

	def test_get_keyboard_show_cc(self, mock_generate_keyboard, mock_generate_cc_buttons,
								  mock_generate_priority_buttons, mock_generate_subchannel_buttons,
								  mock_update_show_buttons, mock__get_channel_ticket_keyboard_state,
								  mock__get_channel_ticket_keyboard, *args):
		channel_id = -100865467
		message_id = 323
		state = forwarding_utils.CB_TYPES.SHOW_CC
		mock_call = Mock(spec=CallbackQuery)
		mock_call.message = test_helper.create_mock_message("", [], -1001234567, 125)
		mock_call.message.reply_markup = Mock(spec=InlineKeyboardMarkup)
		mock_call.message.reply_markup.keyboard = []
		mock__get_channel_ticket_keyboard_state.return_value = state

		forwarding_utils.get_keyboard(mock_call, channel_id, message_id)
		mock__get_channel_ticket_keyboard_state.assert_called_once_with(channel_id, message_id)
		mock__get_channel_ticket_keyboard.assert_not_called()
		mock_update_show_buttons.assert_called_once_with(mock_call.message, state)
		mock_generate_subchannel_buttons.assert_not_called()
		mock_generate_priority_buttons.assert_not_called()
		mock_generate_cc_buttons.assert_called_once_with(mock_call.message)
		mock_generate_keyboard.assert_not_called()

	def test_get_keyboard_show_calendar(self, mock_generate_keyboard, mock_generate_cc_buttons,
										mock_generate_priority_buttons, mock_generate_subchannel_buttons,
										mock_update_show_buttons, mock__get_channel_ticket_keyboard_state,
										mock__get_channel_ticket_keyboard, *args):
		channel_id = -100865467
		message_id = 323
		state = scheduled_messages_utils.ScheduledMessageDispatcher.CALLBACK_PREFIX
		settings_keyboard = {"state": state, "user": 876521,
						"data": f"{scheduled_messages_utils.ScheduledMessageDispatcher._SELECT_DAY_CALLBACK},11.2025"}
		mock_call = Mock(spec=CallbackQuery)
		mock_call.message = test_helper.create_mock_message("", [], -1001234567, 125)
		mock_call.message.reply_markup = Mock(spec=InlineKeyboardMarkup)
		mock_call.message.reply_markup.keyboard = []
		mock_call.data = ""
		mock__get_channel_ticket_keyboard_state.return_value = state
		mock__get_channel_ticket_keyboard.return_value = settings_keyboard
		keyboard = Mock(spec=InlineKeyboardMarkup)
		mock_generate_keyboard.return_value = [keyboard, mock_call.data]

		forwarding_utils.get_keyboard(mock_call, channel_id, message_id)
		mock__get_channel_ticket_keyboard_state.assert_called_once_with(channel_id, message_id)
		mock__get_channel_ticket_keyboard.assert_called_once_with(channel_id, message_id)
		mock_update_show_buttons.assert_called_once_with(mock_call.message, state)
		mock_generate_subchannel_buttons.assert_not_called()
		mock_generate_priority_buttons.assert_not_called()
		mock_generate_cc_buttons.assert_not_called()
		mock_generate_keyboard.assert_called_once_with(mock_call)
		self.assertEqual(mock_call.message.reply_markup, keyboard)
		self.assertEqual(mock_call.data, f"{state},{settings_keyboard["data"]}")


	@patch("utils.get_message_content_by_id")
	@patch("db_utils.get_main_message_from_copied")
	@patch("copy.deepcopy")
	@patch("forwarding_utils.get_keyboard")
	def test_get_keyboard_from_channel_message(self, mock_get_keyboard, mock_deepcopy,
												mock_get_main_message_from_copied, mock_get_message_content_by_id, *args):
		mock_bot = Mock(spec=TeleBot)
		message_id = 123
		channel_id = -10012345678
		dump_channel_id = -100498168751
		main_message_id = 321
		main_channel_id = -10087654321
		mock_call = Mock(spec=CallbackQuery)
		mock_call2 = Mock(spec=CallbackQuery)
		mock_call.message = test_helper.create_mock_message("", [], channel_id, message_id)
		mock_call2.message = test_helper.create_mock_message("", [], dump_channel_id, message_id)
		mock_get_main_message_from_copied.return_value = [main_message_id, main_channel_id]
		mock_deepcopy.return_value = mock_call2

		forwarding_utils.get_keyboard_from_channel_message(mock_bot, mock_call, message_id)
		mock_get_message_content_by_id.assert_not_called()
		mock_get_main_message_from_copied.assert_called_once_with(message_id, channel_id)
		mock_deepcopy.assert_called_once_with(mock_call)
		mock_get_keyboard.assert_called_once_with(mock_call2, channel_id, message_id)
		self.assertEqual(mock_call2.message.chat.id, main_channel_id)
		self.assertEqual(mock_call2.message.id, main_message_id)
		self.assertEqual(mock_call2.message.message_id, main_message_id)


	@patch("utils.get_message_content_by_id")
	@patch("db_utils.get_main_message_from_copied")
	@patch("copy.deepcopy")
	@patch("forwarding_utils.get_keyboard")
	def test_get_keyboard_from_channel_message_on_settings_message(self, mock_get_keyboard, mock_deepcopy,
												mock_get_main_message_from_copied, mock_get_message_content_by_id, *args):
		mock_bot = Mock(spec=TeleBot)
		message_id = 123
		other_message_id = 125
		channel_id = -10012345678
		dump_channel_id = -100498168751
		main_message_id = 321
		main_channel_id = -10087654321
		mock_call = Mock(spec=CallbackQuery)
		mock_call1 = Mock(spec=CallbackQuery)
		mock_call2 = Mock(spec=CallbackQuery)
		mock_call.message = test_helper.create_mock_message("", [], channel_id, message_id)
		mock_message1 = test_helper.create_mock_message("", [], channel_id, other_message_id)
		mock_call2.message = test_helper.create_mock_message("", [], dump_channel_id, message_id)
		mock_get_message_content_by_id.return_value = mock_message1
		mock_get_main_message_from_copied.return_value = [main_message_id, main_channel_id]
		mock_deepcopy.return_value = mock_call2

		forwarding_utils.get_keyboard_from_channel_message(mock_bot, mock_call, other_message_id)
		mock_get_message_content_by_id.assert_called_once_with(mock_bot, channel_id, other_message_id)
		mock_get_main_message_from_copied.assert_called_once_with(other_message_id, channel_id)
		mock_deepcopy.assert_called_once_with(mock_call)
		mock_get_keyboard.assert_called_once_with(mock_call2, channel_id, other_message_id)
		self.assertEqual(mock_message1.chat.id, main_channel_id)
		self.assertEqual(mock_message1.id, main_message_id)
		self.assertEqual(mock_message1.message_id, main_message_id)


@patch("db_utils.get_newest_copied_message")
@patch("channel_manager.clear_channel_ticket_settings_state")
@patch("forwarding_utils.set_channel_ticket_keyboard_state")
class TestHandleCallback(TestCase):
	@patch("forwarding_utils.change_subchannel_button_event")
	def test_change_subchannel(self, mock_change_subchannel_button_event, mock_set_channel_ticket_keyboard_state, *args):
		channel_id = -10012345678
		message_id = 123
		user_id = 8765
		mock_bot = Mock(spec=TeleBot)
		mock_call = Mock(spec=CallbackQuery)
		subchannel_name = "CC 1"
		mock_call.data = f"{forwarding_utils.CALLBACK_PREFIX},{forwarding_utils.CB_TYPES.CHANGE_SUBCHANNEL},{subchannel_name}"
		mock_call.message = test_helper.create_mock_message("", [], channel_id, message_id)
		mock_call.from_user = Mock(spec=User)
		mock_call.from_user.id = user_id

		forwarding_utils.handle_callback(mock_bot, mock_call, channel_id, message_id)
		mock_change_subchannel_button_event.assert_called_once_with(mock_bot, mock_call, subchannel_name)
		mock_set_channel_ticket_keyboard_state.assert_called_once_with(channel_id, message_id, user_id, None)

	@patch("forwarding_utils.change_state_button_event")
	def test_close(self, mock_change_state_button_event, mock_set_channel_ticket_keyboard_state,
				   mock_clear_channel_ticket_settings_state, mock_get_newest_copied_message, *args):
		channel_id = -10012345678
		message_id = 123
		user_id = 8765
		mock_bot = Mock(spec=TeleBot)
		mock_call = Mock(spec=CallbackQuery)
		mock_call.data = f"{forwarding_utils.CALLBACK_PREFIX},{forwarding_utils.CB_TYPES.CLOSE},"
		mock_call.message = test_helper.create_mock_message("", [], channel_id, message_id)
		mock_get_newest_copied_message.return_value = message_id
		mock_call.from_user = Mock(spec=User)
		mock_call.from_user.id = user_id

		forwarding_utils.handle_callback(mock_bot, mock_call, channel_id, message_id)
		mock_change_state_button_event.assert_called_once_with(mock_bot, mock_call, False)
		mock_get_newest_copied_message.assert_not_called()
		mock_clear_channel_ticket_settings_state.assert_not_called()
		mock_set_channel_ticket_keyboard_state.assert_called_once_with(channel_id, message_id, user_id, None)


	@patch("forwarding_utils.change_state_button_event")
	def test_open(self, mock_change_state_button_event, mock_set_channel_ticket_keyboard_state,
				  mock_clear_channel_ticket_settings_state, mock_get_newest_copied_message, *args):
		channel_id = -10012345678
		message_id = 123
		user_id = 8765
		mock_bot = Mock(spec=TeleBot)
		mock_call = Mock(spec=CallbackQuery)
		mock_call.data = f"{forwarding_utils.CALLBACK_PREFIX},{forwarding_utils.CB_TYPES.OPEN},"
		mock_call.message = test_helper.create_mock_message("", [], channel_id, message_id)
		mock_get_newest_copied_message.return_value = message_id
		mock_call.from_user = Mock(spec=User)
		mock_call.from_user.id = user_id

		forwarding_utils.handle_callback(mock_bot, mock_call, channel_id, message_id)
		mock_change_state_button_event.assert_called_once_with(mock_bot, mock_call, True)
		mock_get_newest_copied_message.assert_not_called()
		mock_clear_channel_ticket_settings_state.assert_not_called()
		mock_set_channel_ticket_keyboard_state.assert_called_once_with(channel_id, message_id, user_id, None)

	@patch("forwarding_utils.forward_and_add_inline_keyboard")
	def test_save(self, mock_forward_and_add_inline_keyboard, mock_set_channel_ticket_keyboard_state, *args):
		channel_id = -10012345678
		message_id = 123
		user_id = 8765
		mock_bot = Mock(spec=TeleBot)
		mock_call = Mock(spec=CallbackQuery)
		mock_call.data = f"{forwarding_utils.CALLBACK_PREFIX},{forwarding_utils.CB_TYPES.SAVE},"
		mock_call.message = test_helper.create_mock_message("", [], channel_id, message_id)
		mock_call.from_user = Mock(spec=User)
		mock_call.from_user.id = user_id

		forwarding_utils.handle_callback(mock_bot, mock_call)
		mock_forward_and_add_inline_keyboard.assert_called_once_with(mock_bot, mock_call.message)
		mock_set_channel_ticket_keyboard_state.assert_called_once_with(None, None, user_id, None)

	@patch("forwarding_utils.show_subchannel_buttons")
	def test_show_subchannels(self, mock_show_subchannel_buttons, mock_set_channel_ticket_keyboard_state, *args):
		channel_id = -10012345678
		message_id = 123
		user_id = 8765
		mock_bot = Mock(spec=TeleBot)
		mock_call = Mock(spec=CallbackQuery)
		mock_call.data = f"{forwarding_utils.CALLBACK_PREFIX},{forwarding_utils.CB_TYPES.SHOW_SUBCHANNELS},"
		mock_call.message = test_helper.create_mock_message("", [], channel_id, message_id)
		mock_call.from_user = Mock(spec=User)
		mock_call.from_user.id = user_id

		forwarding_utils.handle_callback(mock_bot, mock_call, channel_id, message_id)
		mock_show_subchannel_buttons.assert_called_once_with(mock_bot, mock_call.message, channel_id, message_id)
		mock_set_channel_ticket_keyboard_state.assert_called_once_with(channel_id, message_id, user_id, forwarding_utils.CB_TYPES.SHOW_SUBCHANNELS)

	@patch("forwarding_utils.show_priority_buttons")
	def test_show_priorities(self, mock_forward_and_add_inline_keyboard, mock_set_channel_ticket_keyboard_state, *args):
		channel_id = -10012345678
		message_id = 123
		user_id = 8765
		mock_bot = Mock(spec=TeleBot)
		mock_call = Mock(spec=CallbackQuery)
		mock_call.data = f"{forwarding_utils.CALLBACK_PREFIX},{forwarding_utils.CB_TYPES.SHOW_PRIORITIES},"
		mock_call.message = test_helper.create_mock_message("", [], channel_id, message_id)
		mock_call.from_user = Mock(spec=User)
		mock_call.from_user.id = user_id

		forwarding_utils.handle_callback(mock_bot, mock_call, channel_id, message_id)
		mock_forward_and_add_inline_keyboard.assert_called_once_with(mock_bot, mock_call.message, channel_id, message_id)
		mock_set_channel_ticket_keyboard_state.assert_called_once_with(channel_id, message_id, user_id, forwarding_utils.CB_TYPES.SHOW_PRIORITIES)

	@patch("forwarding_utils.change_priority_button_event")
	def test_change_priority(self, mock_change_priority_button_event, mock_set_channel_ticket_keyboard_state, *args):
		channel_id = -10012345678
		message_id = 123
		user_id = 8765
		mock_bot = Mock(spec=TeleBot)
		mock_call = Mock(spec=CallbackQuery)
		priority = '2'
		mock_call.data = f"{forwarding_utils.CALLBACK_PREFIX},{forwarding_utils.CB_TYPES.CHANGE_PRIORITY},{priority}"
		mock_call.message = test_helper.create_mock_message("", [], channel_id, message_id)
		mock_call.from_user = Mock(spec=User)
		mock_call.from_user.id = user_id

		forwarding_utils.handle_callback(mock_bot, mock_call, channel_id, message_id)
		mock_change_priority_button_event.assert_called_once_with(mock_bot, mock_call, priority)
		mock_set_channel_ticket_keyboard_state.assert_called_once_with(channel_id, message_id, user_id, None)

	@patch("forwarding_utils.show_cc_buttons")
	def test_show_cc(self, mock_show_cc_buttons, mock_set_channel_ticket_keyboard_state,
					 mock_clear_channel_ticket_settings_state, mock_get_newest_copied_message, *args):
		channel_id = -10012345678
		message_id = 123
		user_id = 8765
		mock_bot = Mock(spec=TeleBot)
		mock_call = Mock(spec=CallbackQuery)
		mock_call.data = f"{forwarding_utils.CALLBACK_PREFIX},{forwarding_utils.CB_TYPES.SHOW_CC},"
		mock_call.message = test_helper.create_mock_message("", [], channel_id, message_id)
		mock_get_newest_copied_message.return_value = message_id
		mock_call.from_user = Mock(spec=User)
		mock_call.from_user.id = user_id

		forwarding_utils.handle_callback(mock_bot, mock_call, channel_id, message_id)
		mock_show_cc_buttons.assert_called_once_with(mock_bot, mock_call.message, channel_id, message_id)
		mock_get_newest_copied_message.assert_called_once_with(channel_id)
		mock_clear_channel_ticket_settings_state.assert_called_once_with(mock_call, channel_manager.TICKET_MENU_TYPE, channel_id)
		mock_set_channel_ticket_keyboard_state.assert_called_once_with(channel_id, message_id, user_id, forwarding_utils.CB_TYPES.SHOW_CC)

	@patch("forwarding_utils.toggle_cc_button_event")
	def test_toggle_cc(self, mock_toggle_cc_button_event, mock_set_channel_ticket_keyboard_state,
					   mock_clear_channel_ticket_settings_state, mock_get_newest_copied_message, *args):
		channel_id = -10012345678
		message_id = 123
		user_id = 8765
		mock_bot = Mock(spec=TeleBot)
		mock_call = Mock(spec=CallbackQuery)
		user = "FF"
		mock_call.data = f"{forwarding_utils.CALLBACK_PREFIX},{forwarding_utils.CB_TYPES.TOGGLE_CC},{user}"
		mock_call.message = test_helper.create_mock_message("", [], channel_id, message_id)
		mock_get_newest_copied_message.return_value = message_id
		mock_call.from_user = Mock(spec=User)
		mock_call.from_user.id = user_id

		forwarding_utils.handle_callback(mock_bot, mock_call, channel_id, message_id)
		mock_toggle_cc_button_event.assert_called_once_with(mock_bot, mock_call, user)
		mock_get_newest_copied_message.assert_called_once_with(channel_id)
		mock_clear_channel_ticket_settings_state.assert_called_once_with(mock_call, channel_manager.TICKET_MENU_TYPE, channel_id)
		mock_set_channel_ticket_keyboard_state.assert_called_once_with(channel_id, message_id, user_id, forwarding_utils.CB_TYPES.SHOW_CC)

	@patch("forwarding_utils.toggle_cc_button_event")
	def test_hide_settings_menu_no_newest(self, mock_toggle_cc_button_event, mock_set_channel_ticket_keyboard_state,
									mock_clear_channel_ticket_settings_state, mock_get_newest_copied_message, *args):
		channel_id = -10012345678
		message_id = 123
		user_id = 8765
		newest_message_id = 125
		mock_bot = Mock(spec=TeleBot)
		mock_call = Mock(spec=CallbackQuery)
		user = "FF"
		mock_call.data = f"{forwarding_utils.CALLBACK_PREFIX},{forwarding_utils.CB_TYPES.TOGGLE_CC},{user}"
		mock_call.message = test_helper.create_mock_message("", [], channel_id, message_id)
		mock_get_newest_copied_message.return_value = newest_message_id
		mock_call.from_user = Mock(spec=User)
		mock_call.from_user.id = user_id

		forwarding_utils.handle_callback(mock_bot, mock_call, channel_id, message_id)
		mock_toggle_cc_button_event.assert_called_once_with(mock_bot, mock_call, user)
		mock_get_newest_copied_message.assert_called_once_with(channel_id)
		mock_clear_channel_ticket_settings_state.assert_not_called()
		mock_set_channel_ticket_keyboard_state.assert_called_once_with(channel_id, message_id, user_id, forwarding_utils.CB_TYPES.SHOW_CC)


class TestSetGetChannelTicketKeyboard(TestCase):
	def test_set_channel_ticket_keyboard_state(self, *args):
		channel_id = -1008765432
		message_id = 324
		user_id = 8765
		state = forwarding_utils.CB_TYPES.CHANGE_SUBCHANNEL
		forwarding_utils.CHANNEL_TICKET_KEYBOARD_TYPE = {}

		forwarding_utils.set_channel_ticket_keyboard_state(channel_id, message_id, user_id, state, None)
		self.assertEqual(forwarding_utils.CHANNEL_TICKET_KEYBOARD_TYPE, {f"{channel_id}_{message_id}": {"state": state, "data": None, "user": user_id}})

	def test_set_channel_ticket_keyboard_state_data(self, *args):
		channel_id = -1008765432
		message_id = 324
		user_id = 8765
		state = scheduled_messages_utils.ScheduledMessageDispatcher.CALLBACK_PREFIX
		forwarding_utils.CHANNEL_TICKET_KEYBOARD_TYPE = {}
		data = f"{scheduled_messages_utils.ScheduledMessageDispatcher._MONTH_CALENDAR_CALLBACK},11.2025"

		forwarding_utils.set_channel_ticket_keyboard_state(channel_id, message_id, user_id, state, data)
		self.assertEqual(forwarding_utils.CHANNEL_TICKET_KEYBOARD_TYPE, {f"{channel_id}_{message_id}": {"state": state, "data": data, "user": user_id}})

	def test_set_channel_ticket_keyboard_state_empty(self, *args):
		channel_id = -1008765432
		message_id = 324
		user_id = 8765
		state = forwarding_utils.CB_TYPES.CHANGE_SUBCHANNEL
		forwarding_utils.CHANNEL_TICKET_KEYBOARD_TYPE = {}

		forwarding_utils.set_channel_ticket_keyboard_state(None, None, user_id, state)
		self.assertEqual(forwarding_utils.CHANNEL_TICKET_KEYBOARD_TYPE, {})

	def test_set_channel_ticket_keyboard_state_empty_channel(self, *args):
		channel_id = -1008765432
		message_id = 324
		user_id = 8765
		state = forwarding_utils.CB_TYPES.CHANGE_SUBCHANNEL
		forwarding_utils.CHANNEL_TICKET_KEYBOARD_TYPE = {}

		forwarding_utils.set_channel_ticket_keyboard_state(None, message_id, user_id, state)
		self.assertEqual(forwarding_utils.CHANNEL_TICKET_KEYBOARD_TYPE, {})

	def test_set_channel_ticket_keyboard_state_empty_message(self, *args):
		channel_id = -1008765432
		user_id = 8765
		state = forwarding_utils.CB_TYPES.CHANGE_SUBCHANNEL
		forwarding_utils.CHANNEL_TICKET_KEYBOARD_TYPE = {}

		forwarding_utils.set_channel_ticket_keyboard_state(channel_id, None, user_id, state)
		self.assertEqual(forwarding_utils.CHANNEL_TICKET_KEYBOARD_TYPE, {})

	def test_set_channel_ticket_keyboard_state_clear(self, *args):
		channel_id = -1008765432
		message_id = 324
		user_id = 8765
		state = forwarding_utils.CB_TYPES.CHANGE_SUBCHANNEL
		forwarding_utils.CHANNEL_TICKET_KEYBOARD_TYPE = {f"{channel_id}_{message_id}": {"state": state, "user": user_id}}

		forwarding_utils.set_channel_ticket_keyboard_state(channel_id, message_id, user_id, None, None)
		self.assertEqual(forwarding_utils.CHANNEL_TICKET_KEYBOARD_TYPE,{})

	def test_clear_channel_ticket_keyboard_by_user(self, *args):
		channel_id = -1008765432
		message_id = 324
		user_id = 8765
		state = forwarding_utils.CB_TYPES.CHANGE_SUBCHANNEL
		forwarding_utils.CHANNEL_TICKET_KEYBOARD_TYPE = {f"{channel_id}_{message_id}": {"state": state, "user": user_id}}

		forwarding_utils.clear_channel_ticket_keyboard_by_user(channel_id, message_id, user_id)
		self.assertEqual(forwarding_utils.CHANNEL_TICKET_KEYBOARD_TYPE, {})

	def test_clear_channel_ticket_keyboard_by_user_another(self, *args):
		channel_id = -1008765432
		message_id = 324
		user_id = 8765
		state = forwarding_utils.CB_TYPES.CHANGE_SUBCHANNEL
		forwarding_utils.CHANNEL_TICKET_KEYBOARD_TYPE = {f"{channel_id}_{message_id}": {"state": state, "user": user_id}}

		forwarding_utils.clear_channel_ticket_keyboard_by_user(channel_id, message_id, 8766)
		self.assertEqual(forwarding_utils.CHANNEL_TICKET_KEYBOARD_TYPE, {f"{channel_id}_{message_id}": {"state": state, "user": user_id}})

	def test__get_channel_ticket_keyboard(self, *args):
		channel_id = -1008765432
		message_id = 324
		user_id = 8765
		state = forwarding_utils.CB_TYPES.CHANGE_SUBCHANNEL
		forwarding_utils.CHANNEL_TICKET_KEYBOARD_TYPE = {f"{channel_id}_{message_id}": {"state": state, "user": user_id}}

		settings = forwarding_utils._get_channel_ticket_keyboard(channel_id, message_id)
		self.assertEqual(settings, {"state": state, "user": user_id})

	def test__get_channel_ticket_keyboard_empty(self, *args):
		channel_id = -1008765432
		channel_id2 = -1008765434
		message_id = 324
		user_id = 8765
		state = forwarding_utils.CB_TYPES.CHANGE_SUBCHANNEL
		forwarding_utils.CHANNEL_TICKET_KEYBOARD_TYPE = {f"{channel_id2}_{message_id}": {"state": state, "user": user_id}}

		settings = forwarding_utils._get_channel_ticket_keyboard(channel_id, message_id)
		self.assertEqual(settings, None)

	def test__get_channel_ticket_keyboard_state(self, *args):
		channel_id = -1008765432
		message_id = 324
		user_id = 8765
		state = forwarding_utils.CB_TYPES.CHANGE_SUBCHANNEL
		forwarding_utils.CHANNEL_TICKET_KEYBOARD_TYPE = {f"{channel_id}_{message_id}": {"state": state, "user": user_id}}

		settings = forwarding_utils._get_channel_ticket_keyboard_state(channel_id, message_id)
		self.assertEqual(settings, state)

	def test__get_channel_ticket_keyboard_state_empty(self, *args):
		channel_id = -1008765432
		channel_id2 = -1008765434
		message_id = 324
		user_id = 8765
		state = forwarding_utils.CB_TYPES.CHANGE_SUBCHANNEL
		forwarding_utils.CHANNEL_TICKET_KEYBOARD_TYPE = {f"{channel_id2}_{message_id}": {"state": state, "user": user_id}}

		settings = forwarding_utils._get_channel_ticket_keyboard_state(channel_id, message_id)
		self.assertEqual(settings, None)


if __name__ == "__main__":
	main()

