"""test module."""
import os

from iqdb_tagger.__main__ import (
    get_posted_image,
    init_program,
)
from iqdb_tagger.models import (
    ImageModel,
    ThumbnailRelationship,
)


from PIL import Image


def test_rgba_on_get_posted_image(tmpdir):
    db_path = tmpdir.join('temp_db.db')
    init_program(db_path=db_path.strpath)
    rgba_file = tmpdir.join('file.png')
    thumb_folder = tmpdir.mkdir('thumb')
    im = Image.new('RGBA', (100, 100))
    im.save(rgba_file.strpath)
    get_posted_image(
        rgba_file.strpath, output_thumb_folder=thumb_folder.strpath)


def test_empty_file_when_get_posted_image(
        tmpdir
):
    db_path = tmpdir.join('temp_db.db')
    init_program(db_path=db_path.strpath)
    thumb_folder = tmpdir.mkdir('thumb')
    # creating image
    img_path = tmpdir.join('image.jpg')
    im = Image.new('RGB', (160, 160))
    im.save(img_path.strpath)

    img, _ = ImageModel.get_or_create_from_path(img_path.strpath)
    res, _ = ThumbnailRelationship.get_or_create_from_image(img, (150, 150))

    # remove and create empty file
    thumbnail_path = res.thumbnail.path
    os.remove(thumbnail_path)
    with open(thumbnail_path, 'a'):
        os.utime(thumbnail_path, None)

    get_posted_image(img_path.strpath, output_thumb_folder=thumb_folder)
