# -*- coding: utf-8 -*-
"""Utils module."""
import os

from appdirs import user_data_dir

user_data_dir = user_data_dir('iqdb_tagger', 'softashell')
default_db_path = os.path.join(user_data_dir, 'iqdb.db')
thumb_folder = os.path.join(user_data_dir, 'thumbs')
