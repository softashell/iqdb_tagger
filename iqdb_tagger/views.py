"""views module."""
from tempfile import NamedTemporaryFile
from typing import Any
from urllib.parse import urlparse

import requests
from flask import abort, current_app, flash, redirect, request, url_for
from flask_admin import AdminIndexView, BaseView, expose
from flask_paginate import Pagination, get_page_parameter
from flask_restful import Resource

from . import forms, models, parse
from .models import (
    ImageMatch,
    ImageMatchRelationship,
    ImageModel,
    get_page_result,
    get_posted_image,
    get_tags_from_match_result,
    iqdb_url_dict,
)


class HomeView(AdminIndexView):
    """Home view."""

    @expose("/", methods=("GET", "POST"))
    def index(self) -> Any:
        """Get index page."""
        form = forms.ImageUploadForm()
        if form.file.data:
            print("resize:{}".format(form.resize.data))
            with NamedTemporaryFile(delete=False) as temp, NamedTemporaryFile(delete=False) as thumb_temp:
                form.file.data.save(temp.name)
                posted_img = get_posted_image(
                    img_path=temp.name,
                    resize=form.resize.data,
                    thumb_path=thumb_temp.name,
                )
                place = [x[1] for x in form.place.choices if x[0] == int(form.place.data)][0]
                url, im_place = iqdb_url_dict[place]
                query = posted_img.imagematchrelationship_set.select().join(ImageMatch).where(ImageMatch.search_place == im_place)
                if not query.exists():
                    try:
                        posted_img_path = temp.name if not form.resize.data else thumb_temp.name
                        result_page = get_page_result(image=posted_img_path, url=url)
                    except requests.exceptions.ConnectionError as e:
                        current_app.logger.error(str(e))
                        flash("Connection error.")
                        return redirect(request.url)
                    list(parse.get_or_create_image_match_from_page(page=result_page, image=posted_img, place=im_place))
            return redirect(url_for("matchview.match_sha256", checksum=posted_img.checksum))

        page = request.args.get(get_page_parameter(), type=int, default=1)
        item_per_page = 10
        entries = (
            ImageModel.select().distinct().join(ImageMatchRelationship).where(ImageMatchRelationship.image).order_by(ImageModel.id.desc())
        )
        pagination = Pagination(page=page, total=entries.count(), per_page=item_per_page, bs_version=3)
        paginated_entries = entries.paginate(page, item_per_page)
        if not entries.exists() and page != 1:
            abort(404)
        # pagination = Pagination(page, item_per_page, entries.count())
        return self.render(
            "iqdb_tagger/index.html",
            entries=paginated_entries,
            pagination=pagination,
            form=form,
        )


class MatchView(BaseView):
    """Match view."""

    @expose("/")
    def index(self) -> Any:
        """Index page."""
        return self.render("iqdb_tagger/match.html")

    @expose("/sha256-<checksum>")
    def match_sha256(self, checksum: str) -> Any:
        """Get image match the checksum."""
        current_app.logger.debug("match sha256: {}".format(request.url))
        entry = models.ImageModel.get(models.ImageModel.checksum == checksum)
        return self.render("iqdb_tagger/match_checksum.html", entry=entry)

    @expose("/d/<pair_id>")
    def match_detail(self, pair_id: str) -> Any:
        """Show single match pair."""
        nocache = False
        entry = ImageMatchRelationship.get(ImageMatchRelationship.id == pair_id)

        match_result = entry.match_result
        mt_rel = models.MatchTagRelationship.select().where(models.MatchTagRelationship.match == match_result)
        tags = [x.tag.full_name for x in mt_rel]
        filtered_hosts = ["anime-pictures.net", "www.theanimegallery.com"]

        if urlparse(match_result.link).netloc in filtered_hosts:
            current_app.logger.debug("URL in filtered hosts, no tag fetched, url:{}".format(match_result.link))
        elif not tags or nocache:
            try:
                tags = list(get_tags_from_match_result(match_result))
                if not tags:
                    current_app.logger.debug("Tags not founds, id:{}".format(pair_id))
            except requests.exceptions.ConnectionError as e:
                current_app.logger.debug(str(e) + "url:{}".format(match_result.link))
        return self.render("iqdb_tagger/match_single.html", entry=entry)


class MatchViewList(Resource):
    """Resource api for MatchViewList."""

    def post(self) -> Any:  # pylint: disable=R0201
        """Post method for MatchViewList."""
        f = request.files["file"]
        resize = True
        place = "iqdb"
        with NamedTemporaryFile(delete=False) as temp, NamedTemporaryFile(delete=False) as thumb_temp:
            f.save(temp.name)
            posted_img = get_posted_image(img_path=temp.name, resize=resize, thumb_path=thumb_temp.name)
            url, im_place = iqdb_url_dict[place]
            query = posted_img.imagematchrelationship_set.select().join(models.ImageMatch).where(models.ImageMatch.search_place == im_place)
            if not query.exists():
                try:
                    posted_img_path = temp.name if not resize else thumb_temp.name
                    result_page = get_page_result(image=posted_img_path, url=url)
                except requests.exceptions.ConnectionError as e:
                    current_app.logger.error(str(e))
                    abort(400, "Connection error.")
                list(parse.get_or_create_image_match_from_page(page=result_page, image=posted_img, place=im_place))  # NOQA
        raise NotImplementedError
