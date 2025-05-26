from unittest import TestCase, main
from unittest.mock import Mock, patch, call

from pyrogram.types import Message
from telebot import TeleBot
from telebot.apihelper import ApiTelegramException

import interval_updating_utils
import utils
from tests import test_helper


# TODO: tests
@patch("utils.get_last_message")
@patch("core_api.get_messages")
@patch("db_utils.get_comment_deleted_message_ids", return_value=[])
@patch("logging.error")
@patch("logging.info")
@patch("interval_updating_utils.store_discussion_message")
class CheckDiscussionMessagesTest(TestCase):
	@patch("interval_updating_utils._UPDATE_STATUS", True)
	def test_check_discussion_messages(self, mock_store_discussion_message, mock_info, mock_error,
									   mock_get_comment_deleted_message_ids, mock_get_messages,
									   mock_get_last_message, *args):
		main_channel_id = -10012345678
		discussion_chat_id = -10087541256
		message_id = 125
		mock_bot = Mock(spec=TeleBot)
		mock_get_last_message.return_value = message_id
		manager = Mock()
		manager.attach_mock(mock_store_discussion_message, 'a')
		calls = []
		message_ids = list(range(125, 0, -1))
		messages = [Mock(id=i) for i in message_ids]
		mock_get_messages.return_value = messages
		for i in messages:
			calls.append(call.a(mock_bot, main_channel_id, i, discussion_chat_id))

		interval_updating_utils.check_discussion_messages(mock_bot, main_channel_id, discussion_chat_id)
		mock_get_last_message.assert_called_once_with(mock_bot, discussion_chat_id)
		mock_get_comment_deleted_message_ids.assert_called_once_with(discussion_chat_id, list(range(1, 126)))
		mock_get_messages.assert_called_once_with(discussion_chat_id, 0, interval_updating_utils._EXPORT_BATCH_SIZE,
												  message_ids=message_ids)
		mock_info.assert_has_calls([call(f"Starting to check discussion channel: {discussion_chat_id}"),
									call(f"Discussion channel check completed in {discussion_chat_id}")])
		mock_error.assert_not_called()
		self.assertEqual(manager.mock_calls, calls)

	@patch("interval_updating_utils._UPDATE_STATUS", True)
	def test_check_discussion_messages_with_deleted(self, mock_store_discussion_message, mock_info, mock_error,
													mock_get_comment_deleted_message_ids, mock_get_messages,
													mock_get_last_message, *args):
		main_channel_id = -10012345678
		discussion_chat_id = -10087541256
		message_id = 125
		deleted_message =  [5, 10, 15, 20, 25]
		mock_bot = Mock(spec=TeleBot)
		mock_get_last_message.return_value = message_id
		mock_get_comment_deleted_message_ids.return_value = deleted_message
		manager = Mock()
		manager.attach_mock(mock_store_discussion_message, 'a')
		calls = []
		message_ids = [i for i in range(125, 0, -1) if i not in deleted_message]
		messages = [Mock(id=i) for i in message_ids]
		mock_get_messages.return_value = messages
		for i in messages:
			if i not in deleted_message:
				calls.append(call.a(mock_bot, main_channel_id, i, discussion_chat_id))


		interval_updating_utils.check_discussion_messages(mock_bot, main_channel_id, discussion_chat_id)
		mock_get_last_message.assert_called_once_with(mock_bot, discussion_chat_id)
		mock_get_comment_deleted_message_ids.assert_called_once_with(discussion_chat_id, list(range(1, 126)))
		mock_get_messages.assert_called_once_with(discussion_chat_id, 0, interval_updating_utils._EXPORT_BATCH_SIZE,
												  message_ids=message_ids)
		mock_info.assert_has_calls([call(f"Starting to check discussion channel: {discussion_chat_id}"),
									call(f"Discussion channel check completed in {discussion_chat_id}")])
		mock_error.assert_not_called()
		self.assertEqual(manager.mock_calls, calls)

	@patch("interval_updating_utils._UPDATE_STATUS", False)
	def test_check_discussion_messages_not_interval_check(self, mock_store_discussion_message, mock_info, mock_error,
														  mock_get_comment_deleted_message_ids, mock_get_messages,
														  mock_get_last_message, *args):
		main_channel_id = -10012345678
		discussion_chat_id = -10087541256
		message_id = 125
		mock_bot = Mock(spec=TeleBot)
		mock_get_last_message.return_value = message_id
		message_ids = list(range(125, 0, -1))
		messages = [Mock(id=i) for i in message_ids]
		mock_get_messages.return_value = messages

		interval_updating_utils.check_discussion_messages(mock_bot, main_channel_id, discussion_chat_id)
		mock_get_last_message.assert_called_once_with(mock_bot, discussion_chat_id)
		mock_get_comment_deleted_message_ids.assert_called_once_with(discussion_chat_id, list(range(1, 126)))
		mock_info.assert_called_once_with(f"Starting to check discussion channel: {discussion_chat_id}")
		mock_get_messages.assert_called_once_with(discussion_chat_id, 0, interval_updating_utils._EXPORT_BATCH_SIZE,
												  message_ids=message_ids)
		mock_error.assert_called_once_with(f"Discussion channel check stopped ({discussion_chat_id, message_id}) - Interval update stop requested")
		mock_store_discussion_message.assert_not_called()

	@patch("interval_updating_utils._UPDATE_STATUS", True)
	def test_check_discussion_messages_empty_chat(self, mock_store_discussion_message, mock_info, mock_error,
												  mock_get_comment_deleted_message_ids, mock_get_messages,
												  mock_get_last_message, *args):
		main_channel_id = -10012345678
		discussion_chat_id = -10087541256
		message_id = None
		mock_bot = Mock(spec=TeleBot)
		mock_get_last_message.return_value = message_id

		interval_updating_utils.check_discussion_messages(mock_bot, main_channel_id, discussion_chat_id)
		mock_get_last_message.assert_called_once_with(mock_bot, discussion_chat_id)
		mock_get_comment_deleted_message_ids.assert_not_called()
		mock_info.assert_not_called()
		mock_get_messages.assert_not_called()
		mock_error.assert_not_called()
		mock_store_discussion_message.assert_not_called()


