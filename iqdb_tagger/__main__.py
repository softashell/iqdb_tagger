#! /usr/bin/env python3
import os
import sys
import re
import imghdr
from pprint import pformat, pprint
from difflib import Differ

from bs4 import BeautifulSoup
from funclog import funclog
from PIL import Image
from robobrowser import RoboBrowser
import click
import mechanicalsoup
import structlog

from iqdb_tagger import sha256
from iqdb_tagger.utils import user_data_dir


db = "~/images/! tagged"
size = 200, 200
minsim = 75
services = [ '1', '2', '3', '4', '5', '6', '10', '11' ]
forcegray = False
log = structlog.getLogger()


def parse_single_result(html_tag):
    """pars html tag to get similar image data."""
    rating_dict = {'e': 'explicit', 's': 'safe', 'q': 'questionable'}
    # e.g.: '//danbooru.donmai.us/posts/993747'
    thumb = html_tag.img.get('src')
    raw_img_tags = html_tag.img.get('alt')
    # e.g.: 'Rating: s Score: 67 Tags: 1girl ...'
    title_attr = html_tag.img.get('title')
    if title_attr != raw_img_tags:
        d = Differ()
        diff_text = '\n'.join(d.compare(raw_img_tags, title_attr))
        log.warning('title and alt attribute is different.\n{}')
    metadata, tags = raw_img_tags.split(' Tags: ', 1)
    score = None
    try:
        rating, score = metadata.split(' Score: ', 1)
        score = score.strip()
    except ValueError:
        # only rating exist, e.g.: 'Rating: s Tags: ...'
        rating = metadata
    rating = rating.split('Rating: ', 1)[1].strip()
    if rating not in rating_dict:
        log.warning('Unknown rating: {}'.format(rating))
    rating = rating_dict.get(rating, rating)
    similarity = html_tag.parent.parent.select('tr')[-1].text.split('% similarity', 1)[0]
    # text from tag: '97% similarity'
    thumb = html_tag.img.get('src')
    href = html_tag.a.get('href')
    status = html_tag.parent.parent.select_one('th')
    if hasattr(status, 'text'):
        status = status.text
    else:
        status = None
    if status:
        if status not in ('Best match', 'Possible match'):
            log.debug('Unknown status', status=status)
    return {
        "href": href,
        # e.g.: //danbooru.donmai.us/posts/993747
        'href_url': 'https://www.donmai.us/posts/{}'.format(href.split('/')[-1]),
        'thumb': thumb,
        # e.g.: /danbooru/d/6/8/d6823ca37fb703b8e2a2f83f832e95aa.jpg
        'thumb_url': 'https://www.donmai.us/data/preview/{}'.format(os.path.basename(thumb)),
        'score': score,
        'rating': rating,
        'similarity': similarity,
        'tags': [x.replace('_', ' ') for x in tags.split(' ')],
        'status': status,
    }

def parse_page_best_match(page):
    """parse page to get best match result."""
    for html_tag in  page.select_one('div.pages').select('td.image')[1:]:
        yield parse_single_result(html_tag=html_tag)

def parse_page_more_match(page):
    """parse page to get more match (exclude best match result)."""
    for html_tag in page.select('div#more1 td.image'):
        yield parse_single_result(html_tag=html_tag)


def get_page_result(image):
    """get page result.

    Args:
        image: Image path to be uploaded.

    Returns:
        HTML page from the result.
    """
    br = mechanicalsoup.StatefulBrowser(soup_config={'features': 'lxml'})
    br.raise_on_404=True
    br.open('http://danbooru.iqdb.org')
    html_form = br.select_form('form')
    html_form.input({'file': image})
    br.submit_selected()
    # if ok, will output: <Response [200]>
    return br.get_current_page()


