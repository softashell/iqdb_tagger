#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Module for parser function."""
from difflib import Differ
from typing import Any, Dict, Iterator

import structlog
from bs4 import BeautifulSoup, element

from .models import ImageMatch, Match, ImageMatchRelationship

log = structlog.getLogger()


def parse_result(page: BeautifulSoup) -> Iterator[Any]:
    """Parse iqdb result page."""
    tables = page.select(".pages table")
    for table in tables:
        res = parse_table(table)
        if not res:
            continue
        additional_res = get_additional_result(table, res)
        if additional_res:
            yield additional_res
        yield res


def parse_table(table: element.Tag) -> Dict[str, Any]:
    """Parse table."""
    header_tag = table.select_one("th")
    status: int = ImageMatch.STATUS_OTHER
    if hasattr(header_tag, "text"):
        header_text = header_tag.text
        best_match_text = ("Best match", "Additional match", "Probable match:")
        if header_text in ("Your image", "No relevant matches"):
            status = -1
        elif header_text == "Possible match":
            status = ImageMatch.STATUS_POSSIBLE_MATCH
        elif header_text in best_match_text:
            status = ImageMatch.STATUS_BEST_MATCH
        elif header_text == "Improbable match:":
            status = ImageMatch.STATUS_OTHER
        else:
            log.debug("header text", v=header_text)
    if status == -1:
        return {}
    td_tags = table.select("td")
    assert "% similarity" in td_tags[-1].text, "similarity was not found in " + header_tag.text
    size_and_rating_text = td_tags[-2].text
    rating = Match.RATING_UNKNOWN
    for item in Match.RATING_CHOICES:
        if "[{}]".format(item[1]) in size_and_rating_text:
            rating = item[0]
    size = size_and_rating_text.strip().split(" ", 1)[0].split("×")
    if len(size) == 1 and "×" not in size_and_rating_text:
        size = (None, None)
    else:
        size = (int(size[0]), int(size[1]))
    img_tag = table.select_one("img")
    img_alt = img_tag.attrs.get("alt")
    img_title = img_tag.attrs.get("title")
    if img_alt == "[IMG]" and img_title is None:
        img_alt = None
    if img_alt != img_title:
        d = Differ()
        diff_text = "\n".join(d.compare(img_alt, img_title))
        log.warning("title and alt attribute of img tag is different.\n{}".format(diff_text))
    return {
        # match
        "status": status,
        "similarity": td_tags[-1].text.split("% similarity", 1)[0],
        # match result
        "href": table.select_one("a").attrs.get("href", None),
        "thumb": table.select_one("img").attrs.get("src", None),
        "rating": rating,
        "size": size,
        "img_alt": img_alt,
    }


def get_additional_result(table: element.Tag, last_result: Dict[str, Any]) -> Dict[str, Any]:
    """Get additional result from html table."""
    a_tags = table.select("a")
    assert len(a_tags) < 3, "Unexpected html received at parse_page. Malformed link"
    additional_res = {}  # type: Dict[str, Any]
    if len(a_tags) == 2:
        additional_res = last_result
        additional_res["href"] = a_tags[1].attrs.get("href", None)
    return additional_res


def get_or_create_image_match_from_page(
    page: BeautifulSoup,
    image: Any,
    place: int = ImageMatch.SP_IQDB,
    force_gray: bool = False,
) -> Iterator["ImageMatch"]:
    """Get or create from page result."""
    items = parse_result(page)
    for item in items:
        match_result, _ = Match.get_or_create(
            href=item["href"],
            defaults={
                "thumb": item["thumb"],
                "rating": item["rating"],
                "img_alt": item["img_alt"],
                "width": item["size"][0],
                "height": item["size"][1],
            },
        )
        imr, _ = ImageMatchRelationship.get_or_create(
            image=image,
            match_result=match_result,
        )
        yield ImageMatch.get_or_create(
            match=imr,
            search_place=place,
            force_gray=force_gray,
            defaults={
                "status": item["status"],
                "similarity": item["similarity"],
            },
        )
