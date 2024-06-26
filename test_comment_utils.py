from unittest import TestCase, main
from unittest.mock import patch, Mock, ANY
from telebot import TeleBot

import comment_utils
import test_helper


@patch("utils.get_main_message_content_by_id")
@patch("hashtag_data.HashtagData.__init__", return_value=None)
@patch("forwarding_utils.generate_control_buttons")
@patch("db_utils.insert_or_update_current_next_action")
@patch("db_utils.update_previous_next_action")
@patch("comment_utils._NEXT_ACTION_TEXT_PREFIX", "::")
class UpdateNextActionTest(TestCase):
	@patch("utils.get_post_content", return_value=("test::qwe", []))
	@patch("utils.set_post_content")
	@patch("utils.edit_message_content")
	def test_update_next_action(self, mock_edit_message_content, mock_set_post_content, *args):
		main_channel_id = 123
		main_message_id = 34
		next_action = "next"
		mock_bot = Mock(spec=TeleBot)

		comment_utils.update_next_action(mock_bot, main_message_id, main_channel_id, next_action)
		mock_set_post_content.assert_called_once_with(ANY, "test::next", [])
		mock_edit_message_content.assert_called_once_with(mock_bot, ANY, chat_id=main_channel_id,
	                           message_id=main_message_id, reply_markup=ANY)

	@patch("utils.get_post_content")
	@patch("utils.set_post_content")
	@patch("utils.edit_message_content")
	def test_last_line_hashtags(self, mock_edit_message_content, mock_set_post_content, mock_get_post_content, *args):
		text = f"text::asdf\n#o #cc #p"
		entities = test_helper.create_hashtag_entity_list(text)
		mock_get_post_content.return_value = (text, entities)

		main_channel_id = 123
		main_message_id = 34
		next_action = "next"
		mock_bot = Mock(spec=TeleBot)

		comment_utils.update_next_action(mock_bot, main_message_id, main_channel_id, next_action)
		mock_set_post_content.assert_called_once_with(ANY, "text::next\n#o #cc #p", entities)
		mock_edit_message_content.assert_called_once_with(mock_bot, ANY, chat_id=main_channel_id,
	                           message_id=main_message_id, reply_markup=ANY)


@patch("comment_utils._NEXT_ACTION_COMMENT_PREFIX", ":")
@patch("comment_utils.DISCUSSION_CHAT_DATA", {3333: 1111})
class SaveCommentTest(TestCase):
	@patch("utils.get_main_message_content_by_id")
	@patch("db_utils.insert_comment_message")
	@patch("db_utils.get_comment_top_parent")
	@patch("db_utils.get_main_from_discussion_message", return_value=33)
	@patch("db_utils.set_ticket_update_time")
	@patch("interval_updating_utils.update_older_message")
	@patch("daily_reminder.update_user_last_interaction")
	@patch("comment_utils.update_next_action")
	def test_update_next_action(self, mock_update_next_action, *args):
		mock_bot = Mock(spec=TeleBot)
		msg_data = test_helper.create_mock_message(":next action", [])
		msg_data.chat = Mock(id=1111)
		msg_data.message_id = 11
		msg_data.reply_to_message = Mock(message_id=22)
		msg_data.from_user = Mock(id=12345)

		comment_utils.save_comment(mock_bot, msg_data)
		mock_update_next_action.assert_called_once_with(mock_bot, 33, 3333, "next action")


@patch("comment_utils._NEXT_ACTION_COMMENT_PREFIX", ":")
@patch("comment_utils._NEXT_ACTION_TEXT_PREFIX", "::")
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

		comment_utils.add_next_action_comment(mock_bot, post_data)
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

		comment_utils.add_next_action_comment(mock_bot, post_data)
		mock_add_comment_to_ticket.assert_called_once_with(mock_bot, post_data, ":current next action")

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

		comment_utils.add_next_action_comment(mock_bot, post_data)
		mock_add_comment_to_ticket.assert_called_once_with(mock_bot, post_data, ":current next action")


if __name__ == "__main__":
	main()
