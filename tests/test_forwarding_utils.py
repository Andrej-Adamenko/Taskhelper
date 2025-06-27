from unittest import TestCase, main
from unittest.mock import patch, Mock, ANY, call

from telebot import TeleBot
from telebot.apihelper import ApiTelegramException
from telebot.types import CallbackQuery, User, InlineKeyboardMarkup

import channel_manager
import config_utils
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

@patch("hashtag_data.HashtagData.is_closed", return_value=False)
@patch("hashtag_data.HashtagData.get_assigned_user", return_value="NN")
@patch("hashtag_data.HashtagData.get_priority_number", return_value="2")
@patch("hashtag_data.HashtagData.is_scheduled", return_value=False)
@patch("hashtag_data.HashtagData.set_scheduled_tag", return_value=False)
@patch("hashtag_data.HashtagData.is_opened", return_value=True)
@patch("hashtag_data.HashtagData.get_hashtag_list", return_value=[None, "", "NN", ""])
@patch("db_utils.get_newest_copied_message", return_value=166)
@patch("hashtag_data.HashtagData.__init__", return_value=None)
@patch("daily_reminder.update_ticket_data")
@patch("forwarding_utils.get_unchanged_posts", return_value=[])
class ForwardForSubchannelTest(TestCase):
	@patch("forwarding_utils.generate_control_buttons")
	@patch("utils.add_channel_id_to_post_data")
	@patch("forwarding_utils.get_subchannel_ids_from_hashtags")
	@patch("forwarding_utils.filter_subchannels_by_members")
	@patch("db_utils.insert_copied_message")
	@patch("db_utils.insert_or_update_last_msg_id")
	@patch("forwarding_utils.update_copied_message")
	@patch("utils.edit_message_keyboard")
	def test_order_add_remove_settings_button(self, mock_edit_message_keyboard, mock_update_copied_message,
											  mock_insert_or_update_last_msg_id, mock_insert_copied_message,
											  mock_filter_subchannels_by_members, mock_get_subchannel_ids_from_hashtags,
											  mock_add_channel_id_to_post_data, mock_generate_control_buttons, *args):
		main_chat_id = 12345678
		main_message_id = 157
		test = "test item"
		mock_bot = Mock(spec=TeleBot)

		mock_message = test_helper.create_mock_message(test, [], main_chat_id, main_message_id)

		sub_chat_id = 87654321
		sub_message_id = 167

		mock_copied_message = test_helper.create_mock_message(test, [], sub_chat_id, sub_message_id)
		mock_bot.send_message.return_value = mock_copied_message
		mock_filter_subchannels_by_members.return_value = [sub_chat_id]

		hashtag_data = HashtagData()

		manager = Mock()
		manager.attach_mock(mock_insert_copied_message, 'a')
		manager.attach_mock(mock_edit_message_keyboard, 'b')
		manager.attach_mock(mock_update_copied_message, 'c')
		manager.attach_mock(mock_insert_or_update_last_msg_id, 'd')

		forwarding_utils.forward_to_subchannel(mock_bot, mock_message, hashtag_data)
		mock_add_channel_id_to_post_data.assert_called_once_with(mock_message)
		mock_get_subchannel_ids_from_hashtags.assert_called_once_with(main_chat_id, main_message_id, hashtag_data)
		mock_filter_subchannels_by_members.assert_called_once_with(main_chat_id, mock_get_subchannel_ids_from_hashtags.return_value)

		expected_calls = [
			call.a(main_message_id, main_chat_id, sub_message_id, sub_chat_id),
			call.d(sub_message_id, sub_chat_id),
			call.b(mock_bot, mock_message, mock_generate_control_buttons.return_value, chat_id=sub_chat_id, message_id=sub_message_id),
			call.c(mock_bot, sub_chat_id, 166),
		]
		self.assertEqual(manager.mock_calls, expected_calls)

	@patch("db_utils.insert_copied_message")
	@patch("db_utils.insert_or_update_last_msg_id")
	@patch("db_utils.get_main_message_from_copied")
	@patch("forwarding_utils.generate_control_buttons")
	@patch("forwarding_utils.get_subchannel_ids_from_hashtags")
	@patch("forwarding_utils.filter_subchannels_by_members")
	@patch("channel_manager.get_ticket_settings_buttons")
	@patch("utils.merge_keyboard_markup")
	@patch("forwarding_utils.update_copied_message")
	def test_create_message_with_keyboard(self, mock_update_copied_message, mock_merge_keyboard_markup,
										  mock_get_ticket_settings_buttons, mock_filter_subchannels_by_members,
										  mock_get_subchannel_ids_from_hashtags, mock_generate_control_buttons,
										  mock_get_main_message_from_copied, *args):
		main_chat_id = 12345678
		main_message_id = 157
		test = "test item"
		mock_bot = Mock(spec=TeleBot)

		mock_message = test_helper.create_mock_message(test, [], main_chat_id, main_message_id)
		mock_get_main_message_from_copied.return_value = [main_message_id, main_chat_id]

		sub_chat_id = 87654321
		sub_message_id = 167

		mock_copied_message = test_helper.create_mock_message(test, [], sub_chat_id, sub_message_id)
		mock_bot.send_message.return_value = mock_copied_message
		mock_filter_subchannels_by_members.return_value = [sub_chat_id]

		hashtag_data = HashtagData()
		forwarding_utils.forward_to_subchannel(mock_bot, mock_message, hashtag_data)
		mock_get_subchannel_ids_from_hashtags.assert_called_once_with(main_chat_id, main_message_id, hashtag_data)
		mock_filter_subchannels_by_members.assert_called_once_with(main_chat_id, mock_get_subchannel_ids_from_hashtags.return_value)
		mock_generate_control_buttons.assert_has_calls([call(hashtag_data, mock_message),
														call(hashtag_data, mock_message)])
		mock_get_ticket_settings_buttons.assert_called_once_with(sub_chat_id)
		mock_merge_keyboard_markup.assert_called_once_with(
			mock_generate_control_buttons.return_value,
			mock_get_ticket_settings_buttons.return_value
		)

		mock_bot.send_message.assert_called_once_with(chat_id=sub_chat_id, text=mock_message.text,
												  entities=mock_message.entities, reply_markup=mock_merge_keyboard_markup.return_value)
		mock_update_copied_message.assert_called_once_with(mock_bot, sub_chat_id, 166)

	@patch("db_utils.get_main_message_from_copied")
	@patch("forwarding_utils.generate_control_buttons")
	@patch("utils.add_channel_id_to_post_data")
	@patch("forwarding_utils.get_keyboard")
	@patch("forwarding_utils.get_subchannel_ids_from_hashtags")
	@patch("forwarding_utils.filter_subchannels_by_members")
	@patch("channel_manager.get_ticket_settings_buttons")
	@patch("utils.merge_keyboard_markup")
	@patch("utils.edit_message_keyboard")
	@patch("forwarding_utils.update_copied_message")
	def test_create_message_for_unchanged(self, mock_update_copied_message, mock_edit_message_keyboard,
										  mock_merge_keyboard_markup, mock_get_ticket_settings_buttons,
										  mock_filter_subchannels_by_members, mock_get_subchannel_ids_from_hashtags,
										  mock_get_keyboard, mock_add_channel_id_to_post_data,
										  mock_generate_control_buttons, mock_get_main_message_from_copied,
										  mock_get_unchanged_posts, *args):
		main_chat_id = 12345678
		main_message_id = 157
		test = "test item"
		mock_bot = Mock(spec=TeleBot)

		mock_message = test_helper.create_mock_message(test, [], main_chat_id, main_message_id)
		mock_get_main_message_from_copied.return_value = [main_message_id, main_chat_id]

		sub_chat_id = 87654321
		sub_message_id = 167

		mock_copied_message = test_helper.create_mock_message(test, [], sub_chat_id, sub_message_id)
		mock_bot.send_message.return_value = mock_copied_message
		mock_get_unchanged_posts.return_value = {sub_chat_id: sub_message_id}
		mock_filter_subchannels_by_members.return_value = [sub_chat_id]

		hashtag_data = HashtagData()
		forwarding_utils.forward_to_subchannel(mock_bot, mock_message, hashtag_data)
		mock_add_channel_id_to_post_data.assert_called_once_with(mock_message)
		mock_get_subchannel_ids_from_hashtags.assert_called_once_with(main_chat_id, main_message_id, hashtag_data)
		mock_filter_subchannels_by_members.assert_called_once_with(main_chat_id, mock_get_subchannel_ids_from_hashtags.return_value)
		mock_generate_control_buttons.assert_not_called()
		mock_get_keyboard.assert_called_once_with(ANY, sub_chat_id, sub_message_id)
		mock_get_ticket_settings_buttons.assert_not_called()
		mock_merge_keyboard_markup.assert_not_called()
		mock_edit_message_keyboard.assert_called_once_with(mock_bot, mock_message, mock_get_keyboard.return_value,
														   chat_id = sub_chat_id, message_id=sub_message_id)
		mock_update_copied_message.assert_not_called()

	@patch("db_utils.get_main_message_from_copied")
	@patch("forwarding_utils.generate_control_buttons")
	@patch("utils.add_channel_id_to_post_data")
	@patch("forwarding_utils.get_keyboard")
	@patch("forwarding_utils.get_subchannel_ids_from_hashtags")
	@patch("forwarding_utils.filter_subchannels_by_members")
	@patch("channel_manager.get_ticket_settings_buttons")
	@patch("utils.merge_keyboard_markup")
	@patch("utils.edit_message_keyboard")
	@patch("forwarding_utils.update_copied_message")
	def test_closed_message(self, mock_update_copied_message, mock_edit_message_keyboard,
										  mock_merge_keyboard_markup, mock_get_ticket_settings_buttons,
										  mock_filter_subchannels_by_members, mock_get_subchannel_ids_from_hashtags,
										  mock_get_keyboard, mock_add_channel_id_to_post_data,
										  mock_generate_control_buttons, mock_get_main_message_from_copied,
										  mock_get_unchanged_posts, mock_update_ticket_data, *args):
		main_chat_id = 12345678
		main_message_id = 157
		test = "test item"
		sub_chat_id = 87654321
		sub_message_id = 167

		mock_bot = Mock(spec=TeleBot)
		mock_message = test_helper.create_mock_message(test, [], main_chat_id, main_message_id)
		mock_get_main_message_from_copied.return_value = [main_message_id, main_chat_id]
		mock_copied_message = test_helper.create_mock_message(test, [], sub_chat_id, sub_message_id)
		mock_bot.send_message.return_value = mock_copied_message
		mock_get_unchanged_posts.return_value = {sub_chat_id: sub_message_id}
		mock_filter_subchannels_by_members.return_value = [sub_chat_id]

		hashtag_data = HashtagData()
		hashtag_data.is_closed.return_value = True

		forwarding_utils.forward_to_subchannel(mock_bot, mock_message, hashtag_data)
		mock_update_ticket_data.assert_called_once_with(main_message_id, main_chat_id, hashtag_data)
		mock_add_channel_id_to_post_data.assert_not_called()
		mock_get_subchannel_ids_from_hashtags.assert_not_called()
		mock_filter_subchannels_by_members.assert_not_called()
		mock_get_unchanged_posts.assert_called_once_with(mock_bot, mock_message, [])
		mock_generate_control_buttons.assert_not_called()
		mock_get_keyboard.assert_not_called()
		mock_get_ticket_settings_buttons.assert_not_called()
		mock_merge_keyboard_markup.assert_not_called()
		mock_edit_message_keyboard.assert_not_called()
		mock_update_copied_message.assert_not_called()

	@patch("user_utils.get_member_ids_channel", return_value=[5486154])
	@patch("db_utils.get_main_message_sender")
	def test_filter_creator_channels(self, mock_get_main_message_sender, *args):
		main_channel_id = -1006532516165
		main_message_id = 453
		user_id = 5486154
		config_utils.USER_TAGS = {"AA": 358435, "CC": user_id, "DD": 5115684, "FF": user_id}
		mock_get_main_message_sender.return_value = user_id
		channel_data = [
			(-10012345678, {channel_manager.SETTING_TYPES.REPORTED: ["CC", "DD"]}),
			(-10087654321, {channel_manager.SETTING_TYPES.REPORTED: ["DD", "FF"]}),
			(-10082165431, {channel_manager.SETTING_TYPES.REPORTED: ["dd", "ff"]}),
		]

		result_channels = forwarding_utils.filter_creator_channels(channel_data, main_channel_id, main_message_id)
		mock_get_main_message_sender.assert_called_once_with(main_channel_id, main_message_id)
		self.assertEqual(result_channels, [-10012345678, -10087654321])

	@patch("user_utils.get_member_ids_channel", return_value=[5486126])
	@patch("db_utils.get_main_message_sender")
	def test_filter_creator_channels_no_member(self, mock_get_main_message_sender, *args):
		main_channel_id = -1006532516165
		main_message_id = 453
		user_id = 5486154
		config_utils.USER_TAGS = {"AA": 358435, "CC": user_id, "DD": 5115684, "FF": user_id}
		mock_get_main_message_sender.return_value = user_id
		channel_data = [
			(-10012345678, {channel_manager.SETTING_TYPES.REPORTED: ["CC", "DD"]}),
			(-10087654321, {channel_manager.SETTING_TYPES.REPORTED: ["DD", "FF"]}),
			(-10082165431, {channel_manager.SETTING_TYPES.REPORTED: ["dd", "ff"]}),
		]

		result_channels = forwarding_utils.filter_creator_channels(channel_data, main_channel_id, main_message_id)
		mock_get_main_message_sender.assert_called_once_with(main_channel_id, main_message_id)
		self.assertEqual(result_channels, [])


