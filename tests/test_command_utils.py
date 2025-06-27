from unittest import TestCase, main
from unittest.mock import Mock, patch, call

from pyrogram.types import User
from telebot import TeleBot

import command_utils
import config_utils
from tests import test_helper

@patch("db_utils.is_main_channel_exists", return_value=True)
@patch("user_utils.get_member_ids_channels", return_value={-10012345678: [876542, 123456]})
@patch("config_utils.DISCUSSION_CHAT_DATA", {"-10012345678": -10087654321})
@patch("user_utils.check_user_id_on_main_channels")
class HandleUserChangeTest(TestCase):
    @patch("core_api.get_user")
    @patch("user_utils.get_user")
    @patch("config_utils.update_config")
    @patch("user_utils.load_users")
    @patch("channel_manager.add_new_user_tag_to_channels")
    @patch("user_utils.insert_user_reference")
    def test_set_user_tag(self, mock_insert_user_reference, mock_add_new_user_tag_to_channels, mock_load_users,
                          mock_update_config, mock_utils_get_user, mock_get_user, mock_check_members_on_main_channels,
                          mock_get_member_ids_channels, mock_is_main_channel_exists,  *args):
        mock_bot = Mock(spec=TeleBot)
        bot_chat_id = -10085214763
        discussion_chat_id = -10087654321
        user_tag = "CC"
        user_id = "876542"
        arguments = f"{user_tag} {user_id}"
        comment_text = f"User tag #{user_tag} was added, assigned user is {{USER}}."
        comment_detach = f"User tag #{user_tag} was detached from {{USER}}."
        text = f"User tag #{user_tag} was added, assigned user is {user_id}."
        mock_message = test_helper.create_mock_message("/set_user_tag ", [], bot_chat_id)
        mock_user = Mock(spec=User)
        mock_user.id = int(user_id)
        mock_utils_get_user.return_value = mock_get_user.return_value = mock_user
        mock_insert_user_reference.return_value = text, None
        result = {"CC": 876542}
        config_utils.USER_TAGS = {}

        command_utils.handle_user_change(mock_bot, mock_message, arguments)
        mock_is_main_channel_exists.assert_not_called()
        mock_get_user.assert_called_once_with(user_id)
        mock_utils_get_user.assert_called_once_with(mock_bot, int(user_id))
        mock_update_config.assert_called_once_with({"USER_TAGS": result})
        mock_load_users.assert_called_once_with(mock_bot)
        mock_add_new_user_tag_to_channels.assert_called_once_with(mock_bot, user_tag)
        mock_get_member_ids_channels.assert_called_once_with([-10012345678])
        mock_insert_user_reference.assert_has_calls([call(user_tag, comment_detach), call(user_tag, comment_text)])
        self.assertEqual(mock_insert_user_reference.call_count, 2)
        mock_bot.send_message.assert_has_calls([call(chat_id=discussion_chat_id, text=text, entities=None),
                                                call(chat_id=bot_chat_id, text="User tag was successfully updated.")])
        self.assertEqual(mock_bot.send_message.call_count, 2)
        mock_check_members_on_main_channels.assert_called_once_with(mock_bot, int(user_id))
        self.assertEqual(config_utils.USER_TAGS, result)

    @patch("core_api.get_user")
    @patch("user_utils.get_user")
    @patch("config_utils.update_config")
    @patch("user_utils.load_users")
    @patch("channel_manager.add_new_user_tag_to_channels")
    @patch("user_utils.insert_user_reference")
    def test_set_user_tag_with_main_channel(self, mock_insert_user_reference, mock_add_new_user_tag_to_channels, mock_load_users,
                          mock_update_config, mock_utils_get_user, mock_get_user, mock_check_members_on_main_channels,
                          mock_get_member_ids_channels, mock_is_main_channel_exists,  *args):
        mock_bot = Mock(spec=TeleBot)
        channel_id = "-10012345678"
        bot_chat_id = -10085214763
        discussion_chat_id = -10087654321
        user_tag = "CC"
        user_id = "876542"
        arguments = f"{channel_id} {user_tag} {user_id}"
        comment_text = f"User tag #{user_tag} was added, assigned user is {{USER}}."
        comment_detach = f"User tag #{user_tag} was detached from {{USER}}."
        text = f"User tag #{user_tag} was added, assigned user is {user_id}."
        mock_message = test_helper.create_mock_message("/set_user_tag ", [], bot_chat_id)
        mock_user = Mock(spec=User)
        mock_user.id = int(user_id)
        mock_utils_get_user.return_value = mock_get_user.return_value = mock_user
        mock_insert_user_reference.return_value = text, None
        result = {"CC": 876542}
        config_utils.USER_TAGS = {}

        command_utils.handle_user_change(mock_bot, mock_message, arguments)
        mock_is_main_channel_exists.assert_not_called()
        mock_get_user.assert_called_once_with(user_id)
        mock_utils_get_user.assert_called_once_with(mock_bot, int(user_id))
        mock_update_config.assert_called_once_with({"USER_TAGS": result})
        mock_load_users.assert_called_once_with(mock_bot)
        mock_add_new_user_tag_to_channels.assert_called_once_with(mock_bot, user_tag)
        mock_get_member_ids_channels.assert_called_once_with([-10012345678])
        mock_insert_user_reference.assert_has_calls([call(user_tag, comment_detach), call(user_tag, comment_text)])
        self.assertEqual(mock_insert_user_reference.call_count, 2)
        mock_bot.send_message.assert_has_calls([call(chat_id=discussion_chat_id, text=text, entities=None),
                                                call(chat_id=bot_chat_id, text="User tag was successfully updated.")])
        self.assertEqual(mock_bot.send_message.call_count, 2)
        mock_check_members_on_main_channels.assert_called_once_with(mock_bot, int(user_id))
        self.assertEqual(config_utils.USER_TAGS, result)

    @patch("core_api.get_user")
    @patch("user_utils.get_user")
    @patch("config_utils.update_config")
    @patch("user_utils.load_users")
    @patch("channel_manager.add_new_user_tag_to_channels")
    @patch("user_utils.insert_user_reference")
    def test_set_user_tag_exist(self, mock_insert_user_reference, mock_add_new_user_tag_to_channels, mock_load_users,
                                mock_update_config, mock_utils_get_user, mock_get_user, mock_check_members_on_main_channels,
                                mock_get_member_ids_channels, mock_is_main_channel_exists,  *args):
        mock_bot = Mock(spec=TeleBot)
        channel_id = "-10012345678"
        bot_chat_id = -10085214763
        discussion_chat_id = -10087654321
        user_tag = "CC"
        user_id = "876542"
        user_old = 822542
        arguments = f"{channel_id} {user_tag} {user_id}"
        comment_text = f"User tag #{user_tag} was reassigned to {{USER}}."
        comment_detach = f"User tag #{user_tag} was detached from {{USER}}."
        text = f"User tag #{user_tag} was reassigned to {user_id}."
        mock_message = test_helper.create_mock_message("/set_user_tag ", [], bot_chat_id)
        mock_user = Mock(spec=User)
        mock_user.id = int(user_id)
        mock_utils_get_user.return_value = mock_get_user.return_value = mock_user
        mock_insert_user_reference.return_value = text, None
        result = {"CC": 876542}
        config_utils.USER_TAGS = {"CC": 822542}


        command_utils.handle_user_change(mock_bot, mock_message, arguments)
        mock_is_main_channel_exists.assert_not_called()
        mock_get_user.assert_called_once_with(user_id)
        mock_utils_get_user.assert_called_once_with(mock_bot, int(user_id))
        mock_update_config.assert_called_once_with({"USER_TAGS": result})
        mock_load_users.assert_called_once_with(mock_bot)
        mock_add_new_user_tag_to_channels.assert_not_called()
        mock_get_member_ids_channels.assert_called_once_with([-10012345678])
        mock_insert_user_reference.assert_has_calls([call(user_tag, comment_detach), call(user_tag, comment_text)])
        self.assertEqual(mock_insert_user_reference.call_count, 2)
        mock_bot.send_message.assert_has_calls([call(chat_id=discussion_chat_id, text=text, entities=None),
                                                call(chat_id=bot_chat_id, text="User tag was successfully updated.")])
        self.assertEqual(mock_bot.send_message.call_count, 2)
        mock_check_members_on_main_channels.assert_has_calls([call(mock_bot, user_old), call(mock_bot, int(user_id))])
        self.assertEqual(config_utils.USER_TAGS, result)

    @patch("core_api.get_user")
    @patch("user_utils.get_user")
    @patch("config_utils.update_config")
    @patch("user_utils.load_users")
    @patch("channel_manager.add_new_user_tag_to_channels")
    @patch("user_utils.insert_user_reference")
    def test_set_user_tag_no_workspace(self, mock_insert_user_reference, mock_add_new_user_tag_to_channels,
                                       mock_load_users, mock_update_config, mock_utils_get_user, mock_get_user,
                                       mock_check_members_on_main_channels, mock_get_member_ids_channels,
                                       mock_is_main_channel_exists, *args):
        mock_bot = Mock(spec=TeleBot)
        bot_chat_id = -10085214763
        user_tag = "CC"
        user_id = "876533"
        arguments = f"{user_tag} {user_id}"
        comment_detach = f"User tag #{user_tag} was detached from {{USER}}."
        mock_message = test_helper.create_mock_message("/set_user_tag ", [], bot_chat_id)
        mock_user = Mock(spec=User)
        mock_user.id = int(user_id)
        mock_utils_get_user.return_value = mock_get_user.return_value = mock_user
        result = {"CC": 876533}
        config_utils.USER_TAGS = {}

        command_utils.handle_user_change(mock_bot, mock_message, arguments)
        mock_is_main_channel_exists.assert_not_called()
        mock_get_user.assert_called_once_with(user_id)
        mock_utils_get_user.assert_called_once_with(mock_bot, int(user_id))
        mock_update_config.assert_called_once_with({"USER_TAGS": result})
        mock_load_users.assert_called_once_with(mock_bot)
        mock_add_new_user_tag_to_channels.assert_called_once_with(mock_bot, user_tag)
        mock_get_member_ids_channels.assert_called_once_with([-10012345678])
        mock_insert_user_reference.assert_called_once_with(user_tag, comment_detach)
        mock_bot.send_message.assert_called_once_with(chat_id=bot_chat_id, text="User tag was successfully updated.")
        mock_check_members_on_main_channels.assert_called_once_with(mock_bot, int(user_id))
        self.assertEqual(config_utils.USER_TAGS, result)

    @patch("core_api.get_user")
    @patch("user_utils.get_user")
    @patch("config_utils.update_config")
    @patch("user_utils.load_users")
    @patch("channel_manager.add_new_user_tag_to_channels")
    @patch("user_utils.insert_user_reference")
    def test_set_user_tag_exist_no_workspace(self, mock_insert_user_reference, mock_add_new_user_tag_to_channels,
                                                              mock_load_users, mock_update_config, mock_utils_get_user,
                                                              mock_get_user, mock_check_members_on_main_channels,
                                                              mock_get_member_ids_channels, mock_is_main_channel_exists, *args):
        mock_bot = Mock(spec=TeleBot)
        channel_id = "-10012345678"
        bot_chat_id = -10085214763
        user_tag = "CC"
        user_id = "876533"
        user_old = 822542
        arguments = f"{channel_id} {user_tag} {user_id}"
        comment_detach = f"User tag #{user_tag} was detached from {{USER}}."
        mock_message = test_helper.create_mock_message("/set_user_tag ", [], bot_chat_id)
        mock_user = Mock(spec=User)
        mock_user.id = int(user_id)
        mock_utils_get_user.return_value = mock_get_user.return_value = mock_user
        result = {"CC": 876533}
        config_utils.USER_TAGS = {"CC": 822542}


        command_utils.handle_user_change(mock_bot, mock_message, arguments)
        mock_is_main_channel_exists.assert_not_called()
        mock_get_user.assert_called_once_with(user_id)
        mock_utils_get_user.assert_called_once_with(mock_bot, int(user_id))
        mock_update_config.assert_called_once_with({"USER_TAGS": result})
        mock_load_users.assert_called_once_with(mock_bot)
        mock_add_new_user_tag_to_channels.assert_not_called()
        mock_get_member_ids_channels.assert_called_once_with([-10012345678])
        mock_insert_user_reference.assert_called_once_with(user_tag, comment_detach)
        mock_bot.send_message.assert_called_once_with(chat_id=bot_chat_id, text="User tag was successfully updated.")
        mock_check_members_on_main_channels.assert_has_calls([call(mock_bot, user_old), call(mock_bot, int(user_id))])
        self.assertEqual(config_utils.USER_TAGS, result)

    @patch("core_api.get_user")
    @patch("user_utils.get_user")
    @patch("config_utils.update_config")
    @patch("user_utils.load_users")
    @patch("channel_manager.add_new_user_tag_to_channels")
    @patch("user_utils.insert_user_reference")
    def test_set_user_tag_exist_no_workspace_with_prev_member(self, mock_insert_user_reference, mock_add_new_user_tag_to_channels,
                                                              mock_load_users, mock_update_config, mock_utils_get_user,
                                                              mock_get_user, mock_check_members_on_main_channels,
                                                              mock_get_member_ids_channels, mock_is_main_channel_exists, *args):
        mock_bot = Mock(spec=TeleBot)
        channel_id = "-10012345678"
        bot_chat_id = -10085214763
        discussion_chat_id = -10087654321
        user_tag = "CC"
        user_id = "876533"
        user_old = 876542
        arguments = f"{channel_id} {user_tag} {user_id}"
        comment_detach = f"User tag #{user_tag} was detached from {{USER}}."
        text = f"User tag #{user_tag} was detached from {user_old}."
        mock_message = test_helper.create_mock_message("/set_user_tag ", [], bot_chat_id)
        mock_user = Mock(spec=User)
        mock_user.id = int(user_id)
        mock_utils_get_user.return_value = mock_get_user.return_value = mock_user
        mock_insert_user_reference.return_value = text, None
        result = {"CC": 876533}
        config_utils.USER_TAGS = {"CC": 876542}


        command_utils.handle_user_change(mock_bot, mock_message, arguments)
        mock_is_main_channel_exists.assert_not_called()
        mock_get_user.assert_called_once_with(user_id)
        mock_utils_get_user.assert_called_once_with(mock_bot, int(user_id))
        mock_update_config.assert_called_once_with({"USER_TAGS": result})
        mock_load_users.assert_called_once_with(mock_bot)
        mock_add_new_user_tag_to_channels.assert_not_called()
        mock_get_member_ids_channels.assert_called_once_with([-10012345678])
        mock_insert_user_reference.assert_called_once_with(user_tag, comment_detach)
        mock_bot.send_message.assert_has_calls([call(chat_id=discussion_chat_id, text=text, entities=None),
                                                call(chat_id=bot_chat_id, text="User tag was successfully updated.")])
        self.assertEqual(mock_bot.send_message.call_count, 2)
        mock_check_members_on_main_channels.assert_has_calls([call(mock_bot, user_old), call(mock_bot, int(user_id))])
        self.assertEqual(config_utils.USER_TAGS, result)

    @patch("core_api.get_user")
    @patch("user_utils.get_user")
    @patch("config_utils.update_config")
    @patch("user_utils.load_users")
    @patch("channel_manager.add_new_user_tag_to_channels")
    @patch("user_utils.insert_user_reference")
    def test_set_user_tag_exist_same(self, mock_insert_user_reference, mock_add_new_user_tag_to_channels, mock_load_users,
                                mock_update_config, mock_utils_get_user, mock_get_user, mock_check_members_on_main_channels,
                                mock_get_member_ids_channels, mock_is_main_channel_exists,  *args):
        mock_bot = Mock(spec=TeleBot)
        channel_id = "-10012345678"
        bot_chat_id = -10085214763
        discussion_chat_id = -10087654321
        user_tag = "CC"
        user_id = "876542"
        arguments = f"{channel_id} {user_tag} {user_id}"
        comment_text = f"User tag #{user_tag} was reassigned to {{USER}}."
        comment_detach = f"User tag #{user_tag} was detached from {{USER}}."
        text = f"User tag #{user_tag} was reassigned to {user_id}."
        mock_message = test_helper.create_mock_message("/set_user_tag ", [], bot_chat_id)
        mock_user = Mock(spec=User)
        mock_user.id = int(user_id)
        mock_utils_get_user.return_value = mock_get_user.return_value = mock_user
        mock_insert_user_reference.return_value = text, None
        result = {"CC": 876542}
        config_utils.USER_TAGS = {"CC": 876542}


        command_utils.handle_user_change(mock_bot, mock_message, arguments)
        mock_is_main_channel_exists.assert_not_called()
        mock_get_user.assert_called_once_with(user_id)
        mock_utils_get_user.assert_called_once_with(mock_bot, int(user_id))
        mock_update_config.assert_called_once_with({"USER_TAGS": result})
        mock_load_users.assert_called_once_with(mock_bot)
        mock_add_new_user_tag_to_channels.assert_not_called()
        mock_get_member_ids_channels.assert_called_once_with([-10012345678])
        mock_insert_user_reference.assert_has_calls([call(user_tag, comment_detach), call(user_tag, comment_text)])
        self.assertEqual(mock_insert_user_reference.call_count, 2)
        mock_bot.send_message.assert_has_calls([call(chat_id=discussion_chat_id, text=text, entities=None),
                                                call(chat_id=bot_chat_id, text="User tag was successfully updated.")])
        self.assertEqual(mock_bot.send_message.call_count, 2)
        mock_check_members_on_main_channels.assert_not_called()
        self.assertEqual(config_utils.USER_TAGS, result)

    @patch("core_api.get_user")
    @patch("user_utils.get_user")
    @patch("config_utils.update_config")
    @patch("user_utils.load_users")
    @patch("channel_manager.add_new_user_tag_to_channels")
    @patch("user_utils.insert_user_reference")
    def test_set_user_tag_no_discussion(self, mock_insert_user_reference, mock_add_new_user_tag_to_channels,
                                        mock_load_users, mock_update_config, mock_utils_get_user, mock_get_user,
                                        mock_check_members_on_main_channels, mock_get_member_ids_channels,
                                        mock_is_main_channel_exists,  *args):
        mock_bot = Mock(spec=TeleBot)
        channel_id = "-10012345679"
        bot_chat_id = -10085214763
        user_tag = "CC"
        user_id = "876542"
        arguments = f"{channel_id} {user_tag} {user_id}"
        mock_message = test_helper.create_mock_message("/set_user_tag ", [], bot_chat_id)
        mock_user = Mock(spec=User)
        mock_user.id = int(user_id)
        mock_utils_get_user.return_value = mock_get_user.return_value = mock_user
        result = {"AA": 254632, "CC": 876542}
        config_utils.USER_TAGS = {"AA": 254632}
        config_utils.DISCUSSION_CHAT_DATA = {}

        command_utils.handle_user_change(mock_bot, mock_message, arguments)
        mock_is_main_channel_exists.assert_not_called()
        mock_get_user.assert_called_once_with(user_id)
        mock_utils_get_user.assert_called_once_with(mock_bot, int(user_id))
        mock_update_config.assert_called_once_with({"USER_TAGS": result})
        mock_load_users.assert_called_once_with(mock_bot)
        mock_add_new_user_tag_to_channels.assert_called_once_with(mock_bot, user_tag)
        mock_get_member_ids_channels.assert_not_called()
        mock_insert_user_reference.assert_not_called()
        mock_bot.send_message.assert_called_once_with(chat_id=bot_chat_id, text="User tag was successfully updated.")
        mock_check_members_on_main_channels.assert_called_once_with(mock_bot, int(user_id))
        self.assertEqual(config_utils.USER_TAGS, result)

    @patch("core_api.get_user")
    @patch("user_utils.get_user")
    @patch("config_utils.update_config")
    @patch("user_utils.load_users")
    @patch("channel_manager.add_new_user_tag_to_channels")
    @patch("user_utils.insert_user_reference")
    def test_set_user_tag_not_found_user(self, mock_insert_user_reference, mock_add_new_user_tag_to_channels,
                                         mock_load_users, mock_update_config, mock_utils_get_user, mock_get_user,
                                         mock_check_members_on_main_channels, mock_get_member_ids_channels,
                                         mock_is_main_channel_exists,  *args):
        mock_bot = Mock(spec=TeleBot)
        bot_chat_id = -10085214763
        user_tag = "CC"
        user_id = "876542"
        arguments = f"{user_tag} {user_id}"
        mock_message = test_helper.create_mock_message("/set_user_tag ", [], bot_chat_id)
        mock_user = Mock(spec=User)
        mock_user.id = int(user_id)
        mock_utils_get_user.return_value = mock_get_user.return_value = None
        config_utils.USER_TAGS = {}


        command_utils.handle_user_change(mock_bot, mock_message, arguments)
        mock_is_main_channel_exists.assert_not_called()
        mock_get_user.assert_called_once_with(user_id)
        mock_utils_get_user.assert_called_once_with(mock_bot, user_id)
        mock_bot.send_message.assert_called_once_with(chat_id=bot_chat_id, text=f"Can't find user by provided id.")
        mock_update_config.assert_not_called()
        mock_load_users.assert_not_called()
        mock_add_new_user_tag_to_channels.assert_not_called()
        mock_get_member_ids_channels.assert_not_called()
        mock_insert_user_reference.assert_not_called()
        mock_check_members_on_main_channels.assert_not_called()
        self.assertEqual(config_utils.USER_TAGS, {})

    @patch("core_api.get_user")
    @patch("user_utils.get_user")
    @patch("config_utils.update_config")
    @patch("user_utils.load_users")
    @patch("channel_manager.add_new_user_tag_to_channels")
    @patch("user_utils.insert_user_reference")
    def test_set_user_tag_not_found_username(self, mock_insert_user_reference, mock_add_new_user_tag_to_channels,
                                             mock_load_users, mock_update_config, mock_utils_get_user, mock_get_user,
                                             mock_check_members_on_main_channels, mock_get_member_ids_channels,
                                             mock_is_main_channel_exists,  *args):
        mock_bot = Mock(spec=TeleBot)
        bot_chat_id = -10085214763
        user_tag = "CC"
        user_id = "@username"
        arguments = f"{user_tag} {user_id}"
        mock_message = test_helper.create_mock_message("/set_user_tag ", [], bot_chat_id)
        mock_utils_get_user.return_value = mock_get_user.return_value = None
        config_utils.USER_TAGS = {}

        command_utils.handle_user_change(mock_bot, mock_message, arguments)
        mock_is_main_channel_exists.assert_not_called()
        mock_get_user.assert_called_once_with(user_id)
        mock_utils_get_user.assert_called_once_with(mock_bot, user_id)
        mock_bot.send_message.assert_called_once_with(chat_id=bot_chat_id, text=f"Can't find user by provided username.")
        mock_update_config.assert_not_called()
        mock_load_users.assert_not_called()
        mock_add_new_user_tag_to_channels.assert_not_called()
        mock_get_member_ids_channels.assert_not_called()
        mock_insert_user_reference.assert_not_called()
        mock_check_members_on_main_channels.assert_not_called()
        self.assertEqual(config_utils.USER_TAGS, {})

    @patch("core_api.get_user")
    @patch("user_utils.get_user")
    @patch("config_utils.update_config")
    @patch("user_utils.load_users")
    @patch("channel_manager.add_new_user_tag_to_channels")
    @patch("user_utils.insert_user_reference")
    def test_set_user_tag_not_exists_main_channel(self, mock_insert_user_reference, mock_add_new_user_tag_to_channels,
                                                  mock_load_users, mock_update_config, mock_utils_get_user, mock_get_user,
                                                  mock_check_members_on_main_channels, mock_get_member_ids_channels,
                                                  mock_is_main_channel_exists, *args):
        mock_bot = Mock(spec=TeleBot)
        bot_chat_id = -10085214763
        discussion_chat_id = -10087654321
        user_tag = "CC"
        user_id = "876542"
        arguments = f"{user_tag} {user_id}"
        comment_text = f"User tag #{user_tag} was added, assigned user is {{USER}}."
        comment_detach = f"User tag #{user_tag} was detached from {{USER}}."
        text = f"User tag #{user_tag} was added, assigned user is {user_id}."
        mock_message = test_helper.create_mock_message("/set_user_tag ", [], bot_chat_id)
        mock_user = Mock(spec=User)
        mock_user.id = int(user_id)
        mock_utils_get_user.return_value = mock_get_user.return_value = mock_user
        mock_insert_user_reference.return_value = text, None
        mock_is_main_channel_exists.return_value = False
        result = {"CC": 876542}
        config_utils.USER_TAGS = {}

        command_utils.handle_user_change(mock_bot, mock_message, arguments)
        mock_is_main_channel_exists.assert_not_called()
        mock_get_user.assert_called_once_with(user_id)
        mock_utils_get_user.assert_called_once_with(mock_bot, int(user_id))
        mock_update_config.assert_called_once_with({"USER_TAGS": result})
        mock_load_users.assert_called_once_with(mock_bot)
        mock_add_new_user_tag_to_channels.assert_called_once_with(mock_bot, user_tag)
        mock_get_member_ids_channels.assert_called_once_with([-10012345678])
        mock_insert_user_reference.assert_has_calls([call(user_tag, comment_detach), call(user_tag, comment_text)])
        self.assertEqual(mock_insert_user_reference.call_count, 2)
        mock_bot.send_message.assert_has_calls([call(chat_id=discussion_chat_id, text=text, entities=None),
                                                call(chat_id=bot_chat_id, text="User tag was successfully updated.")])
        self.assertEqual(mock_bot.send_message.call_count, 2)
        mock_check_members_on_main_channels.assert_called_once_with(mock_bot, int(user_id))
        self.assertEqual(config_utils.USER_TAGS, result)

    @patch("core_api.get_user")
    @patch("user_utils.get_user")
    @patch("config_utils.update_config")
    @patch("user_utils.load_users")
    @patch("channel_manager.add_new_user_tag_to_channels")
    @patch("user_utils.insert_user_reference")
    def test_set_user_tag_error_arguments(self, mock_insert_user_reference, mock_add_new_user_tag_to_channels,
                                          mock_load_users, mock_update_config, mock_utils_get_user, mock_get_user,
                                          mock_check_members_on_main_channels, mock_get_member_ids_channels,
                                          mock_is_main_channel_exists, *args):
        mock_bot = Mock(spec=TeleBot)
        channel_id = "-10012345678"
        bot_chat_id = -10085214763
        arguments = f"{channel_id}"
        mock_message = test_helper.create_mock_message("/set_user_tag ", [], bot_chat_id)
        mock_is_main_channel_exists.return_value = False
        config_utils.USER_TAGS = {}

        command_utils.handle_user_change(mock_bot, mock_message, arguments)
        mock_bot.send_message.assert_called_once_with(chat_id=bot_chat_id, text=f"Wrong arguments.")
        mock_is_main_channel_exists.assert_not_called()
        mock_get_user.assert_not_called()
        mock_utils_get_user.assert_not_called()
        mock_update_config.assert_not_called()
        mock_load_users.assert_not_called()
        mock_add_new_user_tag_to_channels.assert_not_called()
        mock_get_member_ids_channels.assert_not_called()
        mock_insert_user_reference.assert_not_called()
        mock_check_members_on_main_channels.assert_not_called()
        self.assertEqual(config_utils.USER_TAGS, {})

    @patch("config_utils.update_config")
    @patch("channel_manager.remove_user_tag_from_channels")
    @patch("user_utils.load_users")
    def test_remove_user_tag(self, mock_load_users, mock_remove_user_tag_from_channels, mock_update_config,
                             mock_check_members_on_main_channels, mock_get_member_ids_channels,
                             mock_is_main_channel_exists,  *args):
        mock_bot = Mock(spec=TeleBot)
        bot_chat_id = -10085214763
        discussion_chat_id = -10087654321
        user_tag = "CC"
        user_id = "876542"
        arguments = f"{user_tag}"
        comment_text = f"User tag #{user_tag} was deleted."
        mock_message = test_helper.create_mock_message("/remove_user_tag ", [], bot_chat_id)
        mock_user = Mock(spec=User)
        mock_user.id = int(user_id)
        config_utils.USER_TAGS = {"CC": 876542}

        command_utils.handle_user_change(mock_bot, mock_message, arguments)
        mock_is_main_channel_exists.assert_not_called()
        mock_update_config.assert_called_once_with({"USER_TAGS": {}})
        mock_remove_user_tag_from_channels.assert_called_once_with(mock_bot, user_tag)
        mock_load_users.assert_called_once_with(mock_bot)
        mock_get_member_ids_channels.assert_called_once_with([-10012345678])
        mock_bot.send_message.assert_has_calls([call(chat_id=discussion_chat_id, text=comment_text),
                                                call(chat_id=bot_chat_id, text="User tag was removed.")])
        self.assertEqual(mock_bot.send_message.call_count, 2)
        mock_check_members_on_main_channels.assert_called_once_with(mock_bot, int(user_id))
        self.assertEqual(config_utils.USER_TAGS, {})

    @patch("config_utils.update_config")
    @patch("channel_manager.remove_user_tag_from_channels")
    @patch("user_utils.load_users")
    def test_remove_user_tag_no_workspace(self, mock_load_users, mock_remove_user_tag_from_channels, mock_update_config,
                             mock_check_members_on_main_channels, mock_get_member_ids_channels,
                             mock_is_main_channel_exists,  *args):
        mock_bot = Mock(spec=TeleBot)
        bot_chat_id = -10085214763
        user_tag = "CC"
        user_id = "876536"
        arguments = f"{user_tag}"
        mock_message = test_helper.create_mock_message("/remove_user_tag ", [], bot_chat_id)
        mock_user = Mock(spec=User)
        mock_user.id = int(user_id)
        config_utils.USER_TAGS = {"CC": 876536}

        command_utils.handle_user_change(mock_bot, mock_message, arguments)
        mock_is_main_channel_exists.assert_not_called()
        mock_update_config.assert_called_once_with({"USER_TAGS": {}})
        mock_remove_user_tag_from_channels.assert_called_once_with(mock_bot, user_tag)
        mock_load_users.assert_called_once_with(mock_bot)
        mock_get_member_ids_channels.assert_called_once_with([-10012345678])
        mock_bot.send_message.assert_called_once_with(chat_id=bot_chat_id, text="User tag was removed.")
        mock_check_members_on_main_channels.assert_called_once_with(mock_bot, int(user_id))
        self.assertEqual(config_utils.USER_TAGS, {})

    @patch("config_utils.update_config")
    @patch("channel_manager.remove_user_tag_from_channels")
    @patch("user_utils.load_users")
    def test_remove_user_tag_with_main_channel(self, mock_load_users, mock_remove_user_tag_from_channels,
                                               mock_update_config, mock_check_members_on_main_channels,
                                               mock_get_member_ids_channels, mock_is_main_channel_exists, *args):
        mock_bot = Mock(spec=TeleBot)
        channel_id = "-10012345678"
        bot_chat_id = -10085214763
        discussion_chat_id = -10087654321
        user_tag = "CC"
        user_id = "876542"
        arguments = f"{channel_id} {user_tag}"
        comment_text = f"User tag #{user_tag} was deleted."
        mock_message = test_helper.create_mock_message("/remove_user_tag ", [], bot_chat_id)
        mock_user = Mock(spec=User)
        mock_user.id = int(user_id)
        config_utils.USER_TAGS = {"CC": 876542}

        command_utils.handle_user_change(mock_bot, mock_message, arguments)
        mock_is_main_channel_exists.assert_not_called()
        mock_update_config.assert_called_once_with({"USER_TAGS": {}})
        mock_remove_user_tag_from_channels.assert_called_once_with(mock_bot, user_tag)
        mock_load_users.assert_called_once_with(mock_bot)
        mock_get_member_ids_channels.assert_called_once_with([-10012345678])
        mock_bot.send_message.assert_has_calls([call(chat_id=discussion_chat_id, text=comment_text),
                                                call(chat_id=bot_chat_id, text="User tag was removed.")])
        self.assertEqual(mock_bot.send_message.call_count, 2)
        mock_check_members_on_main_channels.assert_called_once_with(mock_bot, int(user_id))
        self.assertEqual(config_utils.USER_TAGS, {})

    @patch("config_utils.update_config")
    @patch("channel_manager.remove_user_tag_from_channels")
    @patch("user_utils.load_users")
    def test_remove_user_tag_no_discussion(self, mock_load_users, mock_remove_user_tag_from_channels,
                                           mock_update_config, mock_check_members_on_main_channels,
                                           mock_get_member_ids_channels, mock_is_main_channel_exists, *args):
        mock_bot = Mock(spec=TeleBot)
        bot_chat_id = -10085214763
        user_tag = "CC"
        user_id = "876542"
        arguments = f"{user_tag}"
        mock_message = test_helper.create_mock_message("/remove_user_tag ", [], bot_chat_id)
        mock_user = Mock(spec=User)
        mock_user.id = int(user_id)
        config_utils.DISCUSSION_CHAT_DATA = {}
        config_utils.USER_TAGS = {"CC": 876542, "DD": 12}

        command_utils.handle_user_change(mock_bot, mock_message, arguments)
        mock_is_main_channel_exists.assert_not_called()
        mock_update_config.assert_called_once_with({"USER_TAGS": {"DD": 12}})
        mock_remove_user_tag_from_channels.assert_called_once_with(mock_bot, user_tag)
        mock_load_users.assert_called_once_with(mock_bot)
        mock_get_member_ids_channels.assert_not_called()
        mock_bot.send_message.assert_called_once_with(chat_id=bot_chat_id, text="User tag was removed.")
        mock_check_members_on_main_channels.assert_called_once_with(mock_bot, int(user_id))
        self.assertEqual(config_utils.USER_TAGS, {"DD": 12})

    @patch("config_utils.update_config")
    @patch("channel_manager.remove_user_tag_from_channels")
    @patch("user_utils.load_users")
    def test_remove_user_tag_not_exist_user_tag(self, mock_load_users, mock_remove_user_tag_from_channels,
                                                mock_update_config, mock_check_members_on_main_channels,
                                                mock_get_member_ids_channels, mock_is_main_channel_exists, *args):
        mock_bot = Mock(spec=TeleBot)
        bot_chat_id = -10085214763
        user_tag = "CC"
        user_id = "876542"
        arguments = f"{user_tag}"
        mock_message = test_helper.create_mock_message("/remove_user_tag ", [], bot_chat_id)
        mock_user = Mock(spec=User)
        mock_user.id = int(user_id)
        config_utils.USER_TAGS = {"DD": 12}

        command_utils.handle_user_change(mock_bot, mock_message, arguments)
        mock_is_main_channel_exists.assert_not_called()
        mock_bot.send_message.assert_called_once_with(chat_id=bot_chat_id, text="This user tag doesn't exists.")
        mock_update_config.assert_not_called()
        mock_remove_user_tag_from_channels.assert_not_called()
        mock_load_users.assert_not_called()
        mock_get_member_ids_channels.assert_not_called()
        mock_check_members_on_main_channels.assert_not_called()

    @patch("config_utils.update_config")
    @patch("channel_manager.remove_user_tag_from_channels")
    @patch("user_utils.load_users")
    def test_remove_user_tag_error_arguments(self, mock_load_users, mock_remove_user_tag_from_channels,
                                             mock_update_config, mock_check_members_on_main_channels,
                                             mock_get_member_ids_channels, mock_is_main_channel_exists, *args):
        mock_bot = Mock(spec=TeleBot)
        bot_chat_id = -10085214763
        user_id = "876542"
        arguments = f""
        mock_message = test_helper.create_mock_message("/remove_user_tag ", [], bot_chat_id)
        mock_user = Mock(spec=User)
        mock_user.id = int(user_id)

        command_utils.handle_user_change(mock_bot, mock_message, arguments)
        mock_bot.send_message.assert_called_once_with(chat_id=bot_chat_id, text="Wrong arguments.")
        mock_is_main_channel_exists.assert_not_called()
        mock_update_config.assert_not_called()
        mock_remove_user_tag_from_channels.assert_not_called()
        mock_load_users.assert_not_called()
        mock_get_member_ids_channels.assert_not_called()
        mock_check_members_on_main_channels.assert_not_called()


