"""Flask configuration"""
import os

SECRET_KEY = os.environ.get("SECRET_KEY")

SQLALCHEMY_TRACK_MODIFICATIONS = False
SQLALCHEMY_DATABASE_URI = os.environ.get("CLEARDB_DATABASE_URL")
SQLALCHEMY_DATABASE_PASSWORD = os.environ.get("DATABASE_PASSWORD")
FLASK_ADMIN_SWATCH = 'slate'

UPLOAD_FOLDER = 'static/images/user_avatars'