@patch("hashtag_data.HashtagData.__init__", return_value=None)
@patch("db_utils.get_scheduled_message_send_time", return_value=False)
@patch("config_utils.USER_TAGS", {"AA": 123456, "BB": 516224})
@patch("user_utils.get_member_ids_channel", return_value=[123456, 516224])
@patch("db_utils.get_main_message_sender", return_value=123456)
@patch("db_utils.get_custom_hashtag", return_value=None)
@patch("db_utils.get_individual_channels_by_priority")
class GetSubchannelIdsFromHashtags(TestCase):
	def test_default(self, mock_get_individual_channel_by_priority, mock_get_custom_hashtag, *args):
		main_channel_id = -10087654321
		main_message_id = 216
		priority = 2
		channel_datum1 = [1, '{"due": true, "deferred": true, "assigned": ["AA", "BB"], "reported": ["BB", "CC"], "cc": ["CC", "DD", "FF"]}']
		channel_datum2 = [2, '{"due": true, "deferred": true, "assigned": ["AA", "BB", "FF"], "reported": ["BB", "CC"], "cc": ["CC", "DD"]}']
		channel_datum3 = [3, '{"due": false, "deferred": true, "assigned": ["AA", "BB", "FF"], "reported": ["BB", "CC"], "cc": ["CC", "DD"]}']
		channel_datum4 = [4, '{"due": true, "deferred": true, "assigned": ["AA", "BB"], "reported": ["BB", "CC"], "cc": ["CC", "DD", "BB"]}']
		channel_datum5 = [5, '{"due": false, "deferred": true, "assigned": ["AA", "BB"], "reported": ["BB", "CC"], "cc": ["CC", "DD", "BB"]}']
		channel_datum6 = [6, '{"due": true, "deferred": true, "assigned": ["AA", "BB"], "reported": ["AA", "BB", "CC"], "cc": ["CC", "DD"]}']
		channel_datum7 = [7, '{"due": false, "deferred": true, "assigned": ["AA", "BB"], "reported": ["AA", "BB", "CC"], "cc": ["CC", "DD"]}']
		channel_data = [channel_datum1, channel_datum2, channel_datum3, channel_datum4, channel_datum5, channel_datum6, channel_datum7]
		mock_hashtag_data = Mock(spec=HashtagData)
		mock_hashtag_data.get_assigned_user.return_value = "FF"
		mock_hashtag_data.get_followed_users.return_value = ["AA", "BB"]
		mock_hashtag_data.get_priority_number_or_default.return_value = priority
		mock_get_individual_channel_by_priority.return_value = channel_data

		result = forwarding_utils.get_subchannel_ids_from_hashtags(main_channel_id, main_message_id, mock_hashtag_data)
		mock_hashtag_data.get_priority_number_or_default.assert_called_once_with()
		mock_get_individual_channel_by_priority.assert_called_once_with(priority)
		self.assertEqual(result, {2, 4, 6})