class HandleHelpCommandTest(TestCase):
    def test_default(self, *args):
        mock_bot = Mock(spec=TeleBot)
        chat_id = -10087654321
        msg_data = test_helper.create_mock_message("", [], chat_id)
        help_text = ""
        help_text += "/set_dump_chat_id <CHAT_ID> — changes dump chat id\n\n"
        help_text += "/set_interval_check_time <MINUTES> — changes delay between interval checks\n\n"
        help_text += "/add_main_channel <CHANNEL_ID> — add main channel\n\n"
        help_text += "/remove_main_channel <CHANNEL_ID> — remove main channel\n\n"
        help_text += "/set_timezone <TIMEZONE> — changes timezone identifier\n"
        help_text += "Example: /set_timezone Europe/Kiev\n\n"
        help_text += "/set_user_tag <TAG> <USERNAME_OR_USER_ID> — add or change username or user id of the tag\n"
        help_text += "Example with username: /set_user_tag aa @username\n"
        help_text += "Example with user id: /set_user_tag aa 321123321\n\n"
        help_text += "/remove_user_tag <TAG> — remove user assigned to specified tag\n"
        help_text += "Example with username: /remove_user_tag aa\n\n"
        help_text += "/set_default_subchannel <MAIN_CHANNEL_ID> <DEFAULT_USER_TAG> <DEFAULT_PRIORITY> — changes default subchannel\n"
        help_text += "Example: /set_default_subchannel -100987987987 aa 1\n\n"
        help_text += "/set_button_text <BUTTON_NAME> <NEW_VALUE> — changes text on one of the buttons\n"
        help_text += "Available buttons: opened, closed, assigned, cc, defer, check, priority\n"
        help_text += "Example: /set_button_text opened Op\n\n"
        help_text += "/set_hashtag_text <HASHTAG_NAME> <NEW_VALUE> — changes hashtag text of one of the service hashtags\n"
        help_text += "Available hashtags: opened, closed, deferred, priority\n"
        help_text += "Example: /set_hashtag_text opened Op\n\n"
        help_text += "/set_remind_without_interaction <MINUTES> — changes timeout for skipping daily reminder if user is interacted with tickets within this time\n"
        help_text += "Example: /set_remind_without_interaction 1440\n\n"

        command_utils.handle_help_command(mock_bot, msg_data, "")
        mock_bot.send_message.assert_called_once_with(chat_id=chat_id, text=help_text)


