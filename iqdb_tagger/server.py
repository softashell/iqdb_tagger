#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""server module."""
import os
from math import ceil
from tempfile import gettempdir
from urllib.parse import urlparse

import click
import requests
import structlog
from flask import (
    Flask,
    abort,
    flash,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for
)
from werkzeug.utils import secure_filename

from iqdb_tagger.__main__ import (
    DEFAULT_PLACE,
    get_page_result,
    get_posted_image,
    get_tags_from_match_result,
    init_program,
    iqdb_url_dict
)
from iqdb_tagger.models import (
    ImageMatch,
    ImageMatchRelationship,
    ImageModel,
    MatchTagRelationship,
    init_db
)
from iqdb_tagger.utils import default_db_path, thumb_folder, user_data_dir

app = Flask(__name__)
log = structlog.getLogger()


@app.route('/thumb/<path:basename>')
def thumb(basename):
    """Get thumbnail."""
    return send_from_directory(thumb_folder, basename)


class Pagination(object):
    """Pagination object."""

    def __init__(self, page, per_page, total_count):
        """Init method."""
        self.page = page
        self.per_page = per_page
        self.total_count = total_count

    @property
    def pages(self):
        """Get pages."""
        return int(ceil(self.total_count / float(self.per_page)))

    @property
    def has_prev(self):
        """Check if it have previous page."""
        return self.page > 1

    @property
    def has_next(self):
        """Check if it have next page."""
        return self.page < self.pages

    def iter_pages(
            self, left_edge=2, left_current=2, right_current=5, right_edge=2):
        """Iterate pages."""
        last = 0
        for num in range(1, self.pages + 1):
            if num <= left_edge or (
                num > self.page - left_current - 1 and
                num < self.page + right_current
            ) or num > self.pages - right_edge:
                if last + 1 != num:
                    yield None
                yield num
                last = num


@app.route('/', methods=['GET', 'POST'], defaults={'page': 1})
@app.route('/page/<int:page>')
def index(page):
    """Get index page."""
    if not os.path.isdir(user_data_dir):
        os.makedirs(user_data_dir, exist_ok=True)
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submit a empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file:
            upload_folder = gettempdir()
            filename = os.path.join(
                upload_folder, secure_filename(file.filename))
            log.debug('file saved', p=filename)
            file.save(filename)
        else:
            flash('Error uploading file.')
            return redirect(request.url)
        size = None
        if 'resize' in request.args:
            resize = True
            resize_value = request.args.get('resize')
            if resize_value and 'x' in resize_value:
                resize_value_parts = resize_value.split('x')
                size = int(resize_value_parts[0]), (resize_value_parts[1])
        else:
            resize = False
        init_db(default_db_path)
        posted_img = get_posted_image(
            img_path=filename, resize=resize, size=size)
        place = request.args.get('place', DEFAULT_PLACE)
        url, im_place = iqdb_url_dict[place]
        query = posted_img.imagematchrelationship_set \
            .select().join(ImageMatch) \
            .where(ImageMatch.search_place == im_place)
        if not query.exists():
            try:
                result_page = get_page_result(image=posted_img.path, url=url)
            except requests.exceptions.ConnectionError as e:
                log.error(str(e))
                flash('Connection error.')
                return redirect(request.url)
            list(ImageMatch.get_or_create_from_page(
                page=result_page, image=posted_img, place=im_place))
        return redirect(url_for('match_sha256', checksum=posted_img.checksum))
    init_db(default_db_path)
    item_per_page = 10
    entries = (
        ImageModel.select()
        .distinct()
        .join(ImageMatchRelationship)
        .where(ImageMatchRelationship.image)
        .order_by(ImageModel.id.desc())
    )
    paginated_entries = entries.paginate(page, item_per_page)
    if not entries.exists() and page != 1:
        abort(404)
    pagination = Pagination(page, item_per_page, entries.count())
    return render_template(
        'index.html', entries=paginated_entries, pagination=pagination)


@app.route('/match/sha256-<checksum>', methods=['GET', 'POST'])
def match_sha256(checksum):
    """Get image match the checksum."""
    init_db()
    entry = ImageModel.get(ImageModel.checksum == checksum)
    return render_template('match.html', entry=entry)


@app.route('/match/d/<pair_id>', methods=['GET'])
def single_match_detail(pair_id):
    """Show single match pair."""
    init_db()
    nocache = False
    entry = ImageMatchRelationship.get(ImageMatchRelationship.id == pair_id)

    match_result = entry.match_result
    mt_rel = MatchTagRelationship.select().where(
        MatchTagRelationship.match == match_result)
    tags = [x.tag.full_name for x in mt_rel]
    filtered_hosts = ['anime-pictures.net', 'www.theanimegallery.com']

    if urlparse(match_result.link).netloc in filtered_hosts:
        log.debug(
            'URL in filtered hosts, no tag fetched', url=match_result.link)
    elif not tags or nocache:
        try:
            tags = list(get_tags_from_match_result(match_result))
            if not tags:
                log.debug('Tags not founds', id=pair_id)
        except requests.exceptions.ConnectionError as e:
            log.error(str(e), url=match_result.link)

    return render_template('single_match.html', entry=entry)


@click.group()
def cli():
    """CLI func."""
    pass


@cli.command()
def init():
    """Init program."""
    init_program()


@cli.command()
@click.option('--debug/--no-debug', default=False)
def start(debug):
    """Start server."""
    # compatibility
    app.run(debug=debug, threaded=True)


def main():
    """Run main function."""
    cli()


if __name__ == '__main__':
    main()