@patch("user_utils.MEMBER_CACHE", {-10012345678: {"user_ids": [12345, 23465, 13508], "time": 1745924296},
								   -10087654321: {"user_ids": [12345], "time": 1745924296},
								   -10012378456: {"user_ids": [24687, 28946], "time": 1745924296},
								   -10087653214: {"user_ids": [12345, 23465, 21682], "time": 1745924296}})
@patch("time.time", return_value=1745924296)
class FilterSubchannelByMembersTest(TestCase):
	@patch("user_utils.get_member_ids_channels")
	def test_functions(self, mock_get_member_ids_channels, *args):
		main_channel_id = -10012345678
		subchannel_ids = {-10087654321, -10012378456, -10087653214}
		all_channels = [-10012345678, -10012378456, -10087653214, -10087654321]

		manager = Mock()
		manager.attach_mock(mock_get_member_ids_channels, 'a')

		forwarding_utils.filter_subchannels_by_members(main_channel_id, set(subchannel_ids))
		mock_get_member_ids_channels.assert_called_once_with(all_channels)

	def test_result(self, *args):
		main_channel_id = -10012345678
		subchannel_ids = [-10087654321, -10012378456, -10087653214]

		result = forwarding_utils.filter_subchannels_by_members(main_channel_id, set(subchannel_ids))
		self.assertEqual(result, [-10087654321])


@patch("hashtag_data.HashtagData.__init__", return_value=None)
@patch("user_utils.get_member_ids_channel", return_value=[875135])
@patch("db_utils.get_main_message_sender")
@patch("hashtag_data.HashtagData.add_user")
@patch("hashtag_data.HashtagData.get_updated_post_data")
@patch("forwarding_utils.update_main_message_content")
@patch("comment_utils.CommentDispatcher.add_next_action_comment")
@patch("forwarding_utils.add_control_buttons")
@patch("forwarding_utils.forward_to_subchannel")
class ForwardAndAddInlineKeyboardTest(TestCase):
	def test_default(self, mock_forward_to_subchannel, mock_add_control_buttons, mock_add_next_action_comment,
					 mock_update_main_message_content, mock_get_updated_post_data, mock_add_user,
					 mock_get_main_message_sender, *args):
		mock_bot = Mock(spec=TeleBot)
		main_channel_id = -10087654321
		main_message_id = 452
		user_id = 875135
		user_tags = ["CC", "DD"]
		config_utils.USER_TAGS = {"AA": 2163156, "CC": user_id, "DD": user_id}
		mock_message = test_helper.create_mock_message("", [], main_channel_id, main_message_id)
		updated = mock_get_updated_post_data.return_value
		mock_get_main_message_sender.return_value = user_id

		forwarding_utils.forward_and_add_inline_keyboard(mock_bot, mock_message, True)
		mock_get_main_message_sender.assert_called_once_with(main_channel_id, main_message_id)
		mock_add_user.assert_has_calls([call(user_tags[0]), call(user_tags[1])])
		mock_get_updated_post_data.assert_called_once_with()
		mock_update_main_message_content.assert_called_once_with(mock_bot, ANY, updated, mock_message)
		mock_add_next_action_comment.assert_called_once_with(mock_bot, updated)
		mock_add_control_buttons.assert_called_once_with(mock_bot, updated, ANY)
		mock_forward_to_subchannel.assert_called_once_with(mock_bot, updated, ANY)

	def test_user_no_workspace_member(self, mock_forward_to_subchannel, mock_add_control_buttons, mock_add_next_action_comment,
					 mock_update_main_message_content, mock_get_updated_post_data, mock_add_user,
					 mock_get_main_message_sender, *args):
		mock_bot = Mock(spec=TeleBot)
		main_channel_id = -10087654321
		main_message_id = 452
		user_id = 875127
		user_tags = ["CC", "DD"]
		config_utils.USER_TAGS = {"AA": 2163156, "CC": user_id, "DD": user_id}
		mock_message = test_helper.create_mock_message("", [], main_channel_id, main_message_id)
		updated = mock_get_updated_post_data.return_value
		mock_get_main_message_sender.return_value = user_id

		forwarding_utils.forward_and_add_inline_keyboard(mock_bot, mock_message, True)
		mock_get_main_message_sender.assert_called_once_with(main_channel_id, main_message_id)
		mock_add_user.assert_not_called()
		mock_get_updated_post_data.assert_called_once_with()
		mock_update_main_message_content.assert_called_once_with(mock_bot, ANY, updated, mock_message)
		mock_add_next_action_comment.assert_called_once_with(mock_bot, updated)
		mock_add_control_buttons.assert_called_once_with(mock_bot, updated, ANY)
		mock_forward_to_subchannel.assert_called_once_with(mock_bot, updated, ANY)

	def test_empty_user_tag(self, mock_forward_to_subchannel, mock_add_control_buttons, mock_add_next_action_comment,
							mock_update_main_message_content, mock_get_updated_post_data, mock_add_user,
							mock_get_main_message_sender, *args):
		mock_bot = Mock(spec=TeleBot)
		main_channel_id = -10087654321
		main_message_id = 452
		user_id = 875135
		config_utils.USER_TAGS = {"AA": 2163156, "CC": 2163156, "DD": 2163156}
		mock_message = test_helper.create_mock_message("", [], main_channel_id, main_message_id)
		mock_get_main_message_sender.return_value = user_id
		updated = mock_get_updated_post_data.return_value

		forwarding_utils.forward_and_add_inline_keyboard(mock_bot, mock_message, True)
		mock_get_main_message_sender.assert_called_once_with(main_channel_id, main_message_id)
		mock_add_user.assert_not_called()
		mock_get_updated_post_data.assert_called_once_with()
		mock_update_main_message_content.assert_called_once_with(mock_bot, ANY, updated, mock_message)
		mock_add_next_action_comment.assert_called_once_with(mock_bot, updated)
		mock_add_control_buttons.assert_called_once_with(mock_bot, updated, ANY)
		mock_forward_to_subchannel.assert_called_once_with(mock_bot, updated, ANY)

	@patch("utils.get_key_by_value")
	def test_empty_sender(self, mock_get_keys_by_value, mock_forward_to_subchannel, mock_add_control_buttons,
						  mock_add_next_action_comment, mock_update_main_message_content, mock_get_updated_post_data,
						  mock_add_user, mock_get_main_message_sender, *args):
		mock_bot = Mock(spec=TeleBot)
		main_channel_id = -10087654321
		main_message_id = 452
		mock_message = test_helper.create_mock_message("", [], main_channel_id, main_message_id)
		updated = mock_get_updated_post_data.return_value
		mock_get_main_message_sender.return_value = None

		forwarding_utils.forward_and_add_inline_keyboard(mock_bot, mock_message, True)
		mock_get_main_message_sender.assert_called_once_with(main_channel_id, main_message_id)
		mock_get_keys_by_value.assert_not_called()
		mock_add_user.assert_not_called()
		mock_get_updated_post_data.assert_called_once_with()
		mock_update_main_message_content.assert_called_once_with(mock_bot, ANY, updated, mock_message)
		mock_add_next_action_comment.assert_called_once_with(mock_bot, updated)
		mock_add_control_buttons.assert_called_once_with(mock_bot, updated, ANY)
		mock_forward_to_subchannel.assert_called_once_with(mock_bot, updated, ANY)

	@patch("utils.get_key_by_value")
	def test_new_ticket_false(self, mock_get_keys_by_value, mock_forward_to_subchannel, mock_add_control_buttons,
							  mock_add_next_action_comment, mock_update_main_message_content, mock_get_updated_post_data,
							  mock_add_user, mock_get_main_message_sender, *args):
		mock_bot = Mock(spec=TeleBot)
		main_channel_id = -10087654321
		main_message_id = 452
		mock_message = test_helper.create_mock_message("", [], main_channel_id, main_message_id)
		updated = mock_get_updated_post_data.return_value

		forwarding_utils.forward_and_add_inline_keyboard(mock_bot, mock_message, False)
		mock_get_main_message_sender.assert_not_called()
		mock_get_keys_by_value.assert_not_called()
		mock_add_user.assert_not_called()
		mock_get_updated_post_data.assert_called_once_with()
		mock_update_main_message_content.assert_called_once_with(mock_bot, ANY, updated, mock_message)
		mock_add_next_action_comment.assert_called_once_with(mock_bot, updated)
		mock_add_control_buttons.assert_called_once_with(mock_bot, updated, ANY)
		mock_forward_to_subchannel.assert_called_once_with(mock_bot, updated, ANY)


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
		self.assertEqual(mock_call.data, f"{state},{settings_keyboard['data']}")


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
		mock_call2.message.reply_markup = Mock(spec=InlineKeyboardMarkup)
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
		mock_message1.reply_markup = Mock(spec=InlineKeyboardMarkup)
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


