from unittest import main, TestCase
from unittest.mock import patch, Mock, call

from telebot import TeleBot
from telebot.apihelper import ApiTelegramException
from telebot.types import ChatMemberBanned, ChatMember

import config_utils
import user_utils


@patch("db_utils.get_all_users")
@patch("user_utils.get_user")
class LoadUsersTest(TestCase):
	def test_without_info(self, mock_get_user, mock_get_all_users, *args):
		user_id = "803945"
		mock_bot = Mock(spec=TeleBot)
		config_utils.USER_TAGS = {"DD": user_id}
		mock_get_user.return_value = None

		user_utils.load_users(mock_bot)
		mock_get_all_users.assert_not_called()
		mock_get_user.assert_called_once_with(mock_bot, user_id)
		self.assertEqual(user_utils.USER_DATA, config_utils.USER_TAGS)

	def test_without_username(self, mock_get_user, mock_get_all_users, *args):
		mock_bot = Mock(spec=TeleBot)
		user_id = "803945"
		user_tag = "DD"
		info = {"id": user_id, "first_name": "Name", "last_name": "Surname", "username": None, "is_bot": False}
		config_utils.USER_TAGS = {user_tag: user_id}
		mock_get_user.return_value = info

		user_utils.load_users(mock_bot)
		mock_get_all_users.assert_not_called()
		mock_get_user.assert_called_once_with(mock_bot, user_id)
		self.assertEqual(user_utils.USER_DATA, {user_tag: info})


@patch("config_utils.USER_TAGS", {"aa": 51456, "bb": 54684, "cc": 68462, "dd": 12345})
@patch("db_utils.get_main_channel_ids")
class CheckMembersOnMainChannelsTest(TestCase):
	def test_unban_chat_member(self, mock_get_main_channel_ids, *args):
		mock_bot = Mock(spec=TeleBot)
		user_id = 12345
		main_channel_ids = [-10012345678, -10087654321]
		mock_get_main_channel_ids.return_value = main_channel_ids
		mock_bot.get_chat_member.side_effect = lambda chat_id, user_id: Mock(status="kicked") if chat_id == main_channel_ids[0] else Mock(status="member")

		manager = Mock()
		manager.attach_mock(mock_bot.get_chat_member, "a")
		manager.attach_mock(mock_bot.unban_chat_member, "b")

		expected_mocks = [
			call.a(main_channel_ids[0], user_id),
			call.b(main_channel_ids[0], user_id, True),
			call.a(main_channel_ids[1], user_id)
		]

		user_utils.check_members_on_main_channels(mock_bot, user_id)
		mock_get_main_channel_ids.assert_called_once_with()
		mock_bot.kick_chat_member.assert_not_called()
		self.assertEqual(manager.mock_calls, expected_mocks)

	def test_unban_no_chat_member(self, mock_get_main_channel_ids, *args):
		mock_bot = Mock(spec=TeleBot)
		user_id = 12345
		main_channel_ids = [-10012345678]
		mock_get_main_channel_ids.return_value = main_channel_ids
		mock_bot.get_chat_member.side_effect = ApiTelegramException("content", "", {"error_code": 400, "description": "Bad Request: message to forward not found"})

		user_utils.check_members_on_main_channels(mock_bot, user_id)
		mock_get_main_channel_ids.assert_called_once_with()
		mock_bot.get_chat_member.assert_called_once_with(main_channel_ids[0], user_id)
		mock_bot.kick_chat_member.assert_not_called()
		mock_bot.unban_chat_member.assert_not_called()

	def test_kicked_chat_member(self, mock_get_main_channel_ids, *args):
		mock_bot = Mock(spec=TeleBot)
		user_id = 21654
		main_channel_ids = [-10012345678, -10087654321, -10045647213]
		mock_get_main_channel_ids.return_value = main_channel_ids
		mock_bot.get_chat_member.side_effect = lambda chat_id, user_id: Mock(status="kicked") if chat_id == main_channel_ids[0] else\
						(Mock(status="member") if chat_id == main_channel_ids[1] else Mock(status="left"))

		manager = Mock()
		manager.attach_mock(mock_bot.get_chat_member, "a")
		manager.attach_mock(mock_bot.kick_chat_member, "b")

		expected_mocks = [
			call.a(main_channel_ids[0], user_id),
			call.a(main_channel_ids[1], user_id),
			call.b(main_channel_ids[1], user_id),
			call.a(main_channel_ids[2], user_id)
		]

		user_utils.check_members_on_main_channels(mock_bot, user_id)
		mock_get_main_channel_ids.assert_called_once_with()
		mock_bot.unban_chat_member.assert_not_called()
		self.assertEqual(manager.mock_calls, expected_mocks)


	def test_kicked_no_chat_member(self, mock_get_main_channel_ids, *args):
		mock_bot = Mock(spec=TeleBot)
		user_id = 21654
		main_channel_ids = [-10012345678]
		mock_get_main_channel_ids.return_value = main_channel_ids
		mock_bot.get_chat_member.side_effect = ApiTelegramException("content", "", {"error_code": 400, "description": "Bad Request: message to forward not found"})

		user_utils.check_members_on_main_channels(mock_bot, user_id)
		mock_get_main_channel_ids.assert_called_once_with()
		mock_bot.get_chat_member.assert_called_once_with(main_channel_ids[0], user_id)
		mock_bot.unban_chat_member.assert_not_called()
		mock_bot.kick_chat_member.assert_not_called()



if __name__ == "__main__":
	main()
