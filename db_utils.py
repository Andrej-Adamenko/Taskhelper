import sqlite3

DB_FILENAME = "taskhelper_data.db"

DB_CONNECTION = sqlite3.connect(DB_FILENAME, check_same_thread=False)
CURSOR = DB_CONNECTION.cursor()


def initialize_db():
	if not is_table_exists("discussion_messages"):
		create_tables()


def is_table_exists(table_name):
	sql = "SELECT count(name) FROM sqlite_master WHERE type='table' AND name=(?)"
	CURSOR.execute(sql, (table_name,))
	result = CURSOR.fetchone()[0]
	return bool(result)


def create_tables():
	discussion_table_sql = "CREATE TABLE discussion_messages (main_message_id INT PRIMARY KEY NOT NULL, discussion_message_id INT NOT NULL);"
	CURSOR.execute(discussion_table_sql)
	DB_CONNECTION.commit()


def insert_discussion_message(main_message_id, discussion_message_id):
	sql = "INSERT INTO discussion_messages (main_message_id, discussion_message_id) VALUES (?, ?)"
	CURSOR.execute(sql, (main_message_id, discussion_message_id,))
	DB_CONNECTION.commit()


def get_discussion_message_id(main_message_id):
	sql = "SELECT discussion_message_id FROM discussion_messages WHERE main_message_id=(?)"
	CURSOR.execute(sql, (main_message_id,))
	result = CURSOR.fetchone()
	if result:
		return result[0]

