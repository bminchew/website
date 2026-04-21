# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Academic CV and personal website for Brent Minchew (Professor of Geophysics, Caltech). The CV is built from LaTeX (`cv.tex`) with BibTeX bibliography integration. The website is static HTML.

## Build Commands

### Build the CV (PDF)
```bash
./build_cv.sh
```
This runs the full pipeline:
1. `bold_bib.py` — copies `../pubs/minchew_journals.bib` to `../pubs/noedit_minchew_journals.bib` with "Minchew" bolded
2. `count_pubs.py` — counts publications in `cv.tex` (between `begin pub count`/`end pub count` markers) and writes the total into the line containing `## write number pubs here ##`
3. Multiple rounds of `pdflatex` + `bibtex` (4 bib sections: cv1-blx through cv4-blx)
4. Copies final `cv.pdf` to `Minchew_cv.pdf`

Requires TeX Live installed at `/Library/TeX/texbin/`.

### Upload CV
```bash
./upload_cv_mit.sh
```
Rsyncs `Minchew_cv.pdf` to the MIT Athena web server.

### Upload website
```bash
../upweb.sh
```

## Key Files

- `cv.tex` — main LaTeX source (encoding: `iso-8859-15`, not UTF-8)
- `build_cv.sh` — full build script
- `bold_bib.py` — preprocesses journal bib to bold author name
- `count_pubs.py` — auto-counts publications and injects total into cv.tex
- `../pubs/minchew_journals.bib` — master journal publications bib (do not edit `noedit_minchew_journals.bib` directly; it is generated)
- `../pubs/minchew_invited.bib`, `minchew_conferences.bib` — other bib sources
- `z_logs/` — build log output

## Important Details

- The CV uses `biblatex` with `bibtex` backend and 4 separate `refsection` blocks, each requiring its own bibtex run (cv1-blx through cv4-blx).
- Publication numbering is reversed (descending) via `\mkbibdesc` so the most recent publication has the highest number.
- `cv.tex` uses `iso-8859-15` encoding — preserve this when editing.
- `count_pubs.py` modifies `cv.tex` in place (writes to `.test` then moves back), so it must run before `pdflatex`.
