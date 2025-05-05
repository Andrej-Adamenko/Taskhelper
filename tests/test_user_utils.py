from unittest import main, TestCase
from unittest.mock import patch, Mock, AsyncMock

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


@patch("core_api.get_members", new_callable=AsyncMock)
class MembersChannel(TestCase):
	@patch("user_utils.MEMBER_CACHE", {})
	@patch("time.time")
	@patch("user_utils.set_member_ids_channel")
	def test_get_members_channel(self, mock_set_members_channel, mock_time, *args):
		channel_id = -10012345678
		user_ids = [12345, 23465]
		mock_set_members_channel.return_value = user_ids
		mock_time.return_value = 1745924325

		result = user_utils.get_member_ids_channel(channel_id)
		mock_set_members_channel.assert_called_once_with(channel_id)
		mock_time.assert_called_once_with()
		self.assertEqual(result, user_ids)

	@patch("user_utils.MEMBER_CACHE", {-10012345678: {"user_ids": [12345, 23465, 13508], "time": 1745924296}})
	@patch("time.time")
	@patch("user_utils.set_member_ids_channel")
	def test_get_members_channel_cache(self, mock_set_members_channel, mock_time, *args):
		channel_id = -10012345678
		mock_time.return_value = 1745924325

		result = user_utils.get_member_ids_channel(channel_id)
		mock_set_members_channel.assert_not_called()
		mock_time.assert_called_once_with()
		self.assertEqual(result, [12345, 23465, 13508])

	@patch("user_utils.MEMBER_CACHE", {-10012345678: {"user_ids": [12345, 23465, 13508], "time": 1745923296}})
	@patch("time.time")
	@patch("user_utils.set_member_ids_channel")
	def test_get_members_channel_cache_expired_time(self, mock_set_members_channel, mock_time, *args):
		channel_id = -10012345678
		user_ids = [12345, 23465]
		mock_set_members_channel.return_value = user_ids
		mock_time.return_value = 1745924325

		result = user_utils.get_member_ids_channel(channel_id)
		mock_set_members_channel.assert_called_once_with(channel_id)
		mock_time.assert_called_once_with()
		self.assertEqual(result, user_ids)

	def test_set_members_channel(self, mock_get_members, *args):
		channel_id = -10012345678
		ids = [155, 4864, 6846]
		mock_get_members.return_value = [Mock(id=i) for i in ids]

		result = user_utils.set_member_ids_channel(channel_id)
		mock_get_members.assert_awaited_once_with(channel_id)
		self.assertEqual(result, ids)

	def test_set_members_channel_no_members(self, mock_get_members, *args):
		channel_id = -10012345678
		mock_get_members.return_value = []

		result = user_utils.set_member_ids_channel(channel_id)
		mock_get_members.assert_awaited_once_with(channel_id)
		self.assertEqual(result, [])

if __name__ == "__main__":
	main()
