from datetime import datetime

def create_new_account(form, filename, db):
	first_name = form.first_name.data
	last_name = form.last_name.data
	username = form.username.data
	password = form.password.data
	email = form.email.data
	avatar = filename
	timestamp = str(datetime.now())

	query = f"""INSERT INTO users (first_name, last_name, username, password, email, avatar, date_created)
		VALUES {first_name, last_name, username, password, email, avatar, timestamp}"""

	# TODO:
	# - way to handle when an email, username already exists.

	db.session.execute(query)
	db.session.commit()


def update_handicap(handicap, total_rounds, user_id, db):
	query = "SELECT * FROM handicaps WHERE user_id = {}".format(user_id)
	resp = db.session.execute(query).fetchone()

	timestamp = str(datetime.now())

	if not resp:
		query = f"""INSERT INTO handicaps (user_id, handicap, total_rounds, last_update)
			VALUES {user_id, handicap, total_rounds, timestamp}"""
		db.session.execute(query)
		db.session.commit()

		return True

	if resp:
		query = f"""UPDATE handicaps SET handicap = '{handicap}', last_update = '{timestamp}', total_rounds = '{total_rounds}' WHERE user_id = {user_id}"""
		db.session.execute(query)
		db.session.commit()

		return True

	return False