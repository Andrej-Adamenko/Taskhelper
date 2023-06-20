import logging
import sqlite3
import threading

DB_FILENAME = "taskhelper_data.db"

DB_CONNECTION = sqlite3.connect(DB_FILENAME, check_same_thread=False)
CURSOR = DB_CONNECTION.cursor()

DB_LOCK = threading.RLock()


def db_thread_lock(func):
	def inner_function(*args, **kwargs):
		try:
			DB_LOCK.acquire(True)
			return func(*args, **kwargs)
		except sqlite3.Error as E:
			logging.error(f"SQLite error in {func.__name__} function, error: {E.args}")
		finally:
			DB_LOCK.release()
	return inner_function


def initialize_db():
	create_tables()


def is_table_exists(table_name):
	sql = "SELECT count(name) FROM sqlite_master WHERE type='table' AND name=(?)"
	CURSOR.execute(sql, (table_name,))
	result = CURSOR.fetchone()[0]
	return bool(result)


def create_tables():
	if not is_table_exists("discussion_messages"):
		discussion_messages_table_sql = '''
			CREATE TABLE "discussion_messages" (
				"id"	INTEGER PRIMARY KEY AUTOINCREMENT,
				"main_message_id"	INT NOT NULL,
				"main_channel_id"	INT NOT NULL,
				"discussion_message_id"	INT NOT NULL
			); '''

		CURSOR.execute(discussion_messages_table_sql)

	if not is_table_exists("copied_messages"):
		copied_messages_table_sql = '''
			CREATE TABLE "copied_messages" (
				"id"	INTEGER PRIMARY KEY AUTOINCREMENT,
				"main_message_id"	INT NOT NULL,
				"main_channel_id"	INT NOT NULL,
				"copied_message_id"	INT NOT NULL,
				"copied_channel_id"	INT NOT NULL
			); '''

		CURSOR.execute(copied_messages_table_sql)

	if not is_table_exists("last_message_ids"):
		last_message_ids_table_sql = '''
			CREATE TABLE "last_message_ids" (
				"id"	INTEGER PRIMARY KEY AUTOINCREMENT,
				"chat_id"	INT NOT NULL,
				"last_message_id"	INT NOT NULL
			); '''

		CURSOR.execute(last_message_ids_table_sql)

	if not is_table_exists("comment_messages"):
		comment_messages_table_sql = '''
			CREATE TABLE "comment_messages" (
				"id"	INTEGER PRIMARY KEY AUTOINCREMENT,
				"discussion_chat_id"	INT NOT NULL,
				"message_id"	INT NOT NULL,
				"reply_to_message_id"	INT NOT NULL,
				"sender_id"	INT NOT NULL
			); '''

		CURSOR.execute(comment_messages_table_sql)

	if not is_table_exists("scheduled_messages"):
		scheduled_messages_table_sql = '''
			CREATE TABLE "scheduled_messages" (
				"id"	INTEGER PRIMARY KEY AUTOINCREMENT,
				"main_message_id"	INT NOT NULL,
				"main_channel_id"	INT NOT NULL,
				"scheduled_message_id"	INT NOT NULL,
				"scheduled_channel_id"	INT NOT NULL,
				"send_time"	INT NOT NULL
			); '''

		CURSOR.execute(scheduled_messages_table_sql)

	if not is_table_exists("interval_updates_status"):
		interval_updates_status_table_sql = '''
			CREATE TABLE "interval_updates_status" (
				"id"	INTEGER PRIMARY KEY AUTOINCREMENT,
				"main_channel_id"	INT NOT NULL,
				"current_message_id"    INT NOT NULL
			); '''

		CURSOR.execute(interval_updates_status_table_sql)

	if not is_table_exists("individual_channels"):
		individual_channels_table_sql = '''
			CREATE TABLE "individual_channels" (
				"id"	INTEGER PRIMARY KEY AUTOINCREMENT,
				"main_channel_id"	INT NOT NULL,
				"channel_id"        INT NOT NULL,
				"priorities"        TEXT,
				"user_tag"          TEXT,
				"types"             TEXT
			); '''

		CURSOR.execute(individual_channels_table_sql)

	if not is_table_exists("users"):
		users_table_sql = '''
			CREATE TABLE "users" (
				"id"	INTEGER PRIMARY KEY AUTOINCREMENT,
				"main_channel_id"	INT NOT NULL,
				"user_id"           INT NOT NULL,
				"initial_value"     TEXT NOT NULL,
				"user_tag"          TEXT NOT NULL		
			); '''

		CURSOR.execute(users_table_sql)

	if not is_table_exists("main_channels"):
		main_channels_table_sql = '''
			CREATE TABLE "main_channels" (
				"id"	INTEGER PRIMARY KEY AUTOINCREMENT,
				"channel_id"    INT NOT NULL
			); '''

		CURSOR.execute(main_channels_table_sql)

	if not is_table_exists("main_messages"):
		main_messages_table_sql = '''
			CREATE TABLE "main_messages" (
				"id"	INTEGER PRIMARY KEY AUTOINCREMENT,
				"main_channel_id"   INT NOT NULL,
				"main_message_id"   INT NOT NULL,
				"sender_id"         INT
			); '''

		CURSOR.execute(main_messages_table_sql)

	DB_CONNECTION.commit()


