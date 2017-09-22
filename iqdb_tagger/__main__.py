#! /usr/bin/env python3
# -*- coding: utf-8 -*-
"""main module."""
import os
import time

import click
import mechanicalsoup
import structlog

from iqdb_tagger import models
from iqdb_tagger.__init__ import db_version
from iqdb_tagger.utils import default_db_path, thumb_folder, user_data_dir

db = '~/images/! tagged'
DEFAULT_SIZE = 150, 150
DEFAULT_PLACE = 'iqdb'
minsim = 75
services = ['1', '2', '3', '4', '5', '6', '10', '11']
forcegray = False
log = structlog.getLogger()
iqdb_url_dict = {
    'iqdb': ('http://iqdb.org', models.ImageMatch.SP_IQDB),
    'danbooru': (
        'http://danbooru.iqdb.org',
        models.ImageMatch.SP_DANBOORU
    ),
}


def get_page_result(image, url):
    """Get page result.

    Args:
        image: Image path to be uploaded.
    Returns:
        HTML page from the result.
    """
    br = mechanicalsoup.StatefulBrowser(soup_config={'features': 'lxml'})
    br.raise_on_404 = True
    br.open(url)
    html_form = br.select_form('form')
    html_form.input({'file': image})
    br.submit_selected()
    # if ok, will output: <Response [200]>
    return br.get_current_page()


def get_posted_image(img_path, resize=False, size=None, output_thumb_folder=None):
    """Get posted image."""
    if output_thumb_folder is None:
        output_thumb_folder = thumb_folder

    img, _ = models.ImageModel.get_or_create_from_path(img_path)
    def_thumb_rel, _ = models.ThumbnailRelationship.get_or_create_from_image(
        image=img, thumb_folder=output_thumb_folder, size=DEFAULT_SIZE)
    resized_thumb_rel = None

    if resize and size:
        resized_thumb_rel, _ = \
            models.ThumbnailRelationship.get_or_create_from_image(
                image=img, thumb_folder=output_thumb_folder, size=size
            )
    elif resize:
        # use thumbnail if no size is given
        resized_thumb_rel = def_thumb_rel
    else:
        log.debug('Unknown config.', resize=resize, size=size)

    return resized_thumb_rel.thumbnail \
        if resized_thumb_rel is not None else img


def init_program(db_path=None):
    """init program."""
    # create user data dir
    if not os.path.isdir(user_data_dir):
        os.makedirs(user_data_dir, exist_ok=True)
        log.debug('User data dir created.')
    # create thumbnail folder
    if not os.path.isdir(thumb_folder):
        os.makedirs(thumb_folder, exist_ok=True)
        log.debug('Thumbnail folder created.')

    # database
    if db_path is None:
        db_path = default_db_path
    models.init_db(db_path, db_version)


@click.command()
@click.option(
    '--place', type=click.Choice(['iqdb', 'danbooru']),
    default=DEFAULT_PLACE,
    help='Specify iqdb place, default:{}'.format(DEFAULT_PLACE)
)
@click.option('--resize', is_flag=True, help='Use resized image.')
@click.option('--size', is_flag=True, help='Specify resized image.')
@click.option('--db-path', help='Specify Database path.')
@click.option('--html-dump', is_flag=True, help='Dump html for debugging')
@click.argument('image')
def main(
    image, resize=False, size=None,
    db_path=None, html_dump=False, place=DEFAULT_PLACE
):
    """Get similar image from iqdb."""
    init_program(db_path)
    post_img = get_posted_image(img_path=image, resize=resize, size=size)
    url, im_place = iqdb_url_dict[place]
    page = get_page_result(image=post_img.path, url=url)
    # if ok, will output: <Response [200]>
    if html_dump:
        timestr = time.strftime('%Y%m%d-%H%M%S') + '.html'
        with open(timestr, 'w') as f:
            f.write(str(page))
    return list(models.ImageMatch.get_or_create_from_page(
        page=page, image=post_img, place=im_place))
