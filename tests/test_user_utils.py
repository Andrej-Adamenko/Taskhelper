from asyncio import ProactorEventLoop
from types import coroutine
from unittest import main, TestCase
from unittest.mock import patch, Mock, AsyncMock, ANY, call

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


@patch("core_api.get_members")
class MembersChannelTest(TestCase):
	@patch("user_utils.MEMBER_CACHE", {})
	@patch("time.time", return_value=1745924325)
	@patch("user_utils.set_member_ids_channels")
	def test_get_members_channel(self, mock_set_members_channel, mock_time, *args):
		channel_ids = [-10012345678]
		channel_users = {channel_ids[0]: [12345, 23465]}
		mock_set_members_channel.return_value = channel_users

		user_utils.get_member_ids_channels(channel_ids)
		mock_set_members_channel.assert_called_once_with(channel_ids)
		mock_time.assert_called_once_with()

	@patch("user_utils.MEMBER_CACHE", {})
	@patch("time.time", return_value=1745924325)
	def test_get_members_channel_result(self, mock_time, mock_get_members, *args):
		channel_ids = [-10012345678]
		ids = [12345, 23465]
		channel_users = {channel_ids[0]: ids}
		mock_get_members.return_value = {channel_ids[0]: [Mock(id=i) for i in ids]}

		result = user_utils.get_member_ids_channels(channel_ids)
		mock_get_members.assert_called_once_with(channel_ids)
		mock_time.assert_has_calls([call(), call()])
		self.assertEqual(result, channel_users)

	@patch("user_utils.MEMBER_CACHE", {})
	@patch("time.time", return_value=1745924325)
	def test_get_members_channel_empty_result(self, mock_time, mock_get_members, *args):
		channel_ids = [-10012345678]
		channel_users = {channel_ids[0]: []}
		mock_get_members.return_value = []

		result = user_utils.get_member_ids_channels(channel_ids)
		mock_get_members.assert_called_once_with(channel_ids)
		mock_time.assert_has_calls([call(), call()])
		self.assertEqual(result, channel_users)

	@patch("user_utils.MEMBER_CACHE", {-10012345678: {"user_ids": [12345, 23465, 13508], "time": 1745924296}})
	@patch("time.time", return_value=1745924325)
	@patch("user_utils.set_member_ids_channels")
	def test_get_members_channel_cache(self, mock_set_members_channel, mock_time, *args):
		channel_ids = [-10012345678]

		user_utils.get_member_ids_channels(channel_ids)
		mock_set_members_channel.assert_not_called()
		mock_time.assert_called_once_with()

	@patch("user_utils.MEMBER_CACHE", {-10012345678: {"user_ids": [12345, 23465], "time": 1745924296},
									   -10087653421: {"user_ids": [12345, 23465, 13508], "time": 1745924296}, })
	@patch("time.time", return_value=1745924325)
	@patch("user_utils.set_member_ids_channels")
	def test_get_members_channel_with_other_channels_result(self, mock_set_members_channel, mock_time, *args):
		channel_ids = [-10012345678]
		ids = [12345, 23465]
		channel_users = {channel_ids[0]: ids}

		result = user_utils.get_member_ids_channels(channel_ids)
		mock_set_members_channel.assert_not_called()
		mock_time.assert_called_once_with()
		self.assertEqual(result, channel_users)

	@patch("user_utils.MEMBER_CACHE", {-10012345678: {"user_ids": [12345, 23465, 13508], "time": 1745923296}})
	@patch("time.time", return_value=1745924325)
	def test_get_members_channel_cache_expired_time_result(self, mock_time, mock_get_members, *args):
		channel_ids = [-10012345678]
		ids = [12345, 23465]
		channel_users = {channel_ids[0]: ids}
		mock_get_members.return_value = {channel_ids[0]: [Mock(id=i) for i in ids]}

		result = user_utils.get_member_ids_channels(channel_ids)
		mock_get_members.assert_called_once_with(channel_ids)
		mock_time.assert_has_calls([call(), call()])
		self.assertEqual(result, channel_users)

	@patch("user_utils.MEMBER_CACHE", {-10012345678: {"user_ids": [12345, 23465, 13508], "time": 1745923296}})
	@patch("time.time", return_value=1745924325)
	@patch("user_utils.set_member_ids_channels")
	def test_get_members_channel_cache_expired_time(self, mock_set_members_channel, mock_time, *args):
		channel_ids = [-10012345678]
		channel_users = {channel_ids[0]: [12345, 23465]}
		mock_set_members_channel.return_value = channel_users

		user_utils.get_member_ids_channels(channel_ids)
		mock_set_members_channel.assert_called_once_with(channel_ids)
		mock_time.assert_called_once_with()

	@patch("user_utils.MEMBER_CACHE", {-10012345678: {"user_ids": [12345, 23465, 13508], "time": 1745923296}})
	def test_set_members_channel(self, mock_get_members, *args):
		channel_ids = [-10012345678]
		ids = [155, 4864, 6846]
		mock_get_members.return_value = {channel_ids[0]: [Mock(id=i) for i in ids]}

		user_utils.set_member_ids_channels(channel_ids)
		mock_get_members.assert_called_once_with(channel_ids)
		self.assertEqual(user_utils.MEMBER_CACHE[channel_ids[0]]["user_ids"], ids)

	@patch("user_utils.MEMBER_CACHE", {-10012345678: {"user_ids": [12345, 23465, 13508], "time": 1745923296}})
	def test_set_members_channel_no_members(self, mock_get_members, *args):
		channel_ids = [-10012345678]
		mock_get_members.return_value = {channel_ids[0]: []}

		user_utils.set_member_ids_channels(channel_ids)
		mock_get_members.assert_called_once_with(channel_ids)
		self.assertEqual(user_utils.MEMBER_CACHE[channel_ids[0]]["user_ids"], [])

	@patch("user_utils.MEMBER_CACHE", {-10012345678: {"user_ids": [12345, 23465, 13508], "time": 1745923296}})
	def test_set_members_channel_check_loop(self, mock_get_members, *args):
		channel_ids = [-10012345678]
		mock_get_members.return_value = {channel_ids[0]: []}

		user_utils.set_member_ids_channels(channel_ids)
		mock_get_members.assert_called_once_with(channel_ids)
		self.assertEqual(user_utils.MEMBER_CACHE[channel_ids[0]]["user_ids"], [])

	@patch("user_utils.MEMBER_CACHE", {-10012345678: {"user_ids": [12345, 23465, 13508], "time": 1745923296}})
	def test_set_members_channel_none_members(self, mock_get_members, *args):
		channel_ids = [-10012345678]
		mock_get_members.return_value = None

		user_utils.set_member_ids_channels(channel_ids)
		mock_get_members.assert_called_once_with(channel_ids)
		self.assertEqual(user_utils.MEMBER_CACHE[channel_ids[0]]["user_ids"], [])

	@patch("user_utils.set_member_ids_channels")
	@patch("db_utils.get_all_individual_channels")
	@patch("db_utils.get_main_channel_ids")
	def test_update_all_channels_members(self, mock_get_main_channel_ids, mock_get_all_individual_channels,
										 mock_set_member_ids_channels, *args):
		main_channels = [-10012345678]
		subchannels = [-10087654321, -10045678123, -10045612378, -10012345678]
		all_subchannels = [-10012345678, -10087654321, -10045678123, -10045612378]
		mock_get_main_channel_ids.return_value = main_channels
		mock_get_all_individual_channels.return_value = [[item, ""] for item in subchannels]

		user_utils.update_all_channel_members()
		mock_get_main_channel_ids.assert_called_once_with()
		mock_get_all_individual_channels.assert_called_once_with()
		mock_set_member_ids_channels.assert_called_once_with(all_subchannels)


