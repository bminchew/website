#!/usr/bin/env python3
"""
Parse bib files and generate publications.html for GitHub Pages site.

Reads the same bib files used by the CV and produces a formatted HTML
publications page. Entries are filtered to only those cited in cv_caltech.tex
(or cv.tex) and sorted in reverse chronological order.

Usage:
    ./build_pubs.py [--bib-dir ../pubs] [--cv ../cv/cv_caltech.tex]
"""

import re
import os
import sys
import argparse
from collections import OrderedDict

# ============================================================
# BibTeX parser (lightweight, no dependencies)
# ============================================================

def parse_bib(filepath):
    """Parse a .bib file and return a dict of {key: {field: value}}."""
    entries = {}
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Match each @type{key, ... }
    # The closing brace may or may not be on its own line
    pattern = r'@(\w+)\s*\{([^,]+),\s*(.*?)\}\s*(?=@|\Z)'
    for match in re.finditer(pattern, content, re.DOTALL):
        entry_type = match.group(1).lower()
        key = match.group(2).strip()
        body = match.group(3)

        fields = {'_type': entry_type}
        # Parse fields using a manual approach to handle nested braces and
        # quoted values that contain \" (LaTeX accents like \"{o})
        pos = 0
        while pos < len(body):
            # Match field name
            m = re.match(r'\s*(\w+)\s*=\s*', body[pos:])
            if not m:
                pos += 1
                continue
            fname = m.group(1).lower()
            pos += m.end()
            # Parse value: brace-delimited, quote-delimited, or bare number
            if pos < len(body) and body[pos] == '{':
                # Brace-delimited: count braces
                depth = 0
                start = pos
                while pos < len(body):
                    if body[pos] == '{':
                        depth += 1
                    elif body[pos] == '}':
                        depth -= 1
                        if depth == 0:
                            pos += 1
                            break
                    pos += 1
                fval = body[start+1:pos-1]
            elif pos < len(body) and body[pos] == '"':
                # Quote-delimited: find closing " not preceded by \
                pos += 1
                start = pos
                while pos < len(body):
                    if body[pos] == '"' and body[pos-1:pos] != '\\':
                        break
                    # Also skip \" that is a LaTeX accent (e.g., \"{o})
                    if body[pos] == '\\' and pos+1 < len(body) and body[pos+1] == '"':
                        pos += 2
                        continue
                    pos += 1
                fval = body[start:pos]
                pos += 1  # skip closing "
            else:
                # Bare value (number)
                m2 = re.match(r'(\d+)', body[pos:])
                if m2:
                    fval = m2.group(1)
                    pos += m2.end()
                else:
                    pos += 1
                    continue
            fields[fname] = fval.strip()

        entries[key] = fields

    return entries


def get_cited_keys(cv_path):
    """Extract all citation keys from \\nocite{} commands, preserving order."""
    keys = []
    seen = set()
    with open(cv_path, 'r', encoding='utf-8') as f:
        content = f.read()
    for match in re.finditer(r'\\nocite\{([^}]+)\}', content):
        for k in match.group(1).split(','):
            k = k.strip()
            if k and k not in seen:
                keys.append(k)
                seen.add(k)
    return keys


def clean_latex(text):
    """Convert common LaTeX markup to HTML."""
    if not text:
        return ''
    # Process accents BEFORE removing braces (e.g., \"{o} -> &ouml;)
    text = re.sub(r"\\'\{?a\}?", '&aacute;', text)
    text = re.sub(r"\\'\{?e\}?", '&eacute;', text)
    text = re.sub(r"\\'\{?i\}?", '&iacute;', text)
    text = re.sub(r"\\'\{?o\}?", '&oacute;', text)
    text = re.sub(r"\\'\{?u\}?", '&uacute;', text)
    text = re.sub(r'\\"\{?o\}?', '&ouml;', text)
    text = re.sub(r'\\"\{?O\}?', '&Ouml;', text)
    text = re.sub(r'\\"\{?u\}?', '&uuml;', text)
    text = re.sub(r'\\"\{?a\}?', '&auml;', text)
    text = re.sub(r'\\"\{?A\}?', '&Auml;', text)
    text = re.sub(r'\\ae\b', '&aelig;', text)
    text = re.sub(r'\\AE\b', '&AElig;', text)
    # Remove braces used for grouping
    text = text.replace('{', '').replace('}', '')
    # Bold for Minchew
    text = text.replace('\\textbf', '')
    # Math mode markers
    text = re.sub(r'\$[^$]*\$', '', text)
    # Remaining backslash commands
    text = re.sub(r'\\[a-zA-Z]+', '', text)
    # Double dashes to en-dash
    text = text.replace('--', '&ndash;')
    # Clean up extra spaces
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def format_author(author_str):
    """Format author string with student/postdoc decorators."""
    if not author_str:
        return ''
    # Clean LaTeX braces and bold commands
    author_str = author_str.replace('{', '').replace('}', '')
    author_str = author_str.replace('\\textbf', '')

    # Split on ' and '
    authors = re.split(r'\s+and\s+', author_str)
    formatted = []
    for a in authors:
        a = a.strip()
        if not a:
            continue
        # Detect and convert markers before removing them from name
        # $^\star$ = postdoc/research scientist
        if r'$^\star$' in a:
            a = a.replace(r'$^\star$', '')
            marker = '<sup>&star;</sup>'
        # ** = undergrad (check before single *)
        elif '**' in a:
            a = a.replace('**', '')
            marker = '**'
        # * = grad student
        elif '*' in a:
            a = a.replace('*', '')
            marker = '*'
        else:
            marker = ''

        display = a.strip()
        # Remove any remaining LaTeX math
        display = re.sub(r'\$[^$]*\$', '', display)
        display = display.strip()

        # Append marker after the name
        if marker:
            display = display + marker

        formatted.append(display)

    if len(formatted) > 2:
        return ', '.join(formatted[:-1]) + ', and ' + formatted[-1]
    elif len(formatted) == 2:
        return ' and '.join(formatted)
    elif formatted:
        return formatted[0]
    return ''


