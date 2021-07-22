import mysql.connector
from mysql.connector import errorcode
# import json

# import db
cnx = mysql.connector.connect(
	host = "localhost",
	user = "root",
	database = "golf_handicap",
	)
cur = cnx.cursor()

# TABLES = {}

# TABLES['rounds'] = (
# 	"""CREATE TABLE rounds (
# 	ID INT(10) NOT NULL AUTO_INCREMENT PRIMARY KEY,
# 	user_id INT(10),
# 	rating DECIMAL(5, 2) NOT NULL,
# 	slope SMALLINT NOT NULL,
# 	score SMALLINT NOT NULL,
# 	score_differential SMALLINT NOT NULL,
# 	course CHAR(100),
# 	zip INT(5),
# 	DATE_TIME TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP)""")


# for table_name in TABLES:
# 	create_table = TABLES[table_name]
# 	try:
# 		print("Creating table {}: ".format(table_name), end='')
# 		cur.execute(create_table)
# 	except mysql.connector.Error as err:
# 		if err.errno == errorcode.ER_TABLE_EXISTS_ERROR:
# 			print("Table already exists.")
# 		else:
# 			print(err.msg)
# 	else:
# 		print("Table {} created.".format(table_name))


def get_round_data(form):
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
	score_differential = (score - rating) * 113 / slope

	return score_differential


def add_round_record(round_data, cur, cnx, user_id):

	user_id = user_id # here we will eventually get userid from the session
	rating = float(round_data['rating'])
	slope = float(round_data['slope'])
	score = float(round_data['score'])
	course = round_data['course']
	zipcode = round_data['zipcode']
	score_differential = score_round(rating, slope, score)

	round_values = (user_id, rating, slope, score, score_differential, course, zipcode)

	add_round = ("""INSERT INTO rounds 
		(user_id, rating, slope, score,	score_differential, course, zip)
		VALUES (%s, %s, %s, %s, %s, %s, %s)""")

	cur.execute(add_round, round_values)
	cnx.commit()

##	#	#	#	#	#	#	#	##
#--------------------------------#
#!Get data from DB and calculate!#
#--------------------------------#
##	#	#	#	#	#	#	#	##

def get_total_rounds(cur, cnx, user_id):
	"""query database to get total number of rounds to display in dashboard"""

	query = """SELECT * FROM rounds WHERE user_id = {}""".format(user_id)
	cur.execute(query)
	data = cur.fetchall()

	total_rounds = len(data)

	return total_rounds


def get_rounds(cur, cnx, user_id):
	"""query database to get rounds for a specific user...
	the result is used to feed the get_handicap function...
	query will pull back 20 most recent rounds for user..."""

	query = """SELECT * FROM rounds WHERE user_id = {} 
		ORDER BY date_time DESC LIMIT 20""".format(user_id)
	cur.execute(query)
	data = cur.fetchall()

	rounds = []

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
		'timestamp': str(x[8]),
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
		score_differentials.append(x['score_differential'])
	
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
		x=10

	# sort score diff in ascending order, limit to x which was set above
	# only append score diffs that will be used for calculate func
	for score in sorted(score_differentials)[:x]: 
		scores.append(score)
	
	handicap = calculate(scores)

	return handicap