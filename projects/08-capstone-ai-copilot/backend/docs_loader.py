"""docs/ ke andar ki har markdown file ko memory mein read karta hai — Project
5 wala hi chhota helper hai, yahan reuse kiya hai taaki agent ke
`search_handbook` tool ke paas apna private knowledge base ho, jise Project
5 ka server chalaye bina bhi search kiya ja sake."""

import glob
import os

DOCS_DIR = os.path.join(os.path.dirname(__file__), "docs")


def load_docs() -> list[dict]:
    docs = []
    for path in sorted(glob.glob(os.path.join(DOCS_DIR, "*.md"))):
        with open(path) as f:
            docs.append({"source": os.path.basename(path), "text": f.read()})
    return docs
