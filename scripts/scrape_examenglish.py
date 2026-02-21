#!/usr/bin/env python3
"""
Scraper for ExamEnglish.com IELTS content.
Downloads XML files and converts to well-labelled markdown.
Source: https://www.examenglish.com/IELTS/
"""

import urllib.request
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
import os
import re
import time

BASE_URL = "https://www.examenglish.com/IELTS/"
OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "tests")

# ── HTML → plain text ──────────────────────────────────────────────────────────

class HTMLStripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text = []

    def handle_data(self, data):
        self.text.append(data)

    def handle_starttag(self, tag, attrs):
        if tag in ('p', 'br', 'div', 'h1', 'h2', 'h3', 'h4'):
            self.text.append('\n')
        elif tag == 'strong':
            self.text.append('**')
        elif tag == 'em':
            self.text.append('*')

    def handle_endtag(self, tag):
        if tag in ('p', 'div', 'h1', 'h2', 'h3', 'h4'):
            self.text.append('\n')
        elif tag == 'strong':
            self.text.append('**')
        elif tag == 'em':
            self.text.append('*')

def html_to_text(html):
    if not html:
        return ''
    stripper = HTMLStripper()
    stripper.feed(html)
    text = ''.join(stripper.text)
    # Clean up excessive newlines
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


# ── XML fetcher ────────────────────────────────────────────────────────────────

def fetch_xml(path):
    url = BASE_URL + path
    print(f"  Fetching {url}")
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw_bytes = resp.read()
            # Try UTF-8 first, fall back to Windows-1252 (older files)
            for enc in ('utf-8', 'windows-1252', 'latin-1'):
                try:
                    return raw_bytes.decode(enc)
                except (UnicodeDecodeError, LookupError):
                    continue
            return raw_bytes.decode('latin-1', errors='replace')
    except Exception as e:
        print(f"  ERROR fetching {url}: {e}")
        return None


# ── XML parser ─────────────────────────────────────────────────────────────────

def cdata(node):
    """Get CDATA text from a node."""
    if node is None:
        return ''
    return (node.text or '').strip()

