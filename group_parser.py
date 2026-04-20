#!/usr/bin/env python3
"""
Parse group.bib — the authoritative group member database.

Returns a list of member dicts, each with:
    _type, _key, name, display_name, start, end, department, degree,
    grad_year, grad_inst, title, now, photo, questions, methods,
    program, note, is_current
"""

import re
import os


def parse_group_bib(filepath):
    """Parse group.bib and return a list of member dicts."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    members = []

    # Match @type{key, ... }
    # Use a manual brace-depth approach for robustness
    for m in re.finditer(r'@(\w+)\s*\{([^,]+),', content):
        entry_type = m.group(1).lower()
        key = m.group(2).strip()
        start_pos = m.end()

        # Find matching closing brace
        depth = 1
        pos = start_pos
        while pos < len(content) and depth > 0:
            if content[pos] == '{':
                depth += 1
            elif content[pos] == '}':
                depth -= 1
            pos += 1
        body = content[start_pos:pos - 1]

        # Parse fields
        fields = {'_type': entry_type, '_key': key}

        # Manual field parser handling nested braces and \" in quotes
        fpos = 0
        while fpos < len(body):
            fm = re.match(r'\s*(\w+)\s*=\s*', body[fpos:])
            if not fm:
                fpos += 1
                continue
            fname = fm.group(1).lower()
            fpos += fm.end()

            if fpos < len(body) and body[fpos] == '{':
                # Brace-delimited value
                fdepth = 0
                fstart = fpos
                while fpos < len(body):
                    if body[fpos] == '{':
                        fdepth += 1
                    elif body[fpos] == '}':
                        fdepth -= 1
                        if fdepth == 0:
                            fpos += 1
                            break
                    fpos += 1
                fval = body[fstart + 1:fpos - 1]
            else:
                # Bare value (number or word)
                fm2 = re.match(r'(\S+)', body[fpos:])
                if fm2:
                    fval = fm2.group(1).rstrip(',')
                    fpos += fm2.end()
                else:
                    fpos += 1
                    continue

            fields[fname] = fval.strip()

        # Derived fields
        fields['is_current'] = 'end' not in fields
        fields['display_name'] = fields.get('display_name', fields.get('name', ''))

        # Parse list fields
        for list_field in ['questions', 'methods']:
            if list_field in fields:
                fields[list_field] = [x.strip() for x in fields[list_field].split(',') if x.strip()]
            else:
                fields[list_field] = []

        members.append(fields)

    return members


def get_by_type(members, entry_type):
    """Filter members by type."""
    return [m for m in members if m['_type'] == entry_type]


def get_current(members):
    """Get current (active) members."""
    return [m for m in members if m['is_current']]


def get_alumni(members):
    """Get alumni (ended) members."""
    return [m for m in members if not m['is_current']]


def clean_latex_for_html(text):
    """Convert LaTeX accents to HTML entities."""
    if not text:
        return text
    text = re.sub(r"\\'\{?([aeiou])\}?", r'&\1acute;', text)
    text = re.sub(r'\\"\{?([aeiouAEIOU])\}?', r'&\1uml;', text)
    text = text.replace('\\ae', '&aelig;')
    text = text.replace('{', '').replace('}', '')
    return text
