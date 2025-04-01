from unittest import TestCase, main
from unittest.mock import Mock, patch, call

from pyrogram.types import User
from telebot import TeleBot

import command_utils
import config_utils
from tests import test_helper

@patch("db_utils.is_main_channel_exists", return_value=True)
@patch("db_utils.is_user_tag_exists", return_value = False)
@patch("config_utils.DISCUSSION_CHAT_DATA", {"-10012345678": -10087654321})
class HandleUserChangeTest(TestCase):
    @patch("core_api.get_user")
    @patch("user_utils.get_user")
    @patch("db_utils.insert_or_update_user")
    @patch("config_utils.update_config")
    @patch("user_utils.load_users")
    @patch("channel_manager.add_new_user_tag_to_channels")
    @patch("user_utils.insert_user_reference")
    def test_set_user_tag(self, mock_insert_user_reference, mock_add_new_user_tag_to_channels, mock_load_users,
                          mock_update_config, mock_insert_or_update_user, mock_utils_get_user, mock_get_user,
                          mock_is_user_tag_exists, mock_is_main_channel_exists,  *args):
        mock_bot = Mock(spec=TeleBot)
        bot_chat_id = -10085214763
        discussion_chat_id = -10087654321
        user_tag = "CC"
        user_id = "876542"
        arguments = f"{user_tag} {user_id}"
        comment_text = f"User tag #{user_tag} was added, assigned user is {{USER}}."
        text = f"User tag #{user_tag} was added, assigned user is {user_id}."
        mock_message = test_helper.create_mock_message("/set_user_tag ", [], bot_chat_id)
        mock_user = Mock(spec=User)
        mock_user.id = user_id
        mock_utils_get_user.return_value = mock_get_user.return_value = mock_user
        mock_insert_user_reference.return_value = text, None
        result = {"CC": "876542"}
        config_utils.USER_TAGS = {}

        command_utils.handle_user_change(mock_bot, mock_message, arguments)
        mock_is_main_channel_exists.assert_not_called()
        mock_get_user.assert_called_once_with(user_id)
        mock_utils_get_user.assert_called_once_with(mock_bot, user_id)
        mock_is_user_tag_exists.assert_not_called()
        mock_insert_or_update_user.assert_not_called()
        mock_update_config.assert_called_once_with({"USER_TAGS": result})
        mock_load_users.assert_called_once_with(mock_bot)
        mock_add_new_user_tag_to_channels.assert_called_once_with(mock_bot, user_tag)
        mock_insert_user_reference.assert_called_once_with(user_tag, comment_text)
        mock_bot.send_message.assert_has_calls([call(chat_id=discussion_chat_id, text=text, entities=None),
                                                call(chat_id=bot_chat_id, text="User tag was successfully updated.")])
        self.assertEqual(config_utils.USER_TAGS, result)

    @patch("core_api.get_user")
    @patch("user_utils.get_user")
    @patch("db_utils.insert_or_update_user")
    @patch("config_utils.update_config")
    @patch("user_utils.load_users")
    @patch("channel_manager.add_new_user_tag_to_channels")
    @patch("user_utils.insert_user_reference")
    def test_set_user_tag_with_main_channel(self, mock_insert_user_reference, mock_add_new_user_tag_to_channels, mock_load_users,
                          mock_update_config, mock_insert_or_update_user, mock_utils_get_user, mock_get_user,
                          mock_is_user_tag_exists, mock_is_main_channel_exists,  *args):
        mock_bot = Mock(spec=TeleBot)
        channel_id = "-10012345678"
        bot_chat_id = -10085214763
        discussion_chat_id = -10087654321
        user_tag = "CC"
        user_id = "876542"
        arguments = f"{channel_id} {user_tag} {user_id}"
        comment_text = f"User tag #{user_tag} was added, assigned user is {{USER}}."
        text = f"User tag #{user_tag} was added, assigned user is {user_id}."
        mock_message = test_helper.create_mock_message("/set_user_tag ", [], bot_chat_id)
        mock_user = Mock(spec=User)
        mock_user.id = user_id
        mock_utils_get_user.return_value = mock_get_user.return_value = mock_user
        mock_insert_user_reference.return_value = text, None
        result = {"CC": "876542"}
        config_utils.USER_TAGS = {}

        command_utils.handle_user_change(mock_bot, mock_message, arguments)
        mock_is_main_channel_exists.assert_not_called()
        mock_get_user.assert_called_once_with(user_id)
        mock_utils_get_user.assert_called_once_with(mock_bot, user_id)
        mock_is_user_tag_exists.assert_not_called()
        mock_insert_or_update_user.assert_not_called()
        mock_update_config.assert_called_once_with({"USER_TAGS": result})
        mock_load_users.assert_called_once_with(mock_bot)
        mock_add_new_user_tag_to_channels.assert_called_once_with(mock_bot, user_tag)
        mock_insert_user_reference.assert_called_once_with(user_tag, comment_text)
        mock_bot.send_message.assert_has_calls([call(chat_id=discussion_chat_id, text=text, entities=None),
                                                call(chat_id=bot_chat_id, text="User tag was successfully updated.")])
        self.assertEqual(config_utils.USER_TAGS, result)

    @patch("core_api.get_user")
    @patch("user_utils.get_user")
    @patch("db_utils.insert_or_update_user")
    @patch("config_utils.update_config")
    @patch("user_utils.load_users")
    @patch("channel_manager.add_new_user_tag_to_channels")
    @patch("user_utils.insert_user_reference")
    def test_set_user_tag_exist(self, mock_insert_user_reference, mock_add_new_user_tag_to_channels, mock_load_users,
                                mock_update_config, mock_insert_or_update_user, mock_utils_get_user, mock_get_user,
                                mock_is_user_tag_exists, mock_is_main_channel_exists,  *args):
        mock_bot = Mock(spec=TeleBot)
        channel_id = "-10012345678"
        bot_chat_id = -10085214763
        discussion_chat_id = -10087654321
        user_tag = "CC"
        user_id = "876542"
        arguments = f"{channel_id} {user_tag} {user_id}"
        comment_text = f"User tag #{user_tag} was reassigned to {{USER}}."
        text = f"User tag #{user_tag} was reassigned to {user_id}."
        mock_message = test_helper.create_mock_message("/set_user_tag ", [], bot_chat_id)
        mock_user = Mock(spec=User)
        mock_user.id = user_id
        mock_utils_get_user.return_value = mock_get_user.return_value = mock_user
        mock_insert_user_reference.return_value = text, None
        mock_is_user_tag_exists.return_value = True
        result = {"CC": "876542"}
        config_utils.USER_TAGS = {"CC": "822542"}


        command_utils.handle_user_change(mock_bot, mock_message, arguments)
        mock_is_main_channel_exists.assert_not_called()
        mock_get_user.assert_called_once_with(user_id)
        mock_utils_get_user.assert_called_once_with(mock_bot, user_id)
        mock_is_user_tag_exists.assert_not_called()
        mock_insert_or_update_user.assert_not_called()
        mock_update_config.assert_called_once_with({"USER_TAGS": result})
        mock_load_users.assert_called_once_with(mock_bot)
        mock_add_new_user_tag_to_channels.assert_not_called()
        mock_insert_user_reference.assert_called_once_with(user_tag, comment_text)
        mock_bot.send_message.assert_has_calls([call(chat_id=discussion_chat_id, text=text, entities=None),
                                                call(chat_id=bot_chat_id, text="User tag was successfully updated.")])
        self.assertEqual(config_utils.USER_TAGS, result)

    @patch("core_api.get_user")
    @patch("user_utils.get_user")
    @patch("db_utils.insert_or_update_user")
    @patch("config_utils.update_config")
    @patch("user_utils.load_users")
    @patch("channel_manager.add_new_user_tag_to_channels")
    @patch("user_utils.insert_user_reference")
    def test_set_user_tag_no_discussion(self, mock_insert_user_reference, mock_add_new_user_tag_to_channels,
                                        mock_load_users, mock_update_config, mock_insert_or_update_user,
                                        mock_utils_get_user, mock_get_user, mock_is_user_tag_exists,
                                        mock_is_main_channel_exists,  *args):
        mock_bot = Mock(spec=TeleBot)
        channel_id = "-10012345679"
        bot_chat_id = -10085214763
        user_tag = "CC"
        user_id = "876542"
        arguments = f"{channel_id} {user_tag} {user_id}"
        text = f"User tag #{user_tag} was reassigned to {user_id}."
        mock_message = test_helper.create_mock_message("/set_user_tag ", [], bot_chat_id)
        mock_user = Mock(spec=User)
        mock_user.id = user_id
        mock_utils_get_user.return_value = mock_get_user.return_value = mock_user
        mock_insert_user_reference.return_value = text, None
        result = {"AA": "254632", "CC": "876542"}
        config_utils.USER_TAGS = {"AA": "254632"}
        config_utils.DISCUSSION_CHAT_DATA = {}

        command_utils.handle_user_change(mock_bot, mock_message, arguments)
        mock_is_main_channel_exists.assert_not_called()
        mock_get_user.assert_called_once_with(user_id)
        mock_utils_get_user.assert_called_once_with(mock_bot, user_id)
        mock_is_user_tag_exists.assert_not_called()
        mock_insert_or_update_user.assert_not_called()
        mock_update_config.assert_called_once_with({"USER_TAGS": result})
        mock_load_users.assert_called_once_with(mock_bot)
        mock_add_new_user_tag_to_channels.assert_called_once_with(mock_bot, user_tag)
        mock_insert_user_reference.assert_not_called()
        mock_bot.send_message.assert_called_once_with(chat_id=bot_chat_id, text="User tag was successfully updated.")
        self.assertEqual(config_utils.USER_TAGS, result)

    @patch("core_api.get_user")
    @patch("user_utils.get_user")
    @patch("db_utils.insert_or_update_user")
    @patch("config_utils.update_config")
    @patch("user_utils.load_users")
    @patch("channel_manager.add_new_user_tag_to_channels")
    @patch("user_utils.insert_user_reference")
    def test_set_user_tag_not_found_user(self, mock_insert_user_reference, mock_add_new_user_tag_to_channels,
                                         mock_load_users, mock_update_config, mock_insert_or_update_user,
                                         mock_utils_get_user, mock_get_user, mock_is_user_tag_exists,
                                         mock_is_main_channel_exists,  *args):
        mock_bot = Mock(spec=TeleBot)
        bot_chat_id = -10085214763
        user_tag = "CC"
        user_id = "876542"
        arguments = f"{user_tag} {user_id}"
        mock_message = test_helper.create_mock_message("/set_user_tag ", [], bot_chat_id)
        mock_user = Mock(spec=User)
        mock_user.id = user_id
        mock_utils_get_user.return_value = mock_get_user.return_value = None
        config_utils.USER_TAGS = {}


        command_utils.handle_user_change(mock_bot, mock_message, arguments)
        mock_is_main_channel_exists.assert_not_called()
        mock_get_user.assert_called_once_with(user_id)
        mock_utils_get_user.assert_called_once_with(mock_bot, user_id)
        mock_bot.send_message.assert_called_once_with(chat_id=bot_chat_id, text=f"Can't find user by provided id.")
        mock_is_user_tag_exists.assert_not_called()
        mock_insert_or_update_user.assert_not_called()
        mock_update_config.assert_not_called()
        mock_load_users.assert_not_called()
        mock_add_new_user_tag_to_channels.assert_not_called()
        mock_insert_user_reference.assert_not_called()
        self.assertEqual(config_utils.USER_TAGS, {})

    @patch("core_api.get_user")
    @patch("user_utils.get_user")
    @patch("db_utils.insert_or_update_user")
    @patch("config_utils.update_config")
    @patch("user_utils.load_users")
    @patch("channel_manager.add_new_user_tag_to_channels")
    @patch("user_utils.insert_user_reference")
    def test_set_user_tag_not_found_username(self, mock_insert_user_reference, mock_add_new_user_tag_to_channels,
                                             mock_load_users, mock_update_config, mock_insert_or_update_user,
                                             mock_utils_get_user, mock_get_user, mock_is_user_tag_exists,
                                             mock_is_main_channel_exists,  *args):
        mock_bot = Mock(spec=TeleBot)
        bot_chat_id = -10085214763
        user_tag = "CC"
        user_id = "@username"
        arguments = f"{user_tag} {user_id}"
        mock_message = test_helper.create_mock_message("/set_user_tag ", [], bot_chat_id)
        mock_user = Mock(spec=User)
        mock_user.id = user_id
        mock_utils_get_user.return_value = mock_get_user.return_value = None
        config_utils.USER_TAGS = {}

        command_utils.handle_user_change(mock_bot, mock_message, arguments)
        mock_is_main_channel_exists.assert_not_called()
        mock_get_user.assert_called_once_with(user_id)
        mock_utils_get_user.assert_called_once_with(mock_bot, user_id)
        mock_bot.send_message.assert_called_once_with(chat_id=bot_chat_id, text=f"Can't find user by provided username.")
        mock_is_user_tag_exists.assert_not_called()
        mock_insert_or_update_user.assert_not_called()
        mock_update_config.assert_not_called()
        mock_load_users.assert_not_called()
        mock_add_new_user_tag_to_channels.assert_not_called()
        mock_insert_user_reference.assert_not_called()
        self.assertEqual(config_utils.USER_TAGS, {})

    @patch("core_api.get_user")
    @patch("user_utils.get_user")
    @patch("db_utils.insert_or_update_user")
    @patch("config_utils.update_config")
    @patch("user_utils.load_users")
    @patch("channel_manager.add_new_user_tag_to_channels")
    @patch("user_utils.insert_user_reference")
    def test_set_user_tag_not_exists_main_channel(self, mock_insert_user_reference, mock_add_new_user_tag_to_channels,
                                                  mock_load_users, mock_update_config, mock_insert_or_update_user,
                                                  mock_utils_get_user, mock_get_user, mock_is_user_tag_exists,
                                                  mock_is_main_channel_exists, *args):
        mock_bot = Mock(spec=TeleBot)
        bot_chat_id = -10085214763
        discussion_chat_id = -10087654321
        user_tag = "CC"
        user_id = "876542"
        arguments = f"{user_tag} {user_id}"
        comment_text = f"User tag #{user_tag} was added, assigned user is {{USER}}."
        text = f"User tag #{user_tag} was added, assigned user is {user_id}."
        mock_message = test_helper.create_mock_message("/set_user_tag ", [], bot_chat_id)
        mock_user = Mock(spec=User)
        mock_user.id = user_id
        mock_utils_get_user.return_value = mock_get_user.return_value = mock_user
        mock_insert_user_reference.return_value = text, None
        mock_is_main_channel_exists.return_value = False
        result = {"CC": "876542"}
        config_utils.USER_TAGS = {}

        command_utils.handle_user_change(mock_bot, mock_message, arguments)
        mock_is_main_channel_exists.assert_not_called()
        mock_get_user.assert_called_once_with(user_id)
        mock_utils_get_user.assert_called_once_with(mock_bot, user_id)
        mock_is_user_tag_exists.assert_not_called()
        mock_insert_or_update_user.assert_not_called()
        mock_update_config.assert_called_once_with({"USER_TAGS": result})
        mock_load_users.assert_called_once_with(mock_bot)
        mock_add_new_user_tag_to_channels.assert_called_once_with(mock_bot, user_tag)
        mock_insert_user_reference.assert_called_once_with(user_tag, comment_text)
        mock_bot.send_message.assert_has_calls([call(chat_id=discussion_chat_id, text=text, entities=None),
                                                call(chat_id=bot_chat_id, text="User tag was successfully updated.")])
        self.assertEqual(config_utils.USER_TAGS, result)

    @patch("core_api.get_user")
    @patch("user_utils.get_user")
    @patch("db_utils.insert_or_update_user")
    @patch("config_utils.update_config")
    @patch("user_utils.load_users")
    @patch("channel_manager.add_new_user_tag_to_channels")
    @patch("user_utils.insert_user_reference")
    def test_set_user_tag_error_arguments(self, mock_insert_user_reference, mock_add_new_user_tag_to_channels,
                                          mock_load_users, mock_update_config, mock_insert_or_update_user,
                                          mock_utils_get_user, mock_get_user, mock_is_user_tag_exists,
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
        mock_is_user_tag_exists.assert_not_called()
        mock_insert_or_update_user.assert_not_called()
        mock_update_config.assert_not_called()
        mock_load_users.assert_not_called()
        mock_add_new_user_tag_to_channels.assert_not_called()
        mock_insert_user_reference.assert_not_called()
        self.assertEqual(config_utils.USER_TAGS, {})

    @patch("db_utils.delete_user_by_tag")
    @patch("config_utils.update_config")
    @patch("channel_manager.remove_user_tag_from_channels")
    @patch("user_utils.load_users")
    def test_remove_user_tag(self, mock_load_users, mock_remove_user_tag_from_channels, mock_update_config,
                             mock_delete_user_by_tag, mock_is_user_tag_exists, mock_is_main_channel_exists,  *args):
        mock_bot = Mock(spec=TeleBot)
        bot_chat_id = -10085214763
        discussion_chat_id = -10087654321
        user_tag = "CC"
        user_id = "876542"
        arguments = f"{user_tag}"
        comment_text = f"User tag #{user_tag} was deleted."
        mock_message = test_helper.create_mock_message("/remove_user_tag ", [], bot_chat_id)
        mock_user = Mock(spec=User)
        mock_user.id = user_id
        config_utils.USER_TAGS = {"CC": "876542"}

        command_utils.handle_user_change(mock_bot, mock_message, arguments)
        mock_is_main_channel_exists.assert_not_called()
        mock_is_user_tag_exists.assert_not_called()
        mock_delete_user_by_tag.assert_not_called()
        mock_update_config.assert_called_once_with({"USER_TAGS": {}})
        mock_remove_user_tag_from_channels.assert_called_once_with(mock_bot, user_tag)
        mock_load_users.assert_called_once_with(mock_bot)
        mock_bot.send_message.assert_has_calls([call(chat_id=discussion_chat_id, text=comment_text),
                                                call(chat_id=bot_chat_id, text="User tag was removed.")])
        self.assertEqual(config_utils.USER_TAGS, {})

    @patch("db_utils.delete_user_by_tag")
    @patch("config_utils.update_config")
    @patch("channel_manager.remove_user_tag_from_channels")
    @patch("user_utils.load_users")
    def test_remove_user_tag_with_main_channel(self, mock_load_users, mock_remove_user_tag_from_channels,
                                               mock_update_config, mock_delete_user_by_tag, mock_is_user_tag_exists,
                                               mock_is_main_channel_exists,  *args):
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
        mock_user.id = user_id
        config_utils.USER_TAGS = {"CC": "876542"}

        command_utils.handle_user_change(mock_bot, mock_message, arguments)
        mock_is_main_channel_exists.assert_not_called()
        mock_is_user_tag_exists.assert_not_called()
        mock_delete_user_by_tag.assert_not_called()
        mock_update_config.assert_called_once_with({"USER_TAGS": {}})
        mock_remove_user_tag_from_channels.assert_called_once_with(mock_bot, user_tag)
        mock_load_users.assert_called_once_with(mock_bot)
        mock_bot.send_message.assert_has_calls([call(chat_id=discussion_chat_id, text=comment_text),
                                                call(chat_id=bot_chat_id, text="User tag was removed.")])
        self.assertEqual(config_utils.USER_TAGS, {})

    @patch("db_utils.delete_user_by_tag")
    @patch("config_utils.update_config")
    @patch("channel_manager.remove_user_tag_from_channels")
    @patch("user_utils.load_users")
    def test_remove_user_tag_no_discussion(self, mock_load_users, mock_remove_user_tag_from_channels,
                                           mock_update_config, mock_delete_user_by_tag, mock_is_user_tag_exists,
                                           mock_is_main_channel_exists,  *args):
        mock_bot = Mock(spec=TeleBot)
        bot_chat_id = -10085214763
        user_tag = "CC"
        user_id = "876542"
        arguments = f"{user_tag}"
        mock_message = test_helper.create_mock_message("/remove_user_tag ", [], bot_chat_id)
        mock_user = Mock(spec=User)
        mock_user.id = user_id
        config_utils.DISCUSSION_CHAT_DATA = {}
        config_utils.USER_TAGS = {"CC": "876542", "DD": "12"}

        command_utils.handle_user_change(mock_bot, mock_message, arguments)
        mock_is_main_channel_exists.assert_not_called()
        mock_is_user_tag_exists.assert_not_called()
        mock_delete_user_by_tag.assert_not_called()
        mock_update_config.assert_called_once_with({"USER_TAGS": {"DD": "12"}})
        mock_remove_user_tag_from_channels.assert_called_once_with(mock_bot, user_tag)
        mock_load_users.assert_called_once_with(mock_bot)
        mock_bot.send_message.assert_called_once_with(chat_id=bot_chat_id, text="User tag was removed.")
        self.assertEqual(config_utils.USER_TAGS, {"DD": "12"})

    @patch("db_utils.delete_user_by_tag")
    @patch("config_utils.update_config")
    @patch("channel_manager.remove_user_tag_from_channels")
    @patch("user_utils.load_users")
    def test_remove_user_tag_not_exist_user_tag(self, mock_load_users, mock_remove_user_tag_from_channels,
                                                mock_update_config, mock_delete_user_by_tag, mock_is_user_tag_exists,
                                                mock_is_main_channel_exists,  *args):
        mock_bot = Mock(spec=TeleBot)
        bot_chat_id = -10085214763
        user_tag = "CC"
        user_id = "876542"
        arguments = f"{user_tag}"
        mock_message = test_helper.create_mock_message("/remove_user_tag ", [], bot_chat_id)
        mock_user = Mock(spec=User)
        mock_user.id = user_id
        config_utils.USER_TAGS = {"DD": "12"}

        command_utils.handle_user_change(mock_bot, mock_message, arguments)
        mock_is_main_channel_exists.assert_not_called()
        mock_is_user_tag_exists.assert_not_called()
        mock_bot.send_message.assert_called_once_with(chat_id=bot_chat_id, text="This user tag doesn't exists.")
        mock_delete_user_by_tag.assert_not_called()
        mock_update_config.assert_not_called()
        mock_remove_user_tag_from_channels.assert_not_called()
        mock_load_users.assert_not_called()

    @patch("db_utils.delete_user_by_tag")
    @patch("config_utils.update_config")
    @patch("channel_manager.remove_user_tag_from_channels")
    @patch("user_utils.load_users")
    def test_remove_user_tag_error_arguments(self, mock_load_users, mock_remove_user_tag_from_channels,
                                             mock_update_config, mock_delete_user_by_tag, mock_is_user_tag_exists,
                                             mock_is_main_channel_exists,  *args):
        mock_bot = Mock(spec=TeleBot)
        bot_chat_id = -10085214763
        user_id = "876542"
        arguments = f""
        mock_message = test_helper.create_mock_message("/remove_user_tag ", [], bot_chat_id)
        mock_user = Mock(spec=User)
        mock_user.id = user_id

        command_utils.handle_user_change(mock_bot, mock_message, arguments)
        mock_bot.send_message.assert_called_once_with(chat_id=bot_chat_id, text="Wrong arguments.")
        mock_is_main_channel_exists.assert_not_called()
        mock_is_user_tag_exists.assert_not_called()
        mock_delete_user_by_tag.assert_not_called()
        mock_update_config.assert_not_called()
        mock_remove_user_tag_from_channels.assert_not_called()
        mock_load_users.assert_not_called()



if __name__ == "__main__":
    main()