class ImageMatcher:

    def __init__(self, image):
        self.image = image
        self.image_sha256 = sha256.sha256_checksum(image)
        thumb_name = self.get_thumbnail_name()
        self.thumbnail_folder = os.path.join(user_data_dir, 'thumbs')
        self.thumb_path = os.path.join(self.thumbnail_folder, thumb_name)

    def get_thumbnail_name(self):
        """get thumbnail name."""
        img_ext = imghdr.what(self.image)
        if not img_ext:
            img_ext = os.path.splitext(self.image)
        return '{}.{}'.format(self.image_sha256, img_ext)

    def create_thumbnail(self):
        """create thumbnail.

        Returns:
            Thumbnail path.
        """
        if not os.path.isdir(self.thumbnail_folder):
            os.makedirs(self.thumbnail_folder, exist_ok=True)
        if not os.path.isfile(self.thumb_path):
            size=(300,300)
            im = Image.open(self.image)
            im.thumbnail(size, Image.ANTIALIAS)
            im.save(self.thumb_path)
        return self.thumb_path

    def sync(self, results):
        pass


@click.command()
@click.option(
    '--show-mode', type=click.Choice(['best-match', 'match', 'others', 'all']), default='match')
@click.option('--pager/--no-pager', default=False)
@click.argument('image')
def main(image, show_mode='match', pager=False):
    """Get similar image from iqdb."""
    im = ImageMatcher(image=image)
    im.create_thumbnail()
    page = get_page_result(image=im.thumb_path)
    # if ok, will output: <Response [200]>
    best_match_result = parse_page_best_match(page)
    others_result = parse_page_more_match(page)
    all_result = list(best_match_result)
    all_result.extend(others_result)
    im.sync(all_result)
    result = []
    if show_mode == 'best-match':
        result.extend([x for x in best_match_result if x['status'] == 'Best match'])
    elif show_mode == 'match':
        result.extend(best_match_result)
    elif show_mode == 'others':
        result.extend(others_result)
    elif show_mode == 'all':
        result.extend(best_match_result)
        result.extend(all_result)
    else:
        raise ValueError('Unknown show mode: {}'.format(show_mode))
    if pager:
        click.echo_via_pager('\n'.join([pformat(x) for x in result]))
    else:
        pprint(result)


def get_tags(image):
    """ Gets tags from iqdb and symlinks images to tags """

    image = os.path.abspath(image)
    name = os.path.basename(image)
    thumb = "/tmp/thumb_%s" % name
    dbpath = os.path.expanduser(db)

    print("Getting tags for %s " % name)

    im = Image.open(image)
    im.thumbnail(size, Image.ANTIALIAS)
    im.save(thumb, "JPEG")

    br = Browser()
    br.open("http://iqdb.org")
    br.select_form(nr=0)
    br.form["service[]"] = services
    if forcegray: br.form["forcegray"] = ["on"]
    br.form.add_file(open(thumb), 'text/plain', image)
    br.submit()

    os.remove(thumb)

    response = br.response().read()

    match = BeautifulSoup(response)
    match = match.findAll('table')[1] # Best match

    message = match.find('th').string #
    if not message == "Best match":
        print("\t%s" % message)
        return

    similarity = match.findAll('tr')[4].td.string
    similarity = re.search("([0-9][0-9])%", similarity).group(1)

    print("\tSimilarity %s%%" % similarity)
    if (int(similarity) < minsim):
        return

    tags = match.find('img').get('title')
    if tags: tags = re.search("Tags: (?P<tags>.*)", tags)
    if tags: tags = tags.group('tags').split(" ")

    if not tags:
        tags = ""

    print("\tFound %d tags" % len(tags))
    if not os.path.exists(dbpath):
        os.mkdir(dbpath)

    for tag in tags:
        tag = re.sub("\/", " ", tag)
        path = os.path.join(dbpath, tag.lower())
        target = os.path.join(path, name)

        if not os.path.isdir(path):
            os.mkdir(path)

        if not os.path.exists(target):
            os.symlink(image, target)

def parse_dir(path):
    """ Finds all images in target directory"""
    print("Searching images in %s" % path)

    for root, dirs, files in os.walk(path):
        print("Entering %s..." % root)
        if (root.startswith(os.path.expanduser(db))):
            continue
        for file in files:
            if re.search("\.(png|jpg|jpeg)$", file):
                file = os.path.join(root, file)
                get_tags(file)


if __name__ == "__main__":
    main()
