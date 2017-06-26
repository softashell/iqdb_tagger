#! /usr/bin/env python3
import os
import sys
import re
import imghdr
from pprint import pprint
from difflib import Differ

from appdirs import user_data_dir
from bs4 import BeautifulSoup
from funclog import funclog
from PIL import Image
from robobrowser import RoboBrowser
import click
import mechanicalsoup
import structlog

from iqdb_tagger import sha256

db = "~/images/! tagged"
size = 200, 200
minsim = 75
services = [ '1', '2', '3', '4', '5', '6', '10', '11' ]
forcegray = False
log = structlog.getLogger()


@funclog(log)
def get_thumbnail_name(filename):
    """get thumbnail name."""
    im_sha256 = sha256.sha256_checksum(filename)
    img_ext = imghdr.what(filename)
    if not img_ext:
        img_ext = os.path.splitext(filename)
    return '{}.{}'.format(im_sha256, img_ext)


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
    status = html_tag.parent.parent.select_one('th').text
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


@click.command()
@click.argument('image')
def main(image, show='match'):
    """Get similar image from iqdb."""
    url = 'http://danbooru.iqdb.org'

    thumbnail = get_thumbnail_name(filename=image)
    thumbnail_folder = os.path.join(user_data_dir('iqdb_tagger', 'softashell'), 'thumbs')
    thumb_path = os.path.join(thumbnail_folder, thumbnail)
    if not os.path.isdir(thumbnail_folder):
        os.makedirs(thumbnail_folder, exist_ok=True)

    if not os.path.isfile(thumb_path):
        size=(300,300)
        im = Image.open(image)
        im.thumbnail(size, Image.ANTIALIAS)
        im.save(thumb_path)

    br = mechanicalsoup.StatefulBrowser(soup_config={'features': 'lxml'})
    br.raise_on_404=True
    br.open(url)
    html_form = br.select_form('form')
    html_form.input({'file': thumb_path})
    br.submit_selected()
    # if ok, will output: <Response [200]>
    best_match_result = parse_page_best_match(br.get_current_page())
    others_result = parse_page_more_match(br.get_current_page())
    result = []
    if show == 'match':
        result.extend(best_match_result)
    elif show == 'others':
        result.extend(others_result)
    for item in result:
        pprint(item)

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