@patch("utils.get_main_message_content_by_id")
@patch("comment_utils.CommentDispatcher.delete_comment")
@patch("time.sleep")
@patch("utils.get_forwarded_from_id")
@patch("db_utils.insert_or_update_discussion_message")
class StoreDiscussionMessageTest(TestCase):
	def test_store_discussion_message(self, mock_insert_or_update_discussion_message, mock_get_forwarded_from_id,
									  mock_sleep, mock_delete_comment, mock_get_main_message_content_by_id, *args):
		mock_bot = Mock(spec=TeleBot)
		main_channel_id = -10012345678
		main_message_id = 6
		message_id = 12
		discussion_chat_id = -10085214763
		mock_message = test_helper.create_mock_pyrogram_message("", [], discussion_chat_id, message_id)
		mock_message.forward_from_message_id = main_message_id
		mock_get_forwarded_from_id.return_value = main_channel_id


		interval_updating_utils.store_discussion_message(mock_bot, main_channel_id, mock_message, discussion_chat_id)
		mock_get_main_message_content_by_id.assert_not_called()
		mock_get_forwarded_from_id.assert_called_once_with(mock_message)
		mock_delete_comment.assert_not_called()
		mock_sleep.assert_not_called()
		mock_insert_or_update_discussion_message.assert_called_once_with(main_message_id, main_channel_id, message_id)

	def test_store_discussion_message_empty_message(self, mock_insert_or_update_discussion_message, mock_get_forwarded_from_id,
									  mock_sleep, mock_delete_comment, mock_get_main_message_content_by_id, *args):
		mock_bot = Mock(spec=TeleBot)
		main_channel_id = -10012345678
		main_message_id = 6
		message_id = 12
		discussion_chat_id = -10085214763
		mock_message = test_helper.create_mock_pyrogram_message("", [], discussion_chat_id, message_id)
		mock_message.forward_from_message_id = main_message_id
		mock_message.empty = True


		interval_updating_utils.store_discussion_message(mock_bot, main_channel_id, mock_message, discussion_chat_id)
		mock_get_main_message_content_by_id.assert_not_called()
		mock_delete_comment.assert_called_once_with(mock_bot, main_channel_id, discussion_chat_id, message_id)
		mock_sleep.assert_called_once_with(interval_updating_utils.DELAY_AFTER_ONE_SCAN)
		mock_get_forwarded_from_id.assert_not_called()
		mock_insert_or_update_discussion_message.assert_not_called()

	def test_store_discussion_message_no_forwarded(self, mock_insert_or_update_discussion_message, mock_get_forwarded_from_id,
									  mock_sleep, mock_delete_comment, mock_get_main_message_content_by_id, *args):
		mock_bot = Mock(spec=TeleBot)
		main_channel_id = -10012345678
		main_message_id = 6
		message_id = 12
		discussion_chat_id = -10085214763
		mock_message = test_helper.create_mock_pyrogram_message("", [], discussion_chat_id, message_id)
		mock_message.forward_from_message_id = main_message_id
		mock_get_forwarded_from_id.return_value = None


		interval_updating_utils.store_discussion_message(mock_bot, main_channel_id, mock_message, discussion_chat_id)
		mock_get_main_message_content_by_id.assert_not_called()
		mock_get_forwarded_from_id.assert_called_once_with(mock_message)
		mock_delete_comment.assert_not_called()
		mock_sleep.assert_not_called()
		mock_insert_or_update_discussion_message.assert_not_called()


