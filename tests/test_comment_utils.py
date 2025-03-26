from unittest import TestCase, main
from unittest.mock import patch, call, Mock, ANY
from telebot import TeleBot
from telebot.apihelper import ApiTelegramException

from comment_utils import CommentDispatcher
from tests import test_helper

comment_dispatcher = CommentDispatcher()
comment_dispatcher.__NEXT_ACTION_TEXT_PREFIX = "::"
comment_dispatcher.__NEXT_ACTION_COMMENT_PREFIX = ":"


@patch("utils.get_main_message_content_by_id")
@patch("hashtag_data.HashtagData.__init__", return_value=None)
@patch("forwarding_utils.generate_control_buttons")
@patch("db_utils.insert_or_update_current_next_action")
@patch("db_utils.update_previous_next_action")
class UpdateNextActionTest(TestCase):
	@patch("hashtag_data.HashtagData.is_last_line_contains_only_hashtags", return_value=False)
	@patch("utils.get_post_content", return_value=("test::qwe", []))
	@patch("utils.set_post_content")
	@patch("comment_utils.CommentDispatcher.apply_hashtags")
	def test_update_next_action(self, mock_apply_hashtags, mock_set_post_content, *args):
		main_channel_id = 123
		main_message_id = 34
		next_action = "next"
		mock_bot = Mock(spec=TeleBot)
		mock_message = test_helper.create_mock_message(":next", [])

		comment_dispatcher.update_next_action(mock_bot, main_message_id, main_channel_id, next_action, mock_message)
		mock_set_post_content.assert_called_once_with(ANY, "test::next", [])
		mock_apply_hashtags.assert_called_once_with(mock_bot, mock_message, main_message_id, main_channel_id, ANY)

	@patch("hashtag_data.HashtagData.is_last_line_contains_only_hashtags", return_value=True)
	@patch("utils.get_post_content")
	@patch("utils.set_post_content")
	@patch("comment_utils.CommentDispatcher.apply_hashtags")
	def test_last_line_hashtags(self, mock_apply_hashtags, mock_set_post_content, mock_get_post_content, *args):
		text = f"text::asdf\n#o #cc #p"
		entities = test_helper.create_hashtag_entity_list(text)
		mock_get_post_content.return_value = (text, entities)

		main_channel_id = 123
		main_message_id = 34
		next_action = "next"
		mock_bot = Mock(spec=TeleBot)
		mock_message = test_helper.create_mock_message(":next", [])

		comment_dispatcher.update_next_action(mock_bot, main_message_id, main_channel_id, next_action, mock_message)
		mock_set_post_content.assert_called_once_with(ANY, "text::next\n#o #cc #p", entities)
		mock_apply_hashtags.assert_called_once_with(mock_bot, mock_message, main_message_id, main_channel_id, ANY)

	@patch("hashtag_data.HashtagData.is_last_line_contains_only_hashtags", return_value=True)
	@patch("utils.get_post_content")
	@patch("utils.set_post_content")
	@patch("comment_utils.CommentDispatcher.apply_hashtags")
	def test_update_entity_offsets(self, mock_apply_hashtags, mock_set_post_content, mock_get_post_content, *args):
		text = f"text::previous next action\n#o #cc #p"
		entities = test_helper.create_hashtag_entity_list(text)
		mock_get_post_content.return_value = (text, entities)

		main_channel_id = 123
		main_message_id = 34
		next_action = "next"
		mock_bot = Mock(spec=TeleBot)
		mock_message = test_helper.create_mock_message(":next", [])

		comment_dispatcher.update_next_action(mock_bot, main_message_id, main_channel_id, next_action, mock_message)
		mock_set_post_content.assert_called_once_with(ANY, "text::next\n#o #cc #p", entities)
		self.assertEqual(entities[0].offset, 11)
		self.assertEqual(entities[1].offset, 14)
		self.assertEqual(entities[2].offset, 18)
		mock_apply_hashtags.assert_called_once_with(mock_bot, mock_message, main_message_id, main_channel_id, ANY)


