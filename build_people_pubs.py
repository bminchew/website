#!/usr/bin/env python3
"""
Add recent publications beside each alumni's entry on people.html.

Uses group.bib for name/end-year mapping (no more hardcoded overrides).
For each alumni, finds papers where they are a co-author published
within 3 years of their end date.
"""

import os
import re
import sys
import datetime

script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)
from build_pubs import parse_bib, clean_latex
from group_parser import parse_group_bib, clean_latex_for_html

YEARS_WINDOW = 3
CURRENT_YEAR = datetime.datetime.now().year
SKIP_NAMES = {'Brent Minchew'}


def get_bib_lastname(name):
    """Get the last name to search for in bib author fields."""
    # Handle display names like "Lizz Ultee"
    parts = name.split()
    return parts[-1]


def build_member_lookup(members):
    """Build a lookup from display name to end year and bib last name."""
    lookup = {}
    for m in members:
        display = m.get('display_name', m['name'])
        end = m.get('end', '')
        if end:
            end_year = int(end)
        elif m['is_current']:
            end_year = CURRENT_YEAR
        else:
            end_year = None

        # Bib last name for matching
        lastname = get_bib_lastname(m['name'])

        lookup[display] = {
            'end_year': end_year,
            'lastname': lastname,
        }
    return lookup


def find_papers(lastname, entries, end_year, window=YEARS_WINDOW):
    """Find papers where lastname appears as author, within window of end_year."""
    results = []
    for key, entry in entries.items():
        author = entry.get('author', '')
        if not re.search(re.escape(lastname), author, re.IGNORECASE):
            continue
        journal = entry.get('journal', '').lower()
        if 'in prep' in journal or 'submitted' in journal or 'in revision' in journal:
            continue
        try:
            pub_year = int(entry.get('year', '0'))
        except ValueError:
            continue
        if end_year and abs(pub_year - end_year) <= window:
            results.append((key, entry, pub_year))
    results.sort(key=lambda x: -x[2])
    return results


def format_compact_pub(key, entry):
    """Format a publication as a compact one-line HTML string."""
    title = clean_latex(entry.get('title', ''))
    journal = clean_latex(entry.get('journal', ''))
    year = entry.get('year', '')
    doi = entry.get('doi', '')

    html = f'<span class="alumni-pub">'
    html += f'&ldquo;{title},&rdquo; <em>{journal}</em>, {year}.'
    if doi:
        doi_clean = doi.strip()
        if not doi_clean.startswith('http'):
            doi_url = f'https://doi.org/{doi_clean}'
        else:
            doi_url = doi_clean
        html += f' <a href="{doi_url}">[doi]</a>'
    pdf_path = os.path.join(script_dir, 'pdfs', f'{key}.pdf')
    if os.path.exists(pdf_path):
        html += f' <a href="pdfs/{key}.pdf">[pdf]</a>'
    html += '</span>'
    return html


def main():
    # Parse group.bib for member info
    bib_path = os.path.join(script_dir, 'group.bib')
    members = parse_group_bib(bib_path)
    member_lookup = build_member_lookup(members)

    # Parse publication bib files
    pub_dir = os.path.join(script_dir, 'pubs')
    all_entries = {}
    for bibfile in ['minchew_journals.bib', 'minchew_general.bib']:
        path = os.path.join(pub_dir, bibfile)
        if os.path.exists(path):
            all_entries.update(parse_bib(path))
    for k, v in all_entries.items():
        v['_key'] = k

    # Read people.html
    people_path = os.path.join(script_dir, 'people.html')
    with open(people_path, 'r', encoding='utf-8') as f:
        html = f.read()

    # Remove previously injected publication lists
    html = re.sub(
        r'<!-- BEGIN AUTO PUBS -->.*?<!-- END AUTO PUBS -->\n?',
        '', html, flags=re.DOTALL
    )

    # Process each person block
    def add_pubs_to_person(match):
        block = match.group(0)
        name_match = re.search(r'<h3>([^<]+)</h3>', block)
        if not name_match:
            return block

        # Extract display name (strip any parenthetical suffix)
        raw_name = name_match.group(1).strip()
        name = re.sub(r'\s*\([^)]*\)\s*$', '', raw_name).strip()

        if name in SKIP_NAMES:
            return block

        info = member_lookup.get(name)
        if not info or not info['end_year']:
            return block

        papers = find_papers(info['lastname'], all_entries, info['end_year'])
        if not papers:
            return block

        pub_lines = []
        for key, entry, _ in papers:
            pub_lines.append(f'          <li>{format_compact_pub(key, entry)}</li>')

        pub_html = '\n'.join(pub_lines)
        injection = (
            f'        <!-- BEGIN AUTO PUBS -->\n'
            f'        <div class="alumni-pubs">\n'
            f'          <ul>\n'
            f'{pub_html}\n'
            f'          </ul>\n'
            f'        </div>\n'
            f'        <!-- END AUTO PUBS -->'
        )

        block = re.sub(
            r'(</div>\s*\n)(\s*</div>\s*\n\s*</div>)',
            r'\1' + injection + r'\n\2',
            block,
            count=1
        )

        print(f'  {name}: {len(papers)} papers (end year {info["end_year"]})')
        return block

    html = re.sub(
        r'<div class="person">.*?</div>\s*\n\s*</div>\s*\n\s*</div>',
        add_pubs_to_person,
        html,
        flags=re.DOTALL
    )

    with open(people_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print('Updated people.html with alumni publications')


if __name__ == '__main__':
    main()
