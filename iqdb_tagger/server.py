#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""server module."""
from logging.handlers import TimedRotatingFileHandler
import logging
import os
import pprint

from flask import (
    Flask,
    send_from_directory,
)
from flask.cli import FlaskGroup
from flask_admin import Admin
# from flask_admin.contrib.peewee import ModelView
import click
import structlog

from iqdb_tagger.__main__ import init_program
from iqdb_tagger.models import init_db
from iqdb_tagger.utils import default_db_path, thumb_folder, user_data_dir
from iqdb_tagger import views

log = structlog.getLogger()


def thumb(basename):
    """Get thumbnail."""
    return send_from_directory(thumb_folder, basename)


def create_app(script_info=None):
    """Create app."""
    app = Flask(__name__)
    # logging
    if not os.path.exists(user_data_dir):
        os.makedirs(user_data_dir)
    log_dir = os.path.join(user_data_dir, 'log')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    peewee_logger = logging.getLogger('peewee')
    peewee_logger.setLevel(logging.INFO)
    chardet_logger = logging.getLogger('chardet')
    chardet_logger.setLevel(logging.INFO)
    default_log_file = os.path.join(log_dir, 'iqdb_tagger_server.log')
    file_handler = TimedRotatingFileHandler(default_log_file, 'midnight')
    file_handler.setLevel(logging.WARNING)
    file_handler.setFormatter(logging.Formatter('<%(asctime)s> <%(levelname)s> %(message)s'))
    app.logger.addHandler(file_handler)
    app.logger.addHandler(peewee_logger)
    app.logger.addHandler(chardet_logger)
    # reloader
    reloader = app.config['TEMPLATES_AUTO_RELOAD'] = \
        bool(os.getenv('IQDB_TAGGER_RELOADER')) or app.config['TEMPLATES_AUTO_RELOAD']  # NOQA
    if reloader:
        app.jinja_env.auto_reload = True
    app.config['SECRET_KEY'] = os.getenv('IQDB_TAGGER_SECRET_KEY') or os.urandom(24)
    app.config['WTF_CSRF_ENABLED'] = False
    # debug
    debug = app.config['DEBUG'] = bool(os.getenv('IQDB_TAGGER_DEBUG')) or app.config['DEBUG']
    if debug:
        app.config['DEBUG'] = True
        app.config['LOGGER_HANDLER_POLICY'] = 'debug'
        logging.basicConfig(level=logging.DEBUG)
        pprint.pprint(app.config)
        print('Log file: {}'.format(default_log_file))
        print('script info:{}'.format(script_info))
    db_path = os.getenv('IQDB_TAGGER_DB_PATH') or default_db_path
    init_program()
    init_db(db_path)
    # app and db
    app.app_context().push()

    @app.shell_context_processor
    def shell_context():  # pylint: disable=unused-variable
        return {'app': app}

    # flask-admin
    app_admin = Admin(
        app, name='IQDB Tagger', template_mode='bootstrap3',
        index_view=views.HomeView(name='Home', template='iqdb_tagger/index.html', url='/'))

    app_admin.add_view(views.MatchView())
    # app_admin.add_view(ModelView(ImageMatch, category='DB'))
    # app_admin.add_view(ModelView(ImageMatchRelationship, category='DB'))
    # app_admin.add_view(ModelView(ImageModel, category='DB'))
    # app_admin.add_view(ModelView(MatchTagRelationship, category='DB'))
    # routing
    app.add_url_rule('/thumb/<path:basename>', view_func=thumb)
    return app


@click.group(cls=FlaskGroup, create_app=create_app)
def cli():
    """Run cli. This is a management script for application."""
    pass


if __name__ == '__main__':
    cli()
