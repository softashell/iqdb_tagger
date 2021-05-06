#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""model module."""
import datetime
import logging
import os
from typing import Any, List, Optional, Tuple, TypeVar
from urllib.parse import urljoin, urlparse

import cfscrape
import mechanicalsoup
import requests
import structlog
from peewee import (
    BooleanField,
    CharField,
    DateTimeField,
    ForeignKeyField,
    IntegerField,
    Model,
    SqliteDatabase,
    TextField,
)
from PIL import Image

from .custom_parser import get_tags as get_tags_from_parser
from .sha256 import sha256_checksum
from .utils import default_db_path
from .utils import thumb_folder as default_thumb_folder

DEFAULT_SIZE = 150, 150
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
    def full_name(self) -> str:
        """Get full name."""
        if self.namespace:
            return self.namespace + ":" + self.name
        return self.name


class Match(BaseModel):
    """Match model."""

    RATING_UNKNOWN = 0
    RATING_SAFE = 1
    RATING_ERO = 2
    RATING_EXPLICIT = 3

    RATING_CHOICES = (
        (RATING_UNKNOWN, "Unknown"),
        (RATING_SAFE, "Safe"),
        (RATING_ERO, "Ero"),
        (RATING_EXPLICIT, "Explicit"),
    )
    href = CharField(unique=True)
    thumb = CharField()
    rating = CharField()
    img_alt = TextField(null=True)
    width = IntegerField(null=True)
    height = IntegerField(null=True)

    @property
    def iqdb_thumb(self) -> str:
        """Get iqdb thumb url."""
        return urljoin("https://iqdb.org", self.thumb)

    @property
    def size(self) -> Optional[str]:
        """Get size string."""
        if self.width and self.height:
            return "{}x{}".format(self.width, self.height)
        return None

    @property
    def link(self) -> str:
        """Get href link."""
        return urljoin("https://", self.href)

    @property
    def link_netloc(self) -> str:
        """Get readable netloc."""
        netloc = urlparse(self.link).netloc
        if netloc.startswith("www."):
            netloc = netloc.split("www.", 1)[1]
        endings = [".net", ".com", ".us"]
        for ending in endings:
            if netloc.endswith(ending):
                netloc = netloc.split(ending, 1)[0]
        return netloc

    @property
    def tags_from_img_alt(self) -> List[Any]:
        """Get readable tag from image alt."""
        result = []
        img_alt = self.img_alt[0]
        non_tags_txt = img_alt.split("Tags:")[0]
        tags_txt = img_alt.split("Tags:")[1]
        result.extend(tags_txt.split(" "))
        non_tags_txt.split("Score:")
        result.append(non_tags_txt.split("Score:")[0])
        result.append("Score:" + non_tags_txt.split("Score:")[1])
        result = [x.strip() for x in result if x]
        return result


class MatchTagRelationship(BaseModel):
    """match tag relationship."""

    match = ForeignKeyField(Match)
    tag = ForeignKeyField(Tag)


IM = TypeVar("IM", bound="ImageModel")