@patch("logging.info")
@patch("db_utils.insert_or_update_channel_update_progress")
@patch("interval_updating_utils.update_by_bot")
@patch("interval_updating_utils.update_by_core")
@patch('db_utils.get_main_message_ids')
class CheckMainMessagesTest(TestCase):
	def test_five_messages(self, mock_get_main_message_ids, mock_update_by_core, mock_update_by_bot,
						mock_insert_or_update_channel_update_progress, mock_info, *args):
		mock_bot = Mock(spec=TeleBot)
		main_channel_id = -10012345678
		main_message_ids = [1, 2, 3, 5, 10]
		main_message_sorted = [10, 5, 3, 2, 1]
		mock_get_main_message_ids.return_value = main_message_ids.copy()


		interval_updating_utils.check_main_messages(mock_bot, main_channel_id)
		mock_get_main_message_ids.assert_called_once_with(main_channel_id)
		mock_update_by_core.assert_not_called()
		mock_update_by_bot.assert_called_once_with(mock_bot, main_channel_id, main_message_sorted)
		mock_insert_or_update_channel_update_progress.assert_called_once_with(main_channel_id, 0)
		mock_info.assert_called_once_with(f"Main channel check completed in {main_channel_id}")

	def test_messages_with_start_from_messages(self, mock_get_main_message_ids, mock_update_by_core, mock_update_by_bot,
						mock_insert_or_update_channel_update_progress, mock_info, *args):
		mock_bot = Mock(spec=TeleBot)
		main_channel_id = -10012345678
		start_from_message = 7
		main_message_ids = [1, 2, 5, 9, 7, 3, 10]
		main_message_sorted = [7, 5, 3, 2, 1]
		mock_get_main_message_ids.return_value = main_message_ids.copy()


		interval_updating_utils.check_main_messages(mock_bot, main_channel_id, start_from_message)
		mock_get_main_message_ids.assert_called_once_with(main_channel_id)
		mock_update_by_core.assert_not_called()
		mock_update_by_bot.assert_called_once_with(mock_bot, main_channel_id, main_message_sorted)
		mock_insert_or_update_channel_update_progress.assert_called_once_with(main_channel_id, 0)
		mock_info.assert_called_once_with(f"Main channel check completed in {main_channel_id}")

	def test_six_messages(self, mock_get_main_message_ids, mock_update_by_core, mock_update_by_bot,
						mock_insert_or_update_channel_update_progress, mock_info, *args):
		mock_bot = Mock(spec=TeleBot)
		main_channel_id = -10012345678
		main_message_ids = [1, 2, 3, 5, 7, 10]
		main_message_sorted = [10, 7, 5, 3, 2, 1]
		mock_get_main_message_ids.return_value = main_message_ids.copy()


		interval_updating_utils.check_main_messages(mock_bot, main_channel_id)
		mock_get_main_message_ids.assert_called_once_with(main_channel_id)
		mock_update_by_core.assert_called_once_with(mock_bot, main_channel_id, main_message_sorted)
		mock_update_by_bot.assert_not_called()
		mock_insert_or_update_channel_update_progress.assert_called_once_with(main_channel_id, 0)
		mock_info.assert_called_once_with(f"Main channel check completed in {main_channel_id}")

	def test_empty_messages(self, mock_get_main_message_ids, mock_update_by_core, mock_update_by_bot,
						mock_insert_or_update_channel_update_progress, mock_info, *args):
		mock_bot = Mock(spec=TeleBot)
		main_channel_id = -10012345678
		main_message_ids = []
		mock_get_main_message_ids.return_value = main_message_ids


		interval_updating_utils.check_main_messages(mock_bot, main_channel_id)
		mock_get_main_message_ids.assert_called_once_with(main_channel_id)
		mock_update_by_core.assert_not_called()
		mock_update_by_bot.assert_not_called()
		mock_insert_or_update_channel_update_progress.assert_not_called()
		mock_info.assert_not_called()


