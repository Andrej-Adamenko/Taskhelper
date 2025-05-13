from asyncio import ProactorEventLoop
from types import coroutine
from unittest import main, TestCase
from unittest.mock import patch, Mock, AsyncMock, ANY, call

from telebot import TeleBot

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
	@patch("time.time")
	@patch("user_utils.set_member_ids_channels")
	def test_get_members_channel(self, mock_set_members_channel, mock_time, *args):
		channel_ids = [-10012345678]
		channel_users = {channel_ids[0]: [12345, 23465]}
		mock_set_members_channel.return_value = channel_users
		mock_time.return_value = 1745924325

		user_utils.get_member_ids_channels(channel_ids)
		mock_set_members_channel.assert_called_once_with(channel_ids)
		mock_time.assert_called_once_with()

	@patch("user_utils.MEMBER_CACHE", {})
	@patch("time.time")
	def test_get_members_channel_result(self, mock_time, mock_get_members, *args):
		channel_ids = [-10012345678]
		ids = [12345, 23465]
		channel_users = {channel_ids[0]: ids}
		mock_get_members.return_value = {channel_ids[0]: [Mock(id=i) for i in ids]}
		mock_time.return_value = 1745924325

		result = user_utils.get_member_ids_channels(channel_ids)
		mock_get_members.assert_called_once_with(channel_ids)
		mock_time.assert_has_calls([call(), call()])
		self.assertEqual(result, channel_users)

	@patch("user_utils.MEMBER_CACHE", {})
	@patch("time.time")
	def test_get_members_channel_empty_result(self, mock_time, mock_get_members, *args):
		channel_ids = [-10012345678]
		channel_users = {channel_ids[0]: []}
		mock_get_members.return_value = []
		mock_time.return_value = 1745924325

		result = user_utils.get_member_ids_channels(channel_ids)
		mock_get_members.assert_called_once_with(channel_ids)
		mock_time.assert_has_calls([call(), call()])
		self.assertEqual(result, channel_users)

	@patch("user_utils.MEMBER_CACHE", {-10012345678: {"user_ids": [12345, 23465, 13508], "time": 1745924296}})
	@patch("time.time")
	@patch("user_utils.set_member_ids_channels")
	def test_get_members_channel_cache(self, mock_set_members_channel, mock_time, *args):
		channel_ids = [-10012345678]
		mock_time.return_value = 1745924325

		user_utils.get_member_ids_channels(channel_ids)
		mock_set_members_channel.assert_not_called()
		mock_time.assert_called_once_with()

	@patch("user_utils.MEMBER_CACHE", {-10012345678: {"user_ids": [12345, 23465], "time": 1745924296},
									   -10087653421: {"user_ids": [12345, 23465, 13508], "time": 1745924296}, })
	@patch("time.time")
	@patch("user_utils.set_member_ids_channels")
	def test_get_members_channel_with_other_channels_result(self, mock_set_members_channel, mock_time, *args):
		channel_ids = [-10012345678]
		ids = [12345, 23465]
		channel_users = {channel_ids[0]: ids}
		mock_time.return_value = 1745924325

		result = user_utils.get_member_ids_channels(channel_ids)
		mock_set_members_channel.assert_not_called()
		mock_time.assert_called_once_with()
		self.assertEqual(result, channel_users)

	@patch("user_utils.MEMBER_CACHE", {-10012345678: {"user_ids": [12345, 23465, 13508], "time": 1745923296}})
	@patch("time.time")
	def test_get_members_channel_cache_expired_time_result(self, mock_time, mock_get_members, *args):
		channel_ids = [-10012345678]
		ids = [12345, 23465]
		channel_users = {channel_ids[0]: ids}
		mock_get_members.return_value = {channel_ids[0]: [Mock(id=i) for i in ids]}
		mock_time.return_value = 1745924325

		result = user_utils.get_member_ids_channels(channel_ids)
		mock_get_members.assert_called_once_with(channel_ids)
		mock_time.assert_has_calls([call(), call()])
		self.assertEqual(result, channel_users)

	@patch("user_utils.MEMBER_CACHE", {-10012345678: {"user_ids": [12345, 23465, 13508], "time": 1745923296}})
	@patch("time.time")
	@patch("user_utils.set_member_ids_channels")
	def test_get_members_channel_cache_expired_time(self, mock_set_members_channel, mock_time, *args):
		channel_ids = [-10012345678]
		channel_users = {channel_ids[0]: [12345, 23465]}
		mock_set_members_channel.return_value = channel_users
		mock_time.return_value = 1745924325

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


if __name__ == "__main__":
	main()
