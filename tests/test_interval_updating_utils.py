from unittest import TestCase, main
from unittest.mock import Mock, patch, call

from telebot import TeleBot
from telebot.apihelper import ApiTelegramException

import interval_updating_utils
from tests import test_helper


# TODO: tests
@patch("utils.get_last_message")
@patch("db_utils.get_comment_deleted_message_ids", return_value=[])
@patch("logging.error")
@patch("logging.info")
@patch("time.sleep")
@patch("interval_updating_utils.store_discussion_message")
class CheckDiscussionMessagesTest(TestCase):
	@patch("interval_updating_utils._UPDATE_STATUS", True)
	def test_check_discussion_messages(self, mock_store_discussion_message, mock_sleep, mock_info, mock_error,
									   mock_get_comment_deleted_message_ids, mock_get_last_message, *args):
		main_channel_id = -10012345678
		discussion_chat_id = -10087541256
		message_id = 125
		mock_bot = Mock(spec=TeleBot)
		mock_get_last_message.return_value = message_id
		manager = Mock()
		manager.attach_mock(mock_sleep, 'a')
		manager.attach_mock(mock_store_discussion_message, 'a')
		calls = []
		for i in range(125, 0, -1):
			calls.append(call.a(4))
			calls.append(call.a(mock_bot, main_channel_id, i, discussion_chat_id))

		interval_updating_utils.check_discussion_messages(mock_bot, main_channel_id, discussion_chat_id)
		mock_get_last_message.assert_called_once_with(mock_bot, discussion_chat_id)
		mock_get_comment_deleted_message_ids.assert_called_once_with(discussion_chat_id, list(range(1, 126)))
		mock_info.assert_has_calls([call(f"Starting to check discussion channel: {discussion_chat_id}"),
									call(f"Discussion channel check completed in {discussion_chat_id}")])
		mock_error.assert_not_called()
		self.assertEqual(manager.mock_calls, calls)

	@patch("interval_updating_utils._UPDATE_STATUS", True)
	def test_check_discussion_messages_with_deleted(self, mock_store_discussion_message, mock_sleep, mock_info, mock_error,
									   mock_get_comment_deleted_message_ids, mock_get_last_message, *args):
		main_channel_id = -10012345678
		discussion_chat_id = -10087541256
		message_id = 125
		deleted_message =  [5, 10, 15, 20, 25]
		mock_bot = Mock(spec=TeleBot)
		mock_get_last_message.return_value = message_id
		mock_get_comment_deleted_message_ids.return_value = deleted_message
		manager = Mock()
		manager.attach_mock(mock_sleep, 'a')
		manager.attach_mock(mock_store_discussion_message, 'a')
		calls = []
		for i in range(125, 0, -1):
			if i not in deleted_message:
				calls.append(call.a(4))
				calls.append(call.a(mock_bot, main_channel_id, i, discussion_chat_id))

		interval_updating_utils.check_discussion_messages(mock_bot, main_channel_id, discussion_chat_id)
		mock_get_last_message.assert_called_once_with(mock_bot, discussion_chat_id)
		mock_get_comment_deleted_message_ids.assert_called_once_with(discussion_chat_id, list(range(1, 126)))
		mock_info.assert_has_calls([call(f"Starting to check discussion channel: {discussion_chat_id}"),
									call(f"Check comment 25 in chat {discussion_chat_id} was skipped because it's in db as deleted"),
									call(f"Check comment 20 in chat {discussion_chat_id} was skipped because it's in db as deleted"),
									call(f"Check comment 15 in chat {discussion_chat_id} was skipped because it's in db as deleted"),
									call(f"Check comment 10 in chat {discussion_chat_id} was skipped because it's in db as deleted"),
									call(f"Check comment 5 in chat {discussion_chat_id} was skipped because it's in db as deleted"),
									call(f"Discussion channel check completed in {discussion_chat_id}")])
		mock_error.assert_not_called()
		self.assertEqual(manager.mock_calls, calls)

	@patch("interval_updating_utils._UPDATE_STATUS", False)
	def test_check_discussion_messages_not_interval_check(self, mock_store_discussion_message, mock_sleep, mock_info, mock_error,
									   mock_get_comment_deleted_message_ids, mock_get_last_message, *args):
		main_channel_id = -10012345678
		discussion_chat_id = -10087541256
		message_id = 125
		mock_bot = Mock(spec=TeleBot)
		mock_get_last_message.return_value = message_id

		interval_updating_utils.check_discussion_messages(mock_bot, main_channel_id, discussion_chat_id)
		mock_get_last_message.assert_called_once_with(mock_bot, discussion_chat_id)
		mock_get_comment_deleted_message_ids.assert_called_once_with(discussion_chat_id, list(range(1, 126)))
		mock_sleep.assert_called_once_with(interval_updating_utils.DELAY_AFTER_ONE_SCAN)
		mock_info.assert_called_once_with(f"Starting to check discussion channel: {discussion_chat_id}")
		mock_error.assert_called_once_with(f"Discussion channel check stopped ({discussion_chat_id, message_id}) - Interval update stop requested")
		mock_store_discussion_message.assert_not_called()

	@patch("interval_updating_utils._UPDATE_STATUS", True)
	def test_check_discussion_messages_empty_chat(self, mock_store_discussion_message, mock_sleep, mock_info, mock_error,
									   mock_get_comment_deleted_message_ids, mock_get_last_message, *args):
		main_channel_id = -10012345678
		discussion_chat_id = -10087541256
		message_id = None
		mock_bot = Mock(spec=TeleBot)
		mock_get_last_message.return_value = message_id

		interval_updating_utils.check_discussion_messages(mock_bot, main_channel_id, discussion_chat_id)
		mock_get_last_message.assert_called_once_with(mock_bot, discussion_chat_id)
		mock_get_comment_deleted_message_ids.assert_not_called()
		mock_sleep.assert_not_called()
		mock_info.assert_not_called()
		mock_error.assert_not_called()
		mock_store_discussion_message.assert_not_called()