def parse_xml(raw_xml):
    """Parse ExamEnglish XML into structured dict."""
    try:
        root = ET.fromstring(raw_xml)
    except ET.ParseError as e:
        print(f"  XML parse error: {e}")
        return None

    doc = {
        'title': '',
        'sections': []
    }

    title_node = root.find('title')
    doc['title'] = cdata(title_node)

    # Reading passage (shared across all sections)
    reading_node = root.find('reading')
    passage_html = cdata(reading_node)
    passage = html_to_text(passage_html) if passage_html else ''

    # text2 is sometimes used instead of reading
    if not passage:
        text2_node = root.find('text2')
        if text2_node is not None:
            passage = html_to_text(cdata(text2_node))

    # Section 1: items (multiple choice or dropdown)
    items1 = root.findall('item')
    instr1_node = root.find('instructions')
    instr1 = html_to_text(cdata(instr1_node))

    if items1:
        questions = []
        for i, item in enumerate(items1):
            q_node = item.find('text')
            q_text = html_to_text(cdata(q_node))
            choices_node = item.find('choices')
            choices = []
            correct = None
            if choices_node is not None:
                for j, choice in enumerate(choices_node.findall('choice')):
                    text = (choice.text or '').strip()
                    feedback = choice.get('feedback', '')
                    if text and text.lower() not in ('select',):
                        choices.append(text)
                        if feedback.lower() == 'correct':
                            correct = text
            questions.append({
                'number': i + 1,
                'question': q_text,
                'type': 'multiple_choice',
                'choices': choices,
                'answer': correct
            })
        doc['sections'].append({
            'instructions': instr1,
            'questions': questions
        })

    # Section 2: item2 (matching / dropdown with shared option list)
    items2 = root.findall('item2')
    instr2_node = root.find('instructions2')
    instr2 = html_to_text(cdata(instr2_node)) if instr2_node is not None else ''

    if items2:
        # Collect the shared option list from first item
        option_list = []
        if items2:
            first_choices = items2[0].find('choices')
            if first_choices:
                for choice in first_choices.findall('choice2'):
                    text = (choice.text or '').strip()
                    if text and text.lower() != 'select':
                        option_list.append(text)

        questions = []
        offset = len(items1)
        for i, item in enumerate(items2):
            q_node = item.find('text')
            q_text = html_to_text(cdata(q_node))
            choices_node = item.find('choices')
            correct = None
            if choices_node is not None:
                for choice in choices_node.findall('choice2'):
                    feedback = choice.get('feedback', '')
                    if feedback.lower() == 'correct':
                        correct = (choice.text or '').strip()
            questions.append({
                'number': offset + i + 1,
                'question': q_text,
                'type': 'matching',
                'options': option_list,
                'answer': correct
            })
        doc['sections'].append({
            'instructions': instr2,
            'options': option_list,
            'questions': questions
        })

    # Section 3: item3 (gap fill / short answer)
    items3 = root.findall('item3')
    instr3_node = root.find('instructions3')
    instr3 = html_to_text(cdata(instr3_node)) if instr3_node is not None else ''

    # Also try gaptext / section[@type=gapfill]
    if not items3:
        section_gapfill = root.find('.//section[@type="gapfill"]')
        if section_gapfill is not None:
            items3 = section_gapfill.findall('item3')
            if not instr3:
                instr3_inner = section_gapfill.find('instructions3')
                instr3 = html_to_text(cdata(instr3_inner)) if instr3_inner is not None else ''

    if items3:
        questions = []
        offset = len(items1) + len(items2)
        for i, item in enumerate(items3):
            q_node = item.find('text') or item.find('question')
            q_text = html_to_text(cdata(q_node)) if q_node is not None else ''
            # Answer is in <answer> tag or attribute
            ans_node = item.find('answer')
            correct = None
            if ans_node is not None:
                correct = (ans_node.text or '').strip()
            else:
                correct = item.get('answer', '')
            questions.append({
                'number': offset + i + 1,
                'question': q_text,
                'type': 'gap_fill',
                'answer': correct
            })
        doc['sections'].append({
            'instructions': instr3,
            'questions': questions
        })

    doc['passage'] = passage
    return doc


# ── Markdown formatter ─────────────────────────────────────────────────────────

def doc_to_markdown(doc, label):
    """Convert parsed doc to labelled markdown."""
    lines = []
    lines.append(f"# {label}")
    lines.append(f"\n**Source:** ExamEnglish.com (https://www.examenglish.com/IELTS/)")
    lines.append(f"**Type:** {doc.get('title', 'IELTS Practice')}")
    lines.append("")

    if doc.get('passage'):
        lines.append("---")
        lines.append("## Reading Passage\n")
        lines.append(doc['passage'])
        lines.append("")

    lines.append("---")
    lines.append("## Questions\n")

    for sec_idx, section in enumerate(doc.get('sections', [])):
        if section.get('instructions'):
            lines.append(f"### Part {sec_idx + 1} Instructions\n")
            lines.append(section['instructions'])
            lines.append("")

        if section.get('options'):
            lines.append("**Options:** " + " / ".join(section['options']))
            lines.append("")

        for q in section.get('questions', []):
            lines.append(f"**Q{q['number']}.** {q['question']}")
            if q['type'] == 'multiple_choice' and q.get('choices'):
                for idx, ch in enumerate(q['choices']):
                    lines.append(f"  - {chr(65+idx)}) {ch}")
            lines.append(f"  ✅ **Answer:** {q.get('answer', '_not found_')}")
            lines.append("")

    return '\n'.join(lines)


# ── File writer ────────────────────────────────────────────────────────────────

def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"  → Saved: {path.replace(OUT_DIR, 'tests')}")


# ── Test definitions ───────────────────────────────────────────────────────────

