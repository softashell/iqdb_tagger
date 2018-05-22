#! /usr/bin/env python3
# -*- coding: utf-8 -*-
"""main module."""
from tempfile import NamedTemporaryFile
from urllib.parse import urlparse
import logging
import os
import platform
import shutil

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
    'iqdb': (
        'http://iqdb.org', models.ImageMatch.SP_IQDB),
    'danbooru': (
        'http://danbooru.iqdb.org', models.ImageMatch.SP_DANBOORU
    ),
    'e621': (
        'http://iqdb.harry.lu', models.ImageMatch.SP_E621),
}


def get_page_result(image, url, browser=None, use_requests=False):
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

    if use_requests:
        files = {'file': open(image, 'rb')}
        resp = requests.post(url, files=files, timeout=10)
        return resp.text
    br.open(url)
    html_form = br.select_form('form')
    html_form.input({'file': image})
    br.submit_selected()
    # if ok, will output: <Response [200]>
    return br.get_current_page()


def get_posted_image(
        img_path, resize=False, size=None, output_thumb_folder=None, thumb_path=None):
    """Get posted image."""
    if output_thumb_folder is None:
        output_thumb_folder = thumb_folder

    img, _ = models.ImageModel.get_or_create_from_path(img_path)
    def_thumb_rel, _ = models.ThumbnailRelationship.get_or_create_from_image(
        image=img,
        thumb_folder=output_thumb_folder,
        size=DEFAULT_SIZE,
        thumb_path=thumb_path,
        img_path=img_path
    )
    resized_thumb_rel = None

    if resize and size:
        resized_thumb_rel, _ = \
            models.ThumbnailRelationship.get_or_create_from_image(
                image=img,
                thumb_folder=output_thumb_folder,
                size=size,
                img_path=img_path
            )
    elif resize:
        # use thumbnail if no size is given
        resized_thumb_rel = def_thumb_rel
    else:
        # no resize, return models.ImageModel obj
        return img

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


def get_tags_from_match_result(match_result, browser=None, scraper=None):
    """Get tags from match result."""
    if browser is None:
        browser = mechanicalsoup.StatefulBrowser(soup_config={'features': 'lxml'})
        browser.raise_on_404 = True

    res = models.MatchTagRelationship.select().where(
        models.MatchTagRelationship.match == match_result)
    tags = [x.tag for x in res]

    filtered_hosts = ['anime-pictures.net', 'www.theanimegallery.com']
    is_url_in_filtered_hosts = urlparse(match_result.link).netloc in \
        filtered_hosts
    if is_url_in_filtered_hosts:
        log.debug('URL in filtered hosts, no tag fetched', url=match_result.link)
    elif not tags:
        try:
            browser.open(match_result.link, timeout=10)
            page = browser.get_current_page()
            new_tags = get_tags_from_parser(page, match_result.link, scraper)
            new_tag_models = []
            if new_tags:
                for tag in new_tags:
                    namespace, tag_name = tag
                    tag_model, _ = models.Tag.get_or_create(
                        name=tag_name, namespace=namespace)
                    models.MatchTagRelationship.get_or_create(
                        match=match_result, tag=tag_model)
                    new_tag_models.append(tag_model)
            else:
                log.debug('No tags found.')

            tags.extend(new_tag_models)
        except (requests.exceptions.ConnectionError, mechanicalsoup.LinkNotFoundError) as e:
            log.error(str(e), url=match_result.link)
    return tags


def write_url_from_match_result(match_result, folder=None):
    """Write url from match result."""
    netloc = urlparse(match_result.link).netloc
    sanitized_netloc = netloc.replace('.', '_')
    text_file_basename = sanitized_netloc + '.txt'
    text_file = os.path.join(folder, text_file_basename) if folder is not None else text_file_basename
    with open(text_file, 'a') as f:
        f.write(match_result.link)
        f.write('\n')


def get_result_on_windows(image, place, resize=None, size=None, browser=None):
    """Get result on Windows."""
    result = []
    # temp_f
    temp_f = NamedTemporaryFile(mode='w+t', delete=False)
    temp_file_name = temp_f.name
    # thumb_temp_f
    thumb_temp_f = NamedTemporaryFile(mode='w+t', delete=False)
    thumb_temp_file_name = thumb_temp_f.name
    # copy to temp file
    shutil.copyfile(image, temp_f.name)
    # get image to be posted based on user input
    try:
        post_img = get_posted_image(
            img_path=temp_f.name, resize=resize, size=size,
            thumb_path=thumb_temp_f.name)
    except OSError as e:
        raise OSError(str(e) + ' when processing {}'.format(image))
    # append data to result
    for img_m_rel_set in post_img.imagematchrelationship_set:
        for item_set in img_m_rel_set.imagematch_set:
            if item_set.search_place_verbose == place:
                result.append(item_set)

    if not result:
        url, im_place = iqdb_url_dict[place]
        use_requests = True if place != 'e621' else False
        post_img_path = temp_f.name if not resize else thumb_temp_f.name
        page = get_page_result(
            image=post_img_path, url=url, browser=browser,
            use_requests=use_requests
        )
        # if ok, will output: <Response [200]>
        result = list(models.ImageMatch.get_or_create_from_page(
            page=page, image=post_img, place=im_place))
        result = [x[0] for x in result]
    # temp_f
    temp_f.close()
    os.remove(temp_file_name)
    # thumb_temp_f
    thumb_temp_f.close()
    os.remove(thumb_temp_file_name)
    return result


