import os
from datetime import datetime
from werkzeug.utils import secure_filename
import bcrypt
from flask import Flask, render_template, redirect, url_for, request, session, flash, make_response, abort
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView

from handicap import *
from forms import *

app = Flask(__name__)
app.config.from_pyfile('config.py')

db = SQLAlchemy(app)

admin = Admin(app, name='The Golf Handicap', template_mode='bootstrap4')

login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
	return users.query.get(int(user_id))


######################
###     		   ###
###     MODELS     ###
###				   ###
######################


class users(UserMixin, db.Model):
	id = db.Column(db.Integer, primary_key=True)
	first_name = db.Column(db.String(20), unique=False)
	last_name = db.Column(db.String(20), unique=False)
	username = db.Column(db.String(20), unique=True)
	password = db.Column(db.Text, unique=False)
	email = db.Column(db.String(25), unique=True)
	avatar = db.Column(db.String(255))
	is_admin = db.Column(db.Boolean, default=False)
	date_created = db.Column(db.DateTime, unique=True, default=datetime.now)


class rounds(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	user_id = db.Column(db.Integer)
	rating = db.Column(db.Numeric(precision=8, scale=2), unique=False)
	slope = db.Column(db.Integer)
	score = db.Column(db.Integer)
	score_differential = db.Column(db.Numeric(precision=8, scale=2))
	course = db.Column(db.String(255))
	zipcode = db.Column(db.Integer)
	time_stamp = db.Column(db.DateTime, default=datetime.now)


class handicaps(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	user_id = db.Column(db.Integer)
	handicap = db.Column(db.Numeric(precision=8, scale=2))
	lowest_score = db.Column(db.Integer)
	total_rounds = db.Column(db.Integer)
	last_update = db.Column(db.DateTime, default=datetime.now)


class blogpost(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	title = db.Column(db.String(255))
	content = db.Column(db.Text)
	preview_content = db.Column(db.Text)
	author = db.Column(db.String(255))
	meta_title = db.Column(db.String(255))
	meta_description = db.Column(db.String(255))
	slug = db.Column(db.String(255)) # url
	hero_image = db.Column(db.String(255))
	preview_image = db.Column(db.String(255))
	date_posted = db.Column(db.DateTime, default=datetime.now)


class friends(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	user_id = db.Column(db.Integer)
	friend_user_id = db.Column(db.Integer)
	approved = db.Column(db.Boolean, default=False)


class Controller(ModelView): # to only allow access to admin to is_admin users
	def is_accessible(self):
		if current_user.is_authenticated:		
			if current_user.is_admin == True:
				return current_user.is_authenticated
			else:
				return abort(403)
		else:
			return abort(403)


db.create_all()

admin.add_view(Controller(users, db.session))
admin.add_view(Controller(rounds, db.session))
admin.add_view(Controller(handicaps, db.session))
admin.add_view(Controller(blogpost, db.session))



ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


######################
###     		   ###
###     ROUTES     ###
###				   ###
######################


@app.route('/')
def index():
	return render_template("index.html")


@app.route('/learn-more')
def learn_more():
	return render_template("learnmore.html")


@app.route('/shop')
def shop():
	return render_template("shop.html")


##################
#				 #
#   BLOG STUFF   #
#				 #
##################


@app.route('/blog')
def blog():
	recent_blogs = blogpost.query.order_by(desc("date_posted")).limit(4)

	return render_template("blog.html", recent_blogs=recent_blogs)


@app.route('/blog/view-all')
def all_blogs():
	blogs = blogpost.query.order_by(desc("date_posted")).all()

	return render_template("allBlogs.html", blogs=blogs)


@app.route('/blog/<slug>')
def individual_blog(slug):
	blog = blogpost.query.filter_by(slug=slug).first()

	return render_template("blogpost.html", blog=blog)



##################
#				 #
# ACCOUNT STUFF  #
#				 #
##################


@app.route('/create-account', methods=["GET","POST"])
def create_account():
	form = createAccount()
	if current_user.is_authenticated:
		flash("Already logged in!", "success")
		return redirect(url_for('dashboard'))

	elif form.validate_on_submit(): # valid form, POST
		## CHECK FOR EXISTING USERS BEFORE DOING ANYTHING ELSE ##

		first_name = form.first_name.data
		last_name = form.last_name.data
		username = form.username.data
		password = form.password.data
		email = form.email.data
		timestamp = str(datetime.now())

		user_with_username = users.query.filter_by(username=username).first()
		user_with_email = users.query.filter_by(email=email).first()

		if user_with_username:
			flash("Username already taken.", "error")
			return render_template("createaccount.html", form=form)
		if user_with_email:
			flash("User with this email already exists.", "error")
			return render_template("createaccount.html", form=form)


		if request.files['avatar']: # if user submitted a profile image
			# TODO - check image size and validate
			file = request.files['avatar']
			if file and allowed_file(file.filename):
				filename = secure_filename(str(form.username.data)) # set filename to username
				file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
		else: # if user did not upload image, set image to default image
			filename = 'default.png'

		
		avatar = filename
		hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

		try: # create the account
			user = users(
				first_name=first_name,
				last_name=last_name,
				username=username,
				password=hashed,
				email=email,
				avatar=avatar,
				date_created=timestamp)
			db.session.add(user)
			db.session.commit()
		except:
			flash("There was an error creating your account.", "error")
			return render_template("createaccount.html", form=form)

		username = form.username.data
		password = form.password.data
		user = users.query.filter_by(username=username).first()

		if user:
			login_user(user)
			user_id = str(user.id)
			resp = make_response(redirect(url_for("dashboard")))
			resp.set_cookie('uid', value=user_id, httponly=True, secure=True)
			flash('Account created! Welcome to The Golf Handicap!', 'success')
			return resp
		else:
			flash("Error creating account.", "error")
			return render_template("createaccount.html", form=form)
	else: # GET request render form
		return render_template("createaccount.html", form=form)


@app.route('/login', methods=["GET", "POST"])
def login():
	form = loginForm()
	if current_user.is_authenticated:
		flash("Already logged in!", "success")
		return redirect(url_for('dashboard'))

	elif form.validate_on_submit():
		username = form.username.data
		password = form.password.data
		# query user table for username and password
		user = users.query.filter_by(username=username).first()

		if not user:
			flash("User not found.", "error")
			return render_template("login.html", form=form)
		if not bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
			flash("Incorrect password.", "error")
			return render_template("login.html", form=form)

		if user: # login user, get user id and store in cookie
			login_user(user)
			user_id = str(user.id)

			resp = make_response(redirect(url_for("dashboard")))
			resp.set_cookie('uid', value=user_id, httponly=True)

			flash(f"Welcome back, {user.username}!", "success")

			return resp

		else: # cant find user, return to login page
			flash("Unable to login.", "error")
			return render_template('login.html', form=form)

	else:
		return render_template("login.html", form=form)


@app.route('/logout')
# @login_required
def logout():
	logout_user()
	session.pop('updates', None) # remove updates counter from session
	#set cookie here to expire in the past to clear uid cookie
	resp = make_response(redirect(url_for("index")))
	resp.set_cookie('uid', value='0', httponly=True, expires=0)
	flash("Logged out!", "success")
	return resp


@app.route('/account/home')
@login_required
def dashboard():
	user_id = request.cookies.get('uid')
	user = users.query.filter_by(id=user_id).first()

	rounds = get_rounds(db, user_id)

	if rounds:
		handicap = round(get_handicap(rounds), 1)
		total_rounds = get_total_rounds(db, user_id)
		lowest_score = get_lowest_score(db, user_id)
	else:
		handicap = 0
		total_rounds = 0
		lowest_score = get_lowest_score(db, user_id)

	if not 'updates' in session:	
		# update handicap in the handicaps table for leaderboard
		update_handicap(handicap, lowest_score, total_rounds, user_id, db)
		session['updates'] = 1
	elif session['updates'] > 5:
		"""limit number of times a person can update handicaps table in a session"""
		pass
	else:
		# update handicap in the handicaps table for leaderboard
		update_handicap(handicap, lowest_score, total_rounds, user_id, db)
		session['updates'] += 1

	friend_list = friends.query.filter_by(user_id=user_id)
	friend_count = 0
	
	for friend in friend_list:
		friend_count += 1


	avatar = user.avatar
	first_name = user.first_name
	last_name = user.last_name
	username = user.username
	email = user.email
	date = user.date_created
	date = date.strftime("%A, %B %d %Y")
	if handicap == 0:
		handicap = "N/A"

	return render_template("dashboard.html",
		first_name=first_name,
		last_name=last_name,
		username = user.username,
		email=email,
		avatar=avatar,
		handicap=handicap,
		total_rounds=total_rounds,
		lowest_score=lowest_score,
		date=date,
		rounds=rounds,
		friend_count=friend_count)


@app.route('/account/add-round', methods=["GET", "POST"])
@login_required
def add_round():
	form = roundForm()
	if form.validate_on_submit():
		# calculate score differential and insert into table
		round_data = get_round_data(form)
		user_id = request.cookies.get('uid')
		add_round_record(round_data, db, int(user_id))

		return redirect(url_for("dashboard"))
	else:
		# page with form to collect round data
		return render_template("addround.html", form=form)



@app.route('/account/edit-round/<round_id>', methods=["POST", "GET"])
@login_required
def edit_round(round_id):
	form = editRound()
	uid = int(request.cookies.get('uid'))
	this_round = rounds.query.filter_by(id=round_id).first()

	if uid != int(this_round.user_id): # stop a-hole from messing with other users rounds
		return abort(403)

	if form.validate_on_submit():
		round_data = get_round_data(form)
		update_round_record(round_data, db, round_id)
		flash("Round updated successfully!", "success")

		return redirect(url_for('dashboard'))
	else:
		return render_template("editround.html", 
			form=form,
			this_round=this_round,
			round_id=round_id)


@app.route('/account/delete-round/<round_id>', methods=["POST", "GET"])
@login_required
def delete_round(round_id):
	uid = int(request.cookies.get('uid'))
	this_round = rounds.query.filter_by(id=round_id).first()

	if uid != int(this_round.user_id): # stop a-hole from messing with other users rounds
		return abort(403)

	else:
		query = f"DELETE FROM rounds WHERE id = {round_id}"
		db.session.execute(query)
		db.session.commit()
		return redirect(url_for('dashboard'))


@app.route('/account/add-friend', methods=["POST", "GET"])
@login_required
def add_friend():
	form = addFriend()
	uid = int(request.cookies.get('uid')) 

	if form.validate_on_submit():
		friend_name = form.username.data
		friend = users.query.filter_by(username=friend_name).first()
		
		if not friend:
			flash("User does not exist.", "error")
			return render_template('addfriend.html',
				form=form)

		elif friend:
			friend_id = friend.id

			if friend_id == uid:
				flash("You can't be friends with yourself, weirdo.", "error")
				return render_template('addfriend.html',
					form=form)

			query = f"SELECT friend_user_id FROM friends WHERE user_id = {uid}"
			res = db.session.execute(query)
			friend_id_list = []

			for friend in res:
				fid = friend['friend_user_id']
				friend_id_list.append(fid)
			
			if friend_id in friend_id_list:
				flash("Already friends with this user!", "error")
				return render_template('addfriend.html',
					form=form)

			query = f"""INSERT INTO friends (user_id, friend_user_id)
				VALUES ({uid}, {friend_id})"""
			db.session.execute(query)
			db.session.commit()
			flash("Friend added.", "success")

			return redirect(url_for('dashboard'))

	return render_template('addfriend.html',
		form=form)


@app.route('/account/friends')
@login_required
def friend_list():
	uid = int(request.cookies.get('uid')) 
	query = f"""SELECT users.username as friend_username, handicaps.handicap, handicaps.lowest_score, handicaps.total_rounds
		FROM friends
		JOIN users ON friends.friend_user_id=users.id
		JOIN handicaps ON friends.friend_user_id=handicaps.user_id
		WHERE friends.user_id = {uid}"""
	friends = db.session.execute(query)

	return render_template('friendslist.html',
		friends=friends)


@app.route('/leaderboard/<leaderboard_type>')
@login_required
def leaderboard(leaderboard_type):
	sort = request.args.get("sort")
	if not sort:
		sort = 'handicap'
	if leaderboard_type == 'all':
		if sort == 'handicap':
			query = """SELECT handicaps.user_id, handicaps.handicap, handicaps.lowest_score, handicaps.total_rounds, users.username
				FROM handicaps
				INNER JOIN users ON handicaps.user_id=users.id
				WHERE handicaps.total_rounds > 0
				ORDER BY handicap;"""
		elif sort == 'rounds':
			query = """SELECT handicaps.user_id, handicaps.handicap, handicaps.lowest_score, handicaps.total_rounds, users.username
				FROM handicaps
				INNER JOIN users ON handicaps.user_id=users.id
				WHERE handicaps.total_rounds > 0
				ORDER BY total_rounds DESC;"""
		elif sort == 'score':
			query = """SELECT handicaps.user_id, handicaps.handicap, handicaps.lowest_score, handicaps.total_rounds, users.username
				FROM handicaps
				INNER JOIN users ON handicaps.user_id=users.id
				WHERE handicaps.total_rounds > 0
				ORDER BY lowest_score;"""
		else:
			return render_template("leaderboard.html",
				sort=sort)

	if leaderboard_type == 'friends':
		uid = int(request.cookies.get('uid'))
		if sort == 'handicap':
			query = f"""SELECT DISTINCT users.username, handicaps.handicap, handicaps.lowest_score, handicaps.total_rounds
				FROM friends
				JOIN users ON friends.friend_user_id=users.id
				JOIN handicaps ON friends.friend_user_id=handicaps.user_id
				WHERE friends.user_id = {uid} or users.id = {uid}
				ORDER BY handicaps.handicap;
				"""
		elif sort == 'rounds':
			query = f"""SELECT DISTINCT users.username, handicaps.handicap, handicaps.lowest_score, handicaps.total_rounds
				FROM friends
				JOIN users ON friends.friend_user_id=users.id
				JOIN handicaps ON friends.friend_user_id=handicaps.user_id
				WHERE friends.user_id = {uid} or users.id = {uid}
				ORDER BY handicaps.total_rounds DESC;"""
		elif sort == 'score':
			query = f"""SELECT DISTINCT users.username, handicaps.handicap, handicaps.lowest_score, handicaps.total_rounds
				FROM friends
				JOIN users ON friends.friend_user_id=users.id
				JOIN handicaps ON friends.friend_user_id=handicaps.user_id
				WHERE friends.user_id = {uid} or users.id = {uid}
				ORDER BY handicaps.lowest_score;"""
		else:
			return render_template("leaderboard.html",
				sort=sort)


	leaderboard = db.session.execute(query)
	return render_template("leaderboard.html",
		leaderboard=leaderboard,
		sort=sort,
		type=leaderboard_type)


@app.route('/email-signup', methods=["POST"])
def email_signup():
	if request.method == "POST":

		flash("Thank you for signing up!", "success")
		url = request.referrer
		return redirect(url)
	else:
		return abort(404)





@app.errorhandler(401)
def unauthorized_error(self):
	flash("Please login to continue.", "error")
	return redirect(url_for("login"))

@app.errorhandler(403)
def forbidden_error(self):
	flash("Action not allowed.", "error")
	return redirect(url_for('index'))

if __name__ == '__main__':
	app.run() 