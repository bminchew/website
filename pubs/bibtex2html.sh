#!/bin/bash

if [[ $# -ne 1 ]]; then
   echo -e "\n\nbibtex2html patch\n"
   echo -e "usage:  bibtex2html file.bib \n"
   echo -e "   for additional options, run the binary:\n" 
   echo -e "      /Users/brentminchew/bin/bibtex2html-1.97 [options] file.bib\n"
   echo -e "   after entering the command line argument:  export TMPDIR=.\n\n"
   exit
fi

file=$1
options="-revkeys"
export TMPDIR=.
bibtex2html $options $file 
