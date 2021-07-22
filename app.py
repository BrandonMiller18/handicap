import os
from werkzeug.utils import secure_filename

from flask import Flask, render_template, redirect, url_for, request, session, flash, make_response
from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, IntegerField, PasswordField, FileField
from wtforms.validators import DataRequired, Length
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user

from handicap import *
from account import *

app = Flask(__name__)
app.config.from_pyfile('config.py')

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
	return users.query.get(int(user_id))


class users(UserMixin, db.Model):
	id = db.Column(db.Integer, primary_key=True)
	first_name = db.Column(db.String(20), unique=False)
	last_name = db.Column(db.String(20), unique=False)
	username = db.Column(db.String(20), unique=True)
	password = db.Column(db.String(20), unique=False)
	email = db.Column(db.String(25), unique=True)
	avatar = db.Column(db.String(255))
	date_created = db.Column(db.DateTime, unique=True, default=datetime.now)
	
db.create_all()

class createAccount(FlaskForm):
	first_name = StringField('First Name',
		render_kw={"Placeholder": "First Name"})
	last_name = StringField('Last Name',
		render_kw={"Placeholder": "Last Name"})
	username = StringField('Username',
		render_kw={"Placeholder": "Username"},
		validators=[DataRequired(message='Must enter username.')])
	password = PasswordField('Password',
		render_kw={"Placeholder": "Password"},
		validators=[DataRequired(message='Must enter password.')])
	email = StringField('Email',
		render_kw={"Placeholder": "Email", "type": "email"},
		validators=[DataRequired(message='Must enter email.')])
	avatar = FileField('Profile Picture:')


class loginForm(FlaskForm):
	username = StringField('Username', validators=[DataRequired(message='Must enter username.')])
	password = PasswordField('Password', validators=[DataRequired(message='Must enter password.')])


class roundForm(FlaskForm):
	course = StringField('Course', render_kw={"Placeholder": "Course Name"})
	rating = FloatField('Course Rating',
		render_kw={"Placeholder": "Course Rating"},
		validators=[DataRequired(message='Course Rating is required')])
	slope = IntegerField('Slope',
		render_kw={"Placeholder": "Slope"},
		validators=[DataRequired(message='Slope is required')])
	score = IntegerField('Score',
		render_kw={"Placeholder": "Score (AGS)"},
		validators=[DataRequired(message='Score is required')])
	zipcode = StringField('Zipcode',
		render_kw={"Placeholder": "Zipcode"},
		validators=[Length(min=0, max=5, message='Zipcode must be 5 digits.')])

ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
	return render_template("index.html")


@app.route('/create-account', methods=["GET","POST"])
def create_account():
	form = createAccount()

	if form.validate_on_submit():
		if request.files['avatar']:
			file = request.files['avatar']
			if file and allowed_file(file.filename):
				filename = secure_filename(str(form.username))
				file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
		else:
			filename = 'default.png'


		create_new_account(form, filename, cur, cnx)

		username = form.username.data
		password = form.password.data
		user = users.query.filter_by(username=username, password=password).first()

		if user:
			login_user(user)
			user_id = str(user.id)
			resp = make_response(redirect(url_for("dashboard")))
			resp.set_cookie('uid', value=user_id, httponly=True)
			flash('Account created! Welcome to The Golf Handicap!', 'success')
			return resp
		else:
			flash("Error creating account.", "error")
			return render_template("createaccount.html", form=form)
	else:
		return render_template("createaccount.html", form=form)


@app.route('/login', methods=["GET", "POST"])
def login():
	form = loginForm()
	if form.validate_on_submit():
		username = form.username.data
		password = form.password.data

		user = users.query.filter_by(username=username, password=password).first()

		if user:
			login_user(user)
			user_id = str(user.id)

			resp = make_response(redirect(url_for("dashboard")))
			resp.set_cookie('uid', value=user_id, httponly=True)

			flash(f"Welcome back, {user.first_name}!", "success")

			return resp

		else:
			flash("Unable to login.", "error")
			return render_template('login.html', form=form)

	else:
		return render_template("login.html", form=form)


@app.route('/logout')
@login_required
def logout():
	logout_user()
	#set cookie here to expire in the past to clear uid cookie
	flash("Logged out!", "success")
	return redirect(url_for('index'))


@app.route('/account/home')
@login_required
def dashboard():
	user_id = request.cookies.get('uid')
	user = users.query.filter_by(id=user_id).first()

	rounds = get_rounds(cur, cnx, user_id)

	if rounds:
		handicap = round(get_handicap(rounds), 1)
		total_rounds = get_total_rounds(cur, cnx, user_id)
	else:
		handicap = "N/A"
		total_rounds = 0

	query = ("""SELECT avatar FROM users WHERE id = '{}'""".format(user_id))
	cur.execute(query)
	# this is the filename of the avatar image
	avatar = cur.fetchone()


	first_name = user.first_name
	last_name = user.last_name
	date = user.date_created

	return render_template("dashboard.html",
		first_name=first_name,
		last_name=last_name,
		avatar=avatar[0],
		handicap=handicap,
		total_rounds=total_rounds,
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
		add_round_record(round_data, cur, cnx, int(user_id))

		return redirect(url_for("dashboard"))
	else:
		# page with form to collect round data
		return render_template("addround.html", form=form)

if __name__ == '__main__':
	app.run() 