@db_thread_lock
def insert_or_update_discussion_message(main_message_id, main_channel_id, discussion_message_id):
	if get_discussion_message_id(main_message_id, main_channel_id):
		sql = "UPDATE discussion_messages SET discussion_message_id=(?) WHERE main_message_id=(?) and main_channel_id=(?)"
	else:
		sql = "INSERT INTO discussion_messages (discussion_message_id, main_message_id, main_channel_id) VALUES (?, ?, ?)"

	CURSOR.execute(sql, (discussion_message_id, main_message_id, main_channel_id, ))
	DB_CONNECTION.commit()


@db_thread_lock
def get_discussion_message_id(main_message_id, main_channel_id):
	sql = "SELECT discussion_message_id FROM discussion_messages WHERE main_message_id=(?) and main_channel_id=(?)"
	CURSOR.execute(sql, (main_message_id, main_channel_id,))
	result = CURSOR.fetchone()
	if result:
		return result[0]


@db_thread_lock
def get_main_from_discussion_message(discussion_message_id, main_channel_id):
	sql = "SELECT main_message_id FROM discussion_messages WHERE discussion_message_id=(?) and main_channel_id=(?)"
	CURSOR.execute(sql, (discussion_message_id, main_channel_id,))
	result = CURSOR.fetchone()
	if result:
		return result[0]


@db_thread_lock
def insert_copied_message(main_message_id, main_channel_id, copied_message_id, copied_channel_id):
	sql = "INSERT INTO copied_messages (copied_message_id, copied_channel_id, main_message_id, main_channel_id) VALUES (?, ?, ?, ?)"
	CURSOR.execute(sql, (copied_message_id, copied_channel_id, main_message_id, main_channel_id,))
	DB_CONNECTION.commit()


@db_thread_lock
def delete_copied_message(copied_message_id, copied_channel_id):
	sql = "DELETE FROM copied_messages WHERE copied_message_id=(?) and copied_channel_id=(?)"
	CURSOR.execute(sql, (copied_message_id, copied_channel_id))
	DB_CONNECTION.commit()


@db_thread_lock
def get_copied_message_data(main_message_id, main_channel_id):
	sql = "SELECT copied_message_id, copied_channel_id FROM copied_messages WHERE main_message_id=(?) and main_channel_id=(?)"
	CURSOR.execute(sql, (main_message_id, main_channel_id,))
	result = CURSOR.fetchall()
	return result