@patch("config_utils.USER_TAGS", {"aa": 51456, "bb": 54684, "cc": 68462, "dd": 12345})
@patch("db_utils.get_main_channel_ids")
class CheckUserIdOnMainChannelsTest(TestCase):
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

		user_utils.check_user_id_on_main_channels(mock_bot, user_id)
		mock_get_main_channel_ids.assert_called_once_with()
		mock_bot.kick_chat_member.assert_not_called()
		self.assertEqual(manager.mock_calls, expected_mocks)

	def test_unban_no_chat_member(self, mock_get_main_channel_ids, *args):
		mock_bot = Mock(spec=TeleBot)
		user_id = 12345
		main_channel_ids = [-10012345678]
		mock_get_main_channel_ids.return_value = main_channel_ids
		mock_bot.get_chat_member.side_effect = ApiTelegramException("content", "", {"error_code": 400, "description": "Bad Request: message to forward not found"})

		user_utils.check_user_id_on_main_channels(mock_bot, user_id)
		mock_get_main_channel_ids.assert_called_once_with()
		mock_bot.get_chat_member.assert_called_once_with(main_channel_ids[0], user_id)
		mock_bot.kick_chat_member.assert_not_called()
		mock_bot.unban_chat_member.assert_not_called()

	def test_kicked_chat_member(self, mock_get_main_channel_ids, *args):
		mock_bot = Mock(spec=TeleBot)
		user_id = 21654
		main_channel_ids = [-10012345678, -10087654321, -10045647213, -10025156486]
		mock_get_main_channel_ids.return_value = main_channel_ids
		mock_bot.get_chat_member.side_effect = lambda chat_id, user_id: Mock(status="kicked") if chat_id == main_channel_ids[0] else\
			(Mock(status="member") if chat_id == main_channel_ids[1] else
			(Mock(status="administrator") if chat_id == main_channel_ids[2] else Mock(status="left")))

		manager = Mock()
		manager.attach_mock(mock_bot.get_chat_member, "a")
		manager.attach_mock(mock_bot.kick_chat_member, "b")

		expected_mocks = [
			call.a(main_channel_ids[0], user_id),
			call.a(main_channel_ids[1], user_id),
			call.b(main_channel_ids[1], user_id),
			call.a(main_channel_ids[2], user_id),
			call.a(main_channel_ids[3], user_id)
		]

		user_utils.check_user_id_on_main_channels(mock_bot, user_id)
		mock_get_main_channel_ids.assert_called_once_with()
		mock_bot.unban_chat_member.assert_not_called()
		self.assertEqual(manager.mock_calls, expected_mocks)


	def test_kicked_no_chat_member(self, mock_get_main_channel_ids, *args):
		mock_bot = Mock(spec=TeleBot)
		user_id = 21654
		main_channel_ids = [-10012345678]
		mock_get_main_channel_ids.return_value = main_channel_ids
		mock_bot.get_chat_member.side_effect = ApiTelegramException("content", "", {"error_code": 400, "description": "Bad Request: message to forward not found"})

		user_utils.check_user_id_on_main_channels(mock_bot, user_id)
		mock_get_main_channel_ids.assert_called_once_with()
		mock_bot.get_chat_member.assert_called_once_with(main_channel_ids[0], user_id)
		mock_bot.unban_chat_member.assert_not_called()
		mock_bot.kick_chat_member.assert_not_called()


@patch("user_utils.MEMBER_CACHE", {-10012345678: {"user_ids": [12345, 23465, 13508], "time": 1745924296}})
@patch("time.time", return_value=1745924325)
@patch("user_utils.check_user_id_on_main_channels")
@patch("db_utils.get_main_channel_ids")
class CheckMembersOnMainChannelsTest(TestCase):
	def test_default(self, mock_get_main_channel_ids,
					 mock_check_user_id_on_main_channels, *args):
		mock_bot = Mock(spec=TeleBot)
		mock_bot.user = Mock(id=23465)
		main_channel_ids = [-10012345678]
		mock_get_main_channel_ids.return_value = main_channel_ids

		user_utils.check_members_on_main_channels(mock_bot)
		mock_get_main_channel_ids.assert_called_once_with()
		mock_check_user_id_on_main_channels.assert_has_calls([call(mock_bot, 12345), call(mock_bot, 13508)])




if __name__ == "__main__":
	main()
