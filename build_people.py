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


def get_alumni_affiliation(m):
    """Get the university affiliation while in the group."""
    entry_type = m.get('_type', '')
    dept = m.get('department', '')
    grad_inst = m.get('grad_inst', '')

    if entry_type in ('postdoc', 'researchscientist'):
        # Postdocs/research scientists were at the PI's institution
        end = int(m.get('end', m.get('start', '2025')))
        return 'Caltech' if end >= 2025 else 'MIT'
    elif entry_type in ('gradprimary', 'gradproject'):
        # Grad students: use grad_inst if available, else extract from department
        if grad_inst:
            return clean_latex_for_html(grad_inst)
        elif dept:
            return clean_latex_for_html(dept)
    elif entry_type == 'undergrad':
        if dept:
            return clean_latex_for_html(dept)
    return ''


def render_person(m, show_degree_in_name=False):
    """Render a person entry as HTML."""
    photo = find_photo(m)
    name = clean_latex_for_html(m.get('display_name', m['name']))

    html = '    <div class="person">\n'
    html += '      <div class="person-photo">\n'
    if photo:
        html += f'        <img src="images/{photo}" alt="{name}">\n'
    else:
        html += '        <div class="placeholder">Photo</div>\n'
    html += '      </div>\n'
    html += '      <div class="person-info">\n'

    entry_type = m.get('_type', '')

    if m['is_current'] and entry_type in ('postdoc', 'researchscientist'):
        html += f'        <h3>{name}</h3>\n'
        title = build_title_current(m)
        if title:
            html += f'        <div class="person-title">{title}</div>\n'
        degree = m.get('degree', '')
        grad_inst = m.get('grad_inst', '')
        grad_year = m.get('grad_year', '')
        if degree and grad_inst:
            detail = f'{degree} {clean_latex_for_html(grad_inst)}'
            if grad_year:
                detail += f', 20{grad_year}'
            html += f'        <div class="person-detail">{detail}</div>\n'
    elif m['is_current']:
        html += f'        <h3>{name}</h3>\n'
        title = build_title_current(m)
        if title:
            html += f'        <div class="person-title">{title}</div>\n'
    else:
        # Alumni: line 1 = name (affiliation), line 2 = dates, line 3 = degree
        affiliation = get_alumni_affiliation(m)
        if affiliation:
            html += f'        <h3>{name} ({affiliation})</h3>\n'
        else:
            html += f'        <h3>{name}</h3>\n'

        start = m.get('start', '')
        end = m.get('end', '')
        entry_type = m.get('_type', '')
        degree = m.get('degree', '')

        # Determine position title
        if entry_type == 'postdoc':
            position = 'Postdoctoral Scholar'
        elif entry_type == 'researchscientist':
            position = 'Research Scientist'
        elif entry_type in ('gradprimary', 'gradproject'):
            if degree == 'PhD':
                position = 'PhD Student'
            elif degree == 'MS':
                position = 'MS Student'
            else:
                position = 'Graduate Student'
        elif entry_type == 'undergrad':
            position = 'Undergraduate Researcher'
        else:
            position = ''

        if start and end:
            if position:
                html += f'        <div class="person-title">{position}, {start}&ndash;{end}</div>\n'
            else:
                html += f'        <div class="person-title">{start}&ndash;{end}</div>\n'

        grad_year = m.get('grad_year', '')
        grad_inst = m.get('grad_inst', '')
        if degree and grad_year:
            if entry_type in ('postdoc', 'researchscientist') and grad_inst:
                html += f'        <div class="person-detail">{degree} {clean_latex_for_html(grad_inst)}, 20{grad_year}</div>\n'
            else:
                html += f'        <div class="person-detail">{degree} 20{grad_year}</div>\n'

        now = m.get('now', '')
        if now:
            html += f'        <div class="person-detail">Now: {clean_latex_for_html(now)}</div>\n'

    html += '      </div>\n'
    html += '    </div>\n'
    return html


def main():
    bib_path = os.path.join(script_dir, 'group.bib')
    people_path = os.path.join(script_dir, 'people.html')

    members = parse_group_bib(bib_path)

    # Categorize
    postdocs = get_by_type(members, 'postdoc')
    research_scientists = get_by_type(members, 'researchscientist')
    primary = get_by_type(members, 'gradprimary')
    project = get_by_type(members, 'gradproject')

    current_postdocs = sorted(
        [m for m in postdocs + research_scientists if m['is_current']],
        key=lambda m: int(m['start'])
    )
    current_students = sorted(
        [m for m in primary + project if m['is_current']],
        key=lambda m: m['display_name'].split()[-1]
    )
    alumni = sorted(
        [m for m in postdocs + research_scientists + primary + project if not m['is_current']],
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