@db_thread_lock
def get_main_message_from_copied(copied_message_id, copied_channel_id):
	sql = "SELECT main_message_id, main_channel_id FROM copied_messages WHERE copied_message_id=(?) and copied_channel_id=(?)"
	CURSOR.execute(sql, (copied_message_id, copied_channel_id,))
	result = CURSOR.fetchone()
	if result:
		return result


@db_thread_lock
def get_oldest_copied_message(copied_channel_id):
	sql = "SELECT min(copied_message_id) FROM copied_messages WHERE copied_channel_id=(?)"
	CURSOR.execute(sql, (copied_channel_id,))
	result = CURSOR.fetchone()
	if result:
		return result[0]


@db_thread_lock
def update_copied_message_id(copied_message_id, copied_channel_id, updated_message_id):
	sql = "UPDATE copied_messages SET copied_message_id=(?) WHERE copied_message_id=(?) AND copied_channel_id=(?)"
	CURSOR.execute(sql, (updated_message_id, copied_message_id, copied_channel_id,))
	DB_CONNECTION.commit()


@db_thread_lock
def insert_or_update_last_msg_id(last_message_id, chat_id):
	if get_last_message_id(chat_id):
		sql = "UPDATE last_message_ids SET last_message_id=(?) WHERE chat_id=(?)"
	else:
		sql = "INSERT INTO last_message_ids (last_message_id, chat_id) VALUES (?, ?)"

	CURSOR.execute(sql, (last_message_id, chat_id,))
	DB_CONNECTION.commit()


@db_thread_lock
def get_last_message_id(chat_id):
	sql = "SELECT last_message_id FROM last_message_ids WHERE chat_id=(?)"
	CURSOR.execute(sql, (chat_id,))
	result = CURSOR.fetchone()
	if result:
		return result[0]


@db_thread_lock
def insert_comment_message(reply_to_message_id, discussion_message_id, discussion_chat_id, sender_id):
	if is_comment_exist(discussion_message_id, discussion_chat_id):
		return

	sql = "INSERT INTO comment_messages (reply_to_message_id, message_id, discussion_chat_id, sender_id) VALUES (?, ?, ?, ?)"
	CURSOR.execute(sql, (reply_to_message_id, discussion_message_id, discussion_chat_id, sender_id,))
	DB_CONNECTION.commit()


@db_thread_lock
def is_comment_exist(discussion_message_id, discussion_chat_id):
	sql = "SELECT id FROM comment_messages WHERE message_id=(?) and discussion_chat_id=(?)"
	CURSOR.execute(sql, (discussion_message_id, discussion_chat_id,))
	result = CURSOR.fetchone()
	return bool(result)


@db_thread_lock
def get_comments_count(discussion_message_id, discussion_chat_id, ignored_sender_id=0):
	sql = '''
		WITH RECURSIVE
		  reply_messages(comment_id) AS (
			 SELECT (?)
			 UNION ALL
			 SELECT message_id FROM comment_messages, reply_messages WHERE reply_to_message_id = reply_messages.comment_id
			 AND discussion_chat_id = (?) AND sender_id != (?)
		  )
		SELECT count(comment_id) - 1 FROM reply_messages;
	'''

	CURSOR.execute(sql, (discussion_message_id, discussion_chat_id, ignored_sender_id,))
	result = CURSOR.fetchone()
	return result[0]


@db_thread_lock
def get_comment_top_parent(discussion_message_id, discussion_chat_id):
	sql = '''
		WITH RECURSIVE
		  reply_messages(comment_id) AS (
		   SELECT (?)
		   UNION ALL
		   SELECT reply_to_message_id FROM comment_messages, reply_messages WHERE message_id = reply_messages.comment_id
		   AND discussion_chat_id = (?)
		  )
		SELECT MIN(comment_id) FROM reply_messages;	
	'''

	CURSOR.execute(sql, (discussion_message_id, discussion_chat_id,))
	result = CURSOR.fetchone()
	return result[0]