def run_program_for_single_img(
        image, resize, size, place, match_filter, browser,
        scraper, disable_tag_print=False, write_tags=False, write_url=False
):
    """Run program for single image."""
    # compatibility
    br = browser

    error_set = []
    tag_textfile = image + '.txt'
    folder = os.path.dirname(image)
    result = []

    if platform.system() == 'Windows':
        result = get_result_on_windows(
            image, place, resize=resize, size=size, browser=br)
    else:
        with NamedTemporaryFile() as temp, NamedTemporaryFile() as thumb_temp:
            shutil.copyfile(image, temp.name)
            try:
                post_img = get_posted_image(
                    img_path=temp.name, resize=resize, size=size, thumb_path=thumb_temp.name)
            except OSError as e:
                raise OSError(str(e) + ' when processing {}'.format(image))

            for img_m_rel_set in post_img.imagematchrelationship_set:
                for item_set in img_m_rel_set.imagematch_set:
                    if item_set.search_place_verbose == place:
                        result.append(item_set)

            if not result:
                url, im_place = iqdb_url_dict[place]
                use_requests = True if place != 'e621' else False
                post_img_path = temp.name if not resize else thumb_temp.name
                page = get_page_result(
                    image=post_img_path, url=url, browser=br,
                    use_requests=use_requests
                )
                # if ok, will output: <Response [200]>
                result = list(models.ImageMatch.get_or_create_from_page(
                    page=page, image=post_img, place=im_place))
                result = [x[0] for x in result]

    if match_filter == 'best-match':
        result = [x for x in result if x.status == x.STATUS_BEST_MATCH]

    log.debug('Number of valid result', n=len(result))
    for item in result:
        # type item: models.ImageMatch
        # type match_result: models.Match object
        match_result = item.match.match_result
        url = match_result.link
        print('{}|{}|{}'.format(
            item.similarity, item.status_verbose, url))

        try:
            tags = get_tags_from_match_result(match_result, browser, scraper)
            tags_verbose = [x.full_name for x in tags]
            log.debug('{} tag(s) founds'.format(len(tags_verbose)))
            if tags and not disable_tag_print:
                print('\n'.join(tags_verbose))

            if tags and write_tags:
                with open(tag_textfile, 'a') as f:
                    f.write('\n'.join(tags_verbose))
                    f.write('\n')
                log.debug('tags written')
            if write_url:
                write_url_from_match_result(match_result, folder)
        except Exception as e:  # pylint:disable=broad-except
            log.error('Error', e=str(e))
            error_set.append(e)

    return {'error': error_set}


@click.group()
@click.version_option()
def cli():
    """Run cli."""
    pass


@cli.command()
@click.version_option()
@click.option(
    '--place', type=click.Choice([x for x in iqdb_url_dict]),
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
@click.option('--write-tags', is_flag=True, help='Write best match\'s tags to text.')
@click.option('--write-url', is_flag=True, help='Write match url to text.')
@click.option(
    '--input-mode', type=click.Choice(['default', 'folder']),
    default='default', help='Set input mode.'
)
@click.option('--verbose', '-v', is_flag=True, help='Verbose output.')
@click.option('--debug', '-d', is_flag=True, help='Print debug output.')
@click.option(
    '--abort-on-error', is_flag=True, help='Stop program when error occured')
@click.argument('prog-input')
def run(
    prog_input=None, resize=False, size=None,
    db_path=None, place=DEFAULT_PLACE, match_filter='default',
    input_mode='default', verbose=False, debug=False,
    abort_on_error=False, write_tags=False, write_url=False

):
    """Get similar image from iqdb."""
    assert prog_input is not None, "Input is not a valid path"

    # logging
    log_level = None
    if verbose:
        log_level = logging.INFO
    if debug:
        log_level = logging.DEBUG
    if log_level:

        logging.basicConfig(handlers=[logging.FileHandler(os.path.join(user_data_dir, 'output.log'), 'w', 'utf-8')], level=log_level)

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
        sorted_files = sorted(files, key=lambda x: os.path.splitext(x)[1])
        for idx, ff in enumerate(sorted_files):
            log.debug(
                'file', f=os.path.basename(ff), idx=idx, total=len(files))
            result = {}
            try:
                result = run_program_for_single_img(
                    ff, resize, size, place, match_filter,
                    browser=br, scraper=scraper, disable_tag_print=True,
                    write_tags=write_tags, write_url=write_url
                )
            except Exception as e:  # pylint:disable=broad-except
                if abort_on_error:
                    raise e
                error_set.append((ff, e))
            if result is not None and result.get('error'):
                error_set.extend([(ff, x) for x in result['error']])
    else:
        image = prog_input
        result = run_program_for_single_img(
            image, resize, size, place, match_filter,
            browser=br, scraper=scraper,
            write_tags=write_tags, write_url=write_url
        )
        if result is not None and result.get('error'):
            error_set.extend([(image, x) for x in result['error']])

    if error_set:
        log.error('Found error(s)')
        for x in error_set:
            log.error('path: ' + x[0] + '\nerror: ' + str(x[1]))


if __name__ == '__main__':
    cli()
