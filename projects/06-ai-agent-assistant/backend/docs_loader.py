"""docs/ mein ki har markdown file ko memory mein padhta hai — Project 5
jaisa hi ek chhota helper, yahan reuse kiya gaya hai taaki agent ke
`search_handbook` tool ke paas apna ek private knowledge base ho search
karne ke liye, bina Project 5 ka server chalaye."""

import glob
import os

DOCS_DIR = os.path.join(os.path.dirname(__file__), "docs")


def load_docs() -> list[dict]:
    docs = []
    for path in sorted(glob.glob(os.path.join(DOCS_DIR, "*.md"))):
        with open(path) as f:
            docs.append({"source": os.path.basename(path), "text": f.read()})
    return docs