@db_thread_lock
def insert_scheduled_message(main_message_id, main_channel_id, scheduled_message_id, scheduled_channel_id, send_time):
	sql = "INSERT INTO scheduled_messages (main_message_id, main_channel_id, scheduled_message_id, scheduled_channel_id, send_time) VALUES (?, ?, ?, ?, ?)"
	CURSOR.execute(sql, (main_message_id, main_channel_id, scheduled_message_id, scheduled_channel_id, send_time,))
	DB_CONNECTION.commit()


@db_thread_lock
def update_scheduled_message(main_message_id, main_channel_id, send_time):
	sql = "UPDATE scheduled_messages SET send_time=(?) WHERE main_message_id=(?) and main_channel_id=(?)"
	CURSOR.execute(sql, (send_time, main_message_id, main_channel_id,))
	DB_CONNECTION.commit()


@db_thread_lock
def update_scheduled_message_id(scheduled_message_id, scheduled_channel_id, updated_message_id):
	sql = "UPDATE scheduled_messages SET scheduled_message_id=(?) WHERE scheduled_message_id=(?) and scheduled_channel_id=(?)"
	CURSOR.execute(sql, (updated_message_id, scheduled_message_id, scheduled_channel_id,))
	DB_CONNECTION.commit()


@db_thread_lock
def get_scheduled_messages(main_message_id, main_channel_id):
	sql = "SELECT scheduled_message_id, scheduled_channel_id, send_time FROM scheduled_messages WHERE main_message_id=(?) and main_channel_id=(?)"
	CURSOR.execute(sql, (main_message_id, main_channel_id,))
	result = CURSOR.fetchall()
	if result:
		return result


@db_thread_lock
def get_main_from_scheduled_message(scheduled_message_id, scheduled_channel_id):
	sql = "SELECT main_message_id, main_channel_id FROM scheduled_messages WHERE scheduled_message_id=(?) and scheduled_channel_id=(?)"
	CURSOR.execute(sql, (scheduled_message_id, scheduled_channel_id,))
	result = CURSOR.fetchone()
	if result:
		return result


@db_thread_lock
def delete_scheduled_message(scheduled_message_id, scheduled_channel_id):
	sql = "DELETE FROM scheduled_messages WHERE scheduled_message_id=(?) AND scheduled_channel_id=(?)"
	CURSOR.execute(sql, (scheduled_message_id, scheduled_channel_id,))
	DB_CONNECTION.commit()


@db_thread_lock
def delete_scheduled_message_main(main_message_id, main_channel_id):
	sql = "DELETE FROM scheduled_messages WHERE main_message_id=(?) AND main_channel_id=(?)"
	CURSOR.execute(sql, (main_message_id, main_channel_id,))
	DB_CONNECTION.commit()


@db_thread_lock
def get_all_scheduled_messages():
	sql = "SELECT main_message_id, main_channel_id, scheduled_message_id, scheduled_channel_id, send_time FROM scheduled_messages"
	CURSOR.execute(sql, ())
	result = CURSOR.fetchall()
	return result


@db_thread_lock
def get_oldest_scheduled_message(scheduled_channel_id):
	sql = "SELECT min(scheduled_message_id) FROM scheduled_messages WHERE scheduled_channel_id=(?)"
	CURSOR.execute(sql, (scheduled_channel_id,))
	result = CURSOR.fetchone()
	if result:
		return result[0]


@db_thread_lock
def get_finished_update_channels():
	sql = "SELECT main_channel_id FROM interval_updates_status WHERE current_message_id <= 0"
	CURSOR.execute(sql, ())
	result = CURSOR.fetchall()
	return result


@db_thread_lock
def get_unfinished_update_channel():
	sql = "SELECT main_channel_id, current_message_id FROM interval_updates_status WHERE current_message_id > 0"
	CURSOR.execute(sql, ())
	result = CURSOR.fetchone()
	if result:
		return result


