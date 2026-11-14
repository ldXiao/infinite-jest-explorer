# Infinite Jest: who's who, and when

An interactive guide to the characters, relationships and Subsidized-Time timeline of
David Foster Wallace's *Infinite Jest*, with search that understands what you mean
("killed himself with a gun", "all affairs by Avril"). Everything runs in the browser;
no server or API.

## Layout

| Path | What it is |
|---|---|
| `site/index.html` | The built page (self-contained apart from the smart-search assets) |
| `site/vocab.txt` | WordPiece vocabulary for the in-browser tokenizer |
| `src/base.html` | The original page: graph, timeline, cast list, character data |
| `src/search.js` | Keyword + synonym search and the in-browser embedding search |
| `src/tags.py` | Fact tags per character and the synonym map |
| `src/facts.py` | Hidden facts per character, each with a regex locating it in the book |
| `data/` | Generated: resolved facts (page + short quote), tags, vectors |
| `tools/` | Build scripts (see below) |

## Running locally

```bash
./scripts/fetch_assets.sh          # ~40 MB: onnxruntime-web + MiniLM model (only needed for Smart search)
cd site && python3 -m http.server 8000
```
Open http://localhost:8000. Keyword search works without the assets.

## Rebuilding

Needs Python with `numpy onnxruntime tokenizers`, and your own copy of the ePub.

```bash
python3 tools/extract.py <unzipped-epub-dir> build/paras.json   # book text, stays local (git-ignored)
python3 tools/resolve.py -v      # locate each fact in src/facts.py -> data/facts_resolved.json
python3 tools/build_data.py      # tags, synonyms, character + fact vectors -> data/
python3 tools/patch.py           # src/base.html + data -> site/index.html
```

To add a fact, append `(character_id, 'fact in your own words', r'regex in the book')`
to `src/facts.py` and rerun the last three steps. `resolve.py -v` prints the matched
context so you can check it.

Page numbers are estimates for the Back Bay paperback, interpolated from known anchors.
The book text itself is not included in this repo.

## Licenses

Smart search uses onnxruntime-web (MIT) and all-MiniLM-L6-v2 (Apache-2.0), fetched at
setup time rather than committed.