@patch("hashtag_data.HashtagData.__init__", return_value=None)
@patch("config_utils.USER_TAGS", {"AA": 1, "BB": 2, "FF": 3, "NN": 4, "DD": 5})
@patch("user_utils.get_member_ids_channel", return_value=[1, 2, 3, 5])
@patch("hashtag_data.HashtagData.get_assigned_user", return_value="BB")
@patch("hashtag_data.HashtagData.get_followed_users", return_value=["AA", "DD"])
@patch("utils.create_callback_str")
class GenerateCcButtonsTest(TestCase):
	def test_default(self, mock_create_callback_str, mock_get_followed_users,
					 mock_get_assigned_user, *args):
		main_channel_id = -10012345678
		mock_message = test_helper.create_mock_message("", [], main_channel_id)

		result = forwarding_utils.generate_cc_buttons(mock_message)
		mock_get_assigned_user.assert_called_once_with()
		mock_get_followed_users.assert_called_once_with()
		mock_create_callback_str.assert_has_calls([
			call(forwarding_utils.CALLBACK_PREFIX, forwarding_utils.CB_TYPES.TOGGLE_CC, "AA"),
			call(forwarding_utils.CALLBACK_PREFIX, forwarding_utils.CB_TYPES.TOGGLE_CC, "FF"),
			call(forwarding_utils.CALLBACK_PREFIX, forwarding_utils.CB_TYPES.TOGGLE_CC, "DD"),
		])
		self.assertEqual(result.keyboard[0][0].text, "#AA" + config_utils.BUTTON_TEXTS["CHECK"])
		self.assertEqual(result.keyboard[0][1].text, "#FF")
		self.assertEqual(result.keyboard[0][2].text, "#DD" + config_utils.BUTTON_TEXTS["CHECK"])

	def test_no_tags(self, mock_create_callback_str, mock_get_followed_users,
					 mock_get_assigned_user, *args):
		main_channel_id = -10012345678
		mock_message = test_helper.create_mock_message("", [], main_channel_id)
		config_utils.USER_TAGS = {}

		result = forwarding_utils.generate_cc_buttons(mock_message)
		mock_get_assigned_user.assert_called_once_with()
		mock_get_followed_users.assert_called_once_with()
		mock_create_callback_str.assert_not_called()
		self.assertEqual(result, None)


@patch("hashtag_data.HashtagData.__init__", return_value=None)
@patch("utils.create_callback_str", return_value="")
@patch("hashtag_data.HashtagData.get_priority_number", return_value=2)
@patch("hashtag_data.HashtagData.get_assigned_user", return_value="BB")
@patch("forwarding_utils.get_subchannels_forwarding_data", return_value=["AA 1", "AA 2", "AA 3",
																		 	   "BB 1", "BB 2", "BB 3"])
class GenerateSubchannelButtonsTest(TestCase):
	def test_default(self, mock_get_subchannels_forwarding_data, mock_get_assigned_user, mock_get_priority_number,
					 mock_create_callback_str, *args):
		channel_id = -10012345678
		message_id = 325
		mock_message = test_helper.create_mock_message("", [], channel_id, message_id)
		callback_calls = []
		for i in mock_get_subchannels_forwarding_data.return_value:
			callback_calls.append(call(forwarding_utils.CALLBACK_PREFIX, forwarding_utils.CB_TYPES.CHANGE_SUBCHANNEL, i))
			if (i == "BB 2"):
				callback_calls.append(call(forwarding_utils.CALLBACK_PREFIX, forwarding_utils.CB_TYPES.SAVE))

		forwarding_utils.generate_subchannel_buttons(mock_message)
		mock_get_subchannels_forwarding_data.assert_called_once_with(channel_id)
		mock_get_assigned_user.assert_called_once_with()
		mock_get_priority_number.assert_called_once_with()
		mock_create_callback_str.assert_has_calls(callback_calls)
		self.assertEqual(mock_create_callback_str.call_count, len(callback_calls))