@db_thread_lock
def insert_or_update_channel_update_progress(main_channel_id, current_message_id):
	if get_update_in_progress_channel(main_channel_id):
		sql = "UPDATE interval_updates_status SET current_message_id=(?) WHERE main_channel_id=(?)"
	else:
		sql = "INSERT INTO interval_updates_status(current_message_id, main_channel_id) VALUES (?, ?)"
	CURSOR.execute(sql, (current_message_id, main_channel_id))
	DB_CONNECTION.commit()


@db_thread_lock
def get_update_in_progress_channel(main_channel_id):
	sql = "SELECT current_message_id FROM interval_updates_status WHERE main_channel_id=(?)"
	CURSOR.execute(sql, (main_channel_id,))
	result = CURSOR.fetchone()
	if result:
		return result


@db_thread_lock
def clear_updates_in_progress():
	sql = "DELETE FROM interval_updates_status"
	CURSOR.execute(sql, ())
	DB_CONNECTION.commit()


@db_thread_lock
def insert_or_update_individual_channel(main_channel_id, channel_id, priorities, channel_types):
	if get_individual_channel(channel_id):
		sql = '''
			UPDATE individual_channels
			SET main_channel_id=(?), priorities=(?), types=(?)
			WHERE channel_id=(?) 
		'''
	else:
		sql = '''
			INSERT INTO individual_channels
			(main_channel_id, priorities, types, channel_id)
			VALUES (?, ?, ?, ?)
		'''
	CURSOR.execute(sql, (main_channel_id, priorities, channel_types, channel_id,))
	DB_CONNECTION.commit()


@db_thread_lock
def get_individual_channel(channel_id):
	sql = "SELECT main_channel_id, user_tag, priorities, types FROM individual_channels WHERE channel_id=(?)"
	CURSOR.execute(sql, (channel_id,))
	result = CURSOR.fetchone()
	return result


@db_thread_lock
def get_individual_channel_user_tag(channel_id):
	sql = "SELECT user_tag FROM individual_channels WHERE channel_id=(?)"
	CURSOR.execute(sql, (channel_id,))
	result = CURSOR.fetchone()
	if result:
		return result[0]


@db_thread_lock
def is_individual_channel_exists(channel_id):
	sql = "SELECT id FROM individual_channels WHERE channel_id=(?)"
	CURSOR.execute(sql, (channel_id,))
	result = CURSOR.fetchone()
	return bool(result)


@db_thread_lock
def get_main_channel_ids():
	sql = "SELECT channel_id FROM main_channels"
	CURSOR.execute(sql, ())
	result = CURSOR.fetchall()
	if result:
		return [row[0] for row in result]


@db_thread_lock
def is_main_channel_exists(main_channel_id):
	sql = "SELECT id FROM main_channels WHERE channel_id=(?)"
	CURSOR.execute(sql, (main_channel_id,))
	result = CURSOR.fetchone()
	return bool(result)


@db_thread_lock
def insert_main_channel(main_channel_id):
	sql = "INSERT INTO main_channels(channel_id) VALUES (?)"
	CURSOR.execute(sql, (main_channel_id,))
	DB_CONNECTION.commit()


@db_thread_lock
def delete_main_channel(main_channel_id):
	sql = "DELETE FROM main_channels WHERE channel_id=(?)"
	CURSOR.execute(sql, (main_channel_id,))
	DB_CONNECTION.commit()


@db_thread_lock
def get_main_channel_from_user(user_id):
	sql = "SELECT main_channel_id FROM users WHERE user_id=(?)"
	CURSOR.execute(sql, (user_id,))
	result = CURSOR.fetchone()
	if result:
		return result[0]


@db_thread_lock
def get_main_channel_user_tags(main_channel_id):
	sql = "SELECT user_tag FROM users WHERE main_channel_id=(?)"
	CURSOR.execute(sql, (main_channel_id,))
	result = CURSOR.fetchall()
	if result:
		return [row[0] for row in result]