@patch("comment_utils.DISCUSSION_CHAT_DATA", {3333: 1111})
class SaveCommentTest(TestCase):
	@patch("utils.get_main_message_content_by_id")
	@patch("db_utils.insert_comment_message")
	@patch("db_utils.get_comment_top_parent")
	@patch("db_utils.get_main_from_discussion_message", return_value=33)
	@patch("db_utils.set_ticket_update_time")
	@patch("interval_updating_utils.update_older_message")
	@patch("comment_utils.CommentDispatcher.update_user_last_interaction")
	@patch("comment_utils.CommentDispatcher.apply_hashtags")
	@patch("comment_utils.CommentDispatcher.update_next_action")
	def test_update_next_action(self, mock_update_next_action, mock_apply_hashtag, *args):
		mock_bot = Mock(spec=TeleBot)
		msg_data = test_helper.create_mock_message(":next action", [])
		msg_data.chat = Mock(id=1111)
		msg_data.message_id = 11
		msg_data.reply_to_message = Mock(message_id=22)
		msg_data.from_user = Mock(id=12345)

		comment_dispatcher.save_comment(mock_bot, msg_data)
		mock_update_next_action.assert_called_once_with(mock_bot, 33, 3333, "next action", msg_data)
		mock_apply_hashtag.assert_not_called()

	@patch("utils.get_main_message_content_by_id")
	@patch("db_utils.insert_comment_message")
	@patch("db_utils.get_comment_top_parent")
	@patch("db_utils.get_main_from_discussion_message", return_value=33)
	@patch("db_utils.set_ticket_update_time")
	@patch("interval_updating_utils.update_older_message")
	@patch("comment_utils.CommentDispatcher.update_user_last_interaction")
	@patch("comment_utils.CommentDispatcher.apply_hashtags")
	@patch("comment_utils.CommentDispatcher.update_next_action")
	def test_apply_hashtag(self, mock_update_next_action, mock_apply_hashtag, *args):
		mock_bot = Mock(spec=TeleBot)
		msg_data = test_helper.create_mock_message("next action", [])
		msg_data.chat = Mock(id=1111)
		msg_data.message_id = 11
		msg_data.reply_to_message = Mock(message_id=22)
		msg_data.from_user = Mock(id=12345)

		comment_dispatcher.save_comment(mock_bot, msg_data)
		mock_apply_hashtag.assert_called_once_with(mock_bot, msg_data, 33, 3333)
		mock_update_next_action.assert_not_called()


