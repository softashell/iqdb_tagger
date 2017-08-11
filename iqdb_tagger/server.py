#!/usr/bin/env python3
"""server module."""
import os

from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for
)
from werkzeug.utils import secure_filename

from iqdb_tagger.__main__ import (
    DEFAULT_PLACE,
    get_page_result,
    get_posted_image,
    iqdb_url_dict
)
from iqdb_tagger.models import (
    ImageMatch,
    ImageMatchRelationship,
    ImageModel,
    init_db
)
from iqdb_tagger.utils import default_db_path, thumb_folder, user_data_dir

app = Flask(__name__)


@app.route('/thumb/<path:basename>')
def thumb(basename):
    """Get thumbnail."""
    return send_from_directory(thumb_folder, basename)


@app.route('/', methods=['GET', 'POST'])
def index():
    """Get index page."""
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submit a empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file:
            upload_folder = os.path.join(user_data_dir, 'upload')
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)
            filename = os.path.join(
                upload_folder, secure_filename(file.filename))
            file.save(filename)
        else:
            flash('Error uploading file.')
            return redirect(request.url)
        size = None
        if 'resize' in request.args:
            resize = True
            resize_value = request.args.get('resize')
            if resize_value and 'x' in resize_value:
                resize_value_parts = resize_value.split('x')
                size = int(resize_value_parts[0]), (resize_value_parts[1])
        else:
            resize = False
        init_db(default_db_path)
        posted_img = get_posted_image(
            img_path=filename, resize=resize, size=size)
        place = request.args.get('place', DEFAULT_PLACE)
        url, im_place = iqdb_url_dict[place]
        query = posted_img.imagematchrelationship_set \
            .select().join(ImageMatch) \
            .where(ImageMatch.search_place == im_place)
        if not query.exists():
            page = get_page_result(image=posted_img.path, url=url)
            list(ImageMatch.get_or_create_from_page(
                page=page, image=posted_img, place=im_place))
        return redirect(url_for('match_sha256', checksum=posted_img.checksum))
    init_db(default_db_path)
    entries = (
        ImageModel.select()
        .distinct()
        .join(ImageMatchRelationship)
        .where(ImageMatchRelationship.image)
        .order_by(ImageModel.id.desc())
    )
    return render_template('index.html', entries=entries)


@app.route('/match/sha256-<checksum>', methods=['GET', 'POST'])
def match_sha256(checksum):
    """Get image match the checksum."""
    init_db()
    entry = ImageModel.get(ImageModel.checksum == checksum)
    return render_template('match.html', entry=entry)


def main():
    """Run main func."""
    app.run()


if __name__ == '__main__':
    app.run(debug=True)
