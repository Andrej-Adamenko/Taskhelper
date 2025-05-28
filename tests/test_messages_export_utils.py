from unittest import TestCase, main
from unittest.mock import patch, Mock, call

from pyrogram.types import Chat, User

import messages_export_utils
from tests import test_helper


@patch("db_utils.get_last_message_id")
@patch("messages_export_utils.export_messages")
@patch("db_utils.delete_comment_message")
@patch("db_utils.insert_comment_message")
@patch("logging.info")
class ExportChatCommentsTest(TestCase):
	def test_export_comment(self, mock_info, mock_insert_comment_message, mock_delete_comment_message,
							mock_export_messages, mock_get_last_message_id, *args):
		discussion_chat_id = -10012345678
		last_message_id = 124
		user_id = 87235
		reply_to_message = 5
		mock_get_last_message_id.return_value = last_message_id
		mock_message1 = test_helper.create_mock_message("", [], discussion_chat_id, 10)  # No
		mock_message2 = test_helper.create_mock_message("", [], discussion_chat_id, 20)  # Chat
		mock_message3 = test_helper.create_mock_message("", [], discussion_chat_id, 30)  # No
		mock_message4 = test_helper.create_mock_message("", [], discussion_chat_id, 42)  # Chat
		mock_message5 = test_helper.create_mock_message("", [], discussion_chat_id, 120) # No
		mock_message6 = test_helper.create_mock_message("", [], discussion_chat_id, 121) # User
		mock_message7 = test_helper.create_mock_message("", [], discussion_chat_id, 122) # Chat
		mock_message8 = test_helper.create_mock_message("", [], discussion_chat_id, 124) # User
		mock_message9 = test_helper.create_mock_message("", [], discussion_chat_id, 100) # Empty
		mock_message10 = test_helper.create_mock_message("", [], discussion_chat_id, 110) # Empty
		mock_message11 = test_helper.create_mock_message("", [], discussion_chat_id, 123) # Empty
		mock_message12 = test_helper.create_mock_message("", [], discussion_chat_id, 127) # Empty
		mock_message13 = test_helper.create_mock_message("", [], discussion_chat_id, 130) # Empty
		mock_message1.reply_to_message = mock_message3.reply_to_message = mock_message5.reply_to_message = \
			mock_message9.reply_to_message = mock_message10.reply_to_message = mock_message11.reply_to_message = \
			mock_message12.reply_to_message = mock_message13.reply_to_message = None
		mock_reply = test_helper.create_mock_message("", [], discussion_chat_id, reply_to_message)
		mock_chat = Mock(spec=Chat)
		mock_chat.id = discussion_chat_id
		mock_user = Mock(spec=User)
		mock_user.id = user_id
		mock_message2.reply_to_message = mock_message4.reply_to_message = mock_message6.reply_to_message = \
										 mock_message7.reply_to_message = mock_message8.reply_to_message = mock_reply
		mock_message2.sender_chat = mock_message4.sender_chat = mock_message7.sender_chat = mock_chat
		mock_message6.sender_chat = mock_message8.sender_chat = None
		mock_message9.empty = mock_message10.empty = mock_message11.empty = mock_message12.empty = mock_message13.empty = True
		mock_message6.from_user = mock_message8.from_user = mock_user
		mock_export_messages.return_value = [mock_message1, mock_message2, mock_message3, mock_message4,
											 mock_message5, mock_message6, mock_message7, mock_message8,
											 mock_message9, mock_message10, mock_message11, mock_message12, mock_message13]
		manager = Mock()
		manager.attach_mock(mock_delete_comment_message, 'a')
		manager.attach_mock(mock_insert_comment_message, 'b')
		manager.attach_mock(mock_info, 'c')

		expected_calls = [
			call.b(reply_to_message, 20, discussion_chat_id, discussion_chat_id),
			call.c(f"Exported comment [{reply_to_message}, 20, {discussion_chat_id}]"),
			call.b(reply_to_message, 42, discussion_chat_id, discussion_chat_id),
			call.c(f"Exported comment [{reply_to_message}, 42, {discussion_chat_id}]"),
			call.b(reply_to_message, 121, discussion_chat_id, user_id),
			call.c(f"Exported comment [{reply_to_message}, 121, {discussion_chat_id}]"),
			call.b(reply_to_message, 122, discussion_chat_id, discussion_chat_id),
			call.c(f"Exported comment [{reply_to_message}, 122, {discussion_chat_id}]"),
			call.b(reply_to_message, 124, discussion_chat_id, user_id),
			call.c(f"Exported comment [{reply_to_message}, 124, {discussion_chat_id}]"),
			call.a(100, discussion_chat_id),
			call.a(110, discussion_chat_id),
			call.a(123, discussion_chat_id)
		]

		messages_export_utils.export_chat_comments(discussion_chat_id)
		mock_get_last_message_id.assert_called_once_with(discussion_chat_id)
		mock_export_messages.assert_called_once_with(discussion_chat_id, last_message_id)
		self.assertEqual(manager.mock_calls, expected_calls)

	def test_export_comment_not_last_message(self, mock_info, mock_insert_comment_message,
											 mock_insert_comment_deleted_message, mock_export_messages,
											 mock_get_last_message_id, *args):
		discussion_chat_id = -10012345678
		mock_get_last_message_id.return_value = None

		messages_export_utils.export_chat_comments(discussion_chat_id)
		mock_get_last_message_id.assert_called_once_with(discussion_chat_id)
		mock_export_messages.assert_not_called()
		mock_insert_comment_deleted_message.assert_not_called()
		mock_insert_comment_message.assert_not_called()
		mock_info.assert_called_once_with(f"Can't find last message in {discussion_chat_id}, export skipped")


class ExportMessagesTest(TestCase):
	@patch("core_api.get_messages")
	def test_default(self, mock_get_messages, *args):
		channel_id = -10012345678
		last_message_id = 12
		messages_export_utils.export_messages(channel_id, last_message_id)
		mock_get_messages.assert_called_once_with(channel_id, last_message_id, messages_export_utils._EXPORT_BATCH_SIZE)


@patch("messages_export_utils.export_comments_from_discussion_chats")
@patch("messages_export_utils.export_main_channels")
class StartExportingTest(TestCase):
	def test_default(self, mock_export_comments_from_discussion_chats, mock_export_main_channels):
		messages_export_utils.start_exporting()
		mock_export_comments_from_discussion_chats.assert_called_once_with()
		mock_export_main_channels.assert_called_once_with()

if __name__ == "__main__":
	main()
