#! /usr/bin/env python3
# -*- coding: utf-8 -*-
"""main module."""
import logging
import os
import pathlib
import platform
import pprint
import shutil
import traceback
from logging.handlers import TimedRotatingFileHandler
from tempfile import NamedTemporaryFile
from typing import Any, Dict, Iterator, List, Optional, Tuple
from urllib.parse import urlparse

import cfscrape
import click
import mechanicalsoup
import requests
import structlog
import werkzeug
from bs4 import BeautifulSoup
from flask import Flask
from flask import __version__ as flask_version  # type: ignore
from flask import cli as flask_cli
from flask import send_from_directory
from flask_admin import Admin
from flask_restful import Api
from hydrus import Client
from hydrus.utils import yield_chunks

from . import models, parse, views
from .__init__ import __version__, db_version
from .models import iqdb_url_dict
from .utils import default_db_path, thumb_folder, user_data_dir

db = "~/images/! tagged"
DEFAULT_PLACE = "iqdb"
minsim = 75
services = ["1", "2", "3", "4", "5", "6", "10", "11"]
forcegray = False
log = structlog.getLogger()


def get_iqdb_result(image: str, iqdb_url: str = "http://iqdb.org/") -> Any:
    """Get iqdb result."""
    files = {"file": open(image, "rb")}
    resp = requests.post(iqdb_url, files=files, timeout=10)
    html_text = BeautifulSoup(resp.text, "lxml")
    return parse.parse_result(html_text)


def init_program(db_path: str = default_db_path) -> None:
    """Init program."""
    # create user data dir
    pathlib.Path(user_data_dir).mkdir(parents=True, exist_ok=True)
    pathlib.Path(thumb_folder).mkdir(parents=True, exist_ok=True)
    models.init_db(db_path, db_version)


def write_url_from_match_result(match_result: models.ImageMatch, folder: str = None) -> None:
    """Write url from match result."""
    netloc = urlparse(match_result.link).netloc
    sanitized_netloc = netloc.replace(".", "_")
    text_file_basename = sanitized_netloc + ".txt"
    text_file = os.path.join(folder, text_file_basename) if folder is not None else text_file_basename
    with open(text_file, "a") as f:
        f.write(match_result.link)
        f.write("\n")


def get_result_on_windows(
    image: str,
    place: str,
    resize: Optional[bool] = False,
    size: Optional[Tuple[int, int]] = None,
    browser: Optional[mechanicalsoup.StatefulBrowser] = None,
) -> List[models.ImageMatch]:
    """Get result on Windows.

    Args:
        image: image path
        place: iqdb place code
        resize: resize the image
        size: resized image size
        browser: browser instance

    Returns:
        matching items
    """
    result = []
    # temp_f

    with NamedTemporaryFile(mode="w+t", delete=False) as temp_f, NamedTemporaryFile(mode="w+t", delete=False) as thumb_temp_f:
        temp_file_name = temp_f.name
        thumb_temp_file_name = thumb_temp_f.name
        # copy to temp file
        shutil.copyfile(image, temp_f.name)
        # get image to be posted based on user input
        try:
            post_img = models.get_posted_image(img_path=temp_f.name, resize=resize, size=size, thumb_path=thumb_temp_f.name)
        except OSError as e:
            raise OSError(str(e) + " when processing {}".format(image)) from e
        # append data to result
        for img_m_rel_set in post_img.imagematchrelationship_set:
            for item_set in img_m_rel_set.imagematch_set:
                if item_set.search_place_verbose == place:
                    result.append(item_set)

        if not result:
            url, im_place = iqdb_url_dict[place]
            use_requests = place != "e621"
            post_img_path = temp_f.name if not resize else thumb_temp_f.name
            page = models.get_page_result(image=post_img_path, url=url, browser=browser, use_requests=use_requests)
            # if ok, will output: <Response [200]>
            page_soup = BeautifulSoup(page, "lxml")
            result = list(parse.get_or_create_image_match_from_page(page=page_soup, image=post_img, place=im_place))
            result = [x[0] for x in result]
    for item in [temp_file_name, thumb_temp_file_name]:
        try:
            os.remove(item)
        except Exception:  # pylint: disable=broad-except
            log.exception("error removing {}".format(item))
    return result


