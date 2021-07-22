"""Flask configuration"""
import os

SECRET_KEY = 'dev'

SQLALCHEMY_TRACK_MODIFICATIONS = False
SQLALCHEMY_DATABASE_URI = "mysql://root:@localhost/golf_handicap"

UPLOAD_FOLDER = 'static/images/user_avatars'