@patch("forwarding_utils.generate_control_buttons")
@patch("db_utils.delete_comment_message")
@patch("db_utils.get_reply_comment_message")
@patch("db_utils.get_main_from_discussion_message")
@patch("utils.get_main_message_content_by_id")
@patch("utils.edit_message_keyboard")
@patch("hashtag_data.HashtagData.__init__", return_value=None)
@patch("forwarding_utils.forward_to_subchannel")
@patch("logging.info")
@patch("logging.error")
class  DeleteCommentTest(TestCase):
	def test_delete_comment(self, mock_error, mock_info, mock_forward_to_subchannel, mock_hashtag_data,
							mock_edit_message_keyboard, mock_get_main_message_content_by_id,
							mock_get_main_from_discussion_message, mock_get_reply_comment_message,
							mock_delete_comment_message, mock_generate_control_buttons, *args):
		mock_bot = Mock(spec=TeleBot)
		main_channel_id = -10012345678
		main_message_id = 125
		chat_id = -10087654321
		message_id = 1255
		reply_comment = 1245
		mock_main_message = test_helper.create_mock_message("", [], main_channel_id, main_message_id)
		mock_get_reply_comment_message.return_value = reply_comment
		mock_get_main_from_discussion_message.return_value = main_message_id
		mock_get_main_message_content_by_id.return_value = mock_main_message


		comment_dispatcher.delete_comment(mock_bot, main_channel_id, chat_id, message_id)
		mock_delete_comment_message.assert_called_once_with(message_id, chat_id)
		mock_get_reply_comment_message.assert_called_once_with(message_id, chat_id)
		mock_get_main_from_discussion_message.assert_called_once_with(reply_comment, main_channel_id)
		mock_get_main_message_content_by_id.assert_called_once_with(mock_bot, main_channel_id, main_message_id)
		mock_generate_control_buttons.assert_called_once_with(ANY, mock_main_message)
		mock_edit_message_keyboard.assert_called_once_with(mock_bot, mock_main_message,
														   mock_generate_control_buttons.return_value)
		mock_hashtag_data.assert_called_once_with(mock_main_message, main_channel_id)
		mock_forward_to_subchannel.assert_called_once_with(mock_bot, mock_main_message, ANY)
		mock_error.assert_not_called()
		mock_info.assert_called_once_with(f"Delete comment {message_id} for message {main_message_id}")

	def test_delete_comment_error_get_main_message_id(self, mock_error, mock_info, mock_forward_to_subchannel, mock_hashtag_data,
							mock_edit_message_keyboard, mock_get_main_message_content_by_id,
							mock_get_main_from_discussion_message, mock_get_reply_comment_message,
							mock_delete_comment_message, mock_generate_control_buttons, *args):
		mock_bot = Mock(spec=TeleBot)
		main_channel_id = -10012345678
		main_message_id = 125
		chat_id = -10087654321
		message_id = 1255
		reply_comment = 1245
		mock_main_message = test_helper.create_mock_message("", [], main_channel_id, main_message_id)
		mock_get_reply_comment_message.return_value = reply_comment
		mock_get_main_from_discussion_message.return_value = main_message_id
		mock_get_main_message_content_by_id.side_effect = ApiTelegramException("content", "", {"error_code": 400,
																							   "description": "Bad Request: message to forward not found"})
		mock_get_main_message_content_by_id.return_value = mock_main_message


		comment_dispatcher.delete_comment(mock_bot, main_channel_id, chat_id, message_id)
		mock_delete_comment_message.assert_called_once_with(message_id, chat_id)
		mock_get_reply_comment_message.assert_called_once_with(message_id, chat_id)
		mock_get_main_from_discussion_message.assert_called_once_with(reply_comment, main_channel_id)
		mock_get_main_message_content_by_id.assert_called_once_with(mock_bot, main_channel_id, main_message_id)
		mock_edit_message_keyboard.assert_not_called()
		mock_hashtag_data.assert_not_called()
		mock_forward_to_subchannel.assert_not_called()
		mock_generate_control_buttons.assert_not_called()
		mock_error.assert_called_once_with(f"Error during getting main message - {mock_get_main_message_content_by_id.side_effect}")
		mock_info.assert_called_once_with(f"Delete comment {message_id} for message {main_message_id}")

	def test_delete_comment_empty_message_content(self, mock_error, mock_info, mock_forward_to_subchannel, mock_hashtag_data,
							mock_edit_message_keyboard, mock_get_main_message_content_by_id,
							mock_get_main_from_discussion_message, mock_get_reply_comment_message,
							mock_delete_comment_message, *args):
		mock_bot = Mock(spec=TeleBot)
		main_channel_id = -10012345678
		main_message_id = 125
		chat_id = -10087654321
		message_id = 1255
		reply_comment = 1245
		mock_get_reply_comment_message.return_value = reply_comment
		mock_get_main_from_discussion_message.return_value = main_message_id
		mock_get_main_message_content_by_id.return_value = None


		comment_dispatcher.delete_comment(mock_bot, main_channel_id, chat_id, message_id)
		mock_delete_comment_message.assert_called_once_with(message_id, chat_id)
		mock_get_reply_comment_message.assert_called_once_with(message_id, chat_id)
		mock_get_main_from_discussion_message.assert_called_once_with(reply_comment, main_channel_id)
		mock_get_main_message_content_by_id.assert_called_once_with(mock_bot, main_channel_id, main_message_id)
		mock_edit_message_keyboard.assert_not_called()
		mock_hashtag_data.assert_not_called()
		mock_forward_to_subchannel.assert_not_called()
		mock_error.assert_not_called()
		mock_info.assert_called_once_with(f"Delete comment {message_id} for message {main_message_id}")

	def test_delete_comment_empty_main_message_id(self, mock_error, mock_info, mock_forward_to_subchannel, mock_hashtag_data,
							mock_edit_message_keyboard, mock_get_main_message_content_by_id,
							mock_get_main_from_discussion_message, mock_get_reply_comment_message,
							mock_delete_comment_message, *args):
		mock_bot = Mock(spec=TeleBot)
		main_channel_id = -10012345678
		main_message_id = None
		chat_id = -10087654321
		message_id = 1255
		reply_comment = 1245
		mock_get_reply_comment_message.return_value = reply_comment
		mock_get_main_from_discussion_message.return_value = main_message_id

		comment_dispatcher.delete_comment(mock_bot, main_channel_id, chat_id, message_id)
		mock_delete_comment_message.assert_called_once_with(message_id, chat_id)
		mock_get_reply_comment_message.assert_called_once_with(message_id, chat_id)
		mock_get_main_from_discussion_message.assert_called_once_with(reply_comment, main_channel_id)
		mock_get_main_message_content_by_id.assert_not_called()
		mock_edit_message_keyboard.assert_not_called()
		mock_hashtag_data.assert_not_called()
		mock_forward_to_subchannel.assert_not_called()
		mock_error.assert_not_called()
		mock_info.assert_called_once_with(f"Delete comment {message_id} for message {main_message_id}")

	def test_delete_comment_empty_reply_comment(self, mock_error, mock_info, mock_forward_to_subchannel, mock_hashtag_data,
							mock_edit_message_keyboard, mock_get_main_message_content_by_id,
							mock_get_main_from_discussion_message, mock_get_reply_comment_message,
							mock_delete_comment_message, *args):
		mock_bot = Mock(spec=TeleBot)
		main_channel_id = -10012345678
		main_message_id = 125
		chat_id = -10087654321
		message_id = 1255
		reply_comment = None
		mock_get_reply_comment_message.return_value = reply_comment

		comment_dispatcher.delete_comment(mock_bot, main_channel_id, chat_id, message_id)
		mock_delete_comment_message.assert_not_called()
		mock_get_reply_comment_message.assert_called_once_with(message_id, chat_id)
		mock_get_main_from_discussion_message.assert_not_called()
		mock_get_main_message_content_by_id.assert_not_called()
		mock_edit_message_keyboard.assert_not_called()
		mock_hashtag_data.assert_not_called()
		mock_forward_to_subchannel.assert_not_called()
		mock_error.assert_not_called()
		mock_info.assert_not_called()