def run_program_for_single_img(  # pylint: disable=too-many-branches, too-many-statements
    image: str,
    resize: bool = False,
    size: Optional[Tuple[int, int]] = None,
    place: str = DEFAULT_PLACE,
    match_filter: Optional[str] = None,
    browser: Optional[mechanicalsoup.StatefulBrowser] = None,
    scraper: Optional[cfscrape.CloudflareScraper] = None,
    disable_tag_print: Optional[bool] = False,
    write_tags: Optional[bool] = False,
    write_url: Optional[bool] = False,
    minimum_similarity: Optional[int] = None,
) -> Dict[str, Any]:
    """Run program for single image.

    Args:
        image: image path
        resize: resize the image
        size: resized image size
        place: iqdb place, see `iqdb_url_dict`
        match_filter: whitelist matched items
        browser: mechanicalsoup browser instance
        scraper: cfscrape instance
        disable_tag_print: don't print the tag
        write_tags: write tags as hydrus tag file
        write_url: write matching items' url to file
        minimum_similarity: filter result items with minimum similarity

    Returns:
        iqdb result and collected errors
    """
    # compatibility
    br = browser  # type: ignore

    error_set = []  # List[Exception]
    tag_textfile = image + ".txt"
    folder = os.path.dirname(image)
    result = []  # type: List[models.ImageMatch]

    if platform.system() == "Windows":
        result = get_result_on_windows(image, place, resize=resize, size=size, browser=br)
    else:
        with NamedTemporaryFile(delete=False) as temp, NamedTemporaryFile(delete=False) as thumb_temp:
            shutil.copyfile(image, temp.name)
            try:
                post_img = models.get_posted_image(
                    img_path=temp.name,
                    resize=resize,
                    size=size,
                    thumb_path=thumb_temp.name,
                )
            except OSError as e:
                raise OSError(str(e) + " when processing {}".format(image)) from e

            for img_m_rel_set in post_img.imagematchrelationship_set:
                for item_set in img_m_rel_set.imagematch_set:
                    if item_set.search_place_verbose == place:
                        result.append(item_set)

            if not result:
                url, im_place = iqdb_url_dict[place]
                use_requests = place != "e621"
                post_img_path = temp.name if not resize else thumb_temp.name
                page = models.get_page_result(image=post_img_path, url=url, browser=br, use_requests=use_requests)
                # if ok, will output: <Response [200]>
                page_soup = BeautifulSoup(page, "lxml")
                result = list(parse.get_or_create_image_match_from_page(page=page_soup, image=post_img, place=im_place))
                result = [x[0] for x in result]

    if match_filter == "best-match":
        result = [x for x in result if x.status == x.STATUS_BEST_MATCH]
    if minimum_similarity:
        result = [x for x in result if float(x.similarity) >= minimum_similarity]

    log.debug("Number of valid result", n=len(result))
    match_result_tag_pairs = []  # type: List[Tuple[models.Match, List[models.Tag]]]
    for item in result:
        match_result = item.match.match_result  # type: models.Match
        url = match_result.link
        log.debug("match status", similarity=item.similarity, status=item.status_verbose)
        log.debug("url", v=url)

        try:
            tags = models.get_tags_from_match_result(match_result, browser, scraper)
            tags_verbose = [x.full_name for x in tags]
            match_result_tag_pairs.append((match_result, tags))
            log.debug("{} tag(s) founds".format(len(tags_verbose)))
            if tags and not disable_tag_print:
                print("\n".join(tags_verbose))

            if tags and write_tags:
                with open(tag_textfile, "a") as f:
                    f.write("\n".join(tags_verbose))
                    f.write("\n")
                log.debug("tags written")
            if write_url:
                write_url_from_match_result(match_result, folder)
        except Exception as e:  # pylint:disable=broad-except
            log.error("Error", e=str(e))
            error_set.append(e)

    return {"error": error_set, "match result tag pairs": match_result_tag_pairs}


