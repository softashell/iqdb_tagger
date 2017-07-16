import os

from peewee import *

from iqdb_tagger.utils import user_data_dir


db_path = os.path.join(user_data_dir, 'iqdb.db')
db = SqliteDatabase(db_path)


class Program(Model):
    version = IntegerField()


class Tag(Model):
    name = CharField()
    namespace = CharField(null=True)

    class Meta:
        database = db


class Match(Model):
    href = CharField()
    thumb = CharField()
    score = IntegerField(null=True)
    rating = CharField(null=True)

    class Meta:
        database = db


class MatchTag(Model):
    match = ForeignKeyField(Match)
    tag = ForeignKeyField(Tag)

    class Meta:
        database = db


class ImageMatch(Model):
    image_checksum = CharField()
    match_result = ForeignKeyField(Match)
    similarity = IntegerField()
    status = CharField(null=True)

    class Meta:
        database = db


def init_db(version):
    """init db."""
    if not os.path.isfile(db_path):
        db.create_tables([Tag, Match, MatchTag, ImageMatch, Program])
        version = models.Program(version=version)
        version.save()
    else:
        logging.debug('db already existed.')


def get_results(image_checksum):
    """get result."""
    pass
