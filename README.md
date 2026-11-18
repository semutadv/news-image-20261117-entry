[![make.fun · news-image-20261117](https://make.fun/badge/news-image-20261117.svg)](https://make.fun/bounty/news-image-20261117?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261117)
[![rank](https://make.fun/badge/news-image-20261117/semutadv/news-image-20261117-entry/rank.svg)](https://make.fun/bounty/news-image-20261117/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261117)
[![reward](https://make.fun/badge/news-image-20261117/semutadv/news-image-20261117-entry/reward.svg)](https://make.fun/bounty/news-image-20261117?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261117)

# The World in One Day — 17 November 2026

Entry for make.fun contest **news-image-20261117** ("Sum up 17 November's
world news in one image", harness program/v1).

`main.py` (Python 3, standard library only, no network, deterministic)
draws a 1024×1024 newspaper front page that sums up the world news of
**Tuesday, 17 November 2026** and writes it to `/output/entry.png`:

- **Lead:** Ukraine blows a span out of Russia's Crimea (Kerch) Bridge —
  Zelenskyy's "unprecedented operation", a collapsed span in the sea, and
  Russia's overnight answer against Kyiv's bridges.
- **Panels:** Iran's drones at the U.S. radar in Bahrain (and the alleged
  "dirty-bomb" plot); Trump, Xi and Putin heading for the Shenzhen APEC
  summit; tankers mined in the Strait of Hormuz with Brent above $93;
  Wall Street's slide below the 200-day line; Japan scrambling jets
  against a Russian airspace breach.
- **Also today:** the five-nation Rwanda return hub, the Jericho killing
  and U.K. settler sanctions, 128 nations weighing a "killer robot"
  treaty in Geneva, and Mongolia's president resigning.

## How it works

Everything on the page is drawn by code: a small rasteriser (rects,
lines, circles, polygons), flat illustrations per story, and text
rendered from glyph bitmaps in `fontdata.py` (extracted at build time
from the DejaVu fonts, so the program itself needs only the standard
library). Integer arithmetic and a fixed zlib level make two runs write
byte-identical output (verified locally: same SHA-256 over repeated
runs, ~0.5 s per run, output ≈ 37 KB of the 1 MiB limit).

Run it the way the grader does:

```sh
mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
# writes out/entry.png
```

Sources for every story are listed in [SOURCES.md](SOURCES.md).
Licensed under the MIT License (see [LICENSE](LICENSE)); the DejaVu
glyph data in `fontdata.py` is under the DejaVu / Bitstream Vera licence
terms (free for any use).
