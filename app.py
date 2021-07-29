import os
from datetime import datetime
from werkzeug.utils import secure_filename

from flask import Flask, render_template, redirect, url_for, request, session, flash, make_response
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView

from handicap import *
from records import *
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
	password = db.Column(db.String(20), unique=False)
	email = db.Column(db.String(25), unique=True)
	avatar = db.Column(db.String(255))
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
	date_posted = db.Column(db.DateTime, default=datetime.now)


db.create_all()

admin.add_view(ModelView(users, db.session))
admin.add_view(ModelView(rounds, db.session))
admin.add_view(ModelView(handicaps, db.session))
admin.add_view(ModelView(blogpost, db.session))



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


### DELETED ROUTE FOR ADDING BLOG POST AS THIS IS DONE IN THE FLASK ADMIN NOW
# @app.route("/blog/add-post", methods=["GET", "POST"])
# def add_post():
# 	form = postForm()

# 	if form.validate_on_submit():
# 		post = blogpost(
# 			title=form.title.data,
# 			content=form.content.data,
# 			preview_content=form.preview_content.data,
# 			author=form.author.data,
# 			meta_title=form.meta_title.data,
# 			meta_description=form.meta_description.data,
# 			slug=form.slug.data,
# 			)
# 		form.title.data = ''
# 		form.content.data = ''
# 		form.preview_content.data = ''
# 		form.author.data = ''
# 		form.meta_title.data = ''
# 		form.meta_description.data = ''
# 		form.slug.data = ''

# 		db.session.add(post)
# 		db.session.commit()

# 		flash("Post submitted!", "success")

# 	return render_template("addpost.html", form=form)



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

		user_with_username = users.query.filter_by(username=form.username.data).first()
		user_with_email = users.query.filter_by(email=form.email.data).first()

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


		try: # create the account
			create_new_account(form, filename, db)
		except mysql.connector.errors.IntegrityError:
			# error is raised if user or email exists, redirect to login
			# flash("Username or email already exists, please login.", 'error')
			return redirect(url_for('login'))

		username = form.username.data
		password = form.password.data
		user = users.query.filter_by(username=username, password=password).first()

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
		user = users.query.filter_by(username=username, password=password).first()

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
	else:
		handicap = 0
		total_rounds = 0

	if not 'updates' in session:	
		# update handicap in the handicaps table for leaderboard
		update_handicap(handicap, total_rounds, user_id, db)
		session['updates'] = 1
	elif session['updates'] > 5:
		"""limit number of times a person can update handicaps table in a session"""
		flash("Leaderboard updated too many times. Log out and back in to reset.", "error")
	else:
		# update handicap in the handicaps table for leaderboard
		update_handicap(handicap, total_rounds, user_id, db)
		session['updates'] += 1


	avatar = user.avatar
	first_name = user.first_name
	last_name = user.last_name
	username = user.username
	email = user.email
	date = user.date_created
	date = date.strftime("%A, %B %d %Y")
	lowest_score = get_lowest_score(db, user_id)
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
		rounds=rounds)


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




if __name__ == '__main__':
	app.run() 