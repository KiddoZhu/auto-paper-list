from __future__ import print_function

import logging

class Formatter(object):

    PREPOSITIONS = {"of", "with", "at", "from", "into", "during", "including", "until", "against", "among",
                    "throughout", "despite", "towards", "upon", "concerning", "to", "in", "for", "on", "by",
                    "about", "like", "through", "over", "before", "between", "after", "since", "without",
                    "under", "within", "along", "following", "across", "behind", "beyond", "plus", "except",
                    "but", "up", "out", "around", "down", "off", "above", "near", "via", "a", "an", "the",
                    "and"}

    def __init__(self):
        self.logger = logging.getLogger("%s.%s" % (self.__module__, self.__class__.__name__))

    def format(self, item):
        new_item = {}
        for key in item:
            format_func = getattr(self, key + "_format", self.default_format)
            new_item[key] = format_func(item[key])
        return new_item

    def default_format(self, attributes):
        if isinstance(attributes, list) and len(attributes) == 1:
            return attributes[0]
        return attributes

    def title_format(self, title):
        if isinstance(title, list):
            title = title[0]
        new_tokens = []
        for i, token in enumerate(title.split()):
            if i == 0 or token not in self.PREPOSITIONS:
                token = token.capitalize()
            new_tokens.append(token)
        new_title = " ".join(new_tokens)
        return new_title

    def year_format(self, year):
        if isinstance(year, list):
            year = year[0]
        year = int(year)
        return year

    def author_format(self, authors):
        new_authors = []
        # format the capitalization
        for author in authors:
            last_char = " "
            new_chars = []
            for char in author.strip():
                if last_char == " " or last_char == "-":
                    new_chars.append(char.upper())
                else:
                    new_chars.append(char.lower())
                last_char = char
            new_author = "".join(new_chars)
            new_authors.append(new_author)

        return new_authors