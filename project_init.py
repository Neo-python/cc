from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def create_app():
    app = Flask(__name__)
    app.secret_key = "my name is neo"
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///./models/DPM.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
    app.config['SQLALCHEMY_ECHO'] = False
    return app
