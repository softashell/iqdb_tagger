"""model module."""
import logging
import os

from PIL import Image
from peewee import (
    CharField,
    ForeignKeyField,
    IntegerField,
    Model,
    SqliteDatabase
)

from iqdb_tagger.sha256 import sha256_checksum

db = SqliteDatabase(None)


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
    """match model."""

    href = CharField()
    thumb = CharField()
    score = IntegerField(null=True)
    rating = CharField(null=True)


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
            checksum=checksum, width=width, height=height, path=img_path)
        return img, created


class ImageMatch(BaseModel):
    """Image match."""

    image = ForeignKeyField(ImageModel)
    match_result = ForeignKeyField(Match)
    similarity = IntegerField()
    status = CharField(null=True)


class ThumbnailRelationship(BaseModel):
    """Thumbnail tag relationship."""

    original = ForeignKeyField(ImageModel, related_name='thumbnail_relationships')
    thumbnail = ForeignKeyField(ImageModel)

    @staticmethod
    def get_or_create_from_image(image, thumb_folder=None, size=None):
        """Get or create from image."""
        pass


def init_db(db_path, version):
    """Init db."""
    if not os.path.isfile(db_path):
        db.init(db_path)
        model_list = [
            ImageMatch,
            ImageModel,
            Match,
            MatchTagRelationship,
            Program,
            Tag,
            ThumbnailRelationship
        ]
        list(map(lambda m: m.create_table(True), model_list))
        version = Program(version=version)
        version.save()
    else:
        logging.debug('db already existed.')