class ImageModel(BaseModel):
    """Image model."""

    checksum = CharField(unique=True)
    width = IntegerField()
    height = IntegerField()
    path = CharField(null=True)

    @property
    def size(self) -> str:
        """Get size string."""
        return "{}x{}".format(self.width, self.height)

    @property
    def path_basename(self) -> str:
        """Get path basename."""
        return os.path.basename(self.path)

    @staticmethod
    def get_or_create_from_path(img_path: str) -> Tuple[IM, bool]:
        """Get or crate from path."""
        checksum = sha256_checksum(img_path)
        img = Image.open(img_path)
        width, height = img.size
        img, created = ImageModel.get_or_create(
            checksum=checksum,
            defaults={
                "width": width,
                "height": height,
                "path": img_path,
            },
        )
        return img, created

    def __str__(self) -> str:
        """Get string repr."""
        return "{}, checksum:{}..., size:{}x{} path:{}".format(super().__str__(), self.checksum[:5], self.width, self.height, self.path)


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
        (STATUS_UNKNOWN, "Unknown"),
        (STATUS_BEST_MATCH, "Best match"),
        (STATUS_POSSIBLE_MATCH, "Possible match"),
        (STATUS_OTHER, "Other"),
    )
    SP_IQDB = 0
    SP_DANBOORU = 1
    SP_E621 = 2
    SP_ANIME_PICTURES = 3
    SP_E_SHUUSHUU = 4
    SP_GELBOORU = 5
    SP_KONACHAN = 6
    SP_SANKAKU = 7
    SP_THEANIMEGALLERY = 8
    SP_YANDERE = 9
    SP_ZEROCHAN = 10
    SP_CHOICES = (
        (SP_IQDB, "iqdb"),
        (SP_DANBOORU, "danbooru"),
        (SP_E621, "e621"),
        (SP_ANIME_PICTURES, "anime_pictures"),
        (SP_E_SHUUSHUU, "e_shuushuu"),
        (SP_GELBOORU, "gelbooru"),
        (SP_KONACHAN, "konachan"),
        (SP_SANKAKU, "sankaku"),
        (SP_THEANIMEGALLERY, "theanimegallery"),
        (SP_YANDERE, "yandere"),
        (SP_ZEROCHAN, "zerochan"),
    )
    match = ForeignKeyField(ImageMatchRelationship)
    similarity = IntegerField()
    status = IntegerField(choices=STATUS_CHOICES)
    search_place = IntegerField(choices=SP_CHOICES)
    created_date = DateTimeField(default=datetime.datetime.now)
    force_gray = BooleanField(default=False)

    @property
    def status_verbose(self) -> str:
        """Get verbose status."""
        return dict(ImageMatch.STATUS_CHOICES)[self.status]

    @property
    def search_place_verbose(self) -> str:
        """Get verbose search place."""
        return dict(ImageMatch.SP_CHOICES)[self.search_place]


iqdb_url_dict = {
    "iqdb": ("http://iqdb.org", ImageMatch.SP_IQDB),
    "danbooru": ("http://danbooru.iqdb.org", ImageMatch.SP_DANBOORU),
    "e621": ("http://iqdb.harry.lu", ImageMatch.SP_E621),
    "anime_pictures": ("https://anime-pictures.iqdb.org", ImageMatch.SP_ANIME_PICTURES),
    "e_shuushuu": ("https://e-shuushuu.iqdb.org", ImageMatch.SP_E_SHUUSHUU),
    "gelbooru": ("https://gelbooru.iqdb.org", ImageMatch.SP_GELBOORU),
    "konachan": ("https://konachan.iqdb.org", ImageMatch.SP_KONACHAN),
    "sankaku": ("https://sankaku.iqdb.org", ImageMatch.SP_SANKAKU),
    "theanimegallery": (
        "https://theanimegallery.iqdb.org",
        ImageMatch.SP_THEANIMEGALLERY,
    ),
    "yandere": ("https://yandere.iqdb.org", ImageMatch.SP_YANDERE),
    "zerochan": ("https://zerochan.iqdb.org", ImageMatch.SP_ZEROCHAN),
}


class ThumbnailRelationship(BaseModel):
    """Thumbnail tag relationship."""

    original = ForeignKeyField(ImageModel, related_name="thumbnails")  # NOQA
    thumbnail = ForeignKeyField(ImageModel)

    @staticmethod
    def get_or_create_from_image(
        image: ImageModel,
        size: Tuple[int, int],
        thumb_folder: Optional[str] = None,
        thumb_path: Optional[str] = None,
        img_path: str = None,
    ) -> Tuple["ThumbnailRelationship", bool]:
        """Get or create from image."""
        thumbnails = [x for x in image.thumbnails if x.thumbnail.width == size[0] and x.thumbnail.height == size[1]]
        if thumbnails:
            assert len(thumbnails) == 1, "There was not one thumbnail for the result"
            return thumbnails[0], False
        if thumb_path is None:
            thumb_path = "{}-{}-{}.jpg".format(image.checksum, size[0], size[1])
            if thumb_folder:
                thumb_path = os.path.join(thumb_folder, thumb_path)
        if not os.path.isfile(thumb_path) or os.path.getsize(thumb_path) == 0:
            im = Image.open(image.path) if img_path is None else Image.open(img_path)
            im.thumbnail(size, Image.ANTIALIAS)
            try:
                im.save(thumb_path, "JPEG")
            except OSError as e:
                valid_err = [
                    "cannot write mode RGBA as JPEG",
                    "cannot write mode P as JPEG",
                    "cannot write mode LA as JPEG",
                ]
                err_str = str(e)
                if err_str in valid_err:
                    #  log.debug('Converting to JPEG for error fix', err=err_str)
                    im = im.convert("RGB")
                    im.save(thumb_path, "JPEG")
                else:
                    raise e
        thumb = ImageModel.get_or_create_from_path(thumb_path)[0]  # type: ImageModel
        return ThumbnailRelationship.get_or_create(original=image, thumbnail=thumb)


