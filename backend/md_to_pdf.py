"""Convert markdown to PDF using fpdf2."""

from fpdf import FPDF
import re

def clean_unicode(text):
    """Replace Unicode characters that cause encoding issues."""
    replacements = {
        '→': '->',
        '←': '<-',
        '↔': '<->',
        '✅': '[Y]',
        '⚠️': '[~]',
        '❌': '[N]',
        '•': '-',
        '–': '-',
        '—': '-',
        '"': '"',
        '"': '"',
        ''': "'",
        ''': "'",
        '…': '...',
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    # Remove any remaining non-latin1 characters
    return text.encode('latin-1', errors='replace').decode('latin-1')

class MarkdownPDF(FPDF):
    def __init__(self):
        super().__init__()
        self.add_page()
        self.set_auto_page_break(auto=True, margin=15)

    def header(self):
        pass

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(128)
        self.cell(0, 10, f'Page {self.page_no()}', align='C')

    def chapter_title(self, title, level=1):
        self.set_x(10)  # Reset position
        title = clean_unicode(title)
        if level == 1:
            self.set_font('Helvetica', 'B', 18)
            self.set_text_color(26, 26, 26)
        elif level == 2:
            self.set_font('Helvetica', 'B', 14)
            self.set_text_color(0, 102, 204)
        elif level == 3:
            self.set_font('Helvetica', 'B', 12)
            self.set_text_color(68, 68, 68)
        else:
            self.set_font('Helvetica', 'B', 11)
            self.set_text_color(102, 102, 102)

        self.multi_cell(0, 8, title)
        self.ln(2)

        if level == 1:
            self.set_draw_color(0, 102, 204)
            self.line(10, self.get_y(), 200, self.get_y())
            self.ln(5)

    def body_text(self, text):
        self.set_x(10)  # Reset position
        text = clean_unicode(text)
        self.set_font('Helvetica', '', 10)
        self.set_text_color(51, 51, 51)
        self.multi_cell(0, 5, text)
        self.ln(2)

    def bullet_point(self, text):
        text = clean_unicode(text)
        self.set_font('Helvetica', '', 10)
        self.set_text_color(51, 51, 51)
        # Reset x position to left margin
        self.set_x(10)
        self.multi_cell(0, 5, '  - ' + text)

    def table(self, headers, rows):
        self.set_x(10)  # Reset to left margin
        self.set_font('Helvetica', 'B', 9)
        self.set_fill_color(0, 102, 204)
        self.set_text_color(255, 255, 255)

        # Calculate column widths
        col_count = len(headers)
        page_width = 190
        col_width = min(page_width / col_count, 45)  # Max 45 per column

        # Headers
        for header in headers:
            self.cell(col_width, 7, clean_unicode(header[:18]), border=1, fill=True, align='C')
        self.ln()

        # Rows
        self.set_font('Helvetica', '', 8)
        self.set_text_color(51, 51, 51)
        fill = False
        for row in rows:
            self.set_x(10)  # Reset to left margin
            if fill:
                self.set_fill_color(249, 249, 249)
            else:
                self.set_fill_color(255, 255, 255)
            for cell in row:
                self.cell(col_width, 6, clean_unicode(str(cell)[:22]), border=1, fill=True)
            self.ln()
            fill = not fill
        self.set_x(10)
        self.ln(3)


def parse_markdown(md_text):
    """Parse markdown and generate PDF."""
    pdf = MarkdownPDF()

    lines = md_text.split('\n')
    i = 0

    while i < len(lines):
        line = lines[i].strip()

        # Skip empty lines
        if not line:
            i += 1
            continue

        # Skip horizontal rules
        if line.startswith('---'):
            pdf.ln(5)
            i += 1
            continue

        # Headers
        if line.startswith('####'):
            pdf.chapter_title(line[4:].strip(), level=4)
        elif line.startswith('###'):
            pdf.chapter_title(line[3:].strip(), level=3)
        elif line.startswith('##'):
            pdf.chapter_title(line[2:].strip(), level=2)
        elif line.startswith('#'):
            pdf.chapter_title(line[1:].strip(), level=1)

        # Tables
        elif line.startswith('|'):
            # Collect table
            table_lines = []
            while i < len(lines) and lines[i].strip().startswith('|'):
                table_lines.append(lines[i].strip())
                i += 1
            i -= 1  # Back up one

            # Parse table
            if len(table_lines) >= 2:
                headers = [c.strip() for c in table_lines[0].split('|')[1:-1]]
                rows = []
                for tl in table_lines[2:]:  # Skip header separator
                    row = [c.strip() for c in tl.split('|')[1:-1]]
                    if row:
                        rows.append(row)
                if headers and rows:
                    pdf.table(headers, rows)

        # Bullet points
        elif line.startswith('- ') or line.startswith('* '):
            pdf.bullet_point(line[2:])

        # Numbered lists
        elif re.match(r'^\d+\. ', line):
            text = re.sub(r'^\d+\. ', '', line)
            pdf.bullet_point(text)

        # Bold text lines (like **Key Finding:**)
        elif line.startswith('**') and '**' in line[2:]:
            # Remove markdown bold
            clean = clean_unicode(line.replace('**', ''))
            pdf.set_x(10)
            pdf.set_font('Helvetica', 'B', 10)
            pdf.set_text_color(51, 51, 51)
            pdf.multi_cell(0, 5, clean)
            pdf.ln(2)

        # Blockquotes
        elif line.startswith('>'):
            text = clean_unicode(line[1:].strip())
            pdf.set_x(10)
            pdf.set_font('Helvetica', 'I', 10)
            pdf.set_text_color(102, 102, 102)
            pdf.multi_cell(0, 5, text)
            pdf.ln(2)

        # Regular text
        else:
            # Clean markdown formatting
            clean = re.sub(r'\*\*([^*]+)\*\*', r'\1', line)  # bold
            clean = re.sub(r'\*([^*]+)\*', r'\1', clean)  # italic
            clean = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', clean)  # links
            clean = re.sub(r'`([^`]+)`', r'\1', clean)  # code
            if clean:
                pdf.body_text(clean)

        i += 1

    return pdf


# Read markdown file
with open('../docs/competitor_analysis.md', 'r', encoding='utf-8') as f:
    md_content = f.read()

# Generate PDF
pdf = parse_markdown(md_content)
pdf.output('../docs/competitor_analysis.pdf')
print('PDF created: docs/competitor_analysis.pdf')
