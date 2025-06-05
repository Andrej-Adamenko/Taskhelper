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

		result = core_api.get_messages(channel_id, last_msg_id, limit, client=mock_client)
		self.assertEqual(expected_calls, manager.mock_calls)
		self.assertEqual(result, [1, 2, 3, 4, 5, 6, 7, 8, 9])

	def test_messages_50_limit_less(self, mock_sleep, mock_info, *args):
		channel_id = -10012345678
		last_msg_id = 350
		limit = 50
		mock_client = Mock(spec=Client)
		mock_client.get_messages = AsyncMock(side_effect=lambda chat_id, message_ids: message_ids)

		manager = Mock()
		manager.attach_mock(mock_client.get_messages, "a")
		manager.attach_mock(mock_info, "b")
		manager.attach_mock(mock_sleep, "c")
		expected_calls = []

		for i in range(0, 7):
			expected_calls.append(call.a(channel_id, [i * 50 + j for j in range(1, 51)]))
			expected_calls.append(call.b(f"Exporting progress: {(i + 1) * 50}/350"))
			if i < 6: expected_calls.append(call.c(1))

		core_api.get_messages(channel_id, last_msg_id, limit, client=mock_client)
		self.assertEqual(expected_calls, manager.mock_calls)

	def test_messages_50_limit_more(self, mock_sleep, mock_info, *args):
		channel_id = -10012345678
		last_msg_id = 360
		limit = 50
		mock_client = Mock(spec=Client)
		mock_client.get_messages = AsyncMock(side_effect=lambda chat_id, message_ids: message_ids)

		manager = Mock()
		manager.attach_mock(mock_client.get_messages, "a")
		manager.attach_mock(mock_info, "b")
		manager.attach_mock(mock_sleep, "c")
		expected_calls = []

		for i in range(0, 7):
			expected_calls.append(call.a(channel_id, [i * 50 + j for j in range(1, 51)]))
			expected_calls.append(call.b(f"Exporting progress: {(i + 1) * 50}/360"))
			expected_calls.append(call.c(5))
		expected_calls.append(call.a(channel_id, [351,352,353,354,355,356,357,358,359,360]))
		expected_calls.append(call.b(f"Exporting progress: 360/360"))

		core_api.get_messages(channel_id, last_msg_id, limit, client=mock_client)
		self.assertEqual(expected_calls, manager.mock_calls)

	def test_messages_65_limit(self, mock_sleep, mock_info, *args):
		channel_id = -10012345678
		last_msg_id = 330
		limit = 65
		mock_client = Mock(spec=Client)
		mock_client.get_messages = AsyncMock(side_effect=lambda chat_id, message_ids: message_ids)

		manager = Mock()
		manager.attach_mock(mock_client.get_messages, "a")
		manager.attach_mock(mock_info, "b")
		manager.attach_mock(mock_sleep, "c")
		expected_calls = []

		for i in range(0, 5):
			expected_calls.append(call.a(channel_id, [i * 65 + j for j in range(1, 66)]))
			expected_calls.append(call.b(f"Exporting progress: {(i + 1) * 65}/330"))
			expected_calls.append(call.c(6.5))
		expected_calls.append(call.a(channel_id, [326,327,328,329,330]))
		expected_calls.append(call.b(f"Exporting progress: 330/330"))

		core_api.get_messages(channel_id, last_msg_id, limit, client=mock_client)
		self.assertEqual(expected_calls, manager.mock_calls)

	def test_messages_with_list(self, mock_sleep, mock_info, *args):
		channel_id = -10012345678
		last_msg_id = 9
		message_ids = [1, 2, 3, 5, 7, 9]
		limit = 2
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

		result = core_api.get_messages(channel_id, last_msg_id, limit, client=mock_client, message_ids=message_ids)
		self.assertEqual(expected_calls, manager.mock_calls)
		self.assertEqual(result, message_ids)

	def test_messages_stop_flag(self, mock_sleep, mock_info, *args):
		channel_id = -10012345678
		last_msg_id = 9
		message_ids = [1, 2, 3, 5, 7, 9]
		limit = 2
		mock_client = Mock(spec=Client)
		mock_client.get_messages = AsyncMock(side_effect=lambda chat_id, message_ids: message_ids)


		result = core_api.get_messages(channel_id, last_msg_id, limit, client=mock_client,
									   message_ids=message_ids, stop_flag={"stop": True})
		mock_client.get_messages.assert_not_called()
		mock_sleep.assert_not_called()
		mock_info.assert_called_once_with(f"Stopping export progress, count exported: 0")
		self.assertEqual(result, None)


@patch("asyncio.sleep")
@patch("core_api.__get_members_for_chat")
class GetMembersTest(TestCase):
	def test_default(self, mock__get_members_for_chat, mock_sleep, *args):
		chat_ids = [-10012345678, -10087654321]
		mock_client = Mock(spec=Client)
		mock__get_members_for_chat.side_effect = lambda chat_id, client: [1, 2, 3] if chat_id == -10087654321 else [4, 5, 6]

		result = core_api.get_members(chat_ids, client=mock_client)
		mock__get_members_for_chat.assert_has_calls([call(-10012345678, client=mock_client), call(-10087654321, client=mock_client)])
		self.assertEqual(mock__get_members_for_chat.call_count, 2)
		mock_sleep.assert_has_calls([call(0.5), call(0.5)])
		self.assertEqual(mock_sleep.call_count, 2)
		self.assertEqual(result, {-10012345678: [4, 5, 6], -10087654321: [1, 2, 3]})

	def test_with_none_users(self, mock__get_members_for_chat, mock_sleep, *args):
		chat_ids = [-10012345678, -10087654321]
		mock_client = Mock(spec=Client)
		mock__get_members_for_chat.side_effect = lambda chat_id, client: [1, 2, 3] if chat_id == -10087654321 else None

		result = core_api.get_members(chat_ids, client=mock_client)
		mock__get_members_for_chat.assert_has_calls([call(-10012345678, client=mock_client), call(-10087654321, client=mock_client)])
		self.assertEqual(mock__get_members_for_chat.call_count, 2)
		mock_sleep.assert_has_calls([call(0.5), call(0.5)])
		self.assertEqual(mock_sleep.call_count, 2)
		self.assertEqual(result, {-10012345678: [], -10087654321: [1, 2, 3]})

	def test_with_empty_users(self, mock__get_members_for_chat, mock_sleep, *args):
		chat_ids = [-10012345678, -10087654321]
		mock_client = Mock(spec=Client)
		mock__get_members_for_chat.side_effect = lambda chat_id, client: [1, 2, 3] if chat_id == -10087654321 else []

		result = core_api.get_members(chat_ids, client=mock_client)
		mock__get_members_for_chat.assert_has_calls([call(-10012345678, client=mock_client), call(-10087654321, client=mock_client)])
		self.assertEqual(mock__get_members_for_chat.call_count, 2)
		mock_sleep.assert_has_calls([call(0.5), call(0.5)])
		self.assertEqual(mock_sleep.call_count, 2)
		self.assertEqual(result, {-10012345678: [], -10087654321: [1, 2, 3]})



if __name__ == "__main__":
	main()
