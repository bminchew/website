#!/usr/bin/env python3
"""
Generate the people page from the CV's mentorship sections.

Parses postdocs, primary advisees, and secondary advisees from cv_caltech.tex.
Determines current vs alumni based on end dates. Maps names to photo files.
Preserves the PI section (manually managed) and page chrome.

Run build_people_pubs.py AFTER this script to add publication lists.
"""

import os
import re
import glob

script_dir = os.path.dirname(os.path.abspath(__file__))

# ============================================================
# Photo filename overrides: display name -> filename in images/
# Only needed when the photo filename doesn't match a normalized
# version of the person's name. Add entries here as needed.
# ============================================================
PHOTO_OVERRIDES = {
    'Brent Minchew': 'P1280056z.jpg',
    'Evan Kramer': 'evan_kramer-250x308.png',
    'Ufuoma Ovienmhada': 'headshot_Ovienmhada.jpg',
    'Faye Hendley Elgart': 'faye.jpg',
    'Joanna Millstein': 'joanna_eaps.jpg',
    'Mila Lubeck': 'mila_picture.png',
    'Neosha Narayanan': 'Neosha_Narayanan_headshot_1_edit.jpg',
    'Annick Dewald': 'AnnickDewald-portrait.png',
    'Natasha Morgan-Witts': 'NatashaMorganWitts-e1738084186427-300x300.png',
    'Yudong Sun': 'yudong_headshot.jpg',
    'Alex Miller': 'asmiller.jpg',
    'Elizabeth (Lizz) Ultee': 'ultee.jpg',
    'Lizz Ultee': 'ultee.jpg',
}

# Display name overrides: CV name -> website display name
DISPLAY_NAME_OVERRIDES = {
    'Elizabeth (Lizz) Ultee': 'Lizz Ultee',
}

# Extra info not parseable from CV (e.g., incoming postdocs)
# These are appended to the postdoc list as current members
EXTRA_POSTDOCS = [
    # {'name': 'George Lu', 'title': 'starting October 2026', 'name_suffix': '(PhD, Columbia University)'},
    # {'name': 'Natasha Morgan-Wells', 'title': 'starting July 2026'},
]

# Override file: extra people not in the CV mentorship section
# Format: list of dicts with keys: name, title, section (postdoc/student/alumni), name_suffix
EXTRA_PEOPLE_FILE = os.path.join(script_dir, 'extra_people.json')


def find_photo(name):
    """Find a photo file for a person by name."""
    if name in PHOTO_OVERRIDES:
        path = os.path.join(script_dir, 'images', PHOTO_OVERRIDES[name])
        if os.path.exists(path):
            return PHOTO_OVERRIDES[name]

    # Try common patterns
    images_dir = os.path.join(script_dir, 'images')
    # Try: firstname_lastname, lastname, firstname
    parts = name.split()
    first = parts[0].lower() if parts else ''
    last = parts[-1].lower() if parts else ''

    candidates = [
        f'{first}_{last}',
        f'{last}_{first}',
        f'{first}',
        f'{last}',
        f'{first}_{last}'.replace('-', '_'),
        name.lower().replace(' ', '_'),
    ]

    for candidate in candidates:
        for ext in ['jpg', 'jpeg', 'png', 'gif']:
            path = os.path.join(images_dir, f'{candidate}.{ext}')
            if os.path.exists(path):
                return f'{candidate}.{ext}'

    return None


