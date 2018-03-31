#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""model module."""
import datetime
import logging
import os
from difflib import Differ
from urllib.parse import urljoin, urlparse

import structlog
from bs4 import BeautifulSoup
from peewee import (
    BooleanField,
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
from iqdb_tagger.utils import default_db_path

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

    @property
    def full_name(self):
        """Get full name."""
        if self.namespace:
            return self.namespace + ':' + self.name
        return self.name


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
    img_alt = TextField(null=True)
    width = IntegerField(null=True)
    height = IntegerField(null=True)

    @property
    def iqdb_thumb(self):
        """Get iqdb thumb url."""
        return urljoin('https://iqdb.org', self.thumb)

    @property
    def size(self):
        """Get size string."""
        if self.width and self.height:
            return '{}x{}'.format(self.width, self.height)

    @property
    def link(self):
        """Get href link."""
        return urljoin('https://', self.href)

    @property
    def link_netloc(self):
        """Get readable netloc."""
        netloc = urlparse(self.link).netloc
        if netloc.startswith('www.'):
            netloc = netloc.split('www.', 1)[1]
        endings = ['.net', '.com', '.us']
        for ending in endings:
            if netloc.endswith(ending):
                netloc = netloc.split(ending, 1)[0]
        return netloc

    @property
    def tags_from_img_alt(self):
        """Get readable tag from image alt."""
        result = []
        img_alt = self.img_alt[0]
        non_tags_txt = img_alt.split('Tags:')[0]
        tags_txt = img_alt.split('Tags:')[1]
        result.extend(tags_txt.split(' '))
        non_tags_txt.split('Score:')
        result.append(non_tags_txt.split('Score:')[0])
        result.append('Score:' + non_tags_txt.split('Score:')[1])
        result = [x.strip() for x in result if x]
        return result


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

    @property
    def size(self):
        """Get size string."""
        return '{}x{}'.format(self.width, self.height)

    @property
    def path_basename(self):
        """Get path basename."""
        return os.path.basename(self.path)

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

    def __str__(self):
        """Get string repr."""
        return '{}, checksum:{}..., size:{}x{} path:{}'.format(
            super().__str__(), self.checksum[:5],
            self.width, self.height, self.path
        )


class ImageMatchRelationship(BaseModel):
    """Image and match result."""

    image = ForeignKeyField(ImageModel)
    match_result = ForeignKeyField(Match)  # NOQA


class ImageMatch(BaseModel):
    """Image match."""

    STATUS_UNKNOWN = 0
    STATUS_BEST_MATCH = 1
    STATUS_POSSIBLE_MATCH = 2
    STATUS_OTHER = 3
    STATUS_CHOICES = (
        (STATUS_UNKNOWN, 'Unknown'),
        (STATUS_BEST_MATCH, 'Best match'),
        (STATUS_POSSIBLE_MATCH, 'Possible match'),
        (STATUS_OTHER, 'Other'),
    )
    SP_IQDB = 0
    SP_DANBOORU = 1
    SP_E621 = 2
    SP_CHOICES = (
        (SP_IQDB, 'iqdb'),
        (SP_DANBOORU, 'danbooru'),
        (SP_E621, 'e621'),
    )
    match = ForeignKeyField(ImageMatchRelationship)
    similarity = IntegerField()
    status = IntegerField(choices=STATUS_CHOICES)
    search_place = IntegerField(choices=SP_CHOICES)
    created_date = DateTimeField(default=datetime.datetime.now)
    force_gray = BooleanField(default=False)

    @staticmethod
    def _get_status_from_header_tag(header_tag):
        """Get status from header tag."""
        if hasattr(header_tag, 'text'):
            header_text = header_tag.text
            if header_text in ('Your image', 'No relevant matches'):
                return None
            best_match_text = \
                ('Best match', 'Additional match', 'Probable match:')
            if header_text == 'Possible match':
                status = ImageMatch.STATUS_POSSIBLE_MATCH
            elif header_text in best_match_text:
                status = ImageMatch.STATUS_BEST_MATCH
            elif header_text == 'Improbable match:':
                status = ImageMatch.STATUS_OTHER
            else:
                log.debug('header text', v=header_text)
                status = ImageMatch.STATUS_OTHER
        else:
            status = ImageMatch.STATUS_OTHER
        return status

    @staticmethod
    def parse_table(table):
        """Parse table."""
        header_tag = table.select_one('th')
        status = ImageMatch._get_status_from_header_tag(header_tag)
        if status is None:
            return None
        td_tags = table.select('td')
        assert '% similarity' in td_tags[-1].text, "similarity was not found in " + header_tag.text
        size_and_rating_text = td_tags[-2].text
        rating = Match.RATING_UNKNOWN
        for item in Match.RATING_CHOICES:
            if '[{}]'.format(item[1]) in size_and_rating_text:
                rating = item[0]
        size = size_and_rating_text.strip().split(' ', 1)[0].split('×')
        if len(size) == 1 and '×' not in size_and_rating_text:
            size = (None, None)
        else:
            size = (int(size[0]), int(size[1]))
        img_tag = table.select_one('img')
        img_alt = img_tag.attrs.get('alt')
        img_title = img_tag.attrs.get('title')
        if img_alt == '[IMG]' and img_title is None:
            img_alt = None
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
        if isinstance(page, str):
            page = BeautifulSoup(page, 'lxml')
        elif not isinstance(page, BeautifulSoup):
            if not os.path.isfile(page):
                raise ValueError('File not Exist: {}'.format(page))
            with open(page) as f:
                soup = BeautifulSoup(f.read(), 'lxml')
            page = soup

        tables = page.select('.pages table')
        for table in tables:
            res = ImageMatch.parse_table(table)
            if not res:
                continue
            a_tags = table.select('a')
            assert len(a_tags) < 3, "Unexpected html received at parse_page. Malformed link"
            if len(a_tags) == 2:
                additional_res = res
                additional_res['href'] = \
                    a_tags[1].attrs.get('href', None)
                yield additional_res
            yield res

    @staticmethod
    def get_or_create_from_page(page, image, place=None, force_gray=False):
        """Get or create from page result."""
        if place is None:
            place = ImageMatch.SP_IQDB
        items = ImageMatch.parse_page(page)
        for item in items:
            match_result, _ = Match.get_or_create(
                href=item['href'], defaults={
                    'thumb': item['thumb'],
                    'rating': item['rating'],
                    'img_alt': item['img_alt'],
                    'width': item['size'][0],
                    'height': item['size'][1],
                }
            )
            imr, _ = ImageMatchRelationship.get_or_create(
                image=image,
                match_result=match_result,
            )
            yield ImageMatch.get_or_create(
                match=imr,
                search_place=place,
                force_gray=force_gray,
                defaults={
                    'status': item['status'],
                    'similarity': item['similarity'],
                }
            )

    @property
    def status_verbose(self):
        """Get verbose status."""
        return dict(ImageMatch.STATUS_CHOICES)[self.status]

    @property
    def search_place_verbose(self):
        """Get verbose search place."""
        return dict(ImageMatch.SP_CHOICES)[self.search_place]


class ThumbnailRelationship(BaseModel):
    """Thumbnail tag relationship."""

    original = ForeignKeyField(ImageModel, related_name='thumbnails')  # NOQA
    thumbnail = ForeignKeyField(ImageModel)

    @staticmethod
    def get_or_create_from_image(
            image, size, thumb_folder=None, thumb_path=None, img_path=None):
        """Get or create from image."""
        thumbnails = [
            x for x in image.thumbnails
            if x.thumbnail.width == size[0] and x.thumbnail.height == size[1]
        ]
        if thumbnails:
            assert len(thumbnails) == 1, "There was not one thumbnail for the result"
            return thumbnails[0], False
        if thumb_path is None:
            thumb_path = '{}-{}-{}.jpg'.format(image.checksum, size[0], size[1])
            if thumb_folder:
                thumb_path = os.path.join(thumb_folder, thumb_path)
        if not os.path.isfile(thumb_path) or os.path.getsize(thumb_path) == 0:
            im = Image.open(image.path) if img_path is None else Image.open(img_path)
            im.thumbnail(size, Image.ANTIALIAS)
            try:
                im.save(thumb_path, 'JPEG')
            except OSError as e:
                valid_err = [
                    'cannot write mode RGBA as JPEG',
                    'cannot write mode P as JPEG',
                    'cannot write mode LA as JPEG',
                ]
                err_str = str(e)
                if err_str in valid_err:
                    log.debug('Converting to JPEG for error fix', err=err_str)
                    im = im.convert('RGB')
                    im.save(thumb_path, 'JPEG')
                else:
                    raise e
        thumb, _ = ImageModel.get_or_create_from_path(thumb_path)
        return ThumbnailRelationship.get_or_create(
            original=image, thumbnail=thumb)


def init_db(db_path=None, version=1):
    """Init db."""
    if db_path is None:
        db_path = default_db_path
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
