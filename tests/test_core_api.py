from unittest import TestCase, main
from unittest.mock import patch, AsyncMock, Mock, call, MagicMock

from pyrogram import Client

import core_api


@patch("logging.info")
@patch("asyncio.sleep")
class GetMessagesTest(TestCase):
	def test_messages(self, mock_sleep, mock_info, *args):
		channel_id = -10012345678
		last_msg_id = 9
		limit = 2
		time_sleep = 1
		mock_client = Mock(spec=Client)
		mock_client.get_messages = AsyncMock(side_effect=lambda chat_id, message_ids: message_ids)

		manager = Mock()
		manager.attach_mock(mock_client.get_messages, "a")
		manager.attach_mock(mock_info, "b")
		manager.attach_mock(mock_sleep, "c")
		expected_calls = []

		for i in range(1, 5):
			expected_calls.append(call.a(channel_id, [i * 2 - 1, i * 2]))
			expected_calls.append(call.b(f"Exporting progress: {i * 2}/9"))
			expected_calls.append(call.c(1))
		expected_calls.append(call.a(channel_id, [9]))
		expected_calls.append(call.b(f"Exporting progress: 9/9"))

		core_api.get_messages(channel_id, last_msg_id, limit, time_sleep, client=mock_client)
		self.assertEqual(expected_calls, manager.mock_calls)

	def test_messages_with_list(self, mock_sleep, mock_info, *args):
		channel_id = -10012345678
		last_msg_id = 9
		message_ids = [1, 2, 3, 5, 7, 9]
		limit = 2
		time_sleep = 1
		mock_client = Mock(spec=Client)
		mock_client.get_messages = AsyncMock(side_effect=lambda chat_id, message_ids: message_ids)

		manager = Mock()
		manager.attach_mock(mock_client.get_messages, "a")
		manager.attach_mock(mock_info, "b")
		manager.attach_mock(mock_sleep, "c")
		expected_calls = []

		for i in range(0, 3):
			expected_calls.append(call.a(channel_id, [message_ids[i * 2], message_ids[i * 2 + 1]]))
			expected_calls.append(call.b(f"Exporting progress: {(i + 1) * 2}/6"))
			if i < 2: expected_calls.append(call.c(1))

		core_api.get_messages(channel_id, last_msg_id, limit, time_sleep, client=mock_client, message_ids=message_ids)
		self.assertEqual(expected_calls, manager.mock_calls)


@patch("core_api.__get_members_for_chat")
class GetMembersTest(TestCase):
	def test_default(self, mock__get_members_for_chat, *args):
		chat_ids = [-10012345678, -10087654321]
		mock_client = Mock(spec=Client)
		mock__get_members_for_chat.side_effect = lambda chat_id, client: [1, 2, 3] if chat_id == -10087654321 else [4, 5, 6]

		result = core_api.get_members(chat_ids, client=mock_client)
		mock__get_members_for_chat.assert_has_calls([call(-10012345678, client=mock_client), call(-10087654321, client=mock_client)])
		self.assertEqual(result, {-10012345678: [4, 5, 6], -10087654321: [1, 2, 3]})

	def test_with_none_users(self, mock__get_members_for_chat, *args):
		chat_ids = [-10012345678, -10087654321]
		mock_client = Mock(spec=Client)
		mock__get_members_for_chat.side_effect = lambda chat_id, client: [1, 2, 3] if chat_id == -10087654321 else None

		result = core_api.get_members(chat_ids, client=mock_client)
		mock__get_members_for_chat.assert_has_calls([call(-10012345678, client=mock_client), call(-10087654321, client=mock_client)])
		self.assertEqual(result, {-10012345678: [], -10087654321: [1, 2, 3]})

	def test_with_empty_users(self, mock__get_members_for_chat, *args):
		chat_ids = [-10012345678, -10087654321]
		mock_client = Mock(spec=Client)
		mock__get_members_for_chat.side_effect = lambda chat_id, client: [1, 2, 3] if chat_id == -10087654321 else []

		result = core_api.get_members(chat_ids, client=mock_client)
		mock__get_members_for_chat.assert_has_calls([call(-10012345678, client=mock_client), call(-10087654321, client=mock_client)])
		self.assertEqual(result, {-10012345678: [], -10087654321: [1, 2, 3]})



if __name__ == "__main__":
	main()