TESTS = [
    # ── Academic Reading ───────────────────────────────────────────────────────
    {
        'xml': 'XML/ieltsacademicreading1.xml',
        'out': 'academic/test-1/reading/passage.md',
        'label': 'IELTS Academic Reading — Test 1 (ExamEnglish)',
    },
    {
        'xml': 'XML/ieltsacademicreading2.xml',
        'out': 'academic/test-2/reading/passage.md',
        'label': 'IELTS Academic Reading — Test 2 (ExamEnglish)',
    },
    {
        'xml': 'XML/ielts_academicreading3.xml',
        'out': 'academic/test-3/reading/passage.md',
        'label': 'IELTS Academic Reading — Test 3 (ExamEnglish)',
    },
    {
        'xml': 'XML/ielts_academic_reading4.xml',
        'out': 'academic/test-4/reading/passage.md',
        'label': 'IELTS Academic Reading — Test 4 (ExamEnglish)',
    },
    {
        'xml': 'XML/ielts_academicreading5.xml',
        'out': 'academic/test-5/reading/passage.md',
        'label': 'IELTS Academic Reading — Test 5 (ExamEnglish)',
    },
    {
        'xml': 'XML/ieltsacademicreading6.xml',
        'out': 'academic/test-6/reading/passage.md',
        'label': 'IELTS Academic Reading — Test 6 (ExamEnglish)',
    },
    {
        'xml': 'XML/ieltsacademicreading7.xml',
        'out': 'academic/test-7/reading/passage.md',
        'label': 'IELTS Academic Reading — Test 7 (ExamEnglish)',
    },
    {
        'xml': 'XML/ieltsacademicreading8.xml',
        'out': 'academic/test-8/reading/passage.md',
        'label': 'IELTS Academic Reading — Test 8 (ExamEnglish)',
    },
    {
        'xml': 'XML/ieltsacademicreading9.xml',
        'out': 'academic/test-9/reading/passage.md',
        'label': 'IELTS Academic Reading — Test 9 (ExamEnglish)',
    },
    {
        'xml': 'XML/ieltsacademicreading10.xml',
        'out': 'academic/test-10/reading/passage.md',
        'label': 'IELTS Academic Reading — Test 10 (ExamEnglish)',
    },
    # ── General Training Reading ───────────────────────────────────────────────
    {
        'xml': 'XML/ielts_reading1.xml',
        'out': 'general-training/test-1/reading/part-1.md',
        'label': 'IELTS General Training Reading — Test 1, Part 1 (ExamEnglish)',
    },
    {
        'xml': 'XML/ielts_reading1_2.xml',
        'out': 'general-training/test-1/reading/part-2.md',
        'label': 'IELTS General Training Reading — Test 1, Part 2 (ExamEnglish)',
    },
    {
        'xml': 'XML/ielts_reading2.xml',
        'out': 'general-training/test-2/reading/part-1.md',
        'label': 'IELTS General Training Reading — Test 2, Part 1 (ExamEnglish)',
    },
    {
        'xml': 'XML/ieltsgeneralreading2_1.xml',
        'out': 'general-training/test-2/reading/part-2.md',
        'label': 'IELTS General Training Reading — Test 2, Part 2 (ExamEnglish)',
    },
    {
        'xml': 'XML/ieltsgeneralreading2_2.xml',
        'out': 'general-training/test-2/reading/part-3.md',
        'label': 'IELTS General Training Reading — Test 2, Part 3 (ExamEnglish)',
    },
    {
        'xml': 'XML/ieltsgeneralreading2_3.xml',
        'out': 'general-training/test-2/reading/part-4.md',
        'label': 'IELTS General Training Reading — Test 2, Part 4 (ExamEnglish)',
    },
    {
        'xml': 'XML/ielts_reading3.xml',
        'out': 'general-training/test-3/reading/part-1.md',
        'label': 'IELTS General Training Reading — Test 3, Part 1 (ExamEnglish)',
    },
    {
        'xml': 'XML/ieltsgeneralreading3_1.xml',
        'out': 'general-training/test-4/reading/part-1.md',
        'label': 'IELTS General Training Reading — Test 4, Part 1 (ExamEnglish)',
    },
    {
        'xml': 'XML/ieltsgeneralreading3_2.xml',
        'out': 'general-training/test-4/reading/part-2.md',
        'label': 'IELTS General Training Reading — Test 4, Part 2 (ExamEnglish)',
    },
    {
        'xml': 'XML/ieltsgeneralreading3_3.xml',
        'out': 'general-training/test-4/reading/part-3.md',
        'label': 'IELTS General Training Reading — Test 4, Part 3 (ExamEnglish)',
    },
    {
        'xml': 'XML/ieltsgeneralreading4_1.xml',
        'out': 'general-training/test-5/reading/part-1.md',
        'label': 'IELTS General Training Reading — Test 5, Part 1 (ExamEnglish)',
    },
    # ── Listening ──────────────────────────────────────────────────────────────
    {
        'xml': 'XML/ielts_listening1.xml',
        'out': 'listening/test-1/section-1.md',
        'label': 'IELTS Listening — Test 1, Section 1 (ExamEnglish)',
    },
    {
        'xml': 'XML/ielts_listening2.xml',
        'out': 'listening/test-1/section-2.md',
        'label': 'IELTS Listening — Test 1, Section 2 (ExamEnglish)',
    },
    {
        'xml': 'XML/ielts_listening3.xml',
        'out': 'listening/test-1/section-3.md',
        'label': 'IELTS Listening — Test 1, Section 3 (ExamEnglish)',
    },
    {
        'xml': 'XML/ielts_listening4.xml',
        'out': 'listening/test-1/section-4.md',
        'label': 'IELTS Listening — Test 1, Section 4 (ExamEnglish)',
    },
    {
        'xml': 'XML/ielts_listening_test2_part1.xml',
        'out': 'listening/test-2/section-1.md',
        'label': 'IELTS Listening — Test 2, Section 1 (ExamEnglish)',
    },
    {
        'xml': 'XML/ielts_listeningtest2part3.xml',
        'out': 'listening/test-2/section-3.md',
        'label': 'IELTS Listening — Test 2, Section 3 (ExamEnglish)',
    },
    {
        'xml': 'XML/ielts_listening_test2_4.xml',
        'out': 'listening/test-2/section-4.md',
        'label': 'IELTS Listening — Test 2, Section 4 (ExamEnglish)',
    },
    {
        'xml': 'XML/ielts_listeningtest2part5.xml',
        'out': 'listening/test-3/section-1.md',
        'label': 'IELTS Listening — Test 3, Section 1 (ExamEnglish)',
    },
    {
        'xml': 'XML/ielts_listening3_2.xml',
        'out': 'listening/test-3/section-2.md',
        'label': 'IELTS Listening — Test 3, Section 2 (ExamEnglish)',
    },
    {
        'xml': 'XML/ielts_listening3_3.xml',
        'out': 'listening/test-3/section-3.md',
        'label': 'IELTS Listening — Test 3, Section 3 (ExamEnglish)',
    },
]


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    print(f"Scraping {len(TESTS)} files from ExamEnglish.com...\n")
    success = 0
    failed = []

    for t in TESTS:
        print(f"\n[{t['label']}]")
        raw = fetch_xml(t['xml'])
        if not raw:
            failed.append(t['xml'])
            continue

        # Save raw XML as source
        xml_out = os.path.join(OUT_DIR, t['out'].replace('.md', '.xml'))
        write_file(xml_out, raw)

        doc = parse_xml(raw)
        if not doc:
            failed.append(t['xml'])
            continue

        md = doc_to_markdown(doc, t['label'])
        md_out = os.path.join(OUT_DIR, t['out'])
        write_file(md_out, md)
        success += 1

        time.sleep(0.5)  # Be polite

    print(f"\n{'='*60}")
    print(f"Done: {success}/{len(TESTS)} successful")
    if failed:
        print(f"Failed ({len(failed)}): {', '.join(failed)}")

if __name__ == '__main__':
    main()
