"""parser module."""
import structlog
import bs4


log = structlog.getLogger()

def get_tags(page, url, scraper=None):
    """Get tags by parsing page from the url.

    url is used as hint to choose which parser will be used.
    """
    parser = [
        YandereParser,
        ChanSankakuParser,
        GelbooruParser,
        ZerochanParser,
    ]
    log.debug('url', url=url)
    for item in parser:
        obj = item(url, page, scraper)
        if obj.is_url(url):
            log.debug('match', parser=item)
            result = list(obj.get_tags())
            return result
    log.debug('No parser found', url=url)


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

    def get_tags(self):
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
                if value:
                    value = value + ':'
                text = item.text.strip().split(' ', 1)[1].rsplit(' ', 1)[0]
                yield value + text


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
        """parse page."""
        classname_to_namespace_dict = {
            'tag-type-artist': 'creator',
            'tag-type-character': 'character',
            'tag-type-copyright': 'series',
            'tag-type-meta': 'meta',
            'tag-type-general': ''
        }
        for key, value in classname_to_namespace_dict.items():
            for item in page.select('li.{}'.format(key)):
                if value:
                    value = value + ':'
                yield value + item.text.rsplit('(?)', 1)[0].strip()

    def get_tags(self):
        """Get tags."""
        page = self.page
        url = self.url
        result = list(self.parse_page(page))
        if not result:
            h1_tag_text = page.select_one('h1').text
            if h1_tag_text != '503 Service Temporarily Unavailable':
                log.error('Unexpected H1-tag text', text=h1_tag_text)
            resp = self.scraper.get(url)
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
        page = self.page
        classname_to_namespace_dict = {
            'tag-type-artist': 'creator',
            'tag-type-character': 'character',
            'tag-type-copyright': 'series',
            'tag-type-general': ''
        }
        for key, value in classname_to_namespace_dict.items():
            for item in page.select('li.{}'.format(key)):
                if value:
                    value = value + ':'
                result = value + item.text.rsplit(' ', 1)[0].split(' ', 1)[1].strip()
                yield result


class ZerochanParser(CustomParser):
    """Parser for zerochan."""

    @staticmethod
    def is_url(url):
        """Check url."""
        if 'www.zerochan.net/' in url:
            return True
        return False

    def get_tags(self):
        page = self.page
        tags = page.select('ul#tags li')
        for tag in tags:
            try:
                tag_text, namespace = tag.text.rsplit(' ', 1)
                result = namespace + ':' + tag_text.strip()
                yield result
            except TypeError as e:
                log.error(str(e), tag_text=tag)
                yield ''
