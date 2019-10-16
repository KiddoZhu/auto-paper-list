from __future__ import print_function

import re
import pause
import datetime
from collections import defaultdict
from six.moves import urllib

from format import Formatter


class SearchEngine(Formatter):

    TIME_INTERVAL = 1

    def __init__(self, pattern, key_patterns):
        super(SearchEngine, self).__init__()
        self.pattern = pattern
        self.key_patterns = key_patterns
        self.last_request = datetime.datetime.now()

        if isinstance(self.pattern, str):
            self.pattern = re.compile(self.pattern, re.DOTALL)
        for key in self.key_patterns:
            key_pattern = self.key_patterns[key]
            if isinstance(key_pattern, str):
                self.key_patterns[key] = re.compile(key_pattern, re.DOTALL)

    def search(self, query, threshold=0):
        pause.until(self.last_request + datetime.timedelta(seconds=self.TIME_INTERVAL))
        page = self.get_page(query)
        self.last_request = datetime.datetime.now()

        if threshold > 0:
            tokens = "|".join(query.split())
            query = re.compile("(?:(?:%s).*?){%d,}" % (tokens, threshold), re.DOTALL | re.IGNORECASE)
        else:
            query = re.compile(query, re.IGNORECASE)

        items = []
        for match in self.pattern.finditer(page):
            paragraph = match.group(0)
            if not query.search(paragraph):
                continue
            item = defaultdict(list)
            for key, pattern in self.key_patterns.items():
                for key_match in pattern.finditer(paragraph):
                    item[key].append(key_match.group(1))
            items.append(self.format(item))

        return items


class GoogleScholar(SearchEngine):

    HTML_TAG = re.compile("</?[^>]*>")
    BOT_CHECK = re.compile("Please show you&#39;re not a robot")

    def __init__(self):
        super(GoogleScholar, self).__init__(
            pattern='<div class="gs_r gs_or gs_scl".*?</svg></a></div></div></div>',
            key_patterns={
                "title": "<a id=.*?>(.*?)</a>",
                "year": '<div class="gs_a">.*?, (\d{4}).*?</div>',
                "pdf": '<a href="([^"]*)".*?<span class=gs_ctg2>\[PDF\]</span>'
            }
        )
        self.banned = False

    def title_format(self, title):
        if isinstance(title, list):
            title = title[0]
        title = self.HTML_TAG.sub("", title)
        title = super(GoogleScholar, self).title_format(title)
        return title

    def get_page(self, query):
        if self.banned:
            return ""

        query = query.replace(" ", "+")
        url = "https://scholar.google.com/scholar?q=%s" % query
        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36"
                              " (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36"
            }
        )

        try:
            with urllib.request.urlopen(request) as fin:
                page = fin.read()
            page = page.decode("utf-8")
            if self.BOT_CHECK.search(page):
                self.logger.warning("Ooops! Banned by Google Scholar")
                self.banned = True
        except urllib.error.URLError:
            self.logger.warning("Can't access Google Scholar")
            return ""

        return page