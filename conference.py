from __future__ import print_function

import os
import re
from datetime import datetime
from collections import defaultdict
from six.moves import urllib

from format import Formatter


this_year = datetime.now().year

MONTHS = {
    "NIPS": 12,
    "NeurIPS": 12,
    "ICML": 6,
    "ICLR": 5,
    "CVPR": 6,
    "ICCV": 11,
    "ECCV": 9,
    "ACL": 7,
    "NAACL": 6,
    "EMNLP": 11,
    "KDD": 8,
    "WSDM": 2,
    "ICDM": 11
}


class Conference(Formatter):

    def __init__(self, venue, pattern, key_patterns, cache="cache/"):
        super(Conference, self).__init__()
        self.venue = venue
        self.pattern = pattern
        self.key_patterns = key_patterns
        self.cache = cache

        if not os.path.exists(self.cache):
            os.mkdir(self.cache)
        if isinstance(self.pattern, str):
            self.pattern = re.compile(self.pattern, re.DOTALL)
        for key in self.key_patterns:
            key_pattern = self.key_patterns[key]
            if isinstance(key_pattern, str):
                self.key_patterns[key] = re.compile(key_pattern, re.DOTALL)

    def extract(self, keywords=None, year=None):
        year = year or this_year

        cache_file = os.path.join(self.cache, "%s_%d.html" % (self.venue, year))
        if not os.path.exists(cache_file):
            url = self.get_url(year)
            try:
                urllib.request.urlretrieve(url, cache_file)
            except urllib.error.URLError:
                self.logger.warning("Can't retrieve %s %d" % (self.venue, year))
                return []
            self.logger.info("Retrieved %s %d" % (self.venue, year))
        else:
            self.logger.info("Load cached %s %d" % (self.venue, year))

        with open(cache_file, "rb") as fin:
            page = fin.read()
        page = page.decode("utf-8")

        if isinstance(keywords, str):
            keywords = [keywords]
        if isinstance(keywords, list):
            keywords = re.compile("[> ](?:%s)[ <]" % "|".join(keywords), re.DOTALL | re.IGNORECASE)

        papers = []
        for match in self.pattern.finditer(page):
            paragraph = match.group(0)
            if keywords is not None:
                if not keywords.search(paragraph):
                    continue
            paper = defaultdict(list)
            paper["venue"] = self.venue
            paper["year"] = year
            for key, pattern in self.key_patterns.items():
                for key_match in pattern.finditer(paragraph):
                    paper[key].append(key_match.group(1))
            papers.append(self.format(paper))

        return papers


class NIPS(Conference):

    def __init__(self, **kwargs):
        super(NIPS, self).__init__(
            "NIPS",
            pattern="<li><a href=.*?</a></li>",
            key_patterns={
                "title": '<li><a href="[^"]*">(.*?)</a>',
                "pdf": '<li><a href="([^"]*)">',
                "author": '<a href="[^"]*" class="author">(.*?)</a>'
            },
            **kwargs
        )

    def get_url(self, year):
        url = "https://papers.nips.cc/book/advances-in-neural-information-processing-systems-%d-%d" \
              % (year - 1987, year)
        return url

    def pdf_format(self, pdfs):
        if len(pdfs) > 1:
            self.logger.fatal("Found multiple pdfs")

        pdf = pdfs[0]
        pdf = "https://papers.nips.cc%s.pdf" % pdf
        return pdf


class NeurIPS(Conference):

    def __init__(self, **kwargs):
        super(NeurIPS, self).__init__(
            "NeurIPS",
            pattern="<p><b>.*?</i></p>",
            key_patterns={
                "title": "<p><b>(.*?)</b>",
                "author": "(?:<i>|&middot;)(.*?)\("
            },
            **kwargs
        )

    def get_url(self, year):
        url = "https://nips.cc/Conferences/%d/AcceptedPapersInitial" % year
        return url


class CVPR(Conference):

    def __init__(self, **kwargs):
        super(CVPR, self).__init__(
            "CVPR",
            pattern='<dt class="ptitle">.*?</dd>.*?<dd>.*?</dd>',
            key_patterns={
                "title": '<br><a href="[^"]*">(.*?)</a>',
                "pdf": '\[<a href="([^"]*)">pdf</a>\]',
                "author": '<a href="#" onclick="[^"]*">(.*?)</a>'
            },
            **kwargs
        )

    def get_url(self, year):
        url = "http://openaccess.thecvf.com/CVPR%d.py" % year
        return url

    def pdf_format(self, pdfs):
        if len(pdfs) > 1:
            self.logger.fatal("Found multiple pdfs")

        pdf = pdfs[0]
        pdf = "http://openaccess.thecvf.com/%s" % pdf
        return pdf