def thumb(basename: str) -> Any:
    """Get thumbnail."""
    return send_from_directory(thumb_folder, basename)


def create_app(script_info: Optional[Any] = None) -> Any:
    """Create app."""
    app = Flask(__name__)
    # logging
    if not os.path.exists(user_data_dir):
        os.makedirs(user_data_dir)
    log_dir = os.path.join(user_data_dir, "log")
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    peewee_logger = logging.getLogger("peewee")
    peewee_logger.setLevel(logging.INFO)
    chardet_logger = logging.getLogger("chardet")
    chardet_logger.setLevel(logging.INFO)
    default_log_file = os.path.join(log_dir, "iqdb_tagger_server.log")
    file_handler = TimedRotatingFileHandler(default_log_file, "midnight")
    file_handler.setLevel(logging.WARNING)
    file_handler.setFormatter(logging.Formatter("<%(asctime)s> <%(levelname)s> %(message)s"))
    app.logger.addHandler(file_handler)
    app.logger.addHandler(peewee_logger)
    app.logger.addHandler(chardet_logger)
    # reloader
    reloader = app.config["TEMPLATES_AUTO_RELOAD"] = bool(os.getenv("IQDB_TAGGER_RELOADER")) or app.config["TEMPLATES_AUTO_RELOAD"]  # NOQA
    if reloader:
        app.jinja_env.auto_reload = True
    app.config["SECRET_KEY"] = os.getenv("IQDB_TAGGER_SECRET_KEY") or os.urandom(24)
    app.config["WTF_CSRF_ENABLED"] = False
    # debug
    debug = app.config["DEBUG"] = bool(os.getenv("IQDB_TAGGER_DEBUG")) or app.config["DEBUG"]
    if debug:
        app.config["DEBUG"] = True
        app.config["LOGGER_HANDLER_POLICY"] = "debug"
        logging.basicConfig(level=logging.DEBUG)
        pprint.pprint(app.config)
        print("Log file: {}".format(default_log_file))
        print("script info:{}".format(script_info))
    db_path = os.getenv("IQDB_TAGGER_DB_PATH") or default_db_path
    init_program()
    models.init_db(db_path)
    # app and db
    app.app_context().push()

    @app.shell_context_processor
    def shell_context() -> Dict["str", Any]:  # pylint: disable=unused-variable
        return {"app": app}

    # api
    api = Api(app)
    api.add_resource(views.MatchViewList, "/api/matchview")
    # flask-admin
    app_admin = Admin(
        app,
        name="IQDB Tagger",
        template_mode="bootstrap3",
        index_view=views.HomeView(name="Home", template="iqdb_tagger/index.html", url="/"),
    )
    app_admin.add_view(views.MatchView())
    # app_admin.add_view(ModelView(ImageMatch, category='DB'))
    # app_admin.add_view(ModelView(ImageMatchRelationship, category='DB'))
    # app_admin.add_view(ModelView(ImageModel, category='DB'))
    # app_admin.add_view(ModelView(MatchTagRelationship, category='DB'))
    # routing
    app.add_url_rule("/thumb/<path:basename>", view_func=thumb)
    return app


class FlaskGroup(flask_cli.FlaskGroup):
    """Custom Flask Group."""

    def __init__(self, **kwargs: Any) -> None:
        """Class init."""
        super().__init__(**kwargs)
        if hasattr(self.params[0], "help"):
            self.params[0].help = "Show the program version"  # type: ignore
        self.params[0].callback = get_version


def get_version(ctx: Any, _: Any, value: Any):
    """Get version."""
    if not value or ctx.resilient_parsing:
        return
    message = "%(app_name)s %(app_version)s\nPython %(python)s\nFlask %(flask)s\nWerkzeug %(werkzeug)s"
    click.echo(
        message
        % {
            "app_name": "Iqdb-Tagger",
            "app_version": __version__,
            "python": platform.python_version(),
            "flask": flask_version,
            "werkzeug": werkzeug.__version__,
        },
        color=ctx.color,
    )
    ctx.exit()


