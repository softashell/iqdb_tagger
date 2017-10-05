#! /usr/bin/env python3
# -*- coding: utf-8 -*-
"""main module."""
import logging
import os
from urllib.parse import urlparse

import cfscrape
import click
import mechanicalsoup
import requests
import structlog

from iqdb_tagger import models
from iqdb_tagger.__init__ import db_version
from iqdb_tagger.custom_parser import get_tags as get_tags_from_parser
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


def get_page_result(image, url, browser=None):
    """Get page result.

    Args:
        image: Image path to be uploaded.
    Returns:
        HTML page from the result.
    """
    # compatibility
    br = browser

    if br is None:
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


def get_tags(match_result, browser=None, scraper=None):
    """Get tags."""
    # compatibility
    br = browser

    if br is None:
        br = mechanicalsoup.StatefulBrowser(soup_config={'features': 'lxml'})
        br.raise_on_404 = True
    if scraper is None:
        scraper = cfscrape.CloudflareScraper()

    url = match_result.link
    br.open(url, timeout=10)
    page = br.get_current_page()
    tags = get_tags_from_parser(page, url, scraper)
    if tags:
        for tag in tags:
            namespace, tag_name = tag
            tag_model, _ = models.Tag.get_or_create(
                name=tag_name, namespace=namespace)
            models.MatchTagRelationship.get_or_create(
                match=match_result, tag=tag_model)
            yield tag_model
    else:
        log.debug('No tags found.')


def run_program_for_single_img(
        image, resize, size, place, match_filter, write_tags, browser,
        scraper, disable_tag_print=False
):
    """Run program for single image."""
    # compatibility
    br = browser

    error_set = []
    post_img = get_posted_image(img_path=image, resize=resize, size=size)
    tag_textfile = image + '.txt'

    result = []
    for img_m_rel_set in post_img.imagematchrelationship_set:
        for item_set in img_m_rel_set.imagematch_set:
            if item_set.search_place_verbose == place:
                result.append(item_set)

    if not result:
        url, im_place = iqdb_url_dict[place]
        page = get_page_result(image=post_img.path, url=url, browser=br)
        # if ok, will output: <Response [200]>
        result = list(models.ImageMatch.get_or_create_from_page(
            page=page, image=post_img, place=im_place))
        result = [x[0] for x in result]

    if match_filter == 'best-match':
        result = [x for x in result if x.status == x.STATUS_BEST_MATCH]

    MatchTagRelationship = models.MatchTagRelationship
    for item in result:
        # type item: models.ImageMatch
        # type match_result: models.Match object
        match_result = item.match.match_result
        url = match_result.link

        print('{}|{}|{}'.format(
            item.similarity, item.status_verbose, url))

        try:
            res = MatchTagRelationship.select().where(
                MatchTagRelationship.match == match_result)
            tags = [x.tag for x in res]

            filtered_hosts = ['anime-pictures.net', 'www.theanimegallery.com']
            is_url_in_filtered_hosts = urlparse(match_result.link).netloc in \
                filtered_hosts
            if is_url_in_filtered_hosts:
                log.debug(
                    'URL in filtered hosts, no tag fetched',
                    url=match_result.link)
            elif not tags:
                try:
                    tags = list(
                        [x for x in get_tags(match_result, br, scraper)])
                except requests.exceptions.ConnectionError as e:
                    log.error(str(e), url=url)

            tags_verbose = [x.full_name for x in tags]
            log.debug('{} tag(s) founds'.format(len(tags_verbose)))
            if tags and not disable_tag_print:
                print('\n'.join(tags_verbose))
            else:
                log.debug('No printing tags.')

            if tags and write_tags:
                with open(tag_textfile, 'a') as f:
                    f.write('\n'.join(tags_verbose))
                    f.write('\n')
                log.debug('tags written')
        except Exception as e:  # pylint:disable=broad-except
            log.error('Error', e=str(e))
            error_set.append(e)

        return {'error': error_set}


@click.command()
@click.option(
    '--place', type=click.Choice(['iqdb', 'danbooru']),
    default=DEFAULT_PLACE,
    help='Specify iqdb place, default:{}'.format(DEFAULT_PLACE)
)
@click.option('--resize', is_flag=True, help='Use resized image.')
@click.option('--size', is_flag=True, help='Specify resized image.')
@click.option('--db-path', help='Specify Database path.')
@click.option(
    '--match-filter', type=click.Choice(['default', 'best-match']),
    default='default', help='Filter the result.'
)
@click.option(
    '--write-tags', is_flag=True, help='Write best match\'s tags to text.')
@click.option(
    '--input-mode', type=click.Choice(['default', 'folder']),
    default='default', help='Set input mode.'
)
@click.option('--verbose', '-v', is_flag=True, help='Verbose output.')
@click.option('--debug', '-d', is_flag=True, help='Print debug output.')
@click.argument('prog-input')
def main(
    prog_input, resize=False, size=None,
    db_path=None, place=DEFAULT_PLACE, match_filter='default',
    write_tags=False, input_mode='default', verbose=False, debug=False
):
    """Get similar image from iqdb."""
    # logging
    log_level = None
    if verbose:
        log_level = logging.INFO
    if debug:
        log_level = logging.DEBUG
    if log_level:
        logging.basicConfig(level=log_level)

    init_program(db_path)
    br = mechanicalsoup.StatefulBrowser(soup_config={'features': 'lxml'})
    br.raise_on_404 = True
    scraper = cfscrape.CloudflareScraper()

    # variable used in both input mode
    error_set = []
    if input_mode == 'folder':
        assert os.path.isdir(prog_input), 'Input is not valid folder'
        files = [os.path.join(prog_input, x) for x in os.listdir(prog_input)]
        if not files:
            print('No files found.')
            return
        for idx, ff in enumerate(files):
            log.debug(
                'file', f=os.path.basename(ff), idx=idx, total=len(files))
            result = {}
            try:
                result = run_program_for_single_img(
                    ff, resize, size, place, match_filter, write_tags,
                    browser=br, scraper=scraper, disable_tag_print=True
                )
            except Exception as e:  # pylint:disable=broad-except
                error_set.append((ff, e))
            if result is not None and result.get('error'):
                error_set.extend([(ff, x) for x in result['error']])
    else:
        image = prog_input
        result = run_program_for_single_img(
            image, resize, size, place, match_filter, write_tags,
            browser=br, scraper=scraper
        )
        if result is not None and result.get('error'):
            error_set.extend([(image, x) for x in result['error']])

    if error_set:
        print('Found error(s)')
        list(map(
            lambda x: print('path:{}\nerror:{}\n'.format(x[0], x[1])),
            error_set
        ))
