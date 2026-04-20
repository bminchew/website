#!/usr/bin/env python3
"""
Generate the Mentorship section of cv_caltech.tex from group.bib.

Replaces everything between the Mentorship section markers in the CV
with content generated from the authoritative group.bib database.
"""

import os
import re
import sys

script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)
from group_parser import parse_group_bib, get_by_type


def format_date_range(m):
    """Format date range for CV."""
    start = m['start']
    end = m.get('end', '')
    if not end:
        return f"{start}--"
    elif start == end:
        return start
    else:
        return f"{start}--{end}"


def format_postdoc(m):
    """Format a postdoc entry for the CV."""
    parts = []
    name = m['name']

    # Add PhD info if available
    grad_info = ''
    if m.get('grad_inst') and m.get('grad_year'):
        grad_info = f"({m['grad_inst']} {m['degree']} `{m['grad_year']})"
    elif m.get('grad_inst'):
        grad_info = f"({m['grad_inst']})"

    desc = name
    if grad_info:
        desc += f" {grad_info}"
    if m.get('title'):
        desc += f", {m['title']}"
    if m.get('now'):
        desc += f"; now {m['now']}"

    return f"{format_date_range(m)} & {desc}"


def format_primary(m):
    """Format a primary advisee entry for the CV."""
    name = m['name']

    if m['is_current']:
        # Current: Name (Degree, Dept) or Name, Dept (Degree, Note)
        dept = m.get('department', '')
        degree = m.get('degree', '')
        note = m.get('note', '')
        if dept and degree and note:
            desc = f"{name}, {dept} ({degree}, {note})"
        elif dept and degree:
            desc = f"{name} ({degree}, {dept})"
        elif degree and note:
            desc = f"{name} ({degree}, {note})"
        elif degree:
            desc = f"{name} ({degree})"
        else:
            desc = name
    else:
        # Alumni: Name (Inst Degree `YY), now ...
        grad_inst = m.get('grad_inst', '')
        degree = m.get('degree', '')
        grad_year = m.get('grad_year', '')
        if grad_inst and degree and grad_year:
            desc = f"{name} ({grad_inst} {degree} `{grad_year})"
        elif grad_inst and degree:
            desc = f"{name} ({grad_inst} {degree})"
        else:
            desc = name
        if m.get('now'):
            desc += f", now {m['now']}"

    return f"{format_date_range(m)} & {desc}"


def format_project(m):
    """Format a project advisee entry for the CV."""
    name = m['name']
    degree = m.get('degree', 'PhD')
    dept = m.get('department', '')

    if m['is_current']:
        desc = f"{degree} project advisor: {name}"
        if dept:
            desc += f", {dept}"
    else:
        # Alumni
        grad_inst = m.get('grad_inst', '')
        grad_year = m.get('grad_year', '')
        if grad_inst and grad_year:
            paren = f"({grad_inst} {degree} `{grad_year}"
            # Include dept only if it adds info beyond grad_inst (e.g., "AeroAstro" but not "MIT EAPS")
            if dept and grad_inst not in dept and dept not in grad_inst:
                paren += f", {dept}"
            paren += ")"
            desc = f"{degree} project {'co-' if degree == 'MS' else ''}advisor: {name} {paren}"
        else:
            desc = f"{degree} project advisor: {name}"
            if dept:
                desc += f", {dept}"
        if m.get('now'):
            desc += f", now {m['now']}"

    return f"{format_date_range(m)} & {desc}"


def format_undergrad(m):
    """Format an undergrad entry for the CV."""
    name = m['name']
    dept = m.get('department', '')
    program = m.get('program', 'Project')

    desc = f"{program} advisor: {name}"
    if dept:
        desc += f", {dept}"

    # Handle single-year with hphantom for alignment
    start = m['start']
    end = m.get('end', '')
    if start == end or not end:
        date = f"{start}\\hphantom{{--{start}}}"
    elif end:
        date = f"{start}--{end}"
    else:
        date = f"{start}--"

    return f"{date} & {desc}"


