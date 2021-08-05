from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, IntegerField, PasswordField, FileField
from wtforms.validators import DataRequired, Length, EqualTo
from wtforms.widgets import TextArea

##################
#				 #
#     FORMS      #
#				 #
##################

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
	confirm_password = PasswordField('Confirm Password',
		render_kw={"Placeholder": "Repeat Password"},
		validators=[
			DataRequired(message='Must enter password.'),
			EqualTo('password', message="Passwords must match.")
		])
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


class editRound(FlaskForm):
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


class addFriend(FlaskForm):
	username = StringField('Friend Name', validators=[DataRequired()],
		render_kw={"Placeholder": "Friend's TGH Username"})