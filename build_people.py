#!/usr/bin/env python3
"""
Generate the people page from group.bib.

Reads the authoritative group database and generates people.html
with current postdocs, current students, and alumni sections.
Preserves the PI section (manually managed).

Run build_people_pubs.py AFTER this script to add publication lists.
"""

import os
import re
import sys

script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)
from group_parser import parse_group_bib, get_by_type, get_current, get_alumni, clean_latex_for_html


def find_photo(member):
    """Find photo file for a member."""
    photo = member.get('photo', '')
    if photo:
        path = os.path.join(script_dir, 'images', photo)
        if os.path.exists(path):
            return photo
    return None


def build_title_current(m):
    """Build display title for a current member."""
    parts = []
    if m.get('title'):
        return clean_latex_for_html(m['title'])
    dept = m.get('department', '')
    degree = m.get('degree', '')
    note = m.get('note', '')
    if dept and note:
        return f"{dept} ({note})"
    elif dept:
        return dept
    elif degree and note:
        return f"{degree}, {note}"
    return ''


def build_title_alumni(m):
    """Build display title for an alumni member."""
    parts = []

    # Degree and graduation info
    grad_inst = m.get('grad_inst', '')
    degree = m.get('degree', '')
    grad_year = m.get('grad_year', '')
    dept = m.get('department', '')
    start = m.get('start', '')
    end = m.get('end', '')

    if grad_inst and degree and grad_year:
        parts.append(f"{degree} 20{grad_year}, {grad_inst}")
    elif degree and end:
        inst = dept.split('(')[0].strip().rstrip(',') if dept else ''
        parts.append(f"{degree} {end}, {inst}" if inst else f"{degree} {end}")
    elif dept:
        parts.append(f"{dept}, {start}&ndash;{end}")
    else:
        parts.append(f"{start}&ndash;{end}")

    title = ', '.join(p for p in parts if p)

    # Current position
    now = m.get('now', '')
    if now:
        title += f" &rarr; {clean_latex_for_html(now)}"

    return title


def render_person(m, show_degree_in_name=False):
    """Render a person entry as HTML."""
    photo = find_photo(m)
    name = clean_latex_for_html(m.get('display_name', m['name']))

    # For postdocs with grad info, show inline
    name_suffix = ''
    if show_degree_in_name and m.get('grad_inst') and m.get('degree'):
        grad_year = m.get('grad_year', '')
        if grad_year:
            name_suffix = f" ({m['degree']}, {m['grad_inst']})"
        else:
            name_suffix = f" ({m['degree']}, {m['grad_inst']})"

    if m['is_current']:
        title = build_title_current(m)
    else:
        title = build_title_alumni(m)

    html = '    <div class="person">\n'
    html += '      <div class="person-photo">\n'
    if photo:
        html += f'        <img src="images/{photo}" alt="{name}">\n'
    else:
        html += '        <div class="placeholder">Photo</div>\n'
    html += '      </div>\n'
    html += '      <div class="person-info">\n'
    html += f'        <h3>{name}{name_suffix}</h3>\n'
    if title:
        html += f'        <div class="person-title">{title}</div>\n'
    html += '      </div>\n'
    html += '    </div>\n'
    return html


def main():
    bib_path = os.path.join(script_dir, 'group.bib')
    people_path = os.path.join(script_dir, 'people.html')

    members = parse_group_bib(bib_path)

    # Categorize
    postdocs = get_by_type(members, 'postdoc')
    primary = get_by_type(members, 'primary')
    project = get_by_type(members, 'project')

    current_postdocs = sorted(
        [m for m in postdocs if m['is_current']],
        key=lambda m: int(m['start'])
    )
    current_students = sorted(
        [m for m in primary + project if m['is_current']],
        key=lambda m: m['display_name'].split()[-1]
    )
    alumni = sorted(
        [m for m in postdocs + primary + project if not m['is_current']],
        key=lambda m: m['display_name'].split()[-1]
    )

    # Read existing people.html to extract PI section and page chrome
    with open(people_path, 'r', encoding='utf-8') as f:
        html = f.read()

    # Extract header
    header_match = re.search(
        r'(.*?<main id="main" class="content-wrap">\s*\n\s*<h1 class="page-title">People</h1>)',
        html, re.DOTALL
    )
    header = header_match.group(1) if header_match else ''

    # Extract PI section
    pi_match = re.search(
        r'(<!-- Principal Investigator -->.*?</div>\s*\n\s*</div>\s*\n\s*</div>)',
        html, re.DOTALL
    )
    pi_section = pi_match.group(1) if pi_match else ''

    # Extract footer
    footer_match = re.search(r'(</main>.*)', html, re.DOTALL)
    footer = footer_match.group(1) if footer_match else '</main>\n</body>\n</html>'

    # Build new HTML
    new_html = header + '\n\n'
    new_html += '  ' + pi_section + '\n\n'

    # Current Postdocs
    new_html += '  <!-- Current Postdoctoral Scholars -->\n'
    new_html += '  <div class="people-section">\n'
    new_html += '    <h2 class="people-section-title">Current Postdoctoral Scholars</h2>\n\n'
    for m in current_postdocs:
        new_html += render_person(m, show_degree_in_name=True)
        new_html += '\n'
    new_html += '  </div>\n\n'

    # Current Graduate Students
    new_html += '  <!-- Current Graduate Students -->\n'
    new_html += '  <div class="people-section">\n'
    new_html += '    <h2 class="people-section-title">Current Graduate Students</h2>\n\n'
    for m in current_students:
        new_html += render_person(m)
        new_html += '\n'
    new_html += '  </div>\n\n'

    # Alumni
    new_html += '  <!-- Alumni -->\n'
    new_html += '  <div class="people-section">\n'
    new_html += '    <h2 class="people-section-title">Alumni</h2>\n\n'
    for m in alumni:
        new_html += render_person(m)
        new_html += '\n'
    new_html += '  </div>\n\n'

    new_html += footer

    with open(people_path, 'w', encoding='utf-8') as f:
        f.write(new_html)

    print(f'Updated people.html:')
    print(f'  {len(current_postdocs)} current postdocs')
    print(f'  {len(current_students)} current students')
    print(f'  {len(alumni)} alumni')


if __name__ == '__main__':
    main()
