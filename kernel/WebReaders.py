import requests
import sys
import logging
from html.parser import HTMLParser
from html.entities import name2codepoint
from re import compile, findall, split, sub, DOTALL, MULTILINE

__author__ = "Manuel Escriche <mev@tid.es>"


def removeHTML(html_text):
    def char_from_entity(match):
        code = name2codepoint.get(match.group(1), 0xFFFD)
        return chr(code)
    text = sub(r'<!--.*?-->', '', html_text, DOTALL)
    text = sub(r'<[Pp][^>]*?>', '\n\n', text)
    text = sub(r'<[^>]*?>', '', text)
    text = sub(r'&#(\d+);', lambda m: chr(int(m.group(1))), text)
    text = sub(r'&([A-Za-z]+);', char_from_entity, text)
    text = sub(r'\n(?:[ \xA0\t]+\n)+', '\n', text)
    return sub(r'\n\n+', '\n', text.strip())


class ItemInfo(dict):
    fields = ('Name', 'Chapter', 'Goal', 'Description', 'Rationale')

    def __init__(self, **kwargs):
        super().__init__()
        for key in kwargs:
            self[key] = kwargs[key]

    def values(self):
        for _id in self.keys():
            yield self[_id]

    def items(self):
        for _id in self.keys():
            yield (_id, self[_id])

    def __iter__(self):
        for _id in sorted(super().keys()):
            yield _id

    keys = __iter__

    def size(self, field):
        return len(findall(r'\b\w+\b', self[field])) if field in self else 0

    @property
    def NSize(self):
        return sum([self.size(field) for field in ItemInfo.fields])


class TextAreaParser(HTMLParser):
    def __init__(self, verbose=False):
        if sys.version_info[:2] == (3, 6):
            super().__init__()
        elif sys.version_info[:2] == (3, 4):
            super().__init__(self)
        else:
            logging.error("Backlog tool requires python3.4 or python3.6")
            exit()

        self._verbose = verbose
        self._flag = False
        self._data = ''

    def handle_starttag(self, tag, attrs):
        if tag != 'textarea':
            return

        self._flag = True

        if self._verbose:
            print(tag)

    def handle_data(self, data):
        if not self._flag:
            return

        self._data = self._data + data

        if self._verbose:
            print(data)

    def handle_endtag(self, tag):
        if tag != 'textarea':
            return

        self._flag = False

        if self._verbose:
            print(tag)

    @property
    def text(self):
        return self._data


class TextAreaExtractor:
    def __init__(self, url_root):
        self._root = url_root[:-1]
        self._pattern = compile(r'\s?(?P<key>\w+)\s?=\s?(?P<value>.*)\s?')
        self._redirect = compile(r'#REDIRECT\s?\[\[(?P<reference>[\w\.\-]+)\]\]')

    def __call__(self, reference):
        _reference = reference.replace('&', '%26')
        newUrl = '{0}?title={1}&action=edit'.format(self._root, _reference)
        source_url = '{0}/{1}'.format(self._root, reference)

        try:
            page = requests.get(newUrl, verify=False)
        except Exception:
            raise

        parser = TextAreaParser(verbose=False)
        parser.feed(page.text)
        text = removeHTML(parser.text)
        chunks = split(r'^\|', text, flags=MULTILINE)

        if len(chunks) == 1:
            for chunk in chunks:
                _chunk = chunk.replace('\n', '')
                m = self._redirect.search(_chunk)
                if m:
                    return self(m.group('reference'))
                else:
                    return ItemInfo(exist=False, reference=reference, source_url=source_url)
        else:
            newItem = ItemInfo(exist=True, reference=reference, source_url=source_url)
            for chunk in chunks:
                _chunk = chunk.replace('\n', '')
                m = self._pattern.search(_chunk)
                if m:
                    key, value = m.group('key').strip(), m.group('value').strip()
                    if key in ('Name', 'Chapter', 'Goal', 'Description', 'Rationale'):
                        newItem[key] = value
            return newItem

if __name__ == "__main__":
    pass