def parse_mentorship(cv_path):
    """Parse the mentorship section of the CV into structured data."""
    with open(cv_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract mentorship section
    m = re.search(r'\\cvsection\{Mentorship\}(.*?)\\cvsection\{', content, re.DOTALL)
    if not m:
        print('ERROR: could not find Mentorship section')
        return [], [], []

    mentorship = m.group(1)

    # Split into sub-sections
    sections = re.split(r'\\cvsubsection\{([^}]+)\}', mentorship)

    postdocs = []
    primary = []
    secondary = []

    i = 1
    while i < len(sections):
        section_name = sections[i].strip()
        section_body = sections[i + 1] if i + 1 < len(sections) else ''
        i += 2

        # Parse entries from longtable
        entries = parse_entries(section_body)

        if 'Postdoctoral' in section_name:
            postdocs = entries
        elif 'primary' in section_name:
            primary = entries
        elif 'secondary' in section_name or 'project' in section_name:
            secondary = entries

    return postdocs, primary, secondary


def parse_entries(body):
    """Parse longtable entries into structured data."""
    entries = []

    # Match lines like: 2025-- & Description \\
    # or: 2018--2022 & Description \\
    # or: 2019--2022 & Description (last line, no \\)
    pattern = r'(\d{4})(?:--(\d{4}|--)?)?\s*&\s*(.*?)(?:\\\\|\n|$)'

    for m in re.finditer(pattern, body):
        start_year = int(m.group(1))
        end_str = m.group(2)
        desc = m.group(3).strip()

        if end_str == '--' or end_str is None or end_str == '':
            end_year = None  # current
            is_current = True
        else:
            end_year = int(end_str)
            is_current = False

        # Parse the description
        entry = parse_description(desc, start_year, end_year, is_current)
        if entry:
            entries.append(entry)

    return entries


def parse_description(desc, start_year, end_year, is_current):
    """Parse a CV entry description into structured person data."""
    # Clean LaTeX
    desc = desc.replace('\\\\', '')
    desc = re.sub(r"\\'\{?([aeiou])\}?", r'\1', desc)
    desc = re.sub(r'\\"\{?([aeiouAEIOU])\}?', r'\1', desc)
    desc = desc.replace('{', '').replace('}', '')
    desc = re.sub(r'\$[^$]*\$', '', desc)
    desc = re.sub(r'\\[a-zA-Z]+', '', desc)
    desc = desc.replace('`', "'")
    desc = re.sub(r'\s+', ' ', desc).strip()

    # Handle parenthetical nicknames like "Elizabeth (Lizz) Ultee"
    desc = re.sub(r'^(\w+)\s*\((\w+)\)\s+(\w+)', r'\1 (\2) \3', desc)

    # Remove "PhD project advisor: " or "MS project co-advisor: " prefix
    is_project = False
    for prefix in ['PhD project advisor:', 'MS project co-advisor:', 'PhD project co-advisor:']:
        if desc.startswith(prefix):
            desc = desc[len(prefix):].strip()
            is_project = True
            break

    # Split on semicolons or ", now " to get name+title vs current position
    if '; now ' in desc or ';' in desc:
        parts = desc.split(';', 1)
        name_title = parts[0].strip()
        current_pos = parts[1].strip() if len(parts) > 1 else ''
    elif ', now ' in desc:
        # ", now " separates the description from current position
        idx = desc.index(', now ')
        name_title = desc[:idx].strip()
        current_pos = desc[idx + 2:].strip()  # keep "now ..."
    else:
        name_title = desc
        current_pos = ''

    # Split name from title/department
    # Name ends at the first comma NOT inside parentheses,
    # or at the first opening parenthesis that isn't a nickname.
    # A nickname paren is like "(Lizz)" — single word, followed by more name.
    paren_depth = 0
    split_idx = len(name_title)
    for i, ch in enumerate(name_title):
        if ch == '(':
            if paren_depth == 0 and i > 0:
                # Check if this is a nickname: (Word) followed by a capitalized name
                close = name_title.find(')', i)
                if close > 0:
                    inner = name_title[i+1:close].strip()
                    after = name_title[close+1:].strip()
                    # Nickname: single word, followed by more name text
                    if ' ' not in inner and after and after[0].isupper():
                        paren_depth += 1
                        continue
                split_idx = i
                break
            paren_depth += 1
        elif ch == ')':
            paren_depth -= 1
        elif ch == ',' and paren_depth == 0:
            split_idx = i
            break

    name = name_title[:split_idx].strip()
    title_part = name_title[split_idx:].strip()
    title_part = title_part.lstrip(',').strip()
    # Remove surrounding parens from title if present
    if title_part.startswith('(') and ')' in title_part:
        close = title_part.index(')')
        title_part = title_part[1:close] + title_part[close+1:]
        title_part = title_part.strip().lstrip(',').strip()

    if not name:
        return None

    # Clean up "now " prefix in current position
    if current_pos.startswith('now '):
        current_pos = current_pos[4:].strip()

    # Build display title
    if is_current:
        display_title = title_part if title_part else ''
    else:
        # For alumni, build: "Degree Year, Department -> current position"
        # Extract degree from title_part (e.g., "PhD, PAOC" or "MIT EAPS (MS)")
        degree = ''
        dept = title_part

        # Check for degree in parenthetical: "MIT EAPS (PhD, PAOC)"
        paren_match = re.search(r'\((PhD|MS|M\.S\.)([^)]*)\)', title_part)
        if paren_match:
            degree = paren_match.group(1)
            # Department is the part before the parenthetical
            dept = title_part[:paren_match.start()].strip().rstrip(',')
        else:
            # Check for degree at start: "PhD, PAOC"
            start_match = re.match(r'^(PhD|MS|M\.S\.)\b[,\s]*(.*)', title_part)
            if start_match:
                degree = start_match.group(1)
                dept = start_match.group(2).strip()
            # Check for embedded degree like "MIT PhD '24, AeroAstro"
            embed_match = re.search(r'MIT PhD .?\d{2}', title_part)
            if embed_match:
                degree = 'PhD'
                dept = re.sub(r'MIT PhD .?\d{2},?\s*', '', title_part).strip()

        if degree and end_year:
            display_title = f'{degree} {end_year}, {dept}' if dept else f'{degree} {end_year}'
        elif end_year:
            display_title = f'{dept}, {start_year}&ndash;{end_year}' if dept else f'{start_year}&ndash;{end_year}'
        else:
            display_title = title_part

        if current_pos:
            display_title += f' &rarr; {current_pos}'

    # Apply display name override
    display_name = DISPLAY_NAME_OVERRIDES.get(name, name)

    return {
        'name': name,
        'display_name': display_name,
        'title': display_title,
        'current_pos': current_pos,
        'start_year': start_year,
        'end_year': end_year,
        'is_current': is_current,
        'is_project': is_project,
    }


def render_person(entry):
    """Render a person entry as HTML."""
    photo = find_photo(entry['name']) or find_photo(entry['display_name'])
    name = entry['display_name']
    title = entry.get('title', '')

    html = '    <div class="person">\n'
    html += '      <div class="person-photo">\n'
    if photo:
        html += f'        <img src="images/{photo}" alt="{name}">\n'
    else:
        html += '        <div class="placeholder">Photo</div>\n'
    html += '      </div>\n'
    html += '      <div class="person-info">\n'
    html += f'        <h3>{name}</h3>\n'
    if title:
        html += f'        <div class="person-title">{title}</div>\n'
    html += '      </div>\n'
    html += '    </div>\n'
    return html


def main():
    cv_path = os.path.join(script_dir, '..', 'mywebsite', 'cv', 'cv_caltech.tex')
    people_path = os.path.join(script_dir, 'people.html')

    # Parse CV
    postdocs, primary, secondary = parse_mentorship(cv_path)

    # Load extra people if file exists
    extra_postdocs = list(EXTRA_POSTDOCS)
    if os.path.exists(EXTRA_PEOPLE_FILE):
        import json
        with open(EXTRA_PEOPLE_FILE) as f:
            extra = json.load(f)
        extra_postdocs.extend(extra.get('postdocs', []))

    # Split into current and alumni
    current_postdocs = [e for e in postdocs if e['is_current']]
    current_students = sorted(
        [e for e in primary + secondary if e['is_current']],
        key=lambda e: e['display_name'].split()[-1]  # sort by last name
    )
    alumni = sorted(
        [e for e in postdocs + primary + secondary if not e['is_current']],
        key=lambda e: e['display_name'].split()[-1]  # sort by last name
    )

    # Read existing people.html to extract PI section
    with open(people_path, 'r', encoding='utf-8') as f:
        html = f.read()

    # Extract everything before the PI section ends
    pi_end = re.search(r'(<!-- Principal Investigator -->.*?</div>\s*\n\s*</div>\s*\n\s*</div>)', html, re.DOTALL)
    if not pi_end:
        print('ERROR: could not find PI section in people.html')
        return

    # Extract header (everything up to and including <main>)
    header_match = re.search(r'(.*?<main id="main" class="content-wrap">\s*\n\s*<h1 class="page-title">People</h1>)', html, re.DOTALL)
    header = header_match.group(1) if header_match else ''

    # Extract PI section
    pi_section = pi_end.group(1)

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
    for entry in current_postdocs:
        new_html += render_person(entry)
        new_html += '\n'
    for extra in extra_postdocs:
        photo = find_photo(extra['name'])
        new_html += '    <div class="person">\n'
        new_html += '      <div class="person-photo">\n'
        if photo:
            new_html += f'        <img src="images/{photo}" alt="{extra["name"]}">\n'
        else:
            new_html += '        <div class="placeholder">Photo</div>\n'
        new_html += '      </div>\n'
        new_html += '      <div class="person-info">\n'
        suffix = f' {extra["name_suffix"]}' if 'name_suffix' in extra else ''
        new_html += f'        <h3>{extra["name"]}{suffix}</h3>\n'
        if extra.get('title'):
            new_html += f'        <div class="person-title">{extra["title"]}</div>\n'
        new_html += '      </div>\n'
        new_html += '    </div>\n\n'
    new_html += '  </div>\n\n'

    # Current Graduate Students
    new_html += '  <!-- Current Graduate Students -->\n'
    new_html += '  <div class="people-section">\n'
    new_html += '    <h2 class="people-section-title">Current Graduate Students</h2>\n\n'
    for entry in current_students:
        new_html += render_person(entry)
        new_html += '\n'
    new_html += '  </div>\n\n'

    # Alumni
    new_html += '  <!-- Alumni -->\n'
    new_html += '  <div class="people-section">\n'
    new_html += '    <h2 class="people-section-title">Alumni</h2>\n\n'
    for entry in alumni:
        new_html += render_person(entry)
        new_html += '\n'
    new_html += '  </div>\n\n'

    new_html += footer

    with open(people_path, 'w', encoding='utf-8') as f:
        f.write(new_html)

    print(f'Updated people.html:')
    print(f'  {len(current_postdocs) + len(extra_postdocs)} current postdocs')
    print(f'  {len(current_students)} current students')
    print(f'  {len(alumni)} alumni')


if __name__ == '__main__':
    main()
