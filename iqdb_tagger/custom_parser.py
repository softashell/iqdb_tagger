"""parser module."""
from typing import Optional, List, Union

import bs4
import cfscrape
import structlog

log = structlog.getLogger()


def get_tags(
        page: bs4.BeautifulSoup,
        url: str,
        scraper: Optional[cfscrape.CloudflareScraper] = None
) -> Union[List[str], None]:
    """Get tags by parsing page from the url.

    Args:
        page: page content
        url: page url, used as hint to choose which parser will be used.
        scraper: scraper instance
    """
    parser = [
        ChanSankakuParser,
        DanbooruParser,
        E621Parser,
        Eshuushuu,
        GelbooruParser,
        Konachan,
        YandereParser,
        ZerochanParser,
    ]
    result = []  # type: List[str]
    for item in parser:
        obj = item(url, page, scraper)
        if obj.is_url(url):
            log.debug('match', parser=item)
            result = list(obj.get_tags())
            return result
    log.debug('No parser found', url=url)
    return []


class CustomParser:
    """Base for custom parser."""

    def __init__(self, url, page, scraper=None):
        """Init method."""
        self.url = url
        self.page = page
        self.scraper = scraper

    @staticmethod
    def is_url(url):
        """Check url."""
        raise NotImplementedError

    def get_tags(self) -> List[str]:
        """Get tags."""
        raise NotImplementedError


class YandereParser(CustomParser):
    """Parser for yande.re."""

    @staticmethod
    def is_url(url):
        """Check url."""
        if 'yande.re/post/show/' in url:
            return True
        return False

    def get_tags(self):
        """Get tags."""
        page = self.page
        classname_to_namespace_dict = {
            'tag-type-copyright': 'series',
            'tag-type-character': 'character',
            'tag-type-general': ''
        }
        for key, value in classname_to_namespace_dict.items():
            for item in page.select('li.{}'.format(key)):
                text = item.text.strip().split(' ', 1)[1].rsplit(' ', 1)[0]
                yield (value, text)


class ChanSankakuParser(CustomParser):
    """Parser for chan.sankakucomplex."""

    @staticmethod
    def is_url(url):
        """Check url."""
        if 'chan.sankakucomplex.com/post/show' in url:
            return True
        return False

    @staticmethod
    def parse_page(page):
        """Parse page."""
        classname_to_namespace_dict = {
            'tag-type-artist': 'creator',
            'tag-type-character': 'character',
            'tag-type-copyright': 'series',
            'tag-type-meta': 'meta',
            'tag-type-general': ''
        }
        for key, namespace in classname_to_namespace_dict.items():
            for item in page.select('li.{}'.format(key)):
                name = item.text.rsplit('(?)', 1)[0].strip()
                yield (namespace, name)

    def get_tags(self):
        """Get tags."""
        page = self.page
        url = self.url
        result = list(self.parse_page(page))
        if not result:
            h1_tag_text = page.select_one('h1').text
            if h1_tag_text != '503 Service Temporarily Unavailable':
                log.error('Unexpected H1-tag text', text=h1_tag_text)
            if self.scraper is None:
                self.scraper = cfscrape.CloudflareScraper()
            resp = self.scraper.get(url, timeout=10)
            html_soup = bs4.BeautifulSoup(resp.text, 'lxml')
            return self.parse_page(html_soup)
        return result


class GelbooruParser(CustomParser):
    """Parser for gelbooru.com."""

    @staticmethod
    def is_url(url):
        """Check url."""
        if 'gelbooru.com/index.php?' in url:
            return True
        return False

    def get_tags(self):
        """Get tags."""
        page_title = self.page.select_one('head title').text.strip()
        if page_title == 'Image List  | Gelbooru':
            log.debug('Image list instead of post found.', url=self.url)
            return
        page = self.page
        classname_to_namespace_dict = {
            'tag-type-artist': 'creator',
            'tag-type-character': 'character',
            'tag-type-copyright': 'series',
            'tag-type-general': ''
        }
        for key, value in classname_to_namespace_dict.items():
            for item in page.select('li.{}'.format(key)):
                try:
                    text = item.text.rsplit(' ', 1)[0].split(' ', 1)[1].strip()
                except IndexError:
                    new_item_text = item.text.replace('\n', ' ')
                    new_item_text = new_item_text.rsplit(' ', 1)[0].strip()
                    new_item_text = new_item_text.split('? + - ', 1)[1]
                    text = new_item_text
                yield(value, text)