class AddNextActionCommentTest(TestCase):
	@patch("db_utils.get_next_action_text", return_value="test action")
	@patch("db_utils.insert_or_update_current_next_action")
	@patch("utils.get_post_content", return_value=("test::test action", []))
	@patch("utils.add_comment_to_ticket")
	def test_unchanged_next_action(self, mock_add_comment_to_ticket, *args):
		mock_bot = Mock(spec=TeleBot)
		post_data = test_helper.create_mock_message("", [])
		post_data.chat = Mock(id=1111)
		post_data.message_id = 11

		comment_dispatcher.add_next_action_comment(mock_bot, post_data)
		mock_add_comment_to_ticket.assert_not_called()

	@patch("db_utils.get_next_action_text", return_value="next action")
	@patch("db_utils.insert_or_update_current_next_action")
	@patch("utils.get_post_content", return_value=("test::current next action", []))
	@patch("utils.add_comment_to_ticket")
	def test_unchanged_next_action(self, mock_add_comment_to_ticket, *args):
		mock_bot = Mock(spec=TeleBot)
		post_data = test_helper.create_mock_message("", [])
		post_data.chat = Mock(id=1111)
		post_data.message_id = 11

		comment_dispatcher.add_next_action_comment(mock_bot, post_data)
		mock_add_comment_to_ticket.assert_called_once_with(mock_bot, post_data, ":current next action")

	@patch("hashtag_data.HashtagData.is_last_line_contains_only_hashtags", return_value=True)
	@patch("db_utils.get_next_action_text", return_value="next action")
	@patch("db_utils.insert_or_update_current_next_action")
	@patch("utils.get_post_content")
	@patch("utils.add_comment_to_ticket")
	def test_last_line_hashtags(self, mock_add_comment_to_ticket, mock_get_post_content, *args):
		text = "test::current next action\n #o #aa #p1"
		entities = test_helper.create_hashtag_entity_list(text)
		mock_get_post_content.return_value = (text, entities)

		mock_bot = Mock(spec=TeleBot)
		post_data = test_helper.create_mock_message("", [])
		post_data.chat = Mock(id=1111)
		post_data.message_id = 11

		comment_dispatcher.add_next_action_comment(mock_bot, post_data)
		mock_add_comment_to_ticket.assert_called_once_with(mock_bot, post_data, ":current next action")


