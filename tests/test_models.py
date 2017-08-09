"""test models."""
import os

from PIL import Image

from iqdb_tagger import db_version, models


def test_get_or_create_from_path(tmpdir):
    """Test method."""
    folder = tmpdir.mkdir("tmp")
    img_path = folder.join('test.jpg').strpath
    size = (128, 128)
    im = Image.new('RGB', size)
    pix = im.load()
    for x in range(128):
        for y in range(128):
            pix[x, y] = (255, 0, 0)

    im.save(img_path, 'JPEG')
    models.init_db(folder.join('iqdb.db').strpath, db_version)
    img, created = models.ImageModel.get_or_create_from_path(img_path)
    assert created
    assert img.width, img.height == size
    assert img.path == img_path
    assert img.checksum == \
        '2a951983fcb673f586c698e4ff8c15d930dcc997f897e42aef77a09099673025'
