import unittest
from unittest.mock import MagicMock

import telebot

from interval_updating_utils import get_current_msg_id


class IntervalUpdatingUtilsTest(unittest.TestCase):
  def test_get_current_msg_id_does_not_throw_if_no_pinned_message(self):
    get_chat_mock = MagicMock()
    get_chat_mock.return_value = telebot.types.Chat(1, "private")

    bot = telebot.TeleBot("token")
    bot.get_chat = get_chat_mock

    get_current_msg_id(bot, 1, 1)


if __name__ == "__main__":
  unittest.main()
