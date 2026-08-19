# I-75 Truck & Car

Static marketing site for I-75 Truck & Car LLC — 704 Hall Ave., Dayton, OH 45404.

## Layout

| Path | What it is |
| --- | --- |
| `index.html` | The deployable page. Generated — do not edit by hand. |
| `logo.webp` | Generated from the source PNG. |
| `src/build.py` | Generator. Run it to rebuild both of the above. |
| `src/design-source/` | The original Claude Design export the page was built from. |

## Building

```
pip install Pillow
python3 src/build.py
```

## Why the page is generated

`src/design-source/I-75 Truck and Car.dc.html` is a Claude Design component. It
renders in the browser via `support.js`, which loads React from a CDN and expands
`<sc-for>` / `<sc-if>` / `{{ }}` at runtime. Shipping that as-is means the site is
blank if the CDN is unreachable, and search engines and link previews see an empty
document.

`build.py` evaluates all of that ahead of time and emits plain HTML and CSS, so the
deployed page runs no JavaScript and carries its content in the markup.

The six vehicle cards use a "Photo coming soon" placeholder. The design source has
`<image-slot>` drop targets there, which only accept images inside the Claude Design
editor — on a static host they would render as empty dashed boxes. To publish real
photos, add them to `src/design-source/`, wire them into `INVENTORY` in `build.py`,
and rebuild.

## Deploying

Any static host works; the output is two files at the repo root. Point the host's
output directory at the repo root with no build command, or run `src/build.py` as
the build step.

## Unrelated: `.claude/skills/robin-trades/`

This repo also carries a Claude Code skill that has nothing to do with the site —
operating rules for the Robinhood Agentic Trading MCP connector. It affects no
part of the build and ships nothing to the deployed page. See
`.claude/skills/robin-trades/README.md`.
