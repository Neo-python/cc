"""防止循环导入,项目初始化所需对象在此创建"""

import redis
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import config

db = SQLAlchemy()
pool = redis.ConnectionPool(host=config.REDIS_HOST, port='6379', db=1, decode_responses=True)
Redis = redis.StrictRedis(connection_pool=pool)


def create_app():
    app = Flask(__name__)
    app.secret_key = "my name is neo"
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///./model/DPM.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
    app.config['SQLALCHEMY_ECHO'] = False
    return app