def generate_mentorship_tex(members):
    """Generate the full mentorship LaTeX section."""
    postdocs = sorted(get_by_type(members, 'postdoc'),
                      key=lambda m: -int(m['start']))
    primary = sorted(get_by_type(members, 'primary'),
                     key=lambda m: -int(m['start']))
    project = sorted(get_by_type(members, 'project'),
                     key=lambda m: -int(m['start']))
    undergrads = sorted(get_by_type(members, 'undergrad'),
                        key=lambda m: -int(m['start']))

    lines = []

    # Postdocs
    lines.append('\\cvsubsection{Postdoctoral researchers}')
    lines.append('\\begin{longtable}[h]{l p{13cm}}')
    for i, m in enumerate(postdocs):
        entry = format_postdoc(m)
        if i < len(postdocs) - 1:
            entry += ' \\\\'
        lines.append(entry)
    lines.append('\\end{longtable}')
    lines.append('')

    # Primary
    lines.append('\\vspace{-3mm}')
    lines.append('\\cvsubsection{Graduate students, as a primary advisor}')
    lines.append('\\begin{longtable}[h]{l p{13cm}}')
    for i, m in enumerate(primary):
        entry = format_primary(m)
        if i < len(primary) - 1:
            entry += ' \\\\'
        lines.append(entry)
    lines.append('\\end{longtable}')
    lines.append('')

    # Project
    lines.append('\\vspace{-3mm}')
    lines.append('\\cvsubsection{Graduate students, as a secondary or project advisor}')
    lines.append('\\begin{longtable}[h]{l p{13cm}}')
    for i, m in enumerate(project):
        entry = format_project(m)
        if i < len(project) - 1:
            entry += ' \\\\'
        lines.append(entry)
    lines.append('\\end{longtable}')
    lines.append('')

    # Undergrads
    lines.append('\\vspace{-3mm}')
    lines.append("\\cvsubsection{Undergraduate students}\\\\")
    lines.append("\\phantom{nt}{\\small\\color{CoolGray}(UROP = MIT Undergrad Research Opportunities Program; MSRP = MIT Summer Research Program)}")
    lines.append('\\vspace{-5mm}')
    lines.append('\\begin{longtable}[h]{l p{13cm}}')
    for i, m in enumerate(undergrads):
        entry = format_undergrad(m)
        if i < len(undergrads) - 1:
            entry += ' \\\\'
        lines.append(entry)
    lines.append('\\end{longtable}')

    return '\n'.join(lines)


def main():
    bib_path = os.path.join(script_dir, 'group.bib')
    cv_path = os.path.join(script_dir, '..', 'mywebsite', 'cv', 'cv_caltech.tex')

    members = parse_group_bib(bib_path)
    print(f'Parsed {len(members)} members from group.bib')

    mentorship_tex = generate_mentorship_tex(members)

    # Read CV
    with open(cv_path, 'r', encoding='utf-8') as f:
        cv = f.read()

    # Replace mentorship section
    # Find the content between \begingroup after \cvsection{Mentorship} and \endgroup
    pattern = (
        r'(\\cvsection\{Mentorship\}.*?'
        r'\\begin\{indentmore\}\s*\n'
        r'\\begingroup\s*\n'
        r'\\renewcommand\{\\section\}\[2\]\{\}%\s*\n)'
        r'(.*?)'
        r'(\n\\endgroup\s*\n\\end\{indentmore\})'
    )

    m = re.search(pattern, cv, re.DOTALL)
    if not m:
        print('ERROR: could not find Mentorship section boundaries in CV')
        sys.exit(1)

    new_cv = cv[:m.start(2)] + '\n' + mentorship_tex + '\n' + cv[m.end(2):]

    with open(cv_path, 'w', encoding='utf-8') as f:
        f.write(new_cv)

    print(f'Updated CV mentorship section')
    print(f'  {len(get_by_type(members, "postdoc"))} postdocs')
    print(f'  {len(get_by_type(members, "primary"))} primary advisees')
    print(f'  {len(get_by_type(members, "project"))} project advisees')
    print(f'  {len(get_by_type(members, "undergrad"))} undergrads')


if __name__ == '__main__':
    main()
