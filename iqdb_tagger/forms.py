from flask_wtf import Form
from wtforms import StringField, BooleanField, SelectField
from flask_wtf.file import FileField, FileAllowed, FileRequired

from . import models


class ImageUploadForm(Form):
    file = FileField('Image', validators=[
        FileRequired(),
        FileAllowed(['jpg', 'png'], 'Images only!')
    ])
    resize = BooleanField()
    place = SelectField('Place', choices=models.ImageMatch.SP_CHOICES)

