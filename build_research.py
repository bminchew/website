#!/usr/bin/env python3
"""
Generate research sub-pages with auto-populated publication lists.

Each research topic has a description and a list of relevant bib keys.
Papers are pulled from the bib files and formatted as HTML.
"""

import os
import sys

# Reuse the bib parser and formatters from build_pubs.py
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)
from build_pubs import parse_bib, format_author, clean_latex

# ============================================================
# Research topics: key, title, image, description, bib keys
# ============================================================

TOPICS = [
    {
        'slug': 'remote-sensing',
        'title': 'Kinematic Remote Sensing',
        'image': '../images/research_remote_sensing.png',
        'description': [
            'Our group focuses on dynamical systems and their various responses to environmental forcing. Dynamics is the study of forces and the motions they produce. Kinematics is the study of motion without regard to force. Kinematic observations are thus measurements of displacement, velocity, and acceleration, and are used to constrain dynamical models. We employ two broad methods for kinematic observations: interferometric methods, which difference the phase of two electromagnetic waves to infer displacement along the instrument line of sight (currently only available from synthetic aperture radar, or SAR), and feature tracking methods, which cross-correlate two images to find the displacement of features between image acquisitions (available from SAR and optical imagery).',
            'We focus on short-timescale variations in glacier flow velocity and thus place a premium on time-dependent kinematic observations. Such observations inform our understanding of water pressure at glacier beds and the resistive buttressing stresses exerted by floating ice shelves on the grounded ice upstream.',
        ],
        'keys': [
            'riel2020a', 'minchew2018', 'minchew2018b', 'milillo2016',
            'minchew2016b', 'minchew2016a', 'milillo2015', 'minchew2015a',
            'scheingross2013',
        ],
    },
    {
        'slug': 'basal-mechanics',
        'title': 'Mechanics of Deformable Glacier Beds',
        'image': '../images/research_basal.jpg',
        'description': [
            'Glaciers flow through a combination of viscous flow within the ice column and basal slip, which encompasses sliding over the bed and deformation within the bed itself. Deformable glacier beds are composed of unfrozen sediment that is granular in nature, with mechanical properties that depend on grain size distribution, porosity, and the state of the subglacial hydrologic system. Despite their importance to glacier dynamics, deformable beds remain poorly understood.',
            'Our approach uses synoptic-scale, time-dependent observations of ice surface velocities to infer the mechanical properties of glacier beds through dynamical modeling. We take a natural-laboratory approach, focusing on areas where environmental forcings are known, allowing us to study the bed response to controlled perturbations.',
        ],
        'keys': [
            'riel2021a', 'ranganathan2020', 'minchew2020a', 'minchew2020b',
            'robel2017', 'minchew2016b', 'minchew2016a', 'minchew2015a',
            'narayanan2025',
        ],
    },
    {
        'slug': 'shear-margins',
        'title': 'Ice Rheology and Shear Margins',
        'image': '../images/research_shear_margins.jpg',
        'description': [
            'Fast glacier flow is restrained by drag in lateral shear margins\u2014bands of intense deformation separating fast-flowing ice streams from stagnant ice or rock walls. The drag exerted by shear margins depends on ice rheology, which evolves through damage, heating, melting, and crystallographic fabric development. We seek to understand the relative contributions of all rheological mechanisms, with particular emphasis on thermomechanics: ice rheology depends strongly on temperature and liquid water content, and deformation produces heat that warms cold ice and melts temperate ice, creating feedbacks that affect both the rheology and the dynamics of ice flow.',
        ],
        'keys': [
            'ranganathan2022c', 'ranganathan2022a', 'millstein2022',
            'ranganathan2021a', 'hunter2020', 'ranganathan2020',
            'clerc2019', 'minchew2018', 'meyer2018', 'meyer2018b',
            'riel2022', 'martin2025',
        ],
    },
    {
        'slug': 'calving',
        'title': 'Fracture, Calving, and Rifting',
        'image': '../images/research_calving.jpg',
        'description': [
            'Fracture mechanics in glacier ice is one of our most active research areas. Surface crevasses produce distinctive patterns, allow meltwater pooling, and pose hazards to field operations. Basal crevasses reduce the flexural rigidity of ice shelves and can trigger calving events. Calving\u2014the breaking off of icebergs\u2014is the culmination of fracture propagation and a primary mechanism of mass loss for marine-terminating glaciers and ice sheets. Rifts are full-thickness fractures in ice shelves that can propagate for years before producing massive tabular icebergs, fundamentally altering the stress state of the remaining shelf.',
        ],
        'keys': [
            'wells-moran2023', 'sun2023', 'millstein2022', 'ultee2020',
            'clerc2019', 'elgart2025',
        ],
    },
    {
        'slug': 'hazards',
        'title': 'Hazard Response and Mitigation',
        'image': '../images/research_hazards.jpeg',
        'description': [
            'We develop methods for applying remote sensing to environmental hazard response and mitigation, with emphasis on polarimetric synthetic aperture radar (PolSAR). Radar operates in all weather and lighting conditions, making it invaluable for rapid response. PolSAR data can locate oil on the sea surface, in bays, and along wetland coasts, and can characterize the properties of spilled oil. These same techniques can be adapted to locate wildfire perimeters under certain conditions. This work makes direct societal contributions and sharpens our broader remote sensing capabilities.',
        ],
        'keys': [
            'angelliaume2018', 'angelliaume2016', 'collins2015',
            'minchew2012b', 'minchew2012a', 'jones_dwh_agu2011',
        ],
    },
]