@patch("utils.get_main_message_content_by_id")
@patch("comment_utils.CommentDispatcher.delete_comment")
@patch("utils.get_forwarded_from_id")
@patch("db_utils.insert_or_update_discussion_message")
class StoreDiscussionMessageTest(TestCase):
	def test_store_discussion_message(self, mock_insert_or_update_discussion_message, mock_get_forwarded_from_id,
									  mock_delete_comment, mock_get_main_message_content_by_id, *args):
		mock_bot = Mock(spec=TeleBot)
		main_channel_id = -10012345678
		main_message_id = 6
		message_id = 12
		discussion_chat_id = -10085214763
		mock_message = test_helper.create_mock_message("", [], discussion_chat_id, message_id)
		mock_message.forward_from_message_id = main_message_id
		mock_get_main_message_content_by_id.return_value = mock_message
		mock_get_forwarded_from_id.return_value = main_channel_id


		interval_updating_utils.store_discussion_message(mock_bot, main_channel_id, message_id, discussion_chat_id)
		mock_get_main_message_content_by_id.assert_called_once_with(mock_bot, discussion_chat_id, message_id)
		mock_get_forwarded_from_id.assert_called_once_with(mock_message)
		mock_delete_comment.assert_not_called()
		mock_insert_or_update_discussion_message.assert_called_once_with(main_message_id, main_channel_id, message_id)

	def test_store_discussion_message_error_no_message(self, mock_insert_or_update_discussion_message, mock_get_forwarded_from_id,
									  mock_delete_comment, mock_get_main_message_content_by_id, *args):
		mock_bot = Mock(spec=TeleBot)
		main_channel_id = -10012345678
		message_id = 12
		discussion_chat_id = -10085214763
		mock_get_main_message_content_by_id.return_value = None
		mock_get_main_message_content_by_id.side_effect = ApiTelegramException("content", "", {"error_code": 400, "description" : "Bad Request: message to forward not found"})


		interval_updating_utils.store_discussion_message(mock_bot, main_channel_id, message_id, discussion_chat_id)
		mock_get_main_message_content_by_id.assert_called_once_with(mock_bot, discussion_chat_id, message_id)
		mock_get_forwarded_from_id.assert_not_called()
		mock_delete_comment.assert_called_once_with(mock_bot, main_channel_id, discussion_chat_id, message_id)
		mock_insert_or_update_discussion_message.assert_not_called()

	def test_store_discussion_message_no_forwarded(self, mock_insert_or_update_discussion_message, mock_get_forwarded_from_id,
									  mock_delete_comment, mock_get_main_message_content_by_id, *args):
		mock_bot = Mock(spec=TeleBot)
		main_channel_id = -10012345678
		main_message_id = 6
		message_id = 12
		discussion_chat_id = -10085214763
		mock_message = test_helper.create_mock_message("", [], discussion_chat_id, message_id)
		mock_message.forward_from_message_id = main_message_id
		mock_get_main_message_content_by_id.return_value = mock_message
		mock_get_forwarded_from_id.return_value = None


		interval_updating_utils.store_discussion_message(mock_bot, main_channel_id, message_id, discussion_chat_id)
		mock_get_main_message_content_by_id.assert_called_once_with(mock_bot, discussion_chat_id, message_id)
		mock_get_forwarded_from_id.assert_called_once_with(mock_message)
		mock_delete_comment.assert_not_called()
		mock_insert_or_update_discussion_message.assert_not_called()


if __name__ == "__main__":
	main()
