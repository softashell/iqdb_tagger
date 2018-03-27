from tempfile import NamedTemporaryFile


from flask import request, render_template, redirect, url_for
from flask_admin import AdminIndexView, expose
from flask_paginate import Pagination, get_page_parameter
import requests

from .models import ImageModel, ImageMatchRelationship, ImageMatch
from . import forms
from .__main__ import get_posted_image, iqdb_url_dict, get_page_result



class HomeView(AdminIndexView):

    @expose('/', methods=('GET', 'POST'))
    def index(self):
        """Get index page."""
        page = request.args.get(get_page_parameter(), type=int, default=1)
        form = forms.ImageUploadForm()
        if form.file.data:
            with NamedTemporaryFile() as temp:
                form.file.data.save(temp.name)
                posted_img = get_posted_image(img_path=temp.name, resize=form.resize.data)
                place = [x[1] for x in form.place.choices if x[0] == int(form.place.data)][0]
                url, im_place = iqdb_url_dict[place]
                query = posted_img.imagematchrelationship_set \
                    .select().join(ImageMatch) \
                    .where(ImageMatch.search_place == im_place)
                if not query.exists():
                    try:
                        result_page = get_page_result(image=posted_img.path, url=url)
                    except requests.exceptions.ConnectionError as e:
                        log.error(str(e))
                        flash('Connection error.')
                        return redirect(request.url)
                    list(ImageMatch.get_or_create_from_page(
                        page=result_page, image=posted_img, place=im_place))
            return redirect(url_for('match_sha256', checksum=posted_img.checksum))

        item_per_page = 10
        entries = (
            ImageModel.select()
            .distinct()
            .join(ImageMatchRelationship)
            .where(ImageMatchRelationship.image)
            .order_by(ImageModel.id.desc())
        )
        paginated_entries = entries.paginate(page, item_per_page)
        if not entries.exists() and page != 1:
            abort(404)
        # pagination = Pagination(page, item_per_page, entries.count())
        return self.render(
            'iqdb_tagger/index.html', entries=paginated_entries,
            pagination=None, form=form)