def sort_key(entry):
    """Sort by year descending, then by key name."""
    try:
        year = int(entry.get('year', '0'))
    except ValueError:
        year = 0
    return (-year, entry.get('_key', ''))


def is_published(entry):
    """Check if an entry is published (not in prep/submitted/revision)."""
    journal = entry.get('journal', '').lower()
    volume = entry.get('volume', '').lower()
    skip_terms = ['in prep', 'submitted', 'in revision']
    for term in skip_terms:
        if term in journal or term in volume:
            return False
    return True


def is_in_review(entry):
    """Check if an entry is in review/submitted."""
    journal = entry.get('journal', '').lower()
    return 'in review' in journal or 'submitted' in journal


def is_in_press(entry):
    """Check if an entry is in press."""
    volume = entry.get('volume', '').lower()
    return 'in press' in volume


def generate_html(entries, title, numbered=True, start_num=None, site_dir='.'):
    """Generate HTML list for a group of entries."""
    if not entries:
        return ''

    html = f'  <div class="pub-group">\n'
    html += f'    <h2 class="pub-group-title">{title}</h2>\n'

    if numbered and start_num is not None:
        html += f'    <ul class="pub-list reverse" style="--pub-start: {start_num};">\n'
    else:
        html += f'    <ul class="pub-list">\n'

    num = start_num if start_num else len(entries)
    for entry in entries:
        authors = format_author(entry.get('author', ''))
        etitle = clean_latex(entry.get('title', ''))
        journal = clean_latex(entry.get('journal', ''))
        year = entry.get('year', '')
        volume = entry.get('volume', '')
        number = entry.get('number', '')
        pages = entry.get('pages', '')
        doi = entry.get('doi', '')

        # Build citation string
        cite = f'{authors}. &ldquo;{etitle}.&rdquo; <em>{journal}</em>'
        if volume and 'in press' not in volume.lower():
            cite += f', {volume}'
            if number:
                cite += f'({number})'
        if pages:
            cite += f', {clean_latex(pages)}'
        cite += f', {year}.'
        note = clean_latex(entry.get('note', ''))
        if note:
            cite += f' <em>{note}.</em>'

        # Links
        links = ''
        bib_key = entry.get('_key', '')
        pdf_path = os.path.join(site_dir, 'pdfs', f'{bib_key}.pdf')
        if os.path.exists(pdf_path):
            links += f'<a href="pdfs/{bib_key}.pdf">[pdf]</a> '
        if doi:
            doi_clean = doi.strip()
            if not doi_clean.startswith('http'):
                doi_url = f'https://doi.org/{doi_clean}'
            else:
                doi_url = doi_clean
            links += f'<a href="{doi_url}">[doi]</a> '
        url = entry.get('url', '').strip()
        if url and not doi:
            if not url.startswith('http'):
                url = 'https://' + url
            links += f'<a href="{url}">[article]</a> '

        html += f'      <li class="pub-item">\n'
        if numbered:
            html += f'        <span class="pub-num">{num}.</span>\n'
            num -= 1
        html += f'        <div>\n'
        html += f'          {cite}\n'
        if links:
            html += f'          <div class="pub-links">{links.strip()}</div>\n'
        html += f'        </div>\n'
        html += f'      </li>\n'

    html += f'    </ul>\n'
    html += f'  </div>\n\n'
    return html


# ============================================================
# HTML template
# ============================================================

HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Publications &mdash; Caltech Glaciology</title>
  <link rel="stylesheet" href="css/style.css">
</head>
<body>
<a href="#main" class="skip-link">Skip to main content</a>

<header class="site-header">
  <div class="header-inner">
    <div>
      <div class="site-title"><a href="index.html"><span class="caltech">Caltech</span> <span class="group-name">Glaciology</span></a></div>
      <div class="site-tagline">Mechanics of glaciers</div>
    </div>
  </div>
