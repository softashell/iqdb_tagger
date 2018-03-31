"""test module."""
import logging
import os

import pytest
import vcr
from click.testing import CliRunner
from PIL import Image

from iqdb_tagger.__main__ import get_posted_image, init_program, run
from iqdb_tagger.models import ImageModel, ThumbnailRelationship

logging.basicConfig()
vcr_log = logging.getLogger('vcr')
vcr_log.setLevel(logging.INFO)


@pytest.fixture
def tmp_img(tmpdir):
    """Get temp image fixture used by some test."""
    img_path = tmpdir.join('image.jpg')
    im = Image.new('RGB', (160, 160))
    im.save(img_path.strpath)
    return img_path


def test_rgba_on_get_posted_image(tmpdir):
    """Test method."""
    db_path = tmpdir.join('temp_db.db')
    init_program(db_path=db_path.strpath)
    rgba_file = tmpdir.join('file.png')
    thumb_folder = tmpdir.mkdir('thumb')
    im = Image.new('RGBA', (100, 100))
    im.save(rgba_file.strpath)
    get_posted_image(
        rgba_file.strpath, output_thumb_folder=thumb_folder.strpath)


def test_empty_file_when_get_posted_image(
        tmpdir, tmp_img  # pylint:disable=redefined-outer-name
):
    """Test method."""
    # compatibility
    img_path = tmp_img

    db_path = tmpdir.join('temp_db.db')
    init_program(db_path=db_path.strpath)
    thumb_folder = tmpdir.mkdir('thumb')

    img, _ = ImageModel.get_or_create_from_path(img_path.strpath)
    res, _ = ThumbnailRelationship.get_or_create_from_image(img, (150, 150))

    # remove and create empty file
    thumbnail_path = res.thumbnail.path
    os.remove(thumbnail_path)
    with open(thumbnail_path, 'a'):
        os.utime(thumbnail_path, None)

    get_posted_image(img_path.strpath, output_thumb_folder=thumb_folder)


@pytest.mark.non_travis_test
@vcr.use_cassette('main.yml', record_mode='new_episodes')
def test_main(tmpdir, tmp_img):  # pylint:disable=redefined-outer-name
    """Test func."""
    # compatibility
    img_path = tmp_img

    db_path = tmpdir.join('temp_db.db')

    runner = CliRunner()
    result = runner.invoke(
        run, [
            '--db-path', db_path.strpath, '--resize',
            '--match-filter', 'best-match', img_path.strpath
        ]
    )
    assert result.exit_code == 0