@patch("config_utils.load_discussion_chat_ids")
@patch("db_utils.delete_main_channel")
@patch("user_utils.send_member_tags")
@patch("forwarding_utils.delete_forwarded_message")
@patch("db_utils.delete_individual_channel")
@patch("db_utils.get_individual_channel_settings")
@patch("db_utils.insert_main_channel")
@patch("db_utils.is_main_channel_exists")
class HandleMainChannelChangeTest(TestCase):
    def test_error_main_id(self, mock_is_main_channel_exists, mock_insert_main_channel, mock_get_individual_channel_settings,
                           mock_delete_individual_channel, mock_delete_forwarded_message, mock_send_member_tags,
                           mock_delete_main_channel, mock_load_discussion_chat_ids, *args):
        mock_bot = Mock(spec=TeleBot)
        channel_id = -10012345678
        arguments = "test_-10087654321"
        mock_message = test_helper.create_mock_message("", [], channel_id)

        command_utils.handle_main_channel_change(mock_bot, mock_message, arguments)
        mock_bot.send_message.assert_called_once_with(chat_id=channel_id, text="Wrong channel id.")
        mock_is_main_channel_exists.assert_not_called()
        mock_insert_main_channel.assert_not_called()
        mock_get_individual_channel_settings.assert_not_called()
        mock_delete_individual_channel.assert_not_called()
        mock_delete_forwarded_message.assert_not_called()
        mock_send_member_tags.assert_not_called()
        mock_delete_main_channel.assert_not_called()
        mock_load_discussion_chat_ids.assert_not_called()

    def test_add_main_channel(self, mock_is_main_channel_exists, mock_insert_main_channel,
                              mock_get_individual_channel_settings, mock_delete_individual_channel,
                              mock_delete_forwarded_message, mock_send_member_tags, mock_delete_main_channel,
                              mock_load_discussion_chat_ids, *args):
        mock_bot = Mock(spec=TeleBot)
        channel_id = -10012345678
        main_channel_id = -10087654321
        settings_id = 2
        arguments = str(main_channel_id)
        mock_message = test_helper.create_mock_message("/add_main_channel -10087654321", [], channel_id)
        mock_is_main_channel_exists.return_value = False
        mock_get_individual_channel_settings.return_value = ("{\"settings_message_id\": " + f"{settings_id}" + "}", "1,2")

        command_utils.handle_main_channel_change(mock_bot, mock_message, arguments)
        mock_is_main_channel_exists.assert_called_once_with(main_channel_id)
        mock_insert_main_channel.assert_called_once_with(main_channel_id)
        mock_get_individual_channel_settings.assert_called_once_with(main_channel_id)
        mock_delete_forwarded_message.assert_called_once_with(mock_bot, main_channel_id, settings_id)
        mock_delete_individual_channel.assert_called_once_with(main_channel_id)
        mock_send_member_tags.assert_called_once_with(main_channel_id, mock_bot)
        mock_bot.send_message.assert_called_once_with(chat_id=channel_id, text="Main channel was successfully added.")
        mock_delete_main_channel.assert_not_called()
        mock_load_discussion_chat_ids.assert_called_once_with(mock_bot)

    def test_add_main_channel_not_exist_settings_message_id(self, mock_is_main_channel_exists, mock_insert_main_channel,
                              mock_get_individual_channel_settings, mock_delete_individual_channel,
                              mock_delete_forwarded_message, mock_send_member_tags,
                              mock_delete_main_channel, mock_load_discussion_chat_ids, *args):
        mock_bot = Mock(spec=TeleBot)
        channel_id = -10012345678
        main_channel_id = -10087654321
        arguments = str(main_channel_id)
        mock_message = test_helper.create_mock_message("/add_main_channel -10087654321", [], channel_id)
        mock_is_main_channel_exists.return_value = False
        mock_get_individual_channel_settings.return_value = ("{}", "1,2")

        command_utils.handle_main_channel_change(mock_bot, mock_message, arguments)
        mock_is_main_channel_exists.assert_called_once_with(main_channel_id)
        mock_insert_main_channel.assert_called_once_with(main_channel_id)
        mock_get_individual_channel_settings.assert_called_once_with(main_channel_id)
        mock_delete_forwarded_message.assert_not_called()
        mock_delete_individual_channel.assert_called_once_with(main_channel_id)
        mock_send_member_tags.assert_called_once_with(main_channel_id, mock_bot)
        mock_bot.send_message.assert_called_once_with(chat_id=channel_id, text="Main channel was successfully added.")
        mock_delete_main_channel.assert_not_called()
        mock_load_discussion_chat_ids.assert_called_once_with(mock_bot)

    def test_add_main_channel_not_exist_individual_settings(self, mock_is_main_channel_exists, mock_insert_main_channel,
                              mock_get_individual_channel_settings, mock_delete_individual_channel,
                              mock_delete_forwarded_message, mock_send_member_tags, mock_delete_main_channel,
                              mock_load_discussion_chat_ids, *args):
        mock_bot = Mock(spec=TeleBot)
        channel_id = -10012345678
        main_channel_id = -10087654321
        arguments = str(main_channel_id)
        mock_message = test_helper.create_mock_message("/add_main_channel -10087654321", [], channel_id)
        mock_is_main_channel_exists.return_value = False
        mock_get_individual_channel_settings.return_value = None

        command_utils.handle_main_channel_change(mock_bot, mock_message, arguments)
        mock_is_main_channel_exists.assert_called_once_with(main_channel_id)
        mock_insert_main_channel.assert_called_once_with(main_channel_id)
        mock_get_individual_channel_settings.assert_called_once_with(main_channel_id)
        mock_delete_forwarded_message.assert_not_called()
        mock_delete_individual_channel.assert_not_called()
        mock_send_member_tags.assert_called_once_with(main_channel_id, mock_bot)
        mock_bot.send_message.assert_called_once_with(chat_id=channel_id, text="Main channel was successfully added.")
        mock_delete_main_channel.assert_not_called()
        mock_load_discussion_chat_ids.assert_called_once_with(mock_bot)

    def test_add_main_channel_exiss(self, mock_is_main_channel_exists, mock_insert_main_channel,
                                    mock_get_individual_channel_settings, mock_delete_individual_channel,
                                    mock_delete_forwarded_message, mock_send_member_tags, mock_delete_main_channel,
                                    mock_load_discussion_chat_ids, *args):
        mock_bot = Mock(spec=TeleBot)
        channel_id = -10012345678
        main_channel_id = -10087654321
        arguments = str(main_channel_id)
        mock_message = test_helper.create_mock_message("/add_main_channel -10087654321", [], channel_id)
        mock_is_main_channel_exists.return_value = True

        command_utils.handle_main_channel_change(mock_bot, mock_message, arguments)
        mock_is_main_channel_exists.assert_called_once_with(main_channel_id)
        mock_insert_main_channel.assert_not_called()
        mock_get_individual_channel_settings.assert_not_called()
        mock_delete_individual_channel.assert_not_called()
        mock_delete_forwarded_message.assert_not_called()
        mock_send_member_tags.assert_not_called()
        mock_bot.send_message.assert_called_once_with(chat_id=channel_id, text="This channel already added.")
        mock_delete_main_channel.assert_not_called()
        mock_load_discussion_chat_ids.assert_not_called()

    def test_delete_main_channel(self, mock_is_main_channel_exists, mock_insert_main_channel,
                                 mock_get_individual_channel_settings, mock_delete_individual_channel,
                                 mock_delete_forwarded_message, mock_send_member_tags, mock_delete_main_channel,
                                 mock_load_discussion_chat_ids, *args):
        mock_bot = Mock(spec=TeleBot)
        channel_id = -10012345678
        main_channel_id = -10087654321
        arguments = str(main_channel_id)
        mock_message = test_helper.create_mock_message("/remove_main_channel -10087654321", [], channel_id)
        mock_is_main_channel_exists.return_value = True

        command_utils.handle_main_channel_change(mock_bot, mock_message, arguments)
        mock_is_main_channel_exists.assert_called_once_with(main_channel_id)
        mock_delete_main_channel.assert_called_once_with(main_channel_id)
        mock_bot.send_message.assert_called_once_with(chat_id=channel_id, text="Main channel was successfully removed.")
        mock_insert_main_channel.assert_not_called()
        mock_get_individual_channel_settings.assert_not_called()
        mock_delete_individual_channel.assert_not_called()
        mock_delete_forwarded_message.assert_not_called()
        mock_send_member_tags.assert_not_called()
        mock_load_discussion_chat_ids.assert_called_once_with(mock_bot)

    def test_delete_main_channel_not_exist(self, mock_is_main_channel_exists, mock_insert_main_channel,
                                           mock_get_individual_channel_settings, mock_delete_individual_channel,
                                           mock_delete_forwarded_message, mock_send_member_tags, mock_delete_main_channel,
                                           mock_load_discussion_chat_ids, *args):
        mock_bot = Mock(spec=TeleBot)
        channel_id = -10012345678
        main_channel_id = -10087654321
        arguments = str(main_channel_id)
        mock_message = test_helper.create_mock_message("/remove_main_channel -10087654321", [], channel_id)
        mock_is_main_channel_exists.return_value = False

        command_utils.handle_main_channel_change(mock_bot, mock_message, arguments)
        mock_is_main_channel_exists.assert_called_once_with(main_channel_id)
        mock_delete_main_channel.assert_not_called()
        mock_bot.send_message.assert_called_once_with(chat_id=channel_id, text="Wrong main channel id.")
        mock_insert_main_channel.assert_not_called()
        mock_get_individual_channel_settings.assert_not_called()
        mock_delete_individual_channel.assert_not_called()
        mock_delete_forwarded_message.assert_not_called()
        mock_send_member_tags.assert_not_called()
        mock_load_discussion_chat_ids.assert_not_called()



if __name__ == "__main__":
    main()
