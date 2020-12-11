"""test module."""
# pylint:disable=redefined-outer-name
import json
import logging
import os
from pathlib import Path

import pytest
import vcr
from bs4 import BeautifulSoup
from click.testing import CliRunner
from PIL import Image

import iqdb_tagger
from iqdb_tagger import __main__ as main, parse
from iqdb_tagger.__main__ import cli_run, init_program
from iqdb_tagger.models import ImageModel, ThumbnailRelationship, get_posted_image

logging.basicConfig()
vcr_log = logging.getLogger("vcr")
vcr_log.setLevel(logging.INFO)


def get_casette_path(filename):
    """Get cassette path."""
    return str(Path(__file__).parent / "cassette" / "{}.yml".format(filename))


@pytest.fixture
def tmp_img(tmpdir):
    """Get temp image fixture used by some test."""
    img_path = tmpdir.join("image.jpg")
    im = Image.new("RGB", (160, 160))
    im.save(img_path.strpath)
    return img_path


def test_rgba_on_get_posted_image(tmpdir):
    """Test method."""
    db_path = tmpdir.join("temp_db.db")
    init_program(db_path=db_path.strpath)
    rgba_file = tmpdir.join("file.png")
    thumb_folder = tmpdir.mkdir("thumb")
    im = Image.new("RGBA", (100, 100))
    im.save(rgba_file.strpath)
    get_posted_image(rgba_file.strpath, output_thumb_folder=thumb_folder.strpath)


def test_empty_file_when_get_posted_image(
    tmpdir, tmp_img  # pylint:disable=redefined-outer-name
):
    """Test method."""
    # compatibility
    img_path = tmp_img

    db_path = tmpdir.join("temp_db.db")
    init_program(db_path=db_path.strpath)
    thumb_folder = tmpdir.mkdir("thumb")

    img, _ = ImageModel.get_or_create_from_path(img_path.strpath)
    res, _ = ThumbnailRelationship.get_or_create_from_image(img, (150, 150))

    # remove and create empty file
    thumbnail_path = res.thumbnail.path
    os.remove(thumbnail_path)
    with open(thumbnail_path, "a"):
        os.utime(thumbnail_path, None)

    get_posted_image(img_path.strpath, output_thumb_folder=thumb_folder)


@pytest.mark.non_travis_test
@vcr.use_cassette("main.yml", record_mode="new_episodes")
def test_main(tmpdir, tmp_img):  # pylint:disable=redefined-outer-name
    """Test func."""
    # compatibility
    img_path = tmp_img

    db_path = tmpdir.join("temp_db.db")

    runner = CliRunner()
    os.environ["FLASK_APP"] = iqdb_tagger.__main__.__file__
    result = runner.invoke(
        cli_run,
        [
            "--db-path",
            db_path.strpath,
            "--resize",
            "--match-filter",
            "best-match",
            img_path.strpath,
        ],
    )
    assert result.exit_code == 0, \
        '{}: {}'.format(
            type(result.exception.__classs__.__name__), result.exception)


@vcr.use_cassette(get_casette_path("main1"), record_mode="new_episodes")
def test_get_iqdb_result(tmp_img):
    """Test get_iqdb_result."""
    with open(str(Path(__file__).parent / "file" / "main1.json")) as f:
        json_res = json.load(f)
    # fix json list which actually a tuple
    temp_list = []
    for x in json_res:
        x["size"] = tuple(x["size"])
        temp_list.append(x)
    json_res = temp_list
    assert list(main.get_iqdb_result(tmp_img.strpath)) == json_res


def test_parse_iqdb_result_page():
    """test iqdb page parsing result."""
    with open(str(Path(__file__).parent / "file" / "main1.html")) as f:
        soup = BeautifulSoup(f.read(), "lxml")
    with open(str(Path(__file__).parent / "file" / "main1.json")) as f:
        json_res = json.load(f)
    # fix json list which actually a tuple
    temp_list = []
    for x in json_res:
        x["size"] = tuple(x["size"])
        temp_list.append(x)
    json_res = temp_list
    res = list(parse.parse_result(soup))
    assert res == json_res
