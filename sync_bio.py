#!/usr/bin/env python3
"""
Extract the bio from cv_caltech.tex and inject it into index.html.
The CV is authoritative; the website follows.
"""

import re
import os
import sys

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    cv_path = os.path.join(script_dir, 'cv', 'cv_caltech.tex')
    index_path = os.path.join(script_dir, 'index.html')

    # Extract bio from CV (between \cvsection{Bio} ... \end{indentmore})
    with open(cv_path, 'r', encoding='utf-8') as f:
        cv = f.read()

    m = re.search(r'\\cvsection\{Bio\}.*?\\begin\{indentmore\}\s*\n(.*?)\n\\end\{indentmore\}', cv, re.DOTALL)
    if not m:
        print('ERROR: could not find Bio section in CV')
        sys.exit(1)

    bio_latex = m.group(1).strip()

    # Convert LaTeX to plain text for HTML
    bio = bio_latex
    bio = re.sub(r"\\'\{?([aeiou])\}?", r'&\1acute;', bio)
    bio = re.sub(r'\\"\{?([aeiouAEIOU])\}?', r'&\1uml;', bio)
    bio = bio.replace('\\ae', '&aelig;')
    bio = bio.replace('{', '').replace('}', '')
    bio = bio.replace('\\textbf', '')
    bio = bio.replace('\\textit', '')
    bio = bio.replace('\\emph', '')
    bio = re.sub(r'\\[a-zA-Z]+', '', bio)
    bio = bio.replace('--', '&ndash;')
    bio = re.sub(r'\s+', ' ', bio).strip()
    # Escape the apostrophe for safe HTML
    bio = bio.replace("'", '&#39;')

    # Read index.html and replace bio content
    with open(index_path, 'r', encoding='utf-8') as f:
        html = f.read()

    # Replace content between AUTO BIO markers
    pattern = r'(<!-- BEGIN AUTO BIO -->\n).*?(\n\s*<!-- END AUTO BIO -->)'
    replacement = r'\1        <p>' + bio + r'</p>\2'
    new_html, count = re.subn(pattern, replacement, html, count=1, flags=re.DOTALL)

    if count == 0:
        print('NOTE: no AUTO BIO markers in index.html, skipping bio sync')
        return

    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(new_html)

    print(f'Synced bio to index.html ({len(bio)} chars)')


if __name__ == '__main__':
    main()
