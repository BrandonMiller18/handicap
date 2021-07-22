from datetime import datetime
import mysql.connector
from mysql.connector import errorcode



# from handicap import cur, cnx

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


def get_user_id(user_email, cur):
	query = ("""SELECT * FROM users WHERE email = '{}'""".format(user_email))
	cur.execute(query)
	resp = cur.fetchall()
	user_id = str(resp[0][0])

	return user_id