@patch("interval_updating_utils.update_interval_message", return_value=True)
@patch("core_api.get_messages")
class UpdateMessagesTest(TestCase):
	def test_update_by_core(self, mock_get_messages, mock_update_interval_message, *args):
		mock_bot = Mock(spec=TeleBot)
		main_channel_id = -10012345678
		message_ids = [1, 2, 3, 4, 5, 7, 9, 10]
		messages = [Mock(id=id) for id in message_ids]
		mock_get_messages.return_value = messages

		manager = Mock()
		manager.attach_mock(mock_update_interval_message, "a")
		expected_calls = []

		for message in messages:
			expected_calls.append(call.a(mock_bot, main_channel_id, message.id, message=message))

		interval_updating_utils.update_by_core(mock_bot, main_channel_id, message_ids)
		mock_get_messages.assert_called_once_with(main_channel_id, 0, interval_updating_utils._EXPORT_BATCH_SIZE, message_ids=message_ids)
		self.assertEqual(expected_calls, manager.mock_calls)

	def test_update_by_core_with_false_message(self, mock_get_messages, mock_update_interval_message, *args):
		mock_bot = Mock(spec=TeleBot)
		main_channel_id = -10012345678
		message_ids = [1, 2, 3, 4, 5, 7, 9, 10]
		messages = [Mock(id=id) for id in message_ids]
		mock_get_messages.return_value = messages
		mock_update_interval_message.return_value = False

		interval_updating_utils.update_by_core(mock_bot, main_channel_id, message_ids)
		mock_get_messages.assert_called_once_with(main_channel_id, 0, interval_updating_utils._EXPORT_BATCH_SIZE, message_ids=message_ids)
		mock_update_interval_message.assert_called_once_with(mock_bot, main_channel_id, 1, message=messages[0])

	def test_update_by_bot(self, mock_get_messages, mock_update_interval_message, *args):
		mock_bot = Mock(spec=TeleBot)
		main_channel_id = -10012345678
		main_message_ids = [1, 2, 3, 4, 5, 7, 9, 10]

		manager = Mock()
		manager.attach_mock(mock_update_interval_message, "a")
		expected_calls = []

		for main_message_id in main_message_ids:
			expected_calls.append(call.a(mock_bot, main_channel_id, main_message_id))

		interval_updating_utils.update_by_bot(mock_bot, main_channel_id, main_message_ids)
		mock_get_messages.assert_not_called()
		self.assertEqual(expected_calls, manager.mock_calls)

	def test_update_by_bot_with_false_message(self, mock_get_messages, mock_update_interval_message, *args):
		mock_bot = Mock(spec=TeleBot)
		main_channel_id = -10012345678
		main_message_ids = [1, 2, 3, 4, 5, 7, 9, 10]
		mock_update_interval_message.return_value = False

		interval_updating_utils.update_by_bot(mock_bot, main_channel_id, main_message_ids)
		mock_get_messages.assert_not_called()
		mock_update_interval_message.assert_called_once_with(mock_bot, main_channel_id, 1)


@patch("db_utils.insert_or_update_channel_update_progress")
@patch("interval_updating_utils.update_older_message")
@patch("time.sleep")
class UpdateIntervalMessageTest(TestCase):
	@patch("interval_updating_utils._UPDATE_STATUS", True)
	def test_update_interval_message(self, mock_sleep, mock_update_older_message,
									 mock_insert_or_update_channel_update_progress, *args):
		mock_bot = Mock(spec=TeleBot)
		main_channel_id = -10012345678
		current_msg_id = 4

		result = interval_updating_utils.update_interval_message(mock_bot, main_channel_id, current_msg_id)
		mock_sleep(interval_updating_utils.DELAY_AFTER_ONE_SCAN)
		mock_update_older_message.assert_called_once_with(mock_bot, main_channel_id, current_msg_id, forwarded_message=None)
		mock_insert_or_update_channel_update_progress.assert_called_once_with(main_channel_id, current_msg_id)
		self.assertEqual(result, True)

	@patch("interval_updating_utils._UPDATE_STATUS", True)
	def test_update_interval_message_with_message(self, mock_sleep, mock_update_older_message,
									 mock_insert_or_update_channel_update_progress, *args):
		mock_bot = Mock(spec=TeleBot)
		main_channel_id = -10012345678
		current_msg_id = 4
		mock_message = Mock(spec=Message)

		result = interval_updating_utils.update_interval_message(mock_bot, main_channel_id, current_msg_id, mock_message)
		mock_sleep(interval_updating_utils.DELAY_AFTER_ONE_SCAN)
		mock_update_older_message.assert_called_once_with(mock_bot, main_channel_id, current_msg_id, forwarded_message=mock_message)
		mock_insert_or_update_channel_update_progress.assert_called_once_with(main_channel_id, current_msg_id)
		self.assertEqual(result, True)

	@patch("logging.error")
	@patch("interval_updating_utils._UPDATE_STATUS", False)
	def test_update_interval_message_error(self, mock_error, mock_sleep, mock_update_older_message,
									 mock_insert_or_update_channel_update_progress, *args):
		mock_bot = Mock(spec=TeleBot)
		main_channel_id = -10012345678
		current_msg_id = 4

		result = interval_updating_utils.update_interval_message(mock_bot, main_channel_id, current_msg_id)
		mock_sleep(interval_updating_utils.DELAY_AFTER_ONE_SCAN)
		mock_update_older_message.assert_not_called()
		mock_insert_or_update_channel_update_progress.assert_not_called()
		mock_error.assert_called_once_with(f"Main channel check stopped ({main_channel_id, current_msg_id}) - Interval update stop requested")
		self.assertEqual(result, False)


