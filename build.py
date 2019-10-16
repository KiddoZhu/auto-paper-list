from __future__ import print_function

import os
import re
import pause
import datetime
from six.moves import urllib

from format import Formatter
from conference import MONTHS

class Builder(Formatter):

    TIME_INTERVAL = 1
    LEVELS = ["*", "=", "-", "+", "^"]
    INVALID_FILE_NAME = re.compile("[^-a-zA-Z0-9_.() ]+")
    HEADER = \
""".. contents::
    :local:
    :depth: 4

.. sectnum::
    :depth: 4

.. role:: authors(emphasis)

.. role:: venue(strong)

.. role:: keywords(emphasis)
"""

    def __init__(self, title="Paper list", description=""):
        super(Builder, self).__init__()
        self.title = title
        self.description = description
        self.key_pattern = re.compile(":(\w+):`([^`]*?)`")
        self.separator = re.compile("[, ]+")
        self.last_request = datetime.datetime.now()
        self.papers = []

    def load(self, file_name):
        assert os.path.splitext(file_name)[1] == ".rst"

        taxonomy = []

        # hard-coded parser
        with open(file_name, "r") as fin:
            count = 0
            last_line = ""
            paper = {}
            for line in fin:
                line = line.strip()
                if not line:
                    if paper:
                        paper["taxonomy"] = taxonomy
                        self.papers.append(self.format(paper))
                        paper = {}
                        count += 1
                    continue
                if line[0] in self.LEVELS:
                    level = self.LEVELS.index(line[0]) - 1
                    taxonomy = taxonomy[:level] + [last_line]
                elif line[0] == "`":
                    paper["title"] = line[1:]
                elif line[0] == "<":
                    paper["pdf"] = line[1: -3]
                else:
                    match = self.key_pattern.search(line)
                    if match:
                        key = match.group(1)
                        value = match.group(2)
                        value = self.separator.split(value)
                        paper[key] = value

                last_line = line

        self.logger.info("Loaded %d papers from %s" % (count, file_name))

    def format(self, item):
        if "venue" in item:
            item = item.copy()
            if len(item["venue"]) > 2:
                item["workshop"] = True
            item["venue"], item["year"] = item["venue"][:2]
            if item["venue"] == "arXiv":
                item["year"] = "20" + item["year"][:2]
        new_item = super(Builder, self).format(item)

        return new_item

    def taxonomy_format(self, taxonomy):
        return taxonomy

    def add(self, papers):
        self.papers += papers

    def download(self, path="pdf/"):
        count = 0
        if not os.path.exists(path):
            os.mkdir(path)
        for paper in self.papers:
            if "pdf" in paper:
                download_file = self.INVALID_FILE_NAME.sub("", paper["title"] + ".pdf")
                download_file = os.path.join(path, download_file)
                if not os.path.exists(download_file):
                    pause.until(self.last_request + datetime.timedelta(seconds=self.TIME_INTERVAL))
                    try:
                        urllib.request.urlretrieve(paper["pdf"], download_file)
                        count += 1
                    except:
                        self.logger.info("Can't download %s" % paper["pdf"])
                    self.last_request = datetime.datetime.now()
        self.logger.info("Downloaded %d papers" % count)

    def build(self, file_name, index="venue"):
        assert index in ["venue", "topic"]

        with open(file_name, "w") as fout:
            fout.write("%s\n" % self.title)
            fout.write("%s\n" % (self.LEVELS[0] * len(self.title)))
            fout.write("%s\n" % self.description)
            fout.write("%s\n" % self.HEADER)

            hierarchy = self.get_hierarchy(index)
            self.recursive_write(fout, hierarchy)

        self.logger.info("Wrote to %s" % file_name)

    def recursive_write(self, fout, hierarchy, level=1):
        if isinstance(hierarchy, dict):
            keys = list(hierarchy.keys())
            if keys[0] in MONTHS:
                keys.sort(key=lambda k: MONTHS.get(k, 6))
            elif "Others" in keys:
                keys.pop(keys.index("Others"))
                keys.sort()
                keys.append("Others")
            else:
                keys.sort()
            for key in keys:
                fout.write("%s\n" % key)
                fout.write("%s\n" % (self.LEVELS[level] * len(str(key))))
                fout.write("\n")
                self.recursive_write(fout, hierarchy[key], level+1)

        if isinstance(hierarchy, list):
            for paper in hierarchy:
                fout.write("`%s\n" % paper["title"])
                fout.write("<%s>`_\n" % paper["pdf"])
                fout.write("    | :authors:`%s`\n" % ", ".join(paper["authors"]))
                if "venue" in paper:
                    if "workshop" in paper:
                        fout.write("    | :venue:`%s %s Workshop`\n" % (paper["venue"], paper["year"]))
                    else:
                        fout.write("    | :venue:`%s %s`\n" % (paper["venue"], paper["year"]))
                if "keywords" in paper:
                    fout.write("    | :keywords:`%s`\n" % ", ".join(paper["keywords"]))
                fout.write("\n")

    def get_hierarchy(self, index="venue"):
        assert index in ["venue", "topic"]

        results = {}
        if index == "venue":
            for paper in self.papers:
                if "venue" in paper:
                    venue = paper["venue"]
                    year = paper["year"]
                    if year not in results:
                        results[year] = {}
                    if venue not in results[year]:
                        results[year][venue] = []
                    results[year][venue].append(paper)
                else:
                    if "Others" not in results:
                        results["Others"] = []
                    results["Others"].append(paper)
        if index == "topic":
            for paper in self.papers:
                taxonomy = paper["taxonomy"]
                current = results
                for category in taxonomy[:-1]:
                    if category not in current:
                        current[category] = {}
                    current = current[category]
                if taxonomy[-1] not in current:
                    current[taxonomy[-1]] = []
                current[taxonomy[-1]].append(paper)

        return results