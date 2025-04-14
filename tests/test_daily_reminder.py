from unittest import TestCase, main
from unittest.mock import Mock, patch, call

from telebot import TeleBot

import config_utils
import daily_reminder
from daily_reminder import send_daily_reminders


@patch("config_utils.REMINDER_TIME_WITHOUT_INTERACTION", 24 * 60)
class SendDailyRemindersTest(TestCase):
	@patch("db_utils.find_copied_message_in_channel", side_effect=[None, 222])
	@patch("db_utils.is_user_reminder_data_exists", return_value=True)
	@patch("db_utils.get_last_interaction_time", return_value=None)
	@patch("time.time", return_value=1700000000)
	@patch("forwarding_utils.delete_forwarded_message")
	@patch("interval_updating_utils.update_older_message")
	@patch("db_utils.insert_or_update_remind_time")
	@patch("db_utils.get_main_channel_id")
	@patch("db_utils.get_all_users")
	@patch("daily_reminder.get_message_for_reminding")
	def test_missing_ticket_for_reminding(self, mock_get_message_for_reminding, mock_get_all_users,
										  mock_get_main_channel_id, mock_insert_or_update_remind_time, *args):
		user_tag = "aa"
		user_id = 12345678
		main_channel_id = -100123456789
		mock_bot = Mock(spec=TeleBot)
		missing_ticket = [123, -100987654321, 33]  # main_message_id, copied_channel_id, copied_message_id
		normal_ticket = [198, -100111122222, 11]  # main_message_id, copied_channel_id, copied_message_id
		mock_get_main_channel_id.return_value = main_channel_id
		config_utils.USER_TAGS = {user_tag: user_id}
		mock_get_message_for_reminding.side_effect = [missing_ticket, normal_ticket]

		send_daily_reminders(mock_bot)
		mock_get_all_users.assert_not_called()
		self.assertEqual(mock_get_message_for_reminding.call_count, 2)
		mock_get_message_for_reminding.assert_has_calls([call(user_id, user_tag), call(user_id, user_tag)])
		mock_insert_or_update_remind_time.assert_called_once_with(198, main_channel_id, user_tag, 1700000000)

	@patch("db_utils.is_user_reminder_data_exists", return_value=True)
	@patch("db_utils.get_last_interaction_time", return_value=None)
	@patch("time.time", return_value=1700000000)
	@patch("forwarding_utils.delete_forwarded_message")
	@patch("interval_updating_utils.update_older_message")
	@patch("db_utils.insert_or_update_remind_time")
	@patch("db_utils.get_main_channel_id")
	@patch("db_utils.get_all_users")
	@patch("daily_reminder.get_message_for_reminding", return_value=None)
	def test_no_tickets_for_reminding(self, mock_get_message_for_reminding, mock_get_all_users, mock_get_main_channel_id,
									  mock_insert_or_update_remind_time, *args):
		user_tag = "aa"
		user_id = 12345678
		main_channel_id = -100123456789
		mock_bot = Mock(spec=TeleBot)
		config_utils.USER_TAGS = {user_tag: user_id}
		mock_get_main_channel_id.return_value = main_channel_id

		send_daily_reminders(mock_bot)
		mock_get_all_users.assert_not_called()
		mock_get_main_channel_id.assert_called_once_with()
		mock_get_message_for_reminding.assert_called_once_with(user_id, user_tag)
		self.assertEqual(mock_get_message_for_reminding.call_count, 1)
		mock_insert_or_update_remind_time.assert_not_called()

