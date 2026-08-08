# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

Personal academic homepage for Honghao Lyu (吕鸿昊), Assistant Professor at the Institute of Advanced Machines, Zhejiang University. The site is deployed via GitHub Pages on the `blog` branch to the custom domain `fsie-robotics.com`.

- **Main branch for PRs**: `gh-pages`
- **Active branch**: `blog`
- **No build system** — the site is a single static `index.html` file; edits are made directly.

## Site Architecture

The entire website lives in `index.html` (~840 lines). It uses:
- Bulma CSS v0.7.5 (CDN), Bootstrap, Open Sans (Google Fonts)
- Font Awesome 5.9.0 (self-hosted in `font-awesome-5.9.0/`)
- `js/menuspy.js` for sticky sidebar nav highlighting

Layout: sticky left sidebar (avatar, name, title, contact, nav) + right content column with sections: Intro, News, Publication, Robot Systems, Professional Service, More About Me.

**HTML constraints**: `index.html` uses `<p>` tags in some places where only inline content is valid. Do not nest block-level elements (`<div>`, `<ul>`, `<article>`, etc.) inside `<p>` tags.

## Publication Data

The public publication and patent sources live in `data/publications.tex` and
`data/patents.tex`. Run `python scripts/gen_publications.py` from the repository
root after changing either file. The script regenerates the marked publication
and intellectual-property sections in `index.html`.

- Add DOI links in `\href{}{}` format.
- Use "DOI: in press" only for work not yet published online.
- Check IEEE Xplore or conference websites for DOI updates.

## Private CV Boundary

The complete bilingual CV, personal photo, LaTeX templates, and PDF build
workflow are maintained in a separate private repository. Do not add CV source
files or generated CV PDFs to this public repository. The homepage intentionally
offers the full CV by email request instead of a direct download.

When position or affiliation changes, update `index.html` here and update the
English and Chinese CV sections in the private repository separately.

## Current Position (as of 2026-03)

- **Role**: Assistant Professor (ZJU 100 Young Professor / 平台百人计划研究员)
- **Institution**: Institute of Advanced Machines, Zhejiang University (浙江大学 高端装备研究院)
- **Previous**: Postdoctoral Researcher, School of Mechanical Engineering, ZJU (2024.03–2026.02)
