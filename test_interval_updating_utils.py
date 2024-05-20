from unittest import TestCase, main
from unittest.mock import Mock, patch

from telebot import TeleBot
from telebot.types import Chat, Message

from interval_updating_utils import get_current_msg_id


class GetCurrentMsgIdTest(TestCase):
  @patch('utils.get_last_message')
  def test_no_pinned_message(self, mock_get_last_message):
    mock_chat = Mock(spec=Chat)
    mock_chat.pinned_message = None

    mock_bot = Mock(spec=TeleBot)
    mock_bot.get_chat.return_value = mock_chat

    mock_message = Mock(spec=Message)
    mock_get_last_message.return_value = mock_message

    main_channel_id = 1
    discussion_chat_id = 2
    result = get_current_msg_id(
        mock_bot, main_channel_id, discussion_chat_id)

    mock_bot.get_chat.assert_called_once_with(discussion_chat_id)
    mock_get_last_message.assert_called_once_with(mock_bot, main_channel_id)
    self.assertEqual(result, mock_message)


if __name__ == "__main__":
  main()
