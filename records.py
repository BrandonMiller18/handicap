from datetime import datetime
import mysql.connector
from mysql.connector import errorcode

def create_new_account(form, filename, cur, cnx):
	first_name = form.first_name.data
	last_name = form.last_name.data
	username = form.username.data
	password = form.password.data
	email = form.email.data
	avatar = filename
	timestamp = datetime.now()

	values = (first_name, last_name, username, password, email, avatar, timestamp)

	query = ("""INSERT INTO users (first_name, last_name, username, password, email, avatar, date_created)
		VALUES (%s, %s, %s, %s, %s, %s, %s)""")

	# TODO:
	# - way to handle when an email, username already exists.

	cur.execute(query, values)
	cnx.commit()


def update_handicap(handicap, total_rounds, user_id, cur, cnx):
	query = "SELECT * FROM handicaps WHERE user_id = {}".format(user_id)
	cur.execute(query)
	resp = cur.fetchall()

	timestamp = datetime.now()

	if not resp:
		query = """INSERT INTO handicaps (user_id, handicap, total_rounds, last_update)
			VALUES (%s, %s, %s, %s)"""
		values = (user_id, handicap, total_rounds, timestamp)
		cur.execute(query, values)
		cnx.commit()

		return True

	if resp:
		query = """UPDATE handicaps 
			SET handicap = %s, last_update = %s, total_rounds = %s 
			WHERE user_id = %s"""
		values = (handicap, timestamp, total_rounds, user_id)
		cur.execute(query, values)
		cnx.commit()

		return True

	return False