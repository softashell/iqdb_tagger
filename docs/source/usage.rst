Usage
=====

Match an image with result page.

.. code:: python

    >>> from iqdb_tagger.models import init_db, ImageModel, ImageMatch
    >>> init_db('test.db')
    >>> img_path = 'test.jpg'
    >>> img, _ = ImageModel.get_or_create_from_path(img_path)
    >>> html_path = 'test.html'
    >>> res = list(
    >>>     ImageMatch.get_or_create_from_page(page=html_path, image=img)
    >>> )
    >>> res
    [(<iqdb_tagger.models.ImageMatch at 0xb357530c>, True),
     # ...
     (<iqdb_tagger.models.ImageMatch at 0xb357aaac>, True)]

Create thumbnail (200x200) from an image.

.. code:: python

    >>> from iqdb_tagger.models import init_db, ImageModel, ImageMatch
    >>> init_db('test.db')
    >>> img_path = 'test.jpg'
    >>> img, _ = ImageModel.get_or_create_from_path(img_path)
    >>> thumb_rel, _ = ThumbnailRelationship.get_or_create_from_image(
    >>>     image=img, size=(200,200)
    >>> )
    >>> thumb_rel
    (<iqdb_tagger.models.ThumbnailRelationship object at 0xb34805ec>, True)
    >>> thumb_rel.original.path
    'test.jpg'
    >>> thumb_rel.thumbnail.path
    '2f1882dfd32c5a3709eaf41052c2a5a0b826c1158066187acd6826b6301c93ab-200-200.jpg'