@patch("logging.info")
@patch("db_utils.get_main_message_sender")
@patch("db_utils.get_user_individual_channels")
@patch("db_utils.get_tickets_for_reminding")
class GetMessageForRemindingTest(TestCase):
	def test_default(self, mock_get_tickets_for_reminding, mock_get_user_individual_channels,
					 mock_get_main_message_sender, mock_info, *args):
		main_channel_id = -10087654231
		main_message_id = 124
		copied_channel_id = -10032164587
		copied_message_id = 165
		user_id = 12354
		user_tag = "CC"
		channel_ids = [(copied_channel_id, '{"remind": ["assigned","cc","reported"]}')]
		ticket_data = [(copied_channel_id, copied_message_id, main_channel_id, main_message_id, "CC,BB", 2, "", "")]
		mock_get_user_individual_channels.return_value = channel_ids
		mock_get_tickets_for_reminding.return_value = ticket_data
		mock_get_main_message_sender.return_value = user_id

		result = daily_reminder.get_message_for_reminding(user_id, user_tag)
		mock_get_tickets_for_reminding.assert_called_once_with(user_id, user_tag)
		mock_get_user_individual_channels.assert_called_once_with(user_id)
		mock_get_main_message_sender.assert_not_called()
		mock_info.assert_not_called()
		self.assertEqual(result, (main_message_id, copied_channel_id, copied_message_id))

	def test_no_ticket_data(self, mock_get_tickets_for_reminding, mock_get_user_individual_channels,
					 mock_get_main_message_sender, mock_info, *args):
		main_channel_id = -10087654231
		user_id = 12354
		user_tag = "CC"
		mock_get_tickets_for_reminding.return_value = None

		result = daily_reminder.get_message_for_reminding(user_id, user_tag)
		mock_get_tickets_for_reminding.assert_called_once_with(user_id, user_tag)
		mock_info.assert_called_once_with(f"No tickets for reminding were found in {user_tag}")
		mock_get_user_individual_channels.assert_not_called()
		mock_get_main_message_sender.assert_not_called()
		self.assertEqual(result, None)

	def test_empty_remind(self, mock_get_tickets_for_reminding, mock_get_user_individual_channels,
					 mock_get_main_message_sender, mock_info, *args):
		main_channel_id = -10087654231
		main_message_id = 124
		copied_channel_id = -10032164587
		copied_message_id = 165
		user_id = 12354
		user_tag = "CC"
		channel_ids = [(copied_channel_id, '{"remind": []}')]
		ticket_data = [(copied_channel_id, copied_message_id, main_channel_id, main_message_id, "CC,BB", 2, "", "")]
		mock_get_user_individual_channels.return_value = channel_ids
		mock_get_tickets_for_reminding.return_value = ticket_data
		mock_get_main_message_sender.return_value = user_id

		result = daily_reminder.get_message_for_reminding(user_id, user_tag)
		mock_get_tickets_for_reminding.assert_called_once_with(user_id, user_tag)
		mock_get_user_individual_channels.assert_called_once_with(user_id)
		mock_get_main_message_sender.assert_not_called()
		mock_info.assert_called_once_with(f"No forwarded tickets for reminding were found in {user_tag}")
		self.assertEqual(result, None)

	def test_invalid(self, mock_get_tickets_for_reminding, mock_get_user_individual_channels,
					 mock_get_main_message_sender, mock_info, *args):
		main_channel_id = -10087654231
		main_message_id = 124
		copied_channel_id = -10032164587
		copied_message_id = 165
		user_id = 12354
		user_tag = "CC"
		channel_ids = [(copied_channel_id, '{"remind": ["assigned","cc","reported"]}')]
		ticket_data = [(copied_channel_id, copied_message_id, main_channel_id, main_message_id, "BB,DD", 2, "", "")]
		mock_get_user_individual_channels.return_value = channel_ids
		mock_get_tickets_for_reminding.return_value = ticket_data
		mock_get_main_message_sender.return_value = 12585

		result = daily_reminder.get_message_for_reminding(user_id, user_tag)
		mock_get_tickets_for_reminding.assert_called_once_with(user_id, user_tag)
		mock_get_user_individual_channels.assert_called_once_with(user_id)
		mock_get_main_message_sender.assert_called_once_with(main_channel_id, main_message_id)
		mock_info.assert_called_once_with(f"No forwarded tickets for reminding were found in {user_tag}")
		self.assertEqual(result, None)

	def test_assigned_valid(self, mock_get_tickets_for_reminding, mock_get_user_individual_channels,
					 mock_get_main_message_sender, mock_info, *args):
		main_channel_id = -10087654231
		main_message_id = 124
		copied_channel_id = -10032164587
		copied_message_id = 165
		user_id = 12354
		user_tag = "CC"
		channel_ids = [(copied_channel_id, '{"remind": ["assigned"]}')]
		ticket_data = [(copied_channel_id, copied_message_id, main_channel_id, main_message_id, "CC,BB", 2, "", "")]
		mock_get_user_individual_channels.return_value = channel_ids
		mock_get_tickets_for_reminding.return_value = ticket_data
		mock_get_main_message_sender.return_value = user_id

		result = daily_reminder.get_message_for_reminding(user_id, user_tag)
		mock_get_tickets_for_reminding.assert_called_once_with(user_id, user_tag)
		mock_get_user_individual_channels.assert_called_once_with(user_id)
		mock_get_main_message_sender.assert_not_called()
		mock_info.assert_not_called()
		self.assertEqual(result, (main_message_id, copied_channel_id, copied_message_id))

	def test_assigned_invalid(self, mock_get_tickets_for_reminding, mock_get_user_individual_channels,
					 mock_get_main_message_sender, mock_info, *args):
		main_channel_id = -10087654231
		main_message_id = 124
		copied_channel_id = -10032164587
		copied_message_id = 165
		user_id = 12354
		user_tag = "CC"
		channel_ids = [(copied_channel_id, '{"remind": ["assigned"]}')]
		ticket_data = [(copied_channel_id, copied_message_id, main_channel_id, main_message_id, "AA,CC,BB", 2, "", "")]
		mock_get_user_individual_channels.return_value = channel_ids
		mock_get_tickets_for_reminding.return_value = ticket_data
		mock_get_main_message_sender.return_value = user_id

		result = daily_reminder.get_message_for_reminding(user_id, user_tag)
		mock_get_tickets_for_reminding.assert_called_once_with(user_id, user_tag)
		mock_get_user_individual_channels.assert_called_once_with(user_id)
		mock_get_main_message_sender.assert_not_called()
		mock_info.assert_called_once_with(f"No forwarded tickets for reminding were found in {user_tag}")
		self.assertEqual(result, None)

	def test_followed_valid(self, mock_get_tickets_for_reminding, mock_get_user_individual_channels,
					 mock_get_main_message_sender, mock_info, *args):
		main_channel_id = -10087654231
		main_message_id = 124
		copied_channel_id = -10032164587
		copied_message_id = 165
		user_id = 12354
		user_tag = "CC"
		channel_ids = [(copied_channel_id, '{"remind": ["cced"]}')]
		ticket_data = [(copied_channel_id, copied_message_id, main_channel_id, main_message_id, "AA,BB,CC", 2, "", "")]
		mock_get_user_individual_channels.return_value = channel_ids
		mock_get_tickets_for_reminding.return_value = ticket_data
		mock_get_main_message_sender.return_value = user_id

		result = daily_reminder.get_message_for_reminding(user_id, user_tag)
		mock_get_tickets_for_reminding.assert_called_once_with(user_id, user_tag)
		mock_get_user_individual_channels.assert_called_once_with(user_id)
		mock_get_main_message_sender.assert_not_called()
		mock_info.assert_not_called()
		self.assertEqual(result, (main_message_id, copied_channel_id, copied_message_id))

	def test_followed_invalid(self, mock_get_tickets_for_reminding, mock_get_user_individual_channels,
					 mock_get_main_message_sender, mock_info, *args):
		main_channel_id = -10087654231
		main_message_id = 124
		copied_channel_id = -10032164587
		copied_message_id = 165
		user_id = 12354
		user_tag = "CC"
		channel_ids = [(copied_channel_id, '{"remind": ["cced"]}')]
		ticket_data = [(copied_channel_id, copied_message_id, main_channel_id, main_message_id, "CC,BB,AA", 2, "", "")]
		mock_get_user_individual_channels.return_value = channel_ids
		mock_get_tickets_for_reminding.return_value = ticket_data
		mock_get_main_message_sender.return_value = user_id

		result = daily_reminder.get_message_for_reminding(user_id, user_tag)
		mock_get_tickets_for_reminding.assert_called_once_with(user_id, user_tag)
		mock_get_user_individual_channels.assert_called_once_with(user_id)
		mock_get_main_message_sender.assert_not_called()
		mock_info.assert_called_once_with(f"No forwarded tickets for reminding were found in {user_tag}")
		self.assertEqual(result, None)

	def test_reported_valid(self, mock_get_tickets_for_reminding, mock_get_user_individual_channels,
					 mock_get_main_message_sender, mock_info, *args):
		main_channel_id = -10087654231
		main_message_id = 124
		copied_channel_id = -10032164587
		copied_message_id = 165
		user_id = 12354
		user_tag = "CC"
		channel_ids = [(copied_channel_id, '{"remind": ["reported"]}')]
		ticket_data = [(copied_channel_id, copied_message_id, main_channel_id, main_message_id, "AA,BB,CC", 2, "", "")]
		mock_get_user_individual_channels.return_value = channel_ids
		mock_get_tickets_for_reminding.return_value = ticket_data
		mock_get_main_message_sender.return_value = user_id

		result = daily_reminder.get_message_for_reminding(user_id, user_tag)
		mock_get_tickets_for_reminding.assert_called_once_with(user_id, user_tag)
		mock_get_user_individual_channels.assert_called_once_with(user_id)
		mock_get_main_message_sender.assert_called_once_with(main_channel_id, main_message_id)
		mock_info.assert_not_called()
		self.assertEqual(result, (main_message_id, copied_channel_id, copied_message_id))

	def test_reported_invalid(self, mock_get_tickets_for_reminding, mock_get_user_individual_channels,
					 mock_get_main_message_sender, mock_info, *args):
		main_channel_id = -10087654231
		main_message_id = 124
		copied_channel_id = -10032164587
		copied_message_id = 165
		user_id = 12354
		user_tag = "CC"
		channel_ids = [(copied_channel_id, '{"remind": ["reported"]}')]
		ticket_data = [(copied_channel_id, copied_message_id, main_channel_id, main_message_id, "CC,BB,AA", 2, "", "")]
		mock_get_user_individual_channels.return_value = channel_ids
		mock_get_tickets_for_reminding.return_value = ticket_data
		mock_get_main_message_sender.return_value = 153121

		result = daily_reminder.get_message_for_reminding(user_id, user_tag)
		mock_get_tickets_for_reminding.assert_called_once_with(user_id, user_tag)
		mock_get_user_individual_channels.assert_called_once_with(user_id)
		mock_get_main_message_sender.assert_called_once_with(main_channel_id, main_message_id)
		mock_info.assert_called_once_with(f"No forwarded tickets for reminding were found in {user_tag}")
		self.assertEqual(result, None)



if __name__ == "__main__":
	main()