# ============================================================
# HTML template for sub-pages
# ============================================================

SUBPAGE_TEMPLATE = '''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title} &mdash; Caltech Glaciology</title>
  <link rel="stylesheet" href="../css/style.css">
</head>
<body>

<header class="site-header">
  <div class="header-inner">
    <div>
      <div class="site-title"><a href="../index.html"><span class="caltech">Caltech</span> <span class="group-name">Glaciology</span></a></div>
      <div class="site-tagline">Mechanics of flowing ice</div>
    </div>
  </div>
</header>

<nav class="site-nav">
  <div class="nav-inner">
    <button class="nav-toggle" aria-label="Menu" onclick="document.querySelector('.nav-links').classList.toggle('open')">&#9776;</button>
    <ul class="nav-links">
      <li><a href="../index.html">Home</a></li>
      <li><a href="../research.html" class="active">Research</a></li>
      <li><a href="../people.html">People</a></li>
      <li><a href="../publications.html">Publications</a></li>
      <li><a href="../software.html">Software</a></li>
      <li><a href="../contact.html">Contact</a></li>
    </ul>
  </div>
</nav>

<main class="content-wrap">
  <h1 class="page-title">{title}</h1>

  <img src="{image}" alt="{title}" style="width: 100%; max-height: 300px; object-fit: cover; border-radius: 3px; margin-bottom: 1.5rem;">

{description_html}

  <h2 class="section-title" style="font-size: 1.2rem; margin-top: 2rem;">Relevant Publications</h2>
  <p class="pub-note">* graduate students, ** undergraduates, &#9734; postdocs and research scientists.</p>

  <ul class="pub-list" style="margin-top: 1rem;">
{pub_html}
  </ul>

  <p style="margin-top: 1.5rem;"><a href="../research.html">&larr; Back to Research Overview</a></p>
</main>

<footer class="site-footer">
  <div class="footer-inner">
    <span>California Institute of Technology &middot; 1200 E. California Blvd. &middot; Pasadena, CA 91125</span>
    <span><a href="mailto:bminchew@caltech.edu">bminchew@caltech.edu</a></span>
  </div>
</footer>

</body>
</html>
'''


def format_pub_item(entry, site_dir):
    """Format a single publication as an HTML list item."""
    authors = format_author(entry.get('author', ''))
    title = clean_latex(entry.get('title', ''))
    journal = clean_latex(entry.get('journal', ''))
    year = entry.get('year', '')
    volume = entry.get('volume', '')
    number = entry.get('number', '')
    pages = entry.get('pages', '')
    doi = entry.get('doi', '')
    bib_key = entry.get('_key', '')

    cite = f'{authors}. &ldquo;{title}.&rdquo; <em>{journal}</em>'
    if volume and 'in press' not in volume.lower():
        cite += f', {volume}'
        if number:
            cite += f'({number})'
    if pages:
        cite += f', {clean_latex(pages)}'
    cite += f', {year}.'

    links = ''
    pdf_path = os.path.join(site_dir, 'pdfs', f'{bib_key}.pdf')
    if os.path.exists(pdf_path):
        links += f'<a href="../pdfs/{bib_key}.pdf">[pdf]</a> '
    if doi:
        doi_clean = doi.strip()
        if not doi_clean.startswith('http'):
            doi_url = f'https://doi.org/{doi_clean}'
        else:
            doi_url = doi_clean
        links += f'<a href="{doi_url}">[doi]</a> '

    html = f'    <li class="pub-item">\n'
    html += f'      <div>\n'
    html += f'        {cite}\n'
    if links:
        html += f'        <div class="pub-links">{links.strip()}</div>\n'
    html += f'      </div>\n'
    html += f'    </li>\n'
    return html


def main():
    bib_dir = os.path.join(script_dir, '..', 'mywebsite', 'pubs')
    journal_bib = os.path.join(bib_dir, 'minchew_journals.bib')

    all_entries = {}
    if os.path.exists(journal_bib):
        all_entries.update(parse_bib(journal_bib))

    # Tag entries with keys
    for k, v in all_entries.items():
        v['_key'] = k

    research_dir = os.path.join(script_dir, 'research')
    os.makedirs(research_dir, exist_ok=True)

    for topic in TOPICS:
        # Build description HTML
        desc_html = ''
        for para in topic['description']:
            desc_html += f'  <p style="margin-bottom: 0.8rem;">{para}</p>\n'

        # Build publication list
        pub_html = ''
        for key in topic['keys']:
            if key in all_entries:
                pub_html += format_pub_item(all_entries[key], script_dir)

        # Render template
        html = SUBPAGE_TEMPLATE.format(
            title=topic['title'],
            image=topic['image'],
            description_html=desc_html,
            pub_html=pub_html,
        )

        outpath = os.path.join(research_dir, f"{topic['slug']}.html")
        with open(outpath, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"  wrote {outpath} ({len(topic['keys'])} papers)")

    print(f'Generated {len(TOPICS)} research sub-pages')


if __name__ == '__main__':
    main()
