#!/usr/bin/env python3
"""Parse data/publications.tex and data/patents.tex,
then inject HTML into index.html between marker comments.

Usage: python scripts/gen_publications.py
Run from the repo root directory.
"""

import re
import sys
from pathlib import Path
from collections import defaultdict

TEX_PATH = Path("data/publications.tex")
PATENTS_TEX_PATH = Path("data/patents.tex")
HTML_PATH = Path("index.html")
START_MARKER = "<!-- PUB_GROUPS_START -->"
END_MARKER = "<!-- PUB_GROUPS_END -->"
PAT_START_MARKER = "<!-- PAT_GROUPS_START -->"
PAT_END_MARKER = "<!-- PAT_GROUPS_END -->"


def tex_to_html(text):
    """Convert LaTeX markup to HTML."""
    # Superscripts (process before \textbf to handle nesting)
    text = re.sub(r'\\textsuperscript\{\\dag\}', '\u2020', text)
    text = re.sub(r'\\textsuperscript\{\\dagger\}', '\u2020', text)
    text = re.sub(r'\\dag\b', '\u2020', text)

    # Bold
    text = re.sub(r'\\textbf\{([^{}]*)\}', r'<b>\1</b>', text)

    # Italic
    text = re.sub(r'\\textit\{([^{}]*)\}', r'<i>\1</i>', text)
    text = re.sub(r'\\emph\{([^{}]*)\}', r'<i>\1</i>', text)

    # \href{url}{display} -> DOI link
    def href_sub(m):
        url = m.group(1)
        return f'<a href="{url}" target="_blank">[<u>DOI</u>]</a>'
    text = re.sub(r'\\href\{([^{}]+)\}\{[^{}]+\}', href_sub, text)

    # LaTeX quotes
    text = text.replace("``", "\u201c").replace("''", "\u201d")

    # Special chars
    text = text.replace(r'\&', '&amp;')
    text = text.replace(r'\_', '_')
    text = text.replace('--', '\u2013')

    # Remove remaining LaTeX commands
    text = re.sub(r'\\[a-zA-Z]+\{([^{}]*)\}', r'\1', text)
    text = re.sub(r'\\[a-zA-Z]+\b', '', text)

    return text.strip()


def extract_year(raw_text):
    """Extract publication year: last 4-digit year before \\href."""
    before_href = raw_text.split(r'\href')[0]
    years = re.findall(r'\b(20\d{2})\b', before_href)
    return int(years[-1]) if years else 0


# ---------------------------------------------------------------------------
# Publications
# ---------------------------------------------------------------------------

def parse_tex(tex_path):
    """Return list of (label, pub_type, year, html_text) tuples."""
    entries = []
    for line in Path(tex_path).read_text(encoding='utf-8').splitlines():
        line = line.strip()
        m = re.match(r'\\item\[\\textbf\{\[([BCJ])\.(\d+)\]\}\]\s*(.*)', line)
        if not m:
            continue
        type_char, num, raw = m.group(1), int(m.group(2)), m.group(3)
        pub_type = {'B': 'book', 'J': 'journal', 'C': 'conference'}[type_char]
        label = f'[{type_char}.{num}]'
        entries.append((label, pub_type, extract_year(raw), tex_to_html(raw)))
    return entries


def generate_groups_html(entries):
    """Generate two-level collapsible HTML: section (type) > year groups."""
    sections = {'book': {}, 'journal': {}, 'conference': {}}
    for label, pub_type, year, html_text in entries:
        sections[pub_type].setdefault(year, []).append((label, html_text))

    section_titles = {'book': 'Book', 'journal': 'Journal Papers', 'conference': 'Conference Papers'}

    lines = [START_MARKER]
    for pub_type in ('book', 'journal', 'conference'):
        years_data = sections[pub_type]
        if not years_data:
            continue
        title = section_titles[pub_type]
        lines += [
            f'            <!-- {title} -->',
            f'            <div class="pub-section" data-type="{pub_type}">',
            f'              <div class="pub-section-header" onclick="toggleSection(this)">',
            f'                <span class="toggle-icon">\u25b6</span>{title}',
            f'              </div>',
            f'              <div class="pub-section-body">',
        ]
        if pub_type == 'book':
            lines.append('                <ul style="list-style:none; padding-left:0; margin-top:0.4em;">')
            for year in sorted(years_data.keys(), reverse=True):
                for label, html_text in years_data[year]:
                    lines += [
                        '                  <li style="margin-bottom:0.6em;">',
                        f'                    {label} {html_text}',
                        '                  </li>',
                    ]
            lines.append('                </ul>')
        else:
            for year in sorted(years_data.keys(), reverse=True):
                lines += [
                    '                <div class="pub-year">',
                    '                  <div class="pub-year-header" onclick="toggleYear(this)">',
                    f'                    <span class="toggle-icon">\u25b6</span>{year}',
                    '                  </div>',
                    '                  <div class="pub-year-body">',
                    '                    <ul style="list-style:none; padding-left:0; margin-top:0.4em;">',
                ]
                for label, html_text in years_data[year]:
                    lines += [
                        '                      <li style="margin-bottom:0.6em;">',
                        f'                        {label} {html_text}',
                        '                      </li>',
                    ]
                lines += [
                    '                    </ul>',
                    '                  </div>',
                    '                </div>',
                ]
        lines += ['              </div>', '            </div>', '']

    lines.append(END_MARKER)
    return '\n'.join(lines)