@click.group(cls=FlaskGroup, create_app=create_app)
def cli() -> None:
    """Run cli. This is a management script for application."""


@cli.command()
@click.version_option()
@click.option(
    "--place",
    type=click.Choice(iqdb_url_dict.keys()),
    default=DEFAULT_PLACE,
    help="Specify iqdb place, default:{}".format(DEFAULT_PLACE),
)
@click.option("--minimum-similarity", type=float, help="Minimum similarity.")
@click.option("--resize", is_flag=True, help="Use resized image.")
@click.option("--size", help="Specify resized image, format: 'w,h'.")
@click.option("--db-path", help="Specify Database path.")
@click.option(
    "--match-filter",
    type=click.Choice(["default", "best-match"]),
    default="default",
    help="Filter the result.",
)
@click.option("--write-tags", is_flag=True, help="Write best match's tags to text.")
@click.option("--write-url", is_flag=True, help="Write match url to text.")
@click.option(
    "--input-mode",
    type=click.Choice(["default", "folder"]),
    default="default",
    help="Set input mode.",
)
@click.option("--verbose", "-v", is_flag=True, help="Verbose output.")
@click.option("--debug", "-d", is_flag=True, help="Print debug output.")
@click.option("--abort-on-error", is_flag=True, help="Stop program when error occured")  # pylint: disable=too-many-branches
@click.argument("prog-input")
def cli_run(
    prog_input: str = None,
    resize: bool = False,
    size: Optional[str] = None,
    db_path: str = default_db_path,
    place: str = DEFAULT_PLACE,
    match_filter: str = "default",
    input_mode: str = "default",
    verbose: bool = False,
    debug: bool = False,
    abort_on_error: bool = False,
    write_tags: bool = False,
    write_url: bool = False,
    minimum_similarity: bool = None,
) -> None:
    """Get similar image from iqdb."""
    assert prog_input is not None, "Input is not a valid path"

    # logging
    log_level = None
    if verbose:
        log_level = logging.INFO
    if debug:
        log_level = logging.DEBUG
    if log_level:

        logging.basicConfig(
            handlers=[logging.FileHandler(os.path.join(user_data_dir, "output.log"), "w", "utf-8")],
            level=log_level,
        )

    init_program(db_path)
    br = mechanicalsoup.StatefulBrowser(soup_config={"features": "lxml"})
    br.raise_on_404 = True
    scraper = cfscrape.CloudflareScraper()

    # variable used in both input mode
    error_set = []
    size_tuple: Optional[Tuple[int, int]] = None
    if size is not None:
        size_tuple = tuple(map(int, size.split(",", 1)))  # type: ignore
    if input_mode == "folder":
        assert os.path.isdir(prog_input), "Input is not valid folder"
        files = [os.path.join(prog_input, x) for x in os.listdir(prog_input)]
        if not files:
            print("No files found.")
            return
        sorted_files = sorted(files, key=lambda x: os.path.splitext(x)[1])
        for idx, ff in enumerate(sorted_files):
            log.debug("file", f=os.path.basename(ff), idx=idx, total=len(files))
            result = {}
            try:
                result = run_program_for_single_img(
                    ff,
                    resize,
                    size_tuple,
                    place,
                    match_filter,
                    browser=br,
                    scraper=scraper,
                    disable_tag_print=True,
                    write_tags=write_tags,
                    write_url=write_url,
                    minimum_similarity=minimum_similarity,
                )
            except Exception as e:  # pylint:disable=broad-except
                if abort_on_error:
                    raise e
                error_set.append((ff, e))
            if result is not None and result.get("error"):
                error_set.extend([(ff, x) for x in result["error"]])
    else:
        image = prog_input
        result = run_program_for_single_img(
            image,
            resize,
            size_tuple,
            place,
            match_filter,
            browser=br,
            scraper=scraper,
            write_tags=write_tags,
            write_url=write_url,
            minimum_similarity=minimum_similarity,
        )
        if result is not None and result.get("error"):
            error_set.extend([(image, x) for x in result["error"]])

    if error_set:
        log.error("Found error(s)")
        for x in error_set:
            log.error("path: " + x[0] + "\nerror: " + str(x[1]))


