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


if __name__ == "__main__":
	main()