</header>

<nav class="site-nav">
  <div class="nav-inner">
    <button class="nav-toggle" aria-label="Menu" onclick="document.querySelector('.nav-links').classList.toggle('open')">&#9776;</button>
    <ul class="nav-links">
      <li><a href="index.html">Home</a></li>
      <li><a href="research.html">Research</a></li>
      <li><a href="people.html">People</a></li>
      <li><a href="publications.html" class="active">Publications</a></li>
      <li><a href="software.html">Software</a></li>
      <li><a href="contact.html">Contact</a></li>
    </ul>
  </div>
</nav>

<main id="main" class="content-wrap">
  <h1 class="page-title">Publications</h1>

  <p class="pub-note">* indicates graduate students, ** undergraduates, and &#9734; postdocs and research scientists.</p>

  <p style="margin-bottom: 2rem;">Also available on <a href="https://scholar.google.com/citations?user=GosoMPIAAAAJ">Google Scholar</a>.</p>

{pub_content}
</main>

<footer class="site-footer">
  <div class="footer-inner">
    <div class="footer-row">
      <span>California Institute of Technology &middot; 1200 E. California Blvd. &middot; Pasadena, CA 91125</span>
      <span><a href="mailto:bminchew@caltech.edu">bminchew@caltech.edu</a></span>
    </div>
    <div class="footer-row">
      <span>&copy; California Institute of Technology</span>
      <div class="footer-links">
        <a href="https://digitalaccessibility.caltech.edu/">Digital Accessibility</a>
        <a href="https://www.caltech.edu/privacy-notice">Privacy Notice</a>
      </div>
    </div>
  </div>
</footer>

</body>
</html>
'''


def main():
    parser = argparse.ArgumentParser(description='Build publications.html from bib files')
    parser.add_argument('--bib-dir', default=None,
                        help='Directory containing .bib files')
    parser.add_argument('--cv', default=None,
                        help='Path to cv .tex file (to filter cited entries)')
    parser.add_argument('--output', default=None,
                        help='Output path for publications.html')
    args = parser.parse_args()

    # Determine paths relative to this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    bib_dir = args.bib_dir or os.path.join(script_dir, 'pubs')
    output = args.output or os.path.join(script_dir, 'publications.html')

    # Find CV file
    cv_path = args.cv
    if not cv_path:
        for candidate in [
            os.path.join(script_dir, 'cv', 'cv_caltech.tex'),
            os.path.join(script_dir, 'cv', 'cv.tex'),
        ]:
            if os.path.exists(candidate):
                cv_path = candidate
                break

    # Parse bib files
    journal_bib = os.path.join(bib_dir, 'minchew_journals.bib')
    general_bib = os.path.join(bib_dir, 'minchew_general.bib')

    all_entries = {}
    for bibfile in [journal_bib, general_bib]:
        if os.path.exists(bibfile):
            all_entries.update(parse_bib(bibfile))
            print(f'Parsed {bibfile}: {len(parse_bib(bibfile))} entries')

    # Filter to cited keys if CV is available, preserving CV order
    if cv_path and os.path.exists(cv_path):
        cited_keys = get_cited_keys(cv_path)
        print(f'Found {len(cited_keys)} cited keys in {cv_path}')
        cited_set = set(cited_keys)
        filtered = {k: v for k, v in all_entries.items() if k in cited_set}
        print(f'Matched {len(filtered)} entries')
    else:
        cited_keys = list(all_entries.keys())
        filtered = all_entries
        print('No CV file found, using all entries')

    # Tag each entry with its key
    for k, v in filtered.items():
        v['_key'] = k

    # Parse general bib keys once
    general_keys = set(parse_bib(general_bib).keys()) if os.path.exists(general_bib) else set()

    # Separate into categories, preserving CV nocite order
    in_review = []
    published = []
    general = []

    for k in cited_keys:
        if k not in filtered:
            continue
        entry = filtered[k]
        if k in general_keys:
            general.append(entry)
        elif is_in_review(entry):
            in_review.append(entry)
        elif is_published(entry) or is_in_press(entry):
            published.append(entry)
        # skip "in prep" entries

    # Generate HTML
    pub_content = ''

    if in_review:
        pub_content += generate_html(in_review, 'Manuscripts in Review', numbered=False, site_dir=script_dir)

    if published:
        pub_content += generate_html(published, 'Published Scholarly Articles',
                                      numbered=True, start_num=len(published), site_dir=script_dir)

    if general:
        pub_content += generate_html(general, 'Other Publications', numbered=False, site_dir=script_dir)

    # Write output
    html = HTML_TEMPLATE.replace('{pub_content}', pub_content)
    with open(output, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f'Wrote {output}')
    print(f'  {len(in_review)} in review, {len(published)} published, {len(general)} other')


if __name__ == '__main__':
    main()
