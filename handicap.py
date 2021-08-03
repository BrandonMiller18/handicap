from datetime import datetime
from decimal import * 

# import os
# import mysql.connector
# from mysql.connector import errorcode

# # import db
# cnx = mysql.connector.connect(
# 	host = os.environ.get("DB_HOST"),
# 	user = os.environ.get("DB_USER"),
# 	password = os.environ.get("DB_PASSWORD"),
# 	database = os.environ.get("SCHEMA_NAME"),
# 	)
# cur = cnx.cursor()


def get_round_data(form):
	"""get round data from user form,
	return data in a dict to be used by other functions"""
	rating = form.rating.data
	slope = form.slope.data
	score = form.score.data
	course = form.course.data
	zipcode = form.zipcode.data

	data = {
		"rating": rating,
		"slope": slope,
		"score": score,
		"course": course,
		"zipcode": zipcode,
		}

	return data


def score_round(rating, slope, score):
	"""used to find the score diff in add_round_record"""
	score_differential = (score - rating) * 113 / slope

	return score_differential


def add_round_record(round_data, db, user_id):
	"""parse round data, write to database"""
	user_id = user_id # here we will eventually get userid from the session
	rating = float(round_data['rating'])
	slope = float(round_data['slope'])
	score = float(round_data['score'])
	course = round_data['course']
	zipcode = round_data['zipcode']
	score_differential = score_round(rating, slope, score)
	timestamp = str(datetime.now())

	query = f"""INSERT INTO rounds (
			user_id,
			rating,
			slope,
			score,
			score_differential,
			course,
			zipcode,
			time_stamp)
		VALUES {
			user_id,
			rating,
			slope,
			score,
			score_differential,
			course,
			zipcode,
			timestamp}"""

	db.session.execute(query)
	db.session.commit()


def update_round_record(round_data, db, round_id):
	"""parse round data, write to database"""
	rating = float(round_data['rating'])
	slope = float(round_data['slope'])
	score = float(round_data['score'])
	course = round_data['course']
	zipcode = round_data['zipcode']
	score_differential = score_round(rating, slope, score)
	timestamp = str(datetime.now())

	query = f"""UPDATE rounds
			SET
			rating = {rating},
			slope = {slope},
			score = {score},
			score_differential = {score_differential},
			course = '{course}',
			zipcode = {zipcode},
			time_stamp = '{timestamp}'
			WHERE id = {round_id};"""

	db.session.execute(query)
	db.session.commit()

##	#	#	#	#	#	#	#	##
#--------------------------------#
#!Get data from DB and calculate!#
#--------------------------------#
##	#	#	#	#	#	#	#	##

def get_total_rounds(db, user_id):
	"""query database to get total number of rounds to display in dashboard"""

	query = """SELECT * FROM rounds WHERE user_id = {}""".format(user_id)
	data = db.session.execute(query)

	total_rounds = 0

	for r in data:
		total_rounds += 1

	return total_rounds


def get_lowest_score(db, user_id):
	"""query database to get rounds for a specific user...
	the result is used to feed the get_handicap function...
	query will pull back 20 most recent rounds for user..."""

	query = """SELECT * FROM rounds WHERE user_id = {} 
		ORDER BY score ASC LIMIT 1""".format(user_id)
	data = db.session.execute(query).fetchone()

	if data:
		lowest_score = data[4]
	else:
		lowest_score = "N/A"

	return lowest_score


def get_rounds(db, user_id):
	"""query database to get rounds for a specific user...
	the result is used to feed the get_handicap function...
	query will pull back 20 most recent rounds for user..."""

	query = """SELECT * FROM rounds WHERE user_id = {} 
		ORDER BY time_stamp DESC LIMIT 20""".format(user_id)
	
	data = db.session.execute(query)


	rounds = []

	# loop through all rounds to creat dict for each round then add dict to list
	for x in data:
		this_round = {
		'id': x[0],
		'user_id': x[1],
		'rating': float(x[2]),
		'slope': x[3],
		'score': x[4],
		'score_differential': x[5],
		'course': x[6],
		'zipcode': x[7],
		'timestamp': x[8].strftime("%B %d %Y"),
		}

		rounds.append(this_round)

	return rounds


def get_handicap(rounds):
	"""uses results from get_rounds function to calculate a user's handicap"""
	
	def calculate(scores):
		hcp = sum(scores) / len(scores) * 0.96
		return hcp

	score_differentials = [] # list to store all score diffs in
	scores = [] # list for scores that will be used to calculate
	no_of_rounds = len(rounds)

	for x in rounds:
		score_differentials.append(float(x['score_differential']))
	
	if no_of_rounds <= 6:
		# lowest one round
		# Treat this one differently and break function as the work is done here
		handicap = min(score_differentials) * 0.96
		return handicap
	elif no_of_rounds >= 7 and no_of_rounds <= 8:
		# lowest 2
		x=2
	elif no_of_rounds >= 9 and no_of_rounds <= 10:
		# lowest 3
		x=3		
	elif no_of_rounds >= 11 and no_of_rounds <= 12:
		# lowest 4
		x=4
	elif no_of_rounds >= 13 and no_of_rounds <= 14:
		# lowest 5
		x=5
	elif no_of_rounds >= 15 and no_of_rounds <= 16:
		# lowest 6
		x=6
	elif no_of_rounds == 17:
		# lowest 7
		x=7
	elif no_of_rounds == 18:
		# lowest 8
		x=8
	elif no_of_rounds == 19:
		# lowest 9
		x=9
	elif no_of_rounds >= 20:
		# lowest 10
		x=10

	# sort score diff in ascending order, limit to x which was set above
	# x lowest scores
	# only append score diffs that will be used for calculate func
	for score in sorted(score_differentials)[:x]: 
		scores.append(score)
	
	handicap = calculate(scores)

	return handicap