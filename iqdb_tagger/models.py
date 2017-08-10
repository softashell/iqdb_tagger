#!/usr/bin/env python3
"""model module."""
import datetime
import logging
import os
from difflib import Differ

import structlog
from bs4 import BeautifulSoup
from peewee import (
    CharField,
    DateTimeField,
    ForeignKeyField,
    IntegerField,
    Model,
    SqliteDatabase,
    TextField
)
from PIL import Image

from iqdb_tagger.sha256 import sha256_checksum

db = SqliteDatabase(None)
log = structlog.getLogger()


class BaseModel(Model):
    """base model."""

    class Meta:
        """meta."""

        database = db


class Program(BaseModel):
    """program model."""

    version = IntegerField()


class Tag(BaseModel):
    """Tag model."""

    name = CharField()
    namespace = CharField(null=True)


class Match(BaseModel):
    """Match model."""

    RATING_UNKNOWN = 0
    RATING_SAFE = 1
    RATING_ERO = 2
    RATING_EXPLICIT = 3

    RATING_CHOICES = (
        (RATING_UNKNOWN, 'Unknown'),
        (RATING_SAFE, 'Safe'),
        (RATING_ERO, 'Ero'),
        (RATING_EXPLICIT, 'Explicit'),
    )
    href = CharField(unique=True)
    thumb = CharField()
    rating = CharField()
    img_alt = TextField()
    width = IntegerField()
    height = IntegerField()


class MatchTagRelationship(BaseModel):
    """match tag relationship."""

    match = ForeignKeyField(Match)
    tag = ForeignKeyField(Tag)


class ImageModel(BaseModel):
    """Image model."""

    checksum = CharField(unique=True)
    width = IntegerField()
    height = IntegerField()
    path = CharField(null=True)

    @staticmethod
    def get_or_create_from_path(img_path):
        """Get or crate from path."""
        checksum = sha256_checksum(img_path)
        img = Image.open(img_path)
        width, height = img.size
        img, created = ImageModel.get_or_create(
            checksum=checksum, defaults={
                'width': width, 'height': height, 'path': img_path,
            }
        )
        return img, created


class ImageMatchRelationship(BaseModel):
    """Image and match result."""

    image = ForeignKeyField(ImageModel, related_name='match_relationship')
    match_result = ForeignKeyField(Match, related_name='related_to_match_image')  # NOQA


class ImageMatch(BaseModel):
    """Image match."""

    STATUS_UNKNOWN = 0
    STATUS_BEST_MATCH = 1
    STATUS_POSSIBLE_MATCH = 2
    STATUS_OTHER = 3
    STATUS_CHOICES = (
        (STATUS_UNKNOWN, 'Unknown'),
        (STATUS_BEST_MATCH, 'Possible match'),
        (STATUS_OTHER, 'Other'),
    )
    SP_IQDB = 0
    SP_DANBOORU = 1
    SP_CHOICES = (
        (SP_IQDB, 'iqdb'),
        (SP_DANBOORU, 'danbooru'),
    )
    match = ForeignKeyField(ImageMatchRelationship)
    similarity = IntegerField()
    status = IntegerField(choices=STATUS_CHOICES)
    search_place = IntegerField(choices=SP_CHOICES)
    created_date = DateTimeField(default=datetime.datetime.now)

    @staticmethod
    def parse_table(table):
        """Parse table."""
        header_text = table.select_one('th').text
        if header_text in ('Your image', 'No relevant matches'):
            return {}
        if header_text == 'Possible match':
            status = ImageMatch.STATUS_POSSIBLE_MATCH
        else:
            status = ImageMatch.STATUS_OTHER
        td_tags = table.select('td')
        assert '% similarity' in td_tags[-1].text
        size_and_rating_text = td_tags[-2].text
        rating = Match.RATING_UNKNOWN
        for item in Match.RATING_CHOICES:
            if '[{}]'.format(item[1]) in size_and_rating_text:
                rating = item[0]
        size = size_and_rating_text.strip().split(' ', 1)[0].split('×')
        img_tag = table.select_one('img')
        img_alt = img_tag.attrs.get('alt')
        img_title = img_tag.attrs.get('title')
        if img_alt != img_title:
            d = Differ()
            diff_text = '\n'.join(d.compare(img_alt, img_title))
            log.warning(
                'title and alt attribute of img tag is different.\n{}'.format(
                    diff_text
                )
            )
        return {
            # match
            'status': status,
            'similarity': td_tags[-1].text.split('% similarity', 1)[0],
            # match result
            'href': table.select_one('a').attrs.get('href', None),
            'thumb': table.select_one('img').attrs.get('src', None),
            'rating': rating,
            'size': size,
            'img_alt': img_alt,
        }

    @staticmethod
    def parse_page(page):
        """Parse page."""
        if not isinstance(page, BeautifulSoup):
            if not os.path.isfile(page):
                raise ValueError('File not Exist: {}'.format(page))
            with open(page) as f:
                soup = BeautifulSoup(f.read(), 'lxml')
            page = soup

        tables = page.select('#pages table')
        for table in tables:
            res = ImageMatch.parse_table(table)
            if not res:
                continue
            yield res

    @staticmethod
    def get_or_create_from_page(page, image, place=None):
        """Get or create from page result."""
        if place is None:
            place = ImageMatch.SP_IQDB
        for item in ImageMatch.parse_page(page):
            match_result, _ = Match.get_or_create(
                href=item['href'], defaults={
                    'thumb': item['thumb'],
                    'rating': item['rating'],
                    'img_alt': item['img_alt'],
                    'width': int(item['size'][0]),
                    'height': int(item['size'][1]),
                }
            )
            imr, _ = ImageMatchRelationship.get_or_create(
                image=image,
                match_result=match_result,
            )
            yield ImageMatch.get_or_create(
                match=imr,
                search_place=place,
                defaults={
                    'status': item['status'],
                    'similarity': item['similarity'],
                }
            )


class ThumbnailRelationship(BaseModel):
    """Thumbnail tag relationship."""

    original = ForeignKeyField(ImageModel, related_name='relationship')  # NOQA
    thumbnail = ForeignKeyField(ImageModel, related_name='related_to')

    @staticmethod
    def get_or_create_from_image(image, size, thumb_folder=None):
        """Get or create from image."""
        # TODO: check if thumbnail is already created.
        thumb_path = '{}-{}-{}.jpg'.format(image.checksum, size[0], size[1])
        if thumb_folder:
            thumb_path = os.path.join(thumb_folder, thumb_path)
        if not os.path.isfile(thumb_path):
            im = Image.open(image.path)
            im.thumbnail(size, Image.ANTIALIAS)
            im.save(thumb_path, 'JPEG')
        thumb, _ = ImageModel.get_or_create_from_path(thumb_path)
        return ThumbnailRelationship.get_or_create(
            original=image, thumbnail=thumb)


def init_db(db_path, version=1):
    """Init db."""
    db.init(db_path)
    if not os.path.isfile(db_path):
        model_list = [
            ImageMatch,
            ImageMatchRelationship,
            ImageModel,
            Match,
            MatchTagRelationship,
            Program,
            Tag,
            ThumbnailRelationship
        ]
        db.create_tables(model_list)
        version = Program(version=version)
        version.save()
    else:
        logging.debug('db already existed.')