@patch("user_utils.get_member_ids_channel", return_value=[1, 2, 3, 5])
@patch("config_utils.USER_TAGS", {"AA": 1, "BB": 2, "FF": 3, "NN": 4, "DD": 5})
class GetSubchannelsForwardingData(TestCase):
	def test_default(self, *args):
		channel_id = -10012345678
		result = forwarding_utils.get_subchannels_forwarding_data(channel_id)
		self.assertEqual(result, [
			"AA 1", "AA 2", "AA 3",
			"BB 1", "BB 2", "BB 3",
			"FF 1", "FF 2", "FF 3",
			"DD 1", "DD 2", "DD 3"
		])

	def test_no_tags(self, *args):
		channel_id = -10012345678
		config_utils.USER_TAGS = {}

		result = forwarding_utils.get_subchannels_forwarding_data(channel_id)
		self.assertEqual(result, [])


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


@patch("logging.info")
@patch("time.sleep")
@patch("forwarding_utils.delete_forwarded_message")
@patch("utils.update_forwarded_fields")
@patch("utils.get_forwarded_from_id")
@patch("core_api.get_messages")
@patch("db_utils.get_copied_messages_existing_main_from_copied_channel")
@patch("db_utils.get_main_message_ids")
@patch("utils.get_last_message")
@patch("db_utils.get_all_individual_channels")
class GetInvalidTicketIdsTest(TestCase):
	def test_default(self, mock_get_all_individual_channels, mock_get_last_message, mock_get_main_message_ids,
					 mock_get_copied_messages_existing_main_from_copied_channel, mock_get_messages, mock_get_forwarded_from_id,
					 mock_update_forwarded_fields, mock_delete_forwarded_message, mock_sleep, mock_info, *args):
		mock_bot = Mock(spec=TeleBot)
		channels_data = [(-10012345678, "{\"settings_message_id\": 12}"), (-10087654321, "{}")]
		channel_messages = {-10012345678: {"last": 25, "settings": 12, "main": [], "copied": [15, 17, 18, 20, 22, 24, 25], "empty": [2, 4, 6, 7], "service": [1, 10], "forwarded": [8, 9, 19, 21], "no_keyboard": [3, 5, 12]},
							-10087654321: {"last": 18, "settings": 0, "main": [10, 11, 12], "copied": [15, 16, 17, 18], "empty": [5, 6], "service": [1, 8], "forwarded": [7, 13, 14], "no_keyboard": [2, 3]}}
		mock_get_all_individual_channels.return_value = channels_data
		mock_get_last_message.side_effect = lambda _, channel_id: channel_messages[channel_id]["last"]
		mock_get_copied_messages_existing_main_from_copied_channel.side_effect = lambda channel_id: channel_messages[channel_id]["copied"]
		mock_get_main_message_ids.side_effect = lambda channel_id: channel_messages[channel_id]['main']
		get_message_calls = []
		sleep_calls = []
		info_calls = [call("Deleting invalid ticket ids"),]
		delete_forwarded_message_calls = []
		update_forwarded_fields_count_calls = 0
		get_forwarded_from_id_calls = 0
		mock_get_messages.side_effect = lambda channel_id, a, b, message_ids: [Mock(id=i, empty=(True if i in channel_messages[channel_id]["empty"] else None),
																					   chat=Mock(id=channel_id),
																					   service=(True if i in channel_messages[channel_id]["service"] else None),
																					   reply_markup=(True if i not in channel_messages[channel_id]["no_keyboard"] else None)) for i in message_ids]
		mock_get_forwarded_from_id.side_effect = lambda message: True if message.id in channel_messages[message.chat.id]["forwarded"] else None
		for ch_id in channel_messages:
			count_calls = 0
			message_ids = [i for i in range(1, channel_messages[ch_id]["last"] + 1) if i not in channel_messages[ch_id]["copied"] and i not in channel_messages[ch_id]["main"] and i != channel_messages[ch_id]["settings"]]
			get_message_calls.append(call(ch_id, 0, 50, message_ids=message_ids))
			info_calls.append(call(f"Checking channel {ch_id}"))
			for message_id in message_ids:
				if (message_id not in channel_messages[ch_id]["empty"] and message_id not in channel_messages[ch_id]["service"]
						and message_id not in channel_messages[ch_id]["no_keyboard"]):
					get_forwarded_from_id_calls += 1
					if message_id not in channel_messages[ch_id]["forwarded"]:
						sleep_calls.append(call(config_utils.DELAY_AFTER_ONE_SCAN))
						update_forwarded_fields_count_calls += 1
						count_calls += 1
						delete_forwarded_message_calls.append(call(mock_bot, ch_id, message_id))
						info_calls.append(call(f"Deleted invalid ticket {message_id} in channel {ch_id}"))

			info_calls.append(call(f"Count deleted invalid tickets in channel {ch_id} is {count_calls}"))


		forwarding_utils.get_invalid_ticket_ids(mock_bot)
		mock_get_all_individual_channels.assert_called_once_with()
		mock_get_last_message.assert_has_calls([call(mock_bot, -10012345678), call(mock_bot, -10087654321)])
		self.assertEqual(mock_get_last_message.call_count, len(channels_data))
		mock_get_copied_messages_existing_main_from_copied_channel.assert_has_calls([call(-10012345678), call(-10087654321)])
		self.assertEqual(mock_get_copied_messages_existing_main_from_copied_channel.call_count, len(channels_data))
		mock_get_main_message_ids.assert_has_calls([call(-10012345678), call(-10087654321)])
		self.assertEqual(mock_get_main_message_ids.call_count, len(channels_data))
		mock_get_messages.assert_has_calls(get_message_calls)
		self.assertEqual(mock_get_messages.call_count, len(get_message_calls))
		self.assertEqual(mock_get_forwarded_from_id.call_count, get_forwarded_from_id_calls)
		self.assertEqual(mock_update_forwarded_fields.call_count, update_forwarded_fields_count_calls)
		mock_delete_forwarded_message.assert_has_calls(delete_forwarded_message_calls)
		self.assertEqual(mock_delete_forwarded_message.call_count, len(delete_forwarded_message_calls))
		mock_sleep.assert_has_calls(sleep_calls)
		self.assertEqual(mock_sleep.call_count, len(sleep_calls))
		mock_info.assert_has_calls(info_calls)
		self.assertEqual(mock_info.call_count, len(info_calls))

	def test_none_messages(self, mock_get_all_individual_channels, mock_get_last_message, mock_get_main_message_ids,
					 mock_get_copied_messages_existing_main_from_copied_channel, mock_get_messages, mock_get_forwarded_from_id,
					 mock_update_forwarded_fields, mock_delete_forwarded_message, mock_sleep, mock_info, *args):
		mock_bot = Mock(spec=TeleBot)
		channels_data = [(-10012345678, "{\"settings_message_id\": 12}"), (-10087654321, "{}")]
		channel_messages = {-10012345678: {"last": 25, "settings": 12, "main": [], "copied": [15, 17, 18, 20, 22, 24, 25], "empty": [2, 4, 6, 7], "service": [1, 10], "forwarded": [8, 9, 19, 21], "no_keyboard": [3, 5, 12]},
							-10087654321: {"last": 18, "settings": 0, "main": [10, 11, 12], "copied": [15, 16, 17, 18], "empty": [5, 6], "service": [1, 8], "forwarded": [7, 13, 14], "no_keyboard": [2, 3]}}
		mock_get_all_individual_channels.return_value = channels_data
		mock_get_last_message.side_effect = lambda _, channel_id: channel_messages[channel_id]["last"]
		mock_get_copied_messages_existing_main_from_copied_channel.side_effect = lambda channel_id: channel_messages[channel_id]["copied"]
		mock_get_main_message_ids.side_effect = lambda channel_id: channel_messages[channel_id]['main']
		get_message_calls = []
		info_calls = [call("Deleting invalid ticket ids"),]
		mock_get_messages.return_value = None
		mock_get_forwarded_from_id.side_effect = lambda message: True if message.id in channel_messages[message.chat.id]["forwarded"] else None
		for ch_id in channel_messages:
			info_calls.append(call(f"Checking channel {ch_id}"))
			message_ids = [i for i in range(1, channel_messages[ch_id]["last"] + 1) if i not in channel_messages[ch_id]["copied"] and i not in channel_messages[ch_id]["main"] and i != channel_messages[ch_id]["settings"]]
			get_message_calls.append(call(ch_id, 0, 50, message_ids=message_ids))
			info_calls.append(call(f"Can't get messages in channel {ch_id}, scanning of invalid tickets is skipped"))

		forwarding_utils.get_invalid_ticket_ids(mock_bot)
		mock_get_all_individual_channels.assert_called_once_with()
		mock_get_last_message.assert_has_calls([call(mock_bot, -10012345678), call(mock_bot, -10087654321)])
		self.assertEqual(mock_get_last_message.call_count, len(channels_data))
		mock_get_copied_messages_existing_main_from_copied_channel.assert_has_calls([call(-10012345678), call(-10087654321)])
		self.assertEqual(mock_get_copied_messages_existing_main_from_copied_channel.call_count, len(channels_data))
		mock_get_main_message_ids.assert_has_calls([call(-10012345678), call(-10087654321)])
		self.assertEqual(mock_get_main_message_ids.call_count, len(channels_data))
		mock_get_messages.assert_has_calls(get_message_calls)
		self.assertEqual(mock_get_messages.call_count, len(get_message_calls))
		mock_get_forwarded_from_id.assert_not_called()
		mock_update_forwarded_fields.assert_not_called()
		mock_delete_forwarded_message.assert_not_called()
		mock_sleep.assert_not_called()
		mock_info.assert_has_calls(info_calls)
		self.assertEqual(mock_info.call_count, len(info_calls))

	def test_none_last_msg(self, mock_get_all_individual_channels, mock_get_last_message, mock_get_main_message_ids,
					 mock_get_copied_messages_existing_main_from_copied_channel, mock_get_messages, mock_get_forwarded_from_id,
					 mock_update_forwarded_fields, mock_delete_forwarded_message, mock_sleep, mock_info, *args):
		mock_bot = Mock(spec=TeleBot)
		channels_data = [(-10012345678, "{\"settings_message_id\": 12}"), (-10087654321, "{}")]
		mock_get_all_individual_channels.return_value = channels_data
		mock_get_last_message.return_value = None
		info_calls = [call("Deleting invalid ticket ids"),]

		for ch_id in [-10012345678, -10087654321]:
			info_calls.append(call(f"Can't get last message in channel {ch_id}, scanning of invalid tickets is skipped"))

		forwarding_utils.get_invalid_ticket_ids(mock_bot)
		mock_get_all_individual_channels.assert_called_once_with()
		mock_get_last_message.assert_has_calls([call(mock_bot, -10012345678), call(mock_bot, -10087654321)])
		self.assertEqual(mock_get_last_message.call_count, len(channels_data))
		mock_get_copied_messages_existing_main_from_copied_channel.assert_not_called()
		mock_get_main_message_ids.assert_not_called()
		mock_get_messages.assert_not_called()
		mock_get_forwarded_from_id.assert_not_called()
		mock_update_forwarded_fields.assert_not_called()
		mock_delete_forwarded_message.assert_not_called()
		mock_sleep.assert_not_called()
		mock_info.assert_has_calls(info_calls)
		self.assertEqual(mock_info.call_count, len(info_calls))


