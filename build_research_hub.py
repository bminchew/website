#!/usr/bin/env python3
"""
Update research_hub.html from group.bib.

Updates:
  1. data-questions and data-methods on each hub-person div
  2. data-people on each hub-question div (controls the wash-out effect)

Reads group.bib via group_parser. Layout, positions, and all other content
are preserved.
"""

import os
import re
import sys
from collections import defaultdict

script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)
from group_parser import parse_group_bib, get_current


def main():
    bib_path = os.path.join(script_dir, 'group.bib')
    hub_path = os.path.join(script_dir, 'research_hub.html')

    members = parse_group_bib(bib_path)
    current = get_current(members)

    # Build lookup: key -> {questions: [...], methods: [...]}
    # and reverse map: question -> [keys who work on it]
    lookup = {}
    question_to_people = defaultdict(list)
    for m in current:
        key = m['_key']
        questions = m.get('questions', [])
        methods = m.get('methods', [])
        lookup[key] = {'questions': questions, 'methods': methods}
        for q in questions:
            question_to_people[q].append(key)

    with open(hub_path, 'r', encoding='utf-8') as f:
        html = f.read()

    # Update hub-person divs: data-questions and data-methods
    def replace_person(match):
        full = match.group(0)
        key = match.group(1)
        if key not in lookup:
            return full
        info = lookup[key]
        questions_str = ','.join(f'q-{q}' for q in info['questions'])
        methods_str = ','.join(info['methods'])
        full = re.sub(r'data-questions="[^"]*"', f'data-questions="{questions_str}"', full)
        full = re.sub(r'data-methods="[^"]*"', f'data-methods="{methods_str}"', full)
        return full

    person_pattern = r'<div\s+class="hub-person"\s+id="p-([^"]+)"[^>]*>'
    html = re.sub(person_pattern, replace_person, html)

    # Update hub-question divs: data-people
    # Match the opening tag which may span multiple lines (data-people is on next line)
    def replace_question(match):
        full = match.group(0)
        q_id = match.group(1)  # e.g. "q-sliding"
        q_name = q_id.replace('q-', '')  # e.g. "sliding"
        people = question_to_people.get(q_name, [])
        people_str = ','.join(sorted(people))
        full = re.sub(r'data-people="[^"]*"', f'data-people="{people_str}"', full)
        return full

    question_pattern = r'<div\s+class="hub-question"\s+id="(q-[^"]+)"[^>]*data-people="[^"]*"[^>]*>'
    html = re.sub(question_pattern, replace_question, html, flags=re.DOTALL)

    with open(hub_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f'  updated research_hub.html ({len(lookup)} members in bib)')


if __name__ == '__main__':
    main()