@patch("utils.get_main_message_content_by_id")
@patch("hashtag_data.HashtagData.__init__", return_value=None)
@patch("db_utils.get_channel_user_tags", return_value=["aa", "bb", "cc"])
@patch("comment_utils.HASHTAGS", {"OPENED": "o", "CLOSED": "x", "SCHEDULED": "s"})
@patch("hashtag_data.SCHEDULED_TAG", "s")
class ApplyHashtagsTest(TestCase):
	@patch("forwarding_utils.update_message_and_forward_to_subchannels")
	@patch("hashtag_data.HashtagData.set_status_tag")
	@patch("utils.get_post_content")
	def test_apply_close_tag(self, mock_get_post_content, mock_set_status_tag, mock_update_message_and_forward_to_subchannels, *args):
		text = "close the ticket #x"
		entities = test_helper.create_hashtag_entity_list(text)
		mock_get_post_content.return_value = (text, entities)

		mock_bot = Mock(spec=TeleBot)
		msg_data = test_helper.create_mock_message(text, [])
		main_message_id = 123
		main_channel_id = 987654321

		comment_dispatcher.apply_hashtags(mock_bot, msg_data, main_message_id, main_channel_id)
		mock_set_status_tag.assert_called_once_with(False)
		mock_update_message_and_forward_to_subchannels.assert_called_once()

	@patch("forwarding_utils.update_message_and_forward_to_subchannels")
	@patch("hashtag_data.HashtagData.set_status_tag")
	@patch("utils.get_post_content")
	def test_apply_open_tag(self, mock_get_post_content, mock_set_status_tag, mock_update_message_and_forward_to_subchannels, *args):
		text = "close the ticket #o"
		entities = test_helper.create_hashtag_entity_list(text)
		mock_get_post_content.return_value = (text, entities)

		mock_bot = Mock(spec=TeleBot)
		msg_data = test_helper.create_mock_message(text, [])
		main_message_id = 123
		main_channel_id = 987654321

		comment_dispatcher.apply_hashtags(mock_bot, msg_data, main_message_id, main_channel_id)
		mock_set_status_tag.assert_called_once_with(True)
		mock_update_message_and_forward_to_subchannels.assert_called_once()

	@patch("forwarding_utils.update_message_and_forward_to_subchannels")
	@patch("hashtag_data.HashtagData.add_user")
	@patch("utils.get_post_content")
	def test_add_user_tags_to_followers(self, mock_get_post_content, mock_add_user, mock_update_message_and_forward_to_subchannels, *args):
		text = "add to followers #aa #bb"
		entities = test_helper.create_hashtag_entity_list(text)
		mock_get_post_content.return_value = (text, entities)

		mock_bot = Mock(spec=TeleBot)
		msg_data = test_helper.create_mock_message(text, [])
		main_message_id = 123
		main_channel_id = 987654321

		comment_dispatcher.apply_hashtags(mock_bot, msg_data, main_message_id, main_channel_id)
		mock_add_user.assert_has_calls([call("aa"), call("bb")])
		self.assertEqual(mock_add_user.call_count, 2)

		mock_update_message_and_forward_to_subchannels.assert_called_once()

	@patch("forwarding_utils.update_message_and_forward_to_subchannels")
	@patch("utils.get_post_content")
	def test_no_service_tags(self, mock_get_post_content, mock_update_message_and_forward_to_subchannels, *args):
		text = "add to followers #test_tag"
		entities = test_helper.create_hashtag_entity_list(text)
		mock_get_post_content.return_value = (text, entities)

		mock_bot = Mock(spec=TeleBot)
		msg_data = test_helper.create_mock_message(text, [])
		main_message_id = 123
		main_channel_id = 987654321

		comment_dispatcher.apply_hashtags(mock_bot, msg_data, main_message_id, main_channel_id)

		mock_update_message_and_forward_to_subchannels.assert_not_called()

	@patch("forwarding_utils.update_message_and_forward_to_subchannels")
	@patch("utils.get_post_content")
	def test_no_service_tags_with_post_data(self, mock_get_post_content, mock_update_message_and_forward_to_subchannels, *args):
		text = "add to followers #test_tag"
		entities = test_helper.create_hashtag_entity_list(text)
		mock_get_post_content.return_value = (text, entities)

		mock_bot = Mock(spec=TeleBot)
		msg_data = test_helper.create_mock_message(text, [], 1, 1)
		main_message_id = 123
		main_channel_id = 987654321

		comment_dispatcher.apply_hashtags(mock_bot, msg_data, main_message_id, main_channel_id, msg_data)

		mock_update_message_and_forward_to_subchannels.assert_called_once()

	@patch("forwarding_utils.update_message_and_forward_to_subchannels")
	@patch("hashtag_data.HashtagData.set_scheduled_tag")
	@patch("utils.get_post_content")
	def test_reschedule(self, mock_get_post_content, mock_set_scheduled_tag, mock_update_message_and_forward_to_subchannels, *args):
		text = "reschedule to #s 2024-01-02 12:00"
		entities = test_helper.create_hashtag_entity_list(text)
		mock_get_post_content.return_value = (text, entities)

		mock_bot = Mock(spec=TeleBot)
		msg_data = test_helper.create_mock_message(text, [])
		main_message_id = 123
		main_channel_id = 987654321

		comment_dispatcher.apply_hashtags(mock_bot, msg_data, main_message_id, main_channel_id)
		mock_set_scheduled_tag.assert_called_once_with("2024-01-02 12:00")
		mock_update_message_and_forward_to_subchannels.assert_called_once()

	@patch("forwarding_utils.update_message_and_forward_to_subchannels")
	@patch("hashtag_data.HashtagData.set_scheduled_tag")
	@patch("utils.get_post_content")
	def test_reschedule_without_time(self, mock_get_post_content, mock_set_scheduled_tag, mock_update_message_and_forward_to_subchannels, *args):
		text = "reschedule to #s 2024-01-02 asdf qwe"
		entities = test_helper.create_hashtag_entity_list(text)
		mock_get_post_content.return_value = (text, entities)

		mock_bot = Mock(spec=TeleBot)
		msg_data = test_helper.create_mock_message(text, [])
		main_message_id = 123
		main_channel_id = 987654321

		comment_dispatcher.apply_hashtags(mock_bot, msg_data, main_message_id, main_channel_id)
		mock_set_scheduled_tag.assert_called_once_with("2024-01-02 00:00")
		mock_update_message_and_forward_to_subchannels.assert_called_once()

	@patch("forwarding_utils.update_message_and_forward_to_subchannels")
	@patch("hashtag_data.HashtagData.set_scheduled_tag")
	@patch("utils.get_post_content")
	def test_reschedule_incorrect_minutes(self, mock_get_post_content, mock_set_scheduled_tag, mock_update_message_and_forward_to_subchannels, *args):
		text = "reschedule to #s 2024-01-02 12:235 asdf qwe"
		entities = test_helper.create_hashtag_entity_list(text)
		mock_get_post_content.return_value = (text, entities)

		mock_bot = Mock(spec=TeleBot)
		msg_data = test_helper.create_mock_message(text, [])
		main_message_id = 123
		main_channel_id = 987654321

		comment_dispatcher.apply_hashtags(mock_bot, msg_data, main_message_id, main_channel_id)
		mock_set_scheduled_tag.assert_called_once_with("2024-01-02 12:00")
		mock_update_message_and_forward_to_subchannels.assert_called_once()

	@patch("forwarding_utils.update_message_and_forward_to_subchannels")
	@patch("hashtag_data.HashtagData.set_scheduled_tag")
	@patch("utils.get_post_content")
	def test_scheduled_date_without_datetime(self, mock_get_post_content, mock_set_scheduled_tag, mock_update_message_and_forward_to_subchannels, *args):
		text = "reschedule to #s asdf qwe"
		entities = test_helper.create_hashtag_entity_list(text)
		mock_get_post_content.return_value = (text, entities)

		mock_bot = Mock(spec=TeleBot)
		msg_data = test_helper.create_mock_message(text, [])
		main_message_id = 123
		main_channel_id = 987654321

		comment_dispatcher.apply_hashtags(mock_bot, msg_data, main_message_id, main_channel_id)
		mock_set_scheduled_tag.assert_not_called()
		mock_update_message_and_forward_to_subchannels.assert_called_once()


if __name__ == "__main__":
	main()
