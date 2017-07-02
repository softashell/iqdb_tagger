import os

from peewee import *

from iqdb_tagger.utils import user_data_dir


db = SqliteDatabase(os.path.join(user_data_dir, 'iqdb.db'))

class Tag(Model):
    name = CharField()
    namespace = CharField()

    class Meta:
        database = db


class Match(Model):
    href = CharField()
    thumb = CharField()
    score = IntegerField()

    class Meta:
        database = db


class MatchTag(Model):
    match = ForeignKeyField(match)
    tag = ForeignKeyField(match)

    class Meta:
        database = db


class ImageMatch(Model):
    image_checksum = CharField()
    thumb_checksum = CharField()
    match_result = ForeignKeyField(Match)
    similarity = IntegerField()
    status = CharField()

    class Meta:
        database = db