@db_thread_lock
def insert_or_update_user(main_channel_id, user_tag, user_id):
	if is_user_tag_exists(main_channel_id, user_tag):
		sql = "UPDATE users SET user_id=(?) WHERE main_channel_id=(?) AND user_tag=(?)"
	else:
		sql = "INSERT INTO users(user_id, main_channel_id, user_tag) VALUES (?, ?, ?)"

	CURSOR.execute(sql, (user_id, main_channel_id, user_tag,))
	DB_CONNECTION.commit()


@db_thread_lock
def delete_user_by_tag(main_channel_id, user_tag):
	sql = "DELETE FROM users WHERE main_channel_id=(?) AND user_tag=(?)"
	CURSOR.execute(sql, (main_channel_id, user_tag,))
	DB_CONNECTION.commit()


@db_thread_lock
def get_main_message_sender(main_channel_id, main_message_id):
	sql = "SELECT sender_id FROM main_messages WHERE main_channel_id=(?) AND main_message_id=(?)"
	CURSOR.execute(sql, (main_channel_id, main_message_id,))
	result = CURSOR.fetchone()
	if result:
		return result[0]


@db_thread_lock
def get_individual_channel_id_by_tag(main_channel_id, user_tag, priority, channel_type):
	sql = '''
		SELECT channel_id FROM individual_channels WHERE main_channel_id=(?) AND user_tag=(?)
		AND types LIKE '%' || ? || '%'
		AND priorities LIKE '%' || ? || '%'
	'''
	CURSOR.execute(sql, (main_channel_id, user_tag, channel_type, priority,))
	result = CURSOR.fetchone()
	if result:
		return result[0]


@db_thread_lock
def get_individual_channel_id_by_user_id(main_channel_id, user_id, priority, channel_type):
	sql = '''
		SELECT channel_id FROM individual_channels WHERE
		main_channel_id=(?) AND user_tag=(SELECT user_tag FROM users WHERE user_id=(?))
		AND types LIKE '%' || ? || '%'
		AND priorities LIKE '%' || ? || '%'
	'''
	CURSOR.execute(sql, (main_channel_id, user_id, channel_type, priority,))
	result = CURSOR.fetchone()
	if result:
		return result[0]


@db_thread_lock
def insert_main_channel_message(main_channel_id, main_message_id, sender_id):
	if not is_main_message_exists(main_channel_id, main_message_id):
		sql = '''
			INSERT INTO main_messages
			(main_channel_id, main_message_id, sender_id)
			VALUES (?, ?, ?)
		'''
		CURSOR.execute(sql, (main_channel_id, main_message_id, sender_id,))
		DB_CONNECTION.commit()


@db_thread_lock
def get_main_message_sender(main_channel_id, main_message_id):
	sql = "SELECT sender_id FROM main_messages WHERE main_channel_id=(?) AND main_message_id=(?)"
	CURSOR.execute(sql, (main_channel_id, main_message_id,))
	result = CURSOR.fetchone()
	if result:
		return result[0]


@db_thread_lock
def is_main_message_exists(main_channel_id, main_message_id):
	sql = "SELECT id FROM main_messages WHERE main_channel_id=(?) AND main_message_id=(?)"
	CURSOR.execute(sql, (main_channel_id, main_message_id,))
	result = CURSOR.fetchone()
	return bool(result)


@db_thread_lock
def update_individual_channel_tag(channel_id, user_tag):
	sql = "UPDATE individual_channels SET user_tag=(?) WHERE channel_id=(?)"
	CURSOR.execute(sql, (user_tag, channel_id,))
	DB_CONNECTION.commit()


@db_thread_lock
def is_user_tag_exists(main_channel_id, user_tag):
	sql = "SELECT id FROM users WHERE main_channel_id=(?) AND user_tag=(?)"
	CURSOR.execute(sql, (main_channel_id, user_tag,))
	result = CURSOR.fetchone()
	return bool(result)


@db_thread_lock
def get_all_users():
	sql = "SELECT main_channel_id, user_id, user_tag FROM users"
	CURSOR.execute(sql, ())
	result = CURSOR.fetchall()
	return result
