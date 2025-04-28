from unittest import TestCase, main
from unittest.mock import patch

import config_utils


@patch("db_utils.is_users_table_exists", return_value=True)
@patch("db_utils.get_all_users")
@patch("logging.error")
@patch("config_utils.update_config")
@patch("db_utils.delete_users_table")
class AddUsersFromDB(TestCase):
	def test_add_user(self, mock_delete_users_table, mock_update_config, mock_error, mock_get_all_users,
					  mock_is_users_table_exists, *args):
		main_channel_id = -1087654321
		user_tag = "CC"
		user_id = 8534562
		mock_get_all_users.return_value = [(main_channel_id, user_id, user_tag)]
		config_utils.USER_TAGS = {}

		config_utils.add_users_from_db()
		mock_is_users_table_exists.assert_called_once_with()
		mock_get_all_users.assert_called_once_with()
		mock_error.assert_not_called()
		self.assertEqual(config_utils.USER_TAGS, {user_tag: user_id})
		mock_update_config.assert_called_once_with({"USER_TAGS": {user_tag: user_id}})
		mock_delete_users_table.assert_called_once_with()

	def test_add_user_exist_user_tags(self, mock_delete_users_table, mock_update_config, mock_error,
									  mock_get_all_users, mock_is_users_table_exists, *args):
		main_channel_id = -1087654321
		user_tag = "CC"
		user_tag1 = "DD"
		user_id = 8534562
		user_id1 = 8534542
		mock_get_all_users.return_value = [(main_channel_id, user_id, user_tag)]
		config_utils.USER_TAGS = {user_tag1: user_id1}

		config_utils.add_users_from_db()
		mock_is_users_table_exists.assert_called_once_with()
		mock_get_all_users.assert_called_once_with()
		mock_error.assert_not_called()
		self.assertEqual(config_utils.USER_TAGS, {user_tag: user_id, user_tag1: user_id1})
		mock_update_config.assert_called_once_with({"USER_TAGS": {user_tag: user_id, user_tag1: user_id1}})
		mock_delete_users_table.assert_called_once_with()

	def test_add_few_user(self, mock_delete_users_table, mock_update_config, mock_error,
						  mock_get_all_users, mock_is_users_table_exists, *args):
		main_channel_id = -1087654321
		user_tag = "CC"
		user_tag1 = "DD"
		user_id = 8534562
		user_id1 = 8534542
		mock_get_all_users.return_value = [(main_channel_id, user_id, user_tag), (main_channel_id, user_id1, user_tag1)]
		config_utils.USER_TAGS = {}

		config_utils.add_users_from_db()
		mock_is_users_table_exists.assert_called_once_with()
		mock_get_all_users.assert_called_once_with()
		mock_error.assert_not_called()
		self.assertEqual(config_utils.USER_TAGS, {user_tag: user_id, user_tag1: user_id1})
		mock_update_config.assert_called_once_with({"USER_TAGS": {user_tag: user_id, user_tag1: user_id1}})
		mock_delete_users_table.assert_called_once_with()

	def test_add_user_not_empty_user_tag(self, mock_delete_users_table, mock_update_config, mock_error,
										 mock_get_all_users, mock_is_users_table_exists, *args):
		main_channel_id = -1087654321
		user_tag = "CC"
		user_id = 8534562
		user_id1 = 2054214
		config_utils.USER_TAGS = {user_tag: user_id}
		mock_get_all_users.return_value = [(main_channel_id, user_id1, user_tag)]

		config_utils.add_users_from_db()
		mock_is_users_table_exists.assert_called_once_with()
		mock_get_all_users.assert_called_once_with()
		mock_error.assert_not_called()
		self.assertEqual(config_utils.USER_TAGS, {user_tag: user_id})
		mock_update_config.assert_called_once_with({"USER_TAGS": {user_tag: user_id}})
		mock_delete_users_table.assert_called_once_with()

	def test_add_user_no_table(self, mock_delete_users_table, mock_update_config, mock_error,
							   mock_get_all_users, mock_is_users_table_exists, *args):
		user_tag = "CC"
		user_id = 8534562
		config_utils.USER_TAGS = {user_tag: user_id}
		mock_is_users_table_exists.return_value = False

		config_utils.add_users_from_db()
		mock_is_users_table_exists.assert_called_once_with()
		mock_get_all_users.assert_not_called()
		mock_error.assert_not_called()
		self.assertEqual(config_utils.USER_TAGS, {user_tag: user_id})
		mock_update_config.assert_not_called()
		mock_delete_users_table.assert_not_called()

	def test_add_user_error_get_all_users(self, mock_delete_users_table, mock_update_config, mock_error,
										  mock_get_all_users, mock_is_users_table_exists, *args):
		user_tag = "CC"
		user_id = 8534562
		E = Exception()
		config_utils.USER_TAGS = {user_tag: user_id}
		mock_is_users_table_exists.return_value = True
		mock_get_all_users.side_effect = E

		config_utils.add_users_from_db()
		mock_is_users_table_exists.assert_called_once_with()
		mock_get_all_users.assert_called_once_with()
		mock_error.assert_called_once_with(f"Error with get all users - {E}")
		self.assertEqual(config_utils.USER_TAGS, {user_tag: user_id})
		mock_update_config.assert_not_called()
		mock_delete_users_table.assert_not_called()


if __name__ == "__main__":
	main()