@patch("forwarding_utils.forward_and_add_inline_keyboard")
@patch("post_link_utils.update_post_link")
@patch("utils.check_content_type", return_value=True)
@patch("forwarding_utils.delete_main_message")
@patch("utils.get_main_message_content_by_id")
@patch("logging.info")
@patch("db_utils.is_main_message_exists")
class UpdateOlderMessageTest(TestCase):
	def test_default(self, mock_is_main_message_exists, mock_info, mock_get_main_message_content_by_id,
					 mock_delete_main_message, mock_check_content_type, mock_update_post_link,
					 mock_forward_and_add_inline_keyboard, *args):
		mock_bot = Mock(spec=TeleBot)
		main_channel_id = -10012345678
		main_message_id = 123
		mock_message = test_helper.create_mock_message("", [], main_channel_id, main_message_id)
		mock_message.forward_from_message_id = main_message_id
		mock_message.forward_from_chat = mock_message.chat
		mock_get_main_message_content_by_id.return_value = mock_message

		result = interval_updating_utils.update_older_message(mock_bot, main_channel_id, main_message_id)
		mock_is_main_message_exists.assert_called_once_with(main_channel_id, main_message_id)
		mock_info.assert_not_called()
		mock_get_main_message_content_by_id.assert_called_once_with(mock_bot, main_channel_id, main_message_id)
		mock_delete_main_message.assert_not_called()
		mock_check_content_type.assert_called_once_with(mock_bot, mock_message)
		mock_update_post_link.assert_called_once_with(mock_bot, mock_message)
		mock_forward_and_add_inline_keyboard.assert_called_once_with(mock_bot, mock_update_post_link.return_value)
		self.assertEqual(result, main_message_id)
		self.assertEqual(mock_message.chat.id, main_channel_id)

	def test_with_message(self, mock_is_main_message_exists, mock_info, mock_get_main_message_content_by_id,
						  mock_delete_main_message, mock_check_content_type, mock_update_post_link,
						  mock_forward_and_add_inline_keyboard, *args):
		mock_bot = Mock(spec=TeleBot)
		main_channel_id = -10012345678
		main_message_id = 123
		mock_message = test_helper.create_mock_pyrogram_message("", [], main_channel_id, main_message_id)
		mock_message.forward_from_message_id = main_message_id
		mock_message.service = None
		mock_message.empty = None
		mock_message.forward_from_chat = mock_message.chat

		result = interval_updating_utils.update_older_message(mock_bot, main_channel_id, main_message_id, forwarded_message=mock_message)
		mock_is_main_message_exists.assert_called_once_with(main_channel_id, main_message_id)
		mock_info.assert_not_called()
		mock_get_main_message_content_by_id.assert_not_called()
		mock_delete_main_message.assert_not_called()
		mock_check_content_type.assert_called_once_with(mock_bot, mock_message)
		mock_update_post_link.assert_called_once_with(mock_bot, mock_message)
		mock_forward_and_add_inline_keyboard.assert_called_once_with(mock_bot, mock_update_post_link.return_value)
		self.assertEqual(result, main_message_id)
		self.assertEqual(mock_message.chat.id, main_channel_id)

	def test_with_empty_message(self, mock_is_main_message_exists, mock_info, mock_get_main_message_content_by_id,
								mock_delete_main_message, mock_check_content_type, mock_update_post_link,
								mock_forward_and_add_inline_keyboard, *args):
		mock_bot = Mock(spec=TeleBot)
		main_channel_id = -10012345678
		main_message_id = 123
		mock_message = test_helper.create_mock_pyrogram_message("", [], main_channel_id, main_message_id)
		mock_message.forward_from_message_id = main_message_id
		mock_message.service = None
		mock_message.empty = True
		mock_message.forward_from_chat = mock_message.chat

		result = interval_updating_utils.update_older_message(mock_bot, main_channel_id, main_message_id, forwarded_message=mock_message)
		mock_is_main_message_exists.assert_called_once_with(main_channel_id, main_message_id)
		mock_info.assert_not_called()
		mock_get_main_message_content_by_id.assert_not_called()
		mock_delete_main_message.assert_called_once_with(mock_bot, main_channel_id, main_message_id)
		mock_check_content_type.assert_not_called()
		mock_update_post_link.assert_not_called()
		mock_forward_and_add_inline_keyboard.assert_not_called()
		self.assertEqual(result, None)

	def test_with_service_message(self, mock_is_main_message_exists, mock_info, mock_get_main_message_content_by_id,
								  mock_delete_main_message, mock_check_content_type, mock_update_post_link,
								  mock_forward_and_add_inline_keyboard, *args):
		mock_bot = Mock(spec=TeleBot)
		main_channel_id = -10012345678
		main_message_id = 123
		mock_message = test_helper.create_mock_pyrogram_message("", [], main_channel_id, main_message_id)
		mock_message.forward_from_message_id = main_message_id
		mock_message.service = True
		mock_message.empty = None
		mock_message.forward_from_chat = mock_message.chat

		result = interval_updating_utils.update_older_message(mock_bot, main_channel_id, main_message_id, forwarded_message=mock_message)
		mock_is_main_message_exists.assert_called_once_with(main_channel_id, main_message_id)
		mock_info.assert_not_called()
		mock_get_main_message_content_by_id.assert_not_called()
		mock_delete_main_message.assert_called_once_with(mock_bot, main_channel_id, main_message_id)
		mock_check_content_type.assert_not_called()
		mock_update_post_link.assert_not_called()
		mock_forward_and_add_inline_keyboard.assert_not_called()
		self.assertEqual(result, None)

	def test_not_updated_post_link(self, mock_is_main_message_exists, mock_info, mock_get_main_message_content_by_id,
								   mock_delete_main_message, mock_check_content_type, mock_update_post_link,
								   mock_forward_and_add_inline_keyboard, *args):
		mock_bot = Mock(spec=TeleBot)
		main_channel_id = -10012345678
		main_message_id = 123
		mock_message = test_helper.create_mock_message("", [], main_channel_id, main_message_id)
		mock_message.forward_from_message_id = main_message_id
		mock_message.forward_from_chat = mock_message.chat
		mock_get_main_message_content_by_id.return_value = mock_message
		mock_update_post_link.return_value = None

		result = interval_updating_utils.update_older_message(mock_bot, main_channel_id, main_message_id)
		mock_is_main_message_exists.assert_called_once_with(main_channel_id, main_message_id)
		mock_info.assert_not_called()
		mock_get_main_message_content_by_id.assert_called_once_with(mock_bot, main_channel_id, main_message_id)
		mock_delete_main_message.assert_not_called()
		mock_check_content_type.assert_called_once_with(mock_bot, mock_message)
		mock_update_post_link.assert_called_once_with(mock_bot, mock_message)
		mock_forward_and_add_inline_keyboard.assert_called_once_with(mock_bot, mock_message)
		self.assertEqual(result, main_message_id)
		self.assertEqual(mock_message.chat.id, main_channel_id)

	def test_no_check_content_type(self, mock_is_main_message_exists, mock_info, mock_get_main_message_content_by_id,
								   mock_delete_main_message, mock_check_content_type, mock_update_post_link,
								   mock_forward_and_add_inline_keyboard, *args):
		mock_bot = Mock(spec=TeleBot)
		main_channel_id = -10012345678
		main_message_id = 123
		mock_message = test_helper.create_mock_message("", [], main_channel_id, main_message_id)
		mock_get_main_message_content_by_id.return_value = mock_message
		mock_check_content_type.return_value = False

		result = interval_updating_utils.update_older_message(mock_bot, main_channel_id, main_message_id)
		mock_is_main_message_exists.assert_called_once_with(main_channel_id, main_message_id)
		mock_info.assert_not_called()
		mock_get_main_message_content_by_id.assert_called_once_with(mock_bot, main_channel_id, main_message_id)
		mock_delete_main_message.assert_not_called()
		mock_check_content_type.assert_called_once_with(mock_bot, mock_message)
		mock_update_post_link.assert_not_called()
		mock_forward_and_add_inline_keyboard.assert_not_called()
		self.assertEqual(result, None)
		self.assertEqual(mock_message.chat.id, main_channel_id)

	def test_no_forwarded_from_main_channel(self, mock_is_main_message_exists, mock_info, mock_get_main_message_content_by_id,
											mock_delete_main_message, mock_check_content_type, mock_update_post_link,
											mock_forward_and_add_inline_keyboard, *args):
		mock_bot = Mock(spec=TeleBot)
		main_channel_id = -10012345678
		main_message_id = 123
		mock_message = test_helper.create_mock_message("", [], -10087654321, main_message_id)
		mock_get_main_message_content_by_id.return_value = mock_message

		result = interval_updating_utils.update_older_message(mock_bot, main_channel_id, main_message_id)
		mock_is_main_message_exists.assert_called_once_with(main_channel_id, main_message_id)
		mock_info.assert_not_called()
		mock_get_main_message_content_by_id.assert_called_once_with(mock_bot, main_channel_id, main_message_id)
		mock_delete_main_message.assert_not_called()
		mock_check_content_type.assert_not_called()
		mock_update_post_link.assert_not_called()
		mock_forward_and_add_inline_keyboard.assert_not_called()
		self.assertEqual(result, None)
		self.assertNotEqual(mock_message.chat.id, main_channel_id)

	def test_no_forwarded_message(self, mock_is_main_message_exists, mock_info, mock_get_main_message_content_by_id,
								  mock_delete_main_message, mock_check_content_type, mock_update_post_link,
								  mock_forward_and_add_inline_keyboard, *args):
		mock_bot = Mock(spec=TeleBot)
		main_channel_id = -10012345678
		main_message_id = 123
		mock_get_main_message_content_by_id.return_value = None

		result = interval_updating_utils.update_older_message(mock_bot, main_channel_id, main_message_id)
		mock_is_main_message_exists.assert_called_once_with(main_channel_id, main_message_id)
		mock_info.assert_not_called()
		mock_get_main_message_content_by_id.assert_called_once_with(mock_bot, main_channel_id, main_message_id)
		mock_delete_main_message.assert_not_called()
		mock_check_content_type.assert_not_called()
		mock_update_post_link.assert_not_called()
		mock_forward_and_add_inline_keyboard.assert_not_called()
		self.assertEqual(result, None)

	def test_error_forwarded_message(self, mock_is_main_message_exists, mock_info, mock_get_main_message_content_by_id,
									 mock_delete_main_message, mock_check_content_type, mock_update_post_link,
									 mock_forward_and_add_inline_keyboard, *args):
		mock_bot = Mock(spec=TeleBot)
		main_channel_id = -10012345678
		main_message_id = 123
		mock_get_main_message_content_by_id.side_effect = ApiTelegramException("content", "", {"error_code": 400,
																							   "description": "Bad Request: message to forward not found"})

		result = interval_updating_utils.update_older_message(mock_bot, main_channel_id, main_message_id)
		mock_is_main_message_exists.assert_called_once_with(main_channel_id, main_message_id)
		mock_info.assert_not_called()
		mock_get_main_message_content_by_id.assert_called_once_with(mock_bot, main_channel_id, main_message_id)
		mock_delete_main_message.assert_called_once_with(mock_bot, main_channel_id, main_message_id)
		mock_check_content_type.assert_not_called()
		mock_update_post_link.assert_not_called()
		mock_forward_and_add_inline_keyboard.assert_not_called()
		self.assertEqual(result, None)

	def test_no_main_message(self, mock_is_main_message_exists, mock_info, mock_get_main_message_content_by_id,
							 mock_delete_main_message, mock_check_content_type, mock_update_post_link,
							 mock_forward_and_add_inline_keyboard, *args):
		mock_bot = Mock(spec=TeleBot)
		main_channel_id = -10012345678
		main_message_id = 123
		mock_is_main_message_exists.return_value = False

		result = interval_updating_utils.update_older_message(mock_bot, main_channel_id, main_message_id)
		mock_is_main_message_exists.assert_called_once_with(main_channel_id, main_message_id)
		mock_info.assert_called_once_with(f"Ticket update for {main_channel_id, main_message_id} was skipped because it's not in db")
		mock_get_main_message_content_by_id.assert_not_called()
		mock_delete_main_message.assert_not_called()
		mock_check_content_type.assert_not_called()
		mock_update_post_link.assert_not_called()
		mock_forward_and_add_inline_keyboard.assert_not_called()
		self.assertEqual(result, None)




if __name__ == "__main__":
	main()