@patch("hashtag_data.HashtagData.__init__", return_value=None)
@patch("channel_manager.set_settings_message_id")
@patch("channel_manager.update_settings_message")
@patch("utils.mark_message_for_deletion")
@patch("channel_manager.get_settings_message_id", return_value=156)
@patch("db_utils.update_copied_message_id")
@patch("forwarding_utils.generate_control_buttons")
@patch("utils.edit_message_content")
@patch("db_utils.get_main_message_from_copied", return_value=(18, -10087654321))
@patch("logging.info")
@patch("utils.get_message_content_by_id", side_effect=lambda _, chat_id, message_id: test_helper.create_mock_message("", [], chat_id, message_id))
@patch("db_utils.get_oldest_copied_message", return_value=160)
@patch("forwarding_utils.update_copied_message")
@patch("db_utils.delete_copied_message")
@patch("utils.delete_message")
@patch("db_utils.get_newest_copied_message", return_value=321)
class DeleteForwardedMessageTest(TestCase):
	def test_delete_newest_message(self, mock_get_newest_copied_message, mock_delete_message, mock_delete_copied_message,
								   mock_update_copied_message, *args):
		mock_bot = Mock(spec=TeleBot)
		channel_id = -10012345678
		message_id = 321

		forwarding_utils.delete_forwarded_message(mock_bot, channel_id, message_id)
		mock_get_newest_copied_message.assert_has_calls([call(channel_id), call(channel_id)])
		mock_delete_message.assert_called_once_with(mock_bot, chat_id=channel_id, message_id=message_id)
		mock_delete_copied_message.assert_called_once_with(message_id, channel_id)
		mock_update_copied_message.assert_called_once_with(mock_bot, channel_id, 321)

	def test_delete_message(self, mock_get_newest_copied_message, mock_delete_message, mock_delete_copied_message,
								   mock_update_copied_message, *args):
		mock_bot = Mock(spec=TeleBot)
		channel_id = -10012345678
		message_id = 123

		forwarding_utils.delete_forwarded_message(mock_bot, channel_id, message_id)
		mock_get_newest_copied_message.assert_called_once_with(channel_id)
		mock_delete_message.assert_called_once_with(mock_bot, chat_id=channel_id, message_id=message_id)
		mock_delete_copied_message.assert_called_once_with(message_id, channel_id)
		mock_update_copied_message.assert_not_called()

	def test_delete_message_with_error_cant_deleted(self, mock_get_newest_copied_message, mock_delete_message,
													mock_delete_copied_message, mock_update_copied_message,
													mock_get_oldest_copied_message, mock_get_message_content_by_id,
													mock_info, mock_get_main_message_from_copied,
													mock_edit_message_content, mock_generate_control_buttons,
													mock_update_copied_message_id, mock_get_settings_message_id,
													mock_mark_message_for_deletion, mock_update_settings_message,
													mock_set_settings_message_id, *args):
		mock_bot = Mock(spec=TeleBot)
		channel_id = -10012345678
		message_id = 185
		mock_delete_message.side_effect = ApiTelegramException("content", "", {"error_code": 400,
															"description": "Bad Request: message can't be deleted"})
		mock_message = test_helper.create_mock_message("", [], channel_id, message_id)
		mock_message_oldest = test_helper.create_mock_message("", [], channel_id, mock_get_oldest_copied_message.return_value)
		mock_get_message_content_by_id.side_effect = lambda _, chat_id, m_id: mock_message_oldest if m_id != message_id else mock_message

		forwarding_utils.delete_forwarded_message(mock_bot, channel_id, message_id)
		mock_get_newest_copied_message.assert_has_calls([call(channel_id), call(channel_id)])
		mock_delete_message.assert_called_once_with(mock_bot, chat_id=channel_id, message_id=message_id)
		mock_get_oldest_copied_message.assert_called_once_with(channel_id)
		mock_get_message_content_by_id.assert_has_calls([call(mock_bot, channel_id, mock_get_oldest_copied_message.return_value),
														 call(mock_bot, channel_id, message_id)])
		mock_get_main_message_from_copied.assert_called_once_with(mock_get_oldest_copied_message.return_value, channel_id)
		mock_generate_control_buttons.assert_called_once_with(ANY, mock_message_oldest)
		mock_edit_message_content.assert_called_once_with(mock_bot, mock_message, text="", reply_markup=mock_generate_control_buttons.return_value,
														  chat_id=channel_id, message_id=message_id, entities=[])
		mock_delete_copied_message.assert_called_once_with(message_id, channel_id)
		mock_update_copied_message_id.assert_called_once_with(mock_get_oldest_copied_message.return_value, channel_id, message_id)
		mock_get_settings_message_id.assert_called_once_with(channel_id)
		mock_mark_message_for_deletion.assert_called_once_with(mock_bot, channel_id, mock_get_settings_message_id.return_value)
		mock_update_settings_message.assert_called_once_with(mock_bot, channel_id, mock_get_oldest_copied_message.return_value)
		mock_set_settings_message_id.assert_called_once_with(channel_id, mock_get_oldest_copied_message.return_value)
		mock_info.assert_not_called()
		mock_update_copied_message.assert_called_once_with(mock_bot, channel_id, mock_get_newest_copied_message.return_value)


	def test_delete_message_with_error_cant_deleted_oldest_message(self, mock_get_newest_copied_message, mock_delete_message,
													mock_delete_copied_message, mock_update_copied_message,
													mock_get_oldest_copied_message, mock_get_message_content_by_id,
													mock_info, mock_get_main_message_from_copied,
													mock_edit_message_content, mock_generate_control_buttons,
													mock_update_copied_message_id, mock_get_settings_message_id,
													mock_mark_message_for_deletion, mock_update_settings_message,
													mock_set_settings_message_id, *args):
		mock_bot = Mock(spec=TeleBot)
		channel_id = -10012345678
		message_id = 160
		mock_delete_message.side_effect = ApiTelegramException("content", "", {"error_code": 400,
															"description": "Bad Request: message can't be deleted"})
		mock_message = test_helper.create_mock_message("", [], channel_id, message_id)
		mock_message_oldest = test_helper.create_mock_message("", [], channel_id, mock_get_oldest_copied_message.return_value)
		mock_get_message_content_by_id.side_effect = lambda _, chat_id, m_id: mock_message_oldest if m_id != message_id else mock_message

		forwarding_utils.delete_forwarded_message(mock_bot, channel_id, message_id)
		mock_get_newest_copied_message.assert_has_calls([call(channel_id), call(channel_id)])
		mock_delete_message.assert_called_once_with(mock_bot, chat_id=channel_id, message_id=message_id)
		mock_get_oldest_copied_message.assert_called_once_with(channel_id)
		mock_get_message_content_by_id.assert_has_calls([call(mock_bot, channel_id, mock_get_oldest_copied_message.return_value),
														 call(mock_bot, channel_id, message_id)])
		mock_get_main_message_from_copied.assert_called_once_with(mock_get_oldest_copied_message.return_value, channel_id)
		mock_generate_control_buttons.assert_not_called()
		mock_edit_message_content.assert_not_called()
		mock_delete_copied_message.assert_called_once_with(message_id, channel_id)
		mock_update_copied_message_id.assert_not_called()
		mock_get_settings_message_id.assert_called_once_with(channel_id)
		mock_mark_message_for_deletion.assert_called_once_with(mock_bot, channel_id, mock_get_settings_message_id.return_value)
		mock_update_settings_message.assert_called_once_with(mock_bot, channel_id, mock_get_oldest_copied_message.return_value)
		mock_set_settings_message_id.assert_called_once_with(channel_id, mock_get_oldest_copied_message.return_value)
		mock_info.assert_not_called()
		mock_update_copied_message.assert_called_once_with(mock_bot, channel_id, mock_get_newest_copied_message.return_value)


	def test_delete_message_with_error_cant_deleted_without_oldest_message(self, mock_get_newest_copied_message, mock_delete_message,
													mock_delete_copied_message, mock_update_copied_message,
													mock_get_oldest_copied_message, mock_get_message_content_by_id,
													mock_info, mock_get_main_message_from_copied,
													mock_edit_message_content, mock_generate_control_buttons,
													mock_update_copied_message_id, mock_get_settings_message_id,
													mock_mark_message_for_deletion, mock_update_settings_message,
													mock_set_settings_message_id, *args):
		mock_bot = Mock(spec=TeleBot)
		channel_id = -10012345678
		message_id = 185
		mock_delete_message.side_effect = ApiTelegramException("content", "", {"error_code": 400,
															"description": "Bad Request: message can't be deleted"})
		mock_message = test_helper.create_mock_message("", [], channel_id, message_id)
		mock_get_oldest_copied_message.return_value = None
		mock_message_oldest = test_helper.create_mock_message("", [], channel_id, mock_get_oldest_copied_message.return_value)
		mock_get_message_content_by_id.side_effect = lambda _, chat_id, m_id: mock_message_oldest if m_id != message_id else mock_message

		forwarding_utils.delete_forwarded_message(mock_bot, channel_id, message_id)
		mock_get_newest_copied_message.assert_called_once_with(channel_id)
		mock_delete_message.assert_called_once_with(mock_bot, chat_id=channel_id, message_id=message_id)
		mock_get_oldest_copied_message.assert_called_once_with(channel_id)
		mock_get_message_content_by_id.assert_called_once_with(mock_bot, channel_id, message_id)
		mock_get_main_message_from_copied.assert_called_once_with(mock_get_oldest_copied_message.return_value, channel_id)
		mock_generate_control_buttons.assert_not_called()
		mock_delete_copied_message.assert_called_once_with(message_id, channel_id)
		mock_edit_message_content.assert_called_once_with(mock_bot, mock_message, text=config_utils.TO_DELETE_MSG_TEXT,
														  chat_id=channel_id, message_id=message_id, entities=None)
		mock_update_copied_message_id.assert_not_called()
		mock_get_settings_message_id.assert_not_called()
		mock_mark_message_for_deletion.assert_not_called()
		mock_update_settings_message.assert_not_called()
		mock_set_settings_message_id.assert_not_called()
		mock_info.assert_not_called()
		mock_update_copied_message.assert_not_called()


	def test_delete_message_with_error_cant_deleted_before_oldest(self, mock_get_newest_copied_message, mock_delete_message,
													mock_delete_copied_message, mock_update_copied_message,
													mock_get_oldest_copied_message, mock_get_message_content_by_id,
													mock_info, mock_get_main_message_from_copied,
													mock_edit_message_content, mock_generate_control_buttons,
													mock_update_copied_message_id, mock_get_settings_message_id,
													mock_mark_message_for_deletion, mock_update_settings_message,
													mock_set_settings_message_id, *args):
		mock_bot = Mock(spec=TeleBot)
		channel_id = -10012345678
		message_id = 158
		mock_delete_message.side_effect = ApiTelegramException("content", "", {"error_code": 400,
															"description": "Bad Request: message can't be deleted"})
		mock_message = test_helper.create_mock_message("", [], channel_id, message_id)
		mock_message_oldest = test_helper.create_mock_message("", [], channel_id, mock_get_oldest_copied_message.return_value)
		mock_get_message_content_by_id.side_effect = lambda _, chat_id, m_id: mock_message_oldest if m_id != message_id else mock_message

		forwarding_utils.delete_forwarded_message(mock_bot, channel_id, message_id)
		mock_get_newest_copied_message.assert_has_calls([call(channel_id), call(channel_id)])
		mock_delete_message.assert_called_once_with(mock_bot, chat_id=channel_id, message_id=message_id)
		mock_get_oldest_copied_message.assert_called_once_with(channel_id)
		mock_get_message_content_by_id.assert_has_calls([call(mock_bot, channel_id, mock_get_oldest_copied_message.return_value),
														 call(mock_bot, channel_id, message_id)])
		mock_get_main_message_from_copied.assert_called_once_with(mock_get_oldest_copied_message.return_value, channel_id)
		mock_generate_control_buttons.assert_not_called()
		mock_delete_copied_message.assert_called_once_with(message_id, channel_id)
		mock_edit_message_content.assert_not_called()
		mock_update_copied_message_id.assert_not_called()
		mock_get_settings_message_id.assert_called_once_with(channel_id)
		mock_mark_message_for_deletion.assert_called_once_with(mock_bot, channel_id, mock_get_settings_message_id.return_value)
		mock_update_settings_message.assert_called_once_with(mock_bot, channel_id, message_id)
		mock_set_settings_message_id.assert_called_once_with(channel_id, message_id)
		mock_info.assert_not_called()
		mock_update_copied_message.assert_called_once_with(mock_bot, channel_id, mock_get_newest_copied_message.return_value)


	def test_delete_message_with_error_cant_deleted_before_oldest_and_settings(self, mock_get_newest_copied_message, mock_delete_message,
													mock_delete_copied_message, mock_update_copied_message,
													mock_get_oldest_copied_message, mock_get_message_content_by_id,
													mock_info, mock_get_main_message_from_copied,
													mock_edit_message_content, mock_generate_control_buttons,
													mock_update_copied_message_id, mock_get_settings_message_id,
													mock_mark_message_for_deletion, mock_update_settings_message,
													mock_set_settings_message_id, *args):
		mock_bot = Mock(spec=TeleBot)
		channel_id = -10012345678
		message_id = 150
		mock_delete_message.side_effect = ApiTelegramException("content", "", {"error_code": 400,
															"description": "Bad Request: message can't be deleted"})
		mock_message = test_helper.create_mock_message("", [], channel_id, message_id)
		mock_message_oldest = test_helper.create_mock_message("", [], channel_id, mock_get_oldest_copied_message.return_value)
		mock_get_message_content_by_id.side_effect = lambda _, chat_id, m_id: mock_message_oldest if m_id != message_id else mock_message

		forwarding_utils.delete_forwarded_message(mock_bot, channel_id, message_id)
		mock_get_newest_copied_message.assert_called_once_with(channel_id)
		mock_delete_message.assert_called_once_with(mock_bot, chat_id=channel_id, message_id=message_id)
		mock_get_oldest_copied_message.assert_called_once_with(channel_id)
		mock_get_message_content_by_id.assert_has_calls([call(mock_bot, channel_id, mock_get_oldest_copied_message.return_value),
														 call(mock_bot, channel_id, message_id)])
		mock_get_main_message_from_copied.assert_called_once_with(mock_get_oldest_copied_message.return_value, channel_id)
		mock_generate_control_buttons.assert_not_called()
		mock_delete_copied_message.assert_called_once_with(message_id, channel_id)
		mock_update_copied_message_id.assert_not_called()
		mock_get_settings_message_id.assert_called_once_with(channel_id)
		mock_edit_message_content.assert_called_once_with(mock_bot, mock_message, text=config_utils.TO_DELETE_MSG_TEXT,
														  chat_id=channel_id, message_id=message_id, entities=None)
		mock_mark_message_for_deletion.assert_not_called()
		mock_update_settings_message.assert_not_called()
		mock_set_settings_message_id.assert_not_called()
		mock_info.assert_not_called()
		mock_update_copied_message.assert_not_called()


	def test_delete_message_with_error_cant_deleted_before_settings(self, mock_get_newest_copied_message, mock_delete_message,
													mock_delete_copied_message, mock_update_copied_message,
													mock_get_oldest_copied_message, mock_get_message_content_by_id,
													mock_info, mock_get_main_message_from_copied,
													mock_edit_message_content, mock_generate_control_buttons,
													mock_update_copied_message_id, mock_get_settings_message_id,
													mock_mark_message_for_deletion, mock_update_settings_message,
													mock_set_settings_message_id, *args):
		mock_bot = Mock(spec=TeleBot)
		channel_id = -10012345678
		message_id = 154
		mock_get_oldest_copied_message.return_value = 150
		mock_delete_message.side_effect = ApiTelegramException("content", "", {"error_code": 400,
															"description": "Bad Request: message can't be deleted"})
		mock_message = test_helper.create_mock_message("", [], channel_id, message_id)
		mock_message_oldest = test_helper.create_mock_message("", [], channel_id, mock_get_oldest_copied_message.return_value)
		mock_get_message_content_by_id.side_effect = lambda _, chat_id, m_id: mock_message_oldest if m_id != message_id else mock_message

		forwarding_utils.delete_forwarded_message(mock_bot, channel_id, message_id)
		mock_get_newest_copied_message.assert_called_once_with(channel_id)
		mock_delete_message.assert_called_once_with(mock_bot, chat_id=channel_id, message_id=message_id)
		mock_get_oldest_copied_message.assert_called_once_with(channel_id)
		mock_get_message_content_by_id.assert_has_calls([call(mock_bot, channel_id, mock_get_oldest_copied_message.return_value),
														 call(mock_bot, channel_id, message_id)])
		mock_get_main_message_from_copied.assert_called_once_with(mock_get_oldest_copied_message.return_value, channel_id)
		mock_generate_control_buttons.assert_called_once_with(ANY, mock_message_oldest)
		mock_edit_message_content.assert_has_calls([call(mock_bot, mock_message, text="", reply_markup=mock_generate_control_buttons.return_value,
														  chat_id=channel_id, message_id=message_id, entities=[]),
													call(mock_bot, mock_message, text=config_utils.TO_DELETE_MSG_TEXT,
														  chat_id=channel_id, message_id=mock_get_oldest_copied_message.return_value, entities=None)])
		mock_delete_copied_message.assert_called_once_with(message_id, channel_id)
		mock_update_copied_message_id.assert_called_once_with(mock_get_oldest_copied_message.return_value, channel_id, message_id)
		mock_get_settings_message_id.assert_called_once_with(channel_id)
		mock_mark_message_for_deletion.assert_not_called()
		mock_update_settings_message.assert_not_called()
		mock_set_settings_message_id.assert_not_called()
		mock_info.assert_not_called()
		mock_update_copied_message.assert_not_called()




if __name__ == "__main__":
	main()

