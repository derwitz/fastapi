import os
import logging
from logging.handlers import TimedRotatingFileHandler

from raven.contrib.flask import Sentry

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow

from fastapi.utils.error import APIError
from fastapi.utils.error_handlers import error_404_handler, error_handler
from fastapi.utils.hooks import before_request_handler, after_request_handler
from fastapi.utils.redis_client import init_redis_client
from fastapi.config import load_config

app = Flask(__name__)
db = SQLAlchemy()
ms = Marshmallow(app)


def init_config():
    config = load_config()
    app.config.from_object(config)


def init_logger():
    LEVELS = {'debug': logging.DEBUG,
              'info':  logging.INFO,
              'warning': logging.WARNING,
              'error': logging.ERROR,
              'critical': logging.CRITICAL}

    log_dir = os.path.join(app.config['LOG_PATH'])
    log_file = os.path.join(app.config['LOG_PATH'], app.config['LOG_FILENAME'])
    if not os.path.isdir(log_dir):
        os.mkdir(log_dir)

    log_level = LEVELS.get(app.config['LOG_LEVEL'].lower(), 'info')

    rotate_handler = TimedRotatingFileHandler(log_file, "D", 1, 30)
    rotate_handler.suffix = "%Y%m%d.log"
    rotate_handler.setLevel(log_level)

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(log_level)

    formatter = logging.Formatter('%(asctime)-10s %(levelname)s %(filename)s %(lineno)d %(process)d %(message)s')
    rotate_handler.setFormatter(formatter)
    stream_handler.setFormatter(formatter)

    app.logger.addHandler(stream_handler)
    app.logger.addHandler(rotate_handler)

    app.logger.info('初始化日志成功')


def init_db():
    db.init_app(app)
    app.logger.info('初始化db成功')

def init_redis():
    init_redis_client(app)
    app.logger.info('初始化Redis成功')


def init_blueprint():
    from fastapi.api import api_blueprint
    app.register_blueprint(api_blueprint, url_prefix='/api')
    app.logger.info('初始化blueprint成功')


def init_error_handlers():
    app.register_error_handler(404, error_404_handler)
    app.register_error_handler(APIError, error_handler)

def init_hooks():
    app.before_request(before_request_handler)
    app.after_request(after_request_handler)


def init_sentry():
    enable_sentry = app.config.get('ENABLE_SENTRY', False)
    if not enable_sentry:
        pass

    Sentry(app, dsn=app.config.get('SENTRY_DSN'))
    app.logger.info('初始化Sentry成功')


def init_app():
    init_config()
    init_logger()
    init_error_handlers()
    init_hooks()
    init_db()
    init_redis()
    init_sentry()
    init_blueprint()


init_app()