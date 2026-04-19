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
        'slug': 'stabilization',
        'title': 'Ice Sheet Stabilization',
        'image': '../images/research_stabilization.jpg',
        'description': [
            'Current projections of sea-level rise carry large uncertainties driven by our incomplete understanding of ice sheet dynamics. Our group is exploring whether targeted interventions\u2014such as strategically slowing glacier flow at key locations\u2014could meaningfully reduce the risk of rapid, irreversible sea-level rise. This work combines fundamental glacier mechanics with applied engineering thinking to assess the feasibility, efficacy, and risks of stabilization concepts.',
            'Through the <a href="https://www.areteglaciers.org/">Ar\u00eate Glacier Initiative</a>, we are taking first steps toward developing the science and technology needed to evaluate glacier stabilization as a complement to emissions reduction.',
        ],
        'keys': [
            'guardian2026', 'minchew2024', 'meyer2025b', 'minchew2020b', 'minchew2020a', 'minchew2016b',
        ],
        'extra_html': '''
  <h2 class="section-title" style="font-size: 1.2rem; margin-top: 2rem;">In the News &amp; Media</h2>
  <ul class="software-list">
    <li class="software-item">
      <h3><a href="https://www.forbes.com/sites/monicasanders/2025/04/24/5-million-to-save-the-doomsday-glacier-can-we-prevent-catastrophe/">Forbes: $5 Million To Save The Doomsday Glacier, Can We Prevent Catastrophe?</a></h3>
    </li>
    <li class="software-item">
      <h3><a href="https://www.technologyreview.com/2025/03/21/1113396/inside-a-new-quest-to-save-the-doomsday-glacier/">MIT Technology Review: Inside a new quest to save the &lsquo;doomsday glacier&rsquo;</a></h3>
    </li>
    <li class="software-item">
      <h3><a href="https://apple.news/AchiyBHcWTy2lGZMBKKnlzw">BBC Science Focus Magazine: Doomsday Glacier</a></h3>
    </li>
    <li class="software-item">
      <h3><a href="https://www.theatlantic.com/magazine/archive/2024/07/nasa-nisar-mission-glaciers-sea-ice-thwaites/678522/">The Atlantic: Glacier Rescue Project</a></h3>
    </li>
    <li class="software-item">
      <h3><a href="https://www.youtube.com/watch?v=ulmrRWy0FSQ">The Atlantic Festival: The Climate Summit</a></h3>
      <p>Video</p>
    </li>
    <li class="software-item">
      <h3><a href="https://mcj.vc/inevitable-podcast/arete-glacier-initiative">My Climate Journey Podcast: Can We Slow the Doomsday Glacier?</a></h3>
      <p>Podcast</p>
    </li>
    <li class="software-item">
      <h3>Curiosity Unbounded: Putting a Glacier In Its Place</h3>
      <p><a href="https://eaps.mit.edu/news-impact/brent-minchew-on-curiosity-unbounded-episode-14-putting-a-glacier-in-its-place/">Podcast</a> &middot; <a href="https://www.youtube.com/watch?v=2KkJLcvpSI4">Video</a></p>
    </li>
    <li class="software-item">
      <h3><a href="https://www.areteglaciers.org/releases">Ar&ecirc;te Glacier Initiative Press Release: Launch Announcement</a></h3>
    </li>
    <li class="software-item">
      <h3><a href="https://drive.google.com/file/d/18JTSrwL5ZaIN5_1Ozl2wkn0gYad95gFV/view?usp=sharing">Ar&ecirc;te 2025 Annual Report</a></h3>
      <p>PDF</p>
    </li>
  </ul>
''',
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
<a href="#main" class="skip-link">Skip to main content</a>

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

<main id="main" class="content-wrap">
  <h1 class="page-title">{title}</h1>

  <img src="{image}" alt="{title}" style="width: 100%; max-height: 300px; object-fit: cover; border-radius: 3px; margin-bottom: 1.5rem;">

{description_html}

{pub_sections}

{extra_html}
  <p style="margin-top: 1.5rem;"><a href="../research.html">&larr; Back to Research Overview</a></p>
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
    general_bib = os.path.join(bib_dir, 'minchew_general.bib')

    all_entries = {}
    if os.path.exists(journal_bib):
        all_entries.update(parse_bib(journal_bib))
    general_keys = set()
    if os.path.exists(general_bib):
        general_entries = parse_bib(general_bib)
        general_keys = set(general_entries.keys())
        all_entries.update(general_entries)

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

        # Separate scholarly from general publications
        scholarly_html = ''
        general_html = ''
        for key in topic['keys']:
            if key in all_entries:
                item = format_pub_item(all_entries[key], script_dir)
                if key in general_keys:
                    general_html += item
                else:
                    scholarly_html += item

        # Build publication sections
        pub_sections = ''
        if scholarly_html:
            pub_sections += '  <h2 class="section-title" style="font-size: 1.2rem; margin-top: 2rem;">Relevant Scholarly Articles</h2>\n'
            pub_sections += '  <p class="pub-note">* graduate students, ** undergraduates, &#9734; postdocs and research scientists.</p>\n'
            pub_sections += '\n  <ul class="pub-list" style="margin-top: 1rem;">\n'
            pub_sections += scholarly_html
            pub_sections += '  </ul>\n'
        if general_html:
            pub_sections += '\n  <h2 class="section-title" style="font-size: 1.2rem; margin-top: 2rem;">Other Publications</h2>\n'
            pub_sections += '\n  <ul class="pub-list" style="margin-top: 1rem;">\n'
            pub_sections += general_html
            pub_sections += '  </ul>\n'

        # Render template
        html = SUBPAGE_TEMPLATE.format(
            title=topic['title'],
            image=topic['image'],
            description_html=desc_html,
            pub_sections=pub_sections,
            extra_html=topic.get('extra_html', ''),
        )

        outpath = os.path.join(research_dir, f"{topic['slug']}.html")
        with open(outpath, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"  wrote {outpath} ({len(topic['keys'])} papers)")

    print(f'Generated {len(TOPICS)} research sub-pages')


if __name__ == '__main__':
    main()