def init_db(db_path: Optional[str] = None, version: int = 1) -> None:
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
            ThumbnailRelationship,
        ]
        db.create_tables(model_list)
        version = Program(version=version)
        version.save()
    else:
        logging.debug("db already existed.")


def get_posted_image(
    img_path: str,
    resize: Optional[bool] = False,
    size: Optional[Tuple[int, int]] = None,
    output_thumb_folder: Optional[str] = default_thumb_folder,
    thumb_path: Optional[str] = None,
) -> ImageModel:
    """Get posted image."""
    img = ImageModel.get_or_create_from_path(img_path)[0]  # type: ImageModel
    def_thumb_rel, _ = ThumbnailRelationship.get_or_create_from_image(
        image=img,
        thumb_folder=output_thumb_folder,
        size=DEFAULT_SIZE,
        thumb_path=thumb_path,
        img_path=img_path,
    )
    resized_thumb_rel = None

    if resize and size:
        resized_thumb_rel, _ = ThumbnailRelationship.get_or_create_from_image(
            image=img, thumb_folder=output_thumb_folder, size=size, img_path=img_path
        )
    elif resize:
        # use thumbnail if no size is given
        resized_thumb_rel = def_thumb_rel
    else:
        # no resize, return actual image
        return img

    return resized_thumb_rel.thumbnail if resized_thumb_rel is not None else img


def get_page_result(
    image: str,
    url: str,
    browser: Optional[mechanicalsoup.StatefulBrowser] = None,
    use_requests: Optional[bool] = False,
) -> str:
    """Get iqdb page result.

    Args:
        image: image path to be uploaded.
        url: iqdb url
        browser: browser instance
        use_requests: use requests package instead from browser

    Returns:
        HTML page from the result.
    """
    if use_requests:
        files = {"file": open(image, "rb")}
        resp = requests.post(url, files=files, timeout=10)
        return resp.text
    browser = mechanicalsoup.StatefulBrowser(soup_config={"features": "lxml"})
    browser.raise_on_404 = True
    browser.open(url)
    html_form = browser.select_form("form")
    html_form.input({"file": image})
    browser.submit_selected()
    # if ok, will output: <Response [200]>
    return browser.get_current_page()


def get_tags_from_match_result(
    match_result: Match,
    browser: Optional[mechanicalsoup.StatefulBrowser] = None,
    scraper: Optional[cfscrape.CloudflareScraper] = None,
) -> List[Tag]:
    """Get tags from match result."""
    filtered_hosts = ["anime-pictures.net", "www.theanimegallery.com"]
    res = MatchTagRelationship.select().where(MatchTagRelationship.match == match_result)
    tags = [x.tag for x in res]
    is_url_in_filtered_hosts = urlparse(match_result.link).netloc in filtered_hosts
    if is_url_in_filtered_hosts:
        log.debug("URL in filtered hosts, no tag fetched", url=match_result.link)
    elif not tags:
        try:
            if browser is None:
                browser = mechanicalsoup.StatefulBrowser(soup_config={"features": "lxml"})
                browser.raise_on_404 = True
            browser.open(match_result.link, timeout=10)
            page = browser.get_current_page()
            new_tags = get_tags_from_parser(page, match_result.link, scraper)
            new_tag_models = []
            if new_tags:
                for tag in new_tags:
                    namespace, tag_name = tag
                    tag_model = Tag.get_or_create(name=tag_name, namespace=namespace)[0]  # type: Tag
                    MatchTagRelationship.get_or_create(match=match_result, tag=tag_model)
                    new_tag_models.append(tag_model)
            else:
                log.debug("No tags found.")

            tags.extend(new_tag_models)
        except (
            requests.exceptions.ConnectionError,
            mechanicalsoup.LinkNotFoundError,
        ) as e:
            log.error(str(e), url=match_result.link)
    return tags
