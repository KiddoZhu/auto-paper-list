from __future__ import print_function

import yaml
import logging

import build
import search
import conference

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    source = conference.Conferences()
    engine = search.GoogleScholar()
    papers = []
    # papers += source.extract(["graph convolution", "knowledge graph", "embedding", "reasoning"], 2018)

    # Search missing links in Google Scholar
    for paper in papers:
        if "pdf" not in paper:
            print(paper)
            results = engine.search(paper["title"])
            if results:
                print(results[0])
                paper["pdf"] = results[0]["pdf"]

    builder = build.Builder(
        title="Literature of Deep Learning for Graphs",
        description=
"""
This is a paper list about deep learning for graphs.

.. raw:: html

    <div><a href="README.rst">Sort by topic</a></div>
    <div><a href="BYVENUE.rst">Sort by venue</a></div>
"""
    )

    builder.load("data/BYTOPIC.rst")
    builder.add(papers)
    # builder.build("data/BYTOPIC.rst", index="topic")
    builder.build("data/BYVENUE.rst", index="venue")
    # builder.download()