class ZerochanParser(CustomParser):
    """Parser for zerochan."""

    @staticmethod
    def is_url(url):
        """Check url."""
        if 'www.zerochan.net/' in url:
            return True
        return False

    def get_tags(self):
        """Get tags."""
        page = self.page
        tags = page.select('ul#tags li')
        for tag in tags:
            try:
                tag_text, namespace = tag.text.rsplit(' ', 1)
                yield (namespace, tag_text)
            except TypeError as e:
                log.error(str(e), tag_text=tag)
                yield ('', '')


class DanbooruParser(CustomParser):
    """Parser for danbooru."""

    @staticmethod
    def is_url(url):
        """Check url."""
        if 'danbooru.donmai.us/posts/' in url:

            return True
        return False

    def get_tags(self):
        """Get tags."""
        page = self.page
        classname_to_namespace_dict = {
            'category-0': '',
            'category-1': 'creator',
            'category-2': 'meta',
            'category-3': 'series',
            'category-4': 'character',
            'category-5': 'meta',
            'category-6': 'meta',
            'category-7': 'meta',
        }
        for key, value in classname_to_namespace_dict.items():
            for item in page.select('li.{}'.format(key)):
                text = item.text.rsplit(' ', 1)[0].split(' ', 1)[1].strip()
                yield value, text


class Eshuushuu(CustomParser):
    """Parser for e-shuushuu.net."""

    @staticmethod
    def is_url(url):
        """Check url."""
        if 'e-shuushuu.net/image/' in url:
            return True
        return False

    def get_tags(self):
        """Get tags."""
        page = self.page
        classname_to_namespace_dict = {
            'quicktag1_': '',
            'quicktag2_': 'series',
            'quicktag3_': 'creator',
            'quicktag4_': 'character',
        }
        for classname, namespace in classname_to_namespace_dict.items():
            tags = page.select(
                'div.meta dd[id^={}] span.tag a'.format(classname))
            for tag in tags:
                yield (namespace, tag.text)


class Konachan(CustomParser):
    """Parser for konachan.com."""

    @staticmethod
    def is_url(url):
        """Check url."""
        if 'konachan.com/post/show/' in url:
            return True
        return False

    def get_tags(self):
        """Get tags."""
        page = self.page
        classname_to_namespace_dict = {
            'tag-type-artist': 'creator',
            'tag-type-character': 'character',
            'tag-type-circle': 'character',
            'tag-type-copyright': 'series',
            'tag-type-style': 'style',
            'tag-type-general': ''
        }
        for classname, namespace in classname_to_namespace_dict.items():
            tags = page.select('ul li.{}'.format(classname))
            for tag in tags:
                text = tag.text.split(' ', 1)[1].strip().rsplit(' ', 1)[0]
                yield namespace, text


class E621Parser(CustomParser):
    """Parser for e621."""

    @staticmethod
    def is_url(url):
        """Check url."""
        if 'e621.net/post/show/' in url:
            return True
        return False

    def get_tags(self):
        """Get tags."""
        classname_to_namespace_dict = {
            'tag-type-artist': 'creator',
            'tag-type-character': 'character',
            'tag-type-copyright': 'series',
            'tag-type-species': 'species',
            'tag-type-general': ''
        }
        scraper = cfscrape.CloudflareScraper()
        resp = scraper.get(self.url, timeout=10)
        page = bs4.BeautifulSoup(resp.text, 'lxml')

        for key, namespace in classname_to_namespace_dict.items():
            for item in page.select('li.{}'.format(key)):
                name = \
                    item.text \
                    .rsplit(' ', 1)[0].strip().split('? ', 1)[1].strip()
                yield (namespace, name)