# ---------------------------------------------------------------------------
# Patents & Software Copyrights
# ---------------------------------------------------------------------------

def parse_patents_tex(tex_path):
    """Parse patents.tex, extracting English text from bilingual blocks.
    Returns list of (label, pat_type, html_text).
    """
    content = Path(tex_path).read_text(encoding='utf-8')
    entries = []
    lines = content.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        m = re.match(r'\\item\[\\textbf\{\[([PS])\.(\d+)\]\}\]\s*(.*)', line)
        if m:
            type_char, num = m.group(1), int(m.group(2))
            label = f'[{type_char}.{num}]'
            pat_type = 'patent' if type_char == 'P' else 'software'
            # Collect block until next \item or end
            block_lines = [m.group(3)]
            i += 1
            while i < len(lines):
                nl = lines[i].strip()
                if re.match(r'\\item\[', nl) or re.match(r'\\end\{', nl) or nl == r'\resumeItemListEnd':
                    break
                block_lines.append(nl)
                i += 1
            block = ' '.join(block_lines)
            # Extract English from \ifchinese...\else...\fi
            en_match = re.search(r'\\else\s+(.*?)\\fi', block, re.DOTALL)
            raw = en_match.group(1).strip() if en_match else block
            entries.append((label, pat_type, tex_to_html(raw)))
            continue
        i += 1
    return entries


def generate_patents_html(entries):
    """Generate collapsible HTML for patents: Patents / Software Copyrights."""
    sections = {'patent': [], 'software': []}
    for label, pat_type, html_text in entries:
        sections[pat_type].append((label, html_text))

    section_titles = {'patent': 'Patents', 'software': 'Software Copyrights'}

    lines = [PAT_START_MARKER]
    for pat_type in ('patent', 'software'):
        items = sections[pat_type]
        if not items:
            continue
        title = section_titles[pat_type]
        lines += [
            f'            <!-- {title} -->',
            f'            <div class="pub-section" data-type="{pat_type}">',
            f'              <div class="pub-section-header" onclick="toggleSection(this)">',
            f'                <span class="toggle-icon">\u25b6</span>{title}',
            f'              </div>',
            f'              <div class="pub-section-body">',
            '                <ul style="list-style:none; padding-left:0; margin-top:0.4em;">',
        ]
        for label, html_text in items:
            lines += [
                '                  <li style="margin-bottom:0.6em;">',
                f'                    {label} {html_text}',
                '                  </li>',
            ]
        lines += ['                </ul>', '              </div>', '            </div>', '']

    lines.append(PAT_END_MARKER)
    return '\n'.join(lines)


# ---------------------------------------------------------------------------
# HTML injection
# ---------------------------------------------------------------------------

def inject_section(content, start_marker, end_marker, new_html):
    if start_marker not in content or end_marker not in content:
        return None
    before = content[:content.index(start_marker)]
    after = content[content.index(end_marker) + len(end_marker):]
    return before + new_html + after


def main():
    for p in (TEX_PATH, PATENTS_TEX_PATH, HTML_PATH):
        if not p.exists():
            print(f"ERROR: {p} not found", file=sys.stderr)
            sys.exit(1)

    content = HTML_PATH.read_text(encoding='utf-8')

    pub_entries = parse_tex(TEX_PATH)
    print(f"Parsed {len(pub_entries)} publication entries")
    content = inject_section(content, START_MARKER, END_MARKER, generate_groups_html(pub_entries))
    if content is None:
        print("ERROR: publication markers not found", file=sys.stderr)
        sys.exit(1)

    pat_entries = parse_patents_tex(PATENTS_TEX_PATH)
    print(f"Parsed {len(pat_entries)} patent/software entries")
    content = inject_section(content, PAT_START_MARKER, PAT_END_MARKER, generate_patents_html(pat_entries))
    if content is None:
        print("ERROR: patent markers not found", file=sys.stderr)
        sys.exit(1)

    HTML_PATH.write_text(content, encoding='utf-8')
    print(f"Updated {HTML_PATH}")


if __name__ == '__main__':
    main()
