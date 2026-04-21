#!/bin/bash

if [[ ! -d z_logs ]]; then
   mkdir z_logs
fi

pth=/Library/TeX/texbin/
SITE_DIR="$(dirname "$0")/.."

### generate CV mentorship section from group.bib
echo generating mentorship from group.bib
"$SITE_DIR/generate_cv_mentorship.py"

### bold my name for pubs
rm -f ../pubs/noedit_minchew_journals.bib
./bold_bib.py

echo counting pubs
./count_pubs_caltech.py

rm -f cv_caltech.aux cv_caltech.log cv_caltech.out cv_caltech.run.xml cv_caltech.bcf cv_caltech.blg cv_caltech-blx.bib
rm -f cv_caltech*-blx.aux cv_caltech*-blx.bbl cv_caltech*-blx.blg

echo initial xelatex
$pth\xelatex -interaction=nonstopmode cv_caltech.tex > z_logs/cvbuild_caltech1.log
for n in 1 2 3 4; do
   echo building blx $n
   $pth\bibtex cv_caltech$n-blx > z_logs/blxbuild_caltech$n.log
done
echo final xelatex
$pth\xelatex -interaction=nonstopmode cv_caltech.tex > z_logs/cvbuild_caltech2.log
$pth\xelatex -interaction=nonstopmode cv_caltech.tex > z_logs/cvbuild_caltech3.log

cp Minchew_cv.pdf old_Minchew_cv.pdf
cp cv_caltech.pdf Minchew_cv.pdf

### update website
echo copying CV to site root
cp Minchew_cv.pdf "$SITE_DIR/Minchew_cv.pdf"

echo syncing bio
"$SITE_DIR/sync_bio.py"

echo updating publications page
"$SITE_DIR/build_pubs.py"

echo updating people page
"$SITE_DIR/build_people.py"

echo updating alumni publications
"$SITE_DIR/build_people_pubs.py"

echo updating research pages
"$SITE_DIR/build_research.py"
