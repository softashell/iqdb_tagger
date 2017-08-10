#!/usr/bin/env python3
"""server module."""
from flask import Flask, render_template, send_from_directory

from iqdb_tagger.models import ImageModel, init_db
from iqdb_tagger.utils import default_db_path, thumb_folder


app = Flask(__name__)


@app.route('/thumb/<path:basename>')
def thumb(basename):
    return send_from_directory(thumb_folder, basename)


@app.route('/')
def index():
    init_db(default_db_path)
    entries = ImageModel.select()
    return render_template('index.html', entries=entries)


def main():
    """main func."""
    app.run()


if __name__ == '__main__':
    app.run(debug=True)