def get_hydrus_set(search_tags: List[str], client: Client, resize: bool = True) -> Iterator[Dict[str, Any]]:
    """Get hydrus result.

    Args:
        search_tags: tags used to search hydrus
        client: client instance

    Returns:
        hydrus metadata and iqdb results
    """
    # compatibility
    cl = client

    file_ids = cl.search_files(search_tags)
    if not file_ids:
        print("No File id found.")
        return
    file_ids_chunks = yield_chunks(file_ids, 100)
    metadata_sets = []  # type: List[Dict[str, Any]]
    for file_ids in file_ids_chunks:
        metadata_sets.extend(cl.file_metadata(file_ids=file_ids, only_identifiers=True))
    for idx, metadata in enumerate(metadata_sets):
        f_id, f_hash = metadata["file_id"], metadata["hash"]
        log.info("Metadata", idx=idx, total=len(metadata_sets), id=f_id, hash=f_hash)
        f_content = cl.get_file(file_id=f_id).content
        init_program()
        with NamedTemporaryFile(delete=False) as f:
            try:
                f.write(f_content)
            except TypeError:
                f.write(f_content.content)
            try:
                res_set = run_program_for_single_img(
                    f.name,
                    resize=resize,
                    place="iqdb",
                    match_filter="best-match",
                    disable_tag_print=True,
                )
            except OSError as err:
                if "can't identify image file" in str(err):
                    log.error("File is not identified as an image")
                else:
                    log.error(str(err))
                continue
            yield {"metadata": metadata, "iqdb_result": res_set}


@cli.command()
@click.argument("tag", nargs=-1)
@click.option("--access_key", help="Hydrus access key")
@click.option("--hydrus_url", help="URL for hydrus client e.g. http://127.0.0.1:45869/")
@click.option("--no-resize", help="Don't resize image when upload", is_flag=True)
def search_hydrus_and_send_url(
    tag: List[str],
    access_key: Optional[str] = None,
    hydrus_url: Optional[str] = "http://127.0.0.1:45869/",
    no_resize: bool = False,
) -> None:
    """Search hydrus and send url."""
    # compatibility
    search_tags = tag
    if Client is None:
        print("Hydrus package is required")
        return

    args = [access_key]
    if hydrus_url:
        args.append(hydrus_url)
    cl = Client(*args)
    for res_dict in get_hydrus_set(search_tags, cl, resize=not no_resize):
        match_results = [x[0] for x in res_dict["iqdb_result"]["match result tag pairs"]]
        if match_results:
            for item in match_results:
                cl.add_url(item.link)


@cli.command()
@click.argument("tag", nargs=-1)
@click.option("--access_key", help="Hydrus access key")
@click.option("--hydrus_url", help="URL for hydrus client e.g. http://127.0.0.1:45869/")
@click.option("--tag_repo", help="tag repo name e.g. local tags", default="local tags")
@click.option("--no-resize", help="Don't resize image when upload", is_flag=True)
def search_hydrus_and_send_tag(
    tag: List[str],
    access_key: Optional[str] = None,
    hydrus_url: Optional[str] = "http://127.0.0.1:45869/",
    tag_repo: Optional[str] = "local tags",
    no_resize: bool = False,
) -> None:
    """Search hydrus and send tag."""
    # compatibility
    search_tags = tag
    if Client is None:
        print("Hydrus package is required")
        return

    args = [access_key]
    if hydrus_url:
        args.append(hydrus_url)
    cl = Client(*args)
    for res_dict in get_hydrus_set(search_tags, cl, resize=not no_resize):
        f_hash = res_dict["metadata"]["hash"]
        tag_sets = [x[1] for x in res_dict["iqdb_result"]["match result tag pairs"]]
        tags = list(set(sum(tag_sets, [])))
        full_name_tags = [x.full_name for x in tags]
        if full_name_tags:
            try:
                cl.add_tags([f_hash], service_to_tags={tag_repo: full_name_tags})
            except Exception:  # pylint: disable=broad-except
                traceback.print_exc()


if __name__ == "__main__":
    cli()