class ACL(Conference):

    def __init__(self, **kwargs):
        super(ACL, self).__init__(
            "ACL",
            pattern='<p class="d-sm-flex align-items-stretch">.*?</p>',
            key_patterns={
                "title": '<a class=align-middle href=[^>]*>(.*?)</a>',
                "pdf": '<a class="badge badge-primary align-middle mr-1" href=([^ ]*) data-toggle',
                "author": '<a href=[^>]*>(.*?)</a>'
            },
            **kwargs
        )

    def get_url(self, year):
        url = "https://www.aclweb.org/anthology/volumes/P%d-1/" % (year % 100)
        return url


class ICML(Conference):

    def __init__(self, **kwargs):
        super(ICML, self).__init__(
            "ICML",
            pattern='<div class="maincard narrower Poster".*?</span></a>.*?</div>.*?</div>',
            key_patterns={
                "title": '<div class="maincardBody">(.*?)</div>',
                "pdf": '<a href="([^"]*)" class="btn btn-default btn-xs href_PDF"',
                "author": '(?:<div class="maincardFooter">|&middot;)(.*?)(?:&middot;|<)'
            },
            **kwargs
        )

    def get_url(self, year):
        url = "https://icml.cc/Conferences/%d/Schedule?type=Poster" % year
        return url

    def pdf_format(self, pdfs):
        if len(pdfs) > 1:
            self.logger.fatal("Found multiple pdfs")

        pdf = pdfs[0]
        pos = pdf.rfind("/")
        pdf = pdf[:pos] + pdf[pos: -5] * 2 + ".pdf"
        return pdf


class KDD(Conference):

    def __init__(self, **kwargs):
        super(KDD, self).__init__(
            "KDD",
            pattern='<li class=.*?</li>',
            key_patterns={
                "title": '<a href="[^"]*">(.*?)</a>',
                "author": '(?:Authors:|\);)(.*?)\('
            },
            **kwargs
        )

    def get_url(self, year):
        url = "https://www.kdd.org/kdd%d/accepted-papers" % year
        return url


class ICCV(CVPR):

    def __init__(self, **kwargs):
        super(ICCV, self).__init__(**kwargs)
        self.venue = "ICCV"

    def get_url(self, year):
        url = "http://openaccess.thecvf.com/ICCV%d.py" % year
        return url


class ECCV(CVPR):

    def __init__(self, **kwargs):
        super(ECCV, self).__init__(**kwargs)
        self.venue = "ECCV"

    def get_url(self, year):
        url = "http://openaccess.thecvf.com/ECCV%d.py" % year
        return url


class EMNLP(ACL):

    def __init__(self, **kwargs):
        super(EMNLP, self).__init__(**kwargs)
        self.venue = "EMNLP"

    def get_url(self, year):
        url = "https://www.aclweb.org/anthology/volumes/D%d-1/" % (year % 100)
        return url


class NAACL(ACL):

    def __init__(self, **kwargs):
        super(NAACL, self).__init__(**kwargs)
        self.venue = "NAACL"

    def get_url(self, year):
        url = "https://www.aclweb.org/anthology/volumes/N%d-1/" % (year % 100)
        return url


class ICLR(ICML):

    def __init__(self, **kwargs):
        super(ICLR, self).__init__(**kwargs)
        self.venue = "ICLR"

    def get_url(self, year):
        url = "https://iclr.cc/Conferences/%d/Schedule?type=Poster" % year
        return url


class Conferences(object):

    CONFERENCES = {
        "ML": [NIPS(), NeurIPS(), ICML(), ICLR()],
        "CV": [CVPR(), ICCV(), ECCV()],
        "NLP": [ACL(), EMNLP(), NAACL()],
        "DM": [KDD()]
    }

    def __init__(self, domains="all"):
        self.domains = domains

        if isinstance(self.domains, str):
            if self.domains == "all":
                self.domains = list(self.CONFERENCES.keys())
            else:
                self.domains = [self.domains]
        self.conferences = []
        for domain in self.domains:
            self.conferences += self.CONFERENCES[domain]
        self.conferences.sort(key=lambda c: MONTHS[c.venue])

    def extract(self, keywords=None, start=None, end=None):
        papers = []
        start = start or this_year
        end = end or this_year
        for year in range(start, end+1):
            for conference in self.conferences:
                papers += conference.extract(keywords, year)

        return papers