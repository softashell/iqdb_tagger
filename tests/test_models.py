"""test models."""
from PIL import Image

from iqdb_tagger import db_version, models


def get_image(folder, size):
    """Get image."""
    folder = folder.mkdir("tmp")
    img_path = folder.join("test.jpg").strpath
    size = (128, 128)
    im = Image.new("RGB", size)
    pix = im.load()
    for x in range(128):
        for y in range(128):
            pix[x, y] = (255, 0, 0)

    im.save(img_path, "JPEG")
    return img_path


def test_get_or_create_from_path(tmpdir):
    """Test method."""
    size = (128, 128)
    img_path = get_image(folder=tmpdir, size=size)
    models.init_db(tmpdir.mkdir("db").join("iqdb.db").strpath, db_version)
    img, created = models.ImageModel.get_or_create_from_path(img_path)
    assert created
    assert img.width, img.height == size
    assert img.path == img_path
    assert img.checksum == "2a951983fcb673f586c698e4ff8c15d930dcc997f897e42aef77a09099673025"


def test_thumbnail_rel_get_or_create_existing_thumbnail(tmpdir):
    """Test method."""
    img_path = get_image(folder=tmpdir, size=(300, 300))
    models.init_db(tmpdir.mkdir("db").join("iqdb.db").strpath, db_version)
    img, _ = models.ImageModel.get_or_create_from_path(img_path)
    res1 = models.ThumbnailRelationship.get_or_create_from_image(img, size=(150, 150))
    assert res1[1]
    res2 = models.ThumbnailRelationship.get_or_create_from_image(img, size=(150, 150))
    assert not res2[1]


def test_tags_from_img_alt():
    """Test method."""
    m1 = models.Match()
    m1.img_alt = ["Rating: e Score: 5 Tags: " "dungeon_ni_deai_wo_motomeru_no_wa_machigatteiru_darou_ka " "hestia_(dungeon)"]

    exp_result = [
        "Rating: e",
        "Score: 5",
        "dungeon_ni_deai_wo_motomeru_no_wa_machigatteiru_darou_ka",
        "hestia_(dungeon)",
    ]
    assert set(m1.tags_from_img_alt) == set(exp_result)
