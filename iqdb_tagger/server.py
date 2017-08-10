#!/usr/bin/env python3
"""server module."""
from flask import Flask, render_template

from iqdb_tagger.models import ImageMatch, init_db
from iqdb_tagger.utils import default_db_path


app = Flask(__name__)


@app.route('/')
def index():
    init_db(default_db_path)
    entries = ImageMatch.select()
    return render_template('index.html', entries=entries)


def main():
    """main func."""
    app.run()


if __name__ == '__main__':
    app.run()
