#!/usr/bin/env python3
"""
Add recent publications beside each alumni's entry on people.html.

For each alumni, finds papers where they are a co-author and the paper
was published within 3 years of their end date. Injects a compact
publication list into their person-info div.

Publications are sourced from the bib files (authoritative).
"""

import os
import re
import sys

script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)
from build_pubs import parse_bib, clean_latex

# ============================================================
# Alumni config: last_name -> matching info
# End year is parsed from people.html automatically.
# Override last names that need special matching.
# ============================================================

# Map of display name (as in people.html <h3>) to bib author last name
# Only needed when the name in the bib differs from the display name
NAME_OVERRIDES = {
    'Faye Hendley Elgart': 'Elgart',
    'Lizz Ultee': 'Ultee',
}

# People to skip (PI, not alumni)
SKIP_NAMES = {'Brent Minchew'}

YEARS_WINDOW = 3

# Current postdocs/research scientists: use current year as end year
# so their recent papers show up
import datetime
CURRENT_YEAR = datetime.datetime.now().year

CURRENT_MEMBERS_END_YEAR = {
    'Evan Kramer': CURRENT_YEAR,
}

# Override end years for people whose title text doesn't contain a parseable year
END_YEAR_OVERRIDES = {
    'Bryan Riel': 2022,
    'Lizz Ultee': 2021,
}


def extract_end_year(title_text):
    """Extract the end/graduation year from a person-title string."""
    # Try patterns like "PhD 2022", "MS 2025", "Postdoc...2021"
    # Also "2021-2023" date ranges
    m = re.search(r'(\d{4})\s*&ndash;\s*(\d{4})', title_text)
    if m:
        return int(m.group(2))
    m = re.search(r'(?:PhD|MS|Postdoc)[^,]*?(\d{4})', title_text)
    if m:
        return int(m.group(1))
    # Try any 4-digit year
    years = re.findall(r'(\d{4})', title_text)
    if years:
        return int(years[-1])
    return None


def get_bib_lastname(display_name):
    """Get the last name to search for in bib author fields."""
    if display_name in NAME_OVERRIDES:
        return NAME_OVERRIDES[display_name]
    # Handle names like "Sarah Wells-Moran" -> "Wells-Moran"
    parts = display_name.split()
    return parts[-1]


def find_papers(lastname, entries, end_year, window=YEARS_WINDOW):
    """Find papers where lastname appears as author, within window of end_year."""
    results = []
    for key, entry in entries.items():
        author = entry.get('author', '')
        # Match last name in author field (case-insensitive)
        if not re.search(re.escape(lastname), author, re.IGNORECASE):
            continue
        # Don't include "in prep" or "submitted"
        journal = entry.get('journal', '').lower()
        if 'in prep' in journal or 'submitted' in journal or 'in revision' in journal:
            continue
        try:
            pub_year = int(entry.get('year', '0'))
        except ValueError:
            continue
        if end_year and abs(pub_year - end_year) <= window:
            results.append((key, entry, pub_year))
    # Sort by year descending
    results.sort(key=lambda x: -x[2])
    return results


def format_compact_pub(key, entry):
    """Format a publication as a compact one-line HTML string."""
    # Clean title
    title = clean_latex(entry.get('title', ''))
    # Truncate long titles
    if len(title) > 100:
        title = title[:97] + '...'
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
    # Check for local PDF
    pdf_path = os.path.join(script_dir, 'pdfs', f'{key}.pdf')
    if os.path.exists(pdf_path):
        html += f' <a href="pdfs/{key}.pdf">[pdf]</a>'
    html += '</span>'
    return html


def main():
    # Parse bib files
    bib_dir = os.path.join(script_dir, '..', 'mywebsite', 'pubs')
    all_entries = {}
    for bibfile in ['minchew_journals.bib', 'minchew_general.bib']:
        path = os.path.join(bib_dir, bibfile)
        if os.path.exists(path):
            all_entries.update(parse_bib(path))

    # Tag entries
    for k, v in all_entries.items():
        v['_key'] = k

    # Read people.html
    people_path = os.path.join(script_dir, 'people.html')
    with open(people_path, 'r', encoding='utf-8') as f:
        html = f.read()

    # First, remove any previously injected publication lists
    html = re.sub(
        r'<!-- BEGIN AUTO PUBS -->.*?<!-- END AUTO PUBS -->\n?',
        '', html, flags=re.DOTALL
    )

    # Process each person block across the entire page
    def add_pubs_to_person(match):
        block = match.group(0)
        name_match = re.search(r'<h3>([^<]+)</h3>', block)
        title_match = re.search(r'<div class="person-title">([^<]+)</div>', block)

        if not name_match or not title_match:
            return block

        name = name_match.group(1).strip()
        title_text = title_match.group(1).strip()

        if name in SKIP_NAMES:
            return block

        lastname = get_bib_lastname(name)
        end_year = (CURRENT_MEMBERS_END_YEAR.get(name)
                    or END_YEAR_OVERRIDES.get(name)
                    or extract_end_year(title_text))

        if not end_year:
            return block

        papers = find_papers(lastname, all_entries, end_year)
        if not papers:
            return block

        # Build compact pub list
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

        # Insert after the last person-title or person-contact div
        block = re.sub(
            r'(</div>\s*\n)(\s*</div>\s*\n\s*</div>)',
            r'\1' + injection + r'\n\2',
            block,
            count=1
        )

        print(f'  {name}: {len(papers)} papers (end year {end_year})')
        return block

    # Match each person block across the whole page
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
