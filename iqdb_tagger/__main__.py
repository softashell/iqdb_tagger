#! /usr/bin/env python3
# -*- coding: utf-8 -*-
"""main module."""
import os
import time

import cfscrape
import click
import mechanicalsoup
import requests
import structlog

from iqdb_tagger import models
from iqdb_tagger.__init__ import db_version
from iqdb_tagger.utils import default_db_path, thumb_folder, user_data_dir
from iqdb_tagger.custom_parser import get_tags

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


def get_posted_image(
        img_path, resize=False, size=None, output_thumb_folder=None):
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
    """Init program."""
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


def get_tags(browser, url, scraper):
    """Get tags."""
    # compatibility
    br = browser

    br.open(url)
    page = br.get_current_page()
    tags = get_tags(page, url, scraper)
    if tags:
        for tag in tags:
            tag_parts = tag.split(':', 1)
            if ':' in tag:
                tag_name = tag_parts[1]
                namespace = tag_parts[0]
            else:
                tag_name = tag_parts[0]
                namespace = None
            tag_model, _ = models.Tag.get_or_create(
                name=tag_name, namespace=namespace)
            MatchTagRelationship.get_or_create(match=match_result, tag=tag_model)
        return tags
    else:
        log.debug('No tags found.')


@click.command()
@click.option(
    '--place', type=click.Choice(['iqdb', 'danbooru']),
    default=DEFAULT_PLACE, help='Specify iqdb place, default:{}'.format(DEFAULT_PLACE)
)
@click.option('--resize', is_flag=True, help='Use resized image.')
@click.option('--size', is_flag=True, help='Specify resized image.')
@click.option('--db-path', help='Specify Database path.')
@click.option('--html-dump', is_flag=True, help='Dump html for debugging')
@click.option(
    '--match-filter', type=click.Choice(['default', 'best-match']),
    default='default', help='Filter the result.')
@click.argument('image')
def main(
    image, resize=False, size=None,
    db_path=None, html_dump=False, place=DEFAULT_PLACE, match_filter='default'
):
    """Get similar image from iqdb."""
    init_program(db_path)
    post_img = get_posted_image(img_path=image, resize=resize, size=size)
    url, im_place = iqdb_url_dict[place]
    page = get_page_result(image=post_img.path, url=url)
    # if ok, will output: <Response [200]>
    result = list(models.ImageMatch.get_or_create_from_page(
        page=page, image=post_img, place=im_place))
    result = [x[0] for x in result]
    if match_filter == 'best-match':
        result = [x for x in result if x.status == x.STATUS_BEST_MATCH]

    br = mechanicalsoup.StatefulBrowser(soup_config={'features': 'lxml'})
    br.raise_on_404 = True
    scraper = cfscrape.CloudflareScraper()
    MatchTagRelationship = models.MatchTagRelationship
    for item in result:
        match_result = item.match.match_result
        url = match_result.link

        print('{}|{}|{}'.format(
            item.similarity, item.status_verbose, url
        ))

        res = MatchTagRelationship.select().where(MatchTagRelationship.match == match_result)
        tags = [x.tag.full_name for x in res]
        if not tags:
            try:
                tags = get_tags(br, url, scraper)
            except requests.exceptions.ConnectionError as e:
                log.error(str(e), url=url)
        if tags:
            print('\n'.join(tags))
        else:
            log.debug('No tags found.')
        print('\n')
