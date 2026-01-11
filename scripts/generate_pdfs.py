#!/usr/bin/env python3
"""
Generate ROADMAP.pdf and Agenda.pdf for RISKCORE
"""

from fpdf import FPDF
from datetime import datetime, timedelta


class RiskCorePDF(FPDF):
    """Custom PDF class with RISKCORE styling."""

    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=15)

    def header(self):
        self.set_font('Helvetica', 'B', 10)
        self.set_text_color(100, 100, 100)
        self.cell(0, 10, 'RISKCORE', align='L')
        self.cell(0, 10, datetime.now().strftime('%Y-%m-%d'), align='R', new_x='LMARGIN', new_y='NEXT')
        self.line(10, 20, 200, 20)
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Page {self.page_no()}', align='C')

    def title_section(self, title):
        self.set_font('Helvetica', 'B', 24)
        self.set_text_color(0, 0, 0)
        self.cell(0, 15, title, new_x='LMARGIN', new_y='NEXT')
        self.ln(5)

    def subtitle(self, text):
        self.set_font('Helvetica', 'B', 14)
        self.set_text_color(50, 50, 50)
        self.cell(0, 10, text, new_x='LMARGIN', new_y='NEXT')
        self.ln(2)

    def section_header(self, text):
        self.set_font('Helvetica', 'B', 12)
        self.set_text_color(0, 100, 150)
        self.cell(0, 8, text, new_x='LMARGIN', new_y='NEXT')
        self.ln(2)

    def body_text(self, text):
        self.set_font('Helvetica', '', 10)
        self.set_text_color(0, 0, 0)
        self.multi_cell(0, 6, text)
        self.ln(2)

    def bullet_item(self, text, checked=False, indent=10):
        self.set_font('Helvetica', '', 10)
        self.set_text_color(0, 0, 0)
        marker = "[x]" if checked else "[ ]"
        self.set_x(indent + 10)
        self.multi_cell(0, 6, f"{marker} {text}")

    def status_badge(self, status):
        """Add a colored status badge."""
        colors = {
            'COMPLETE': (34, 139, 34),      # Green
            'IN PROGRESS': (255, 165, 0),   # Orange
            'NOT STARTED': (169, 169, 169), # Gray
        }
        color = colors.get(status, (0, 0, 0))
        self.set_fill_color(*color)
        self.set_text_color(255, 255, 255)
        self.set_font('Helvetica', 'B', 9)
        self.cell(35, 6, status, fill=True, align='C')
        self.set_text_color(0, 0, 0)

    def table_row(self, cells, widths, header=False):
        self.set_font('Helvetica', 'B' if header else '', 9)
        if header:
            self.set_fill_color(240, 240, 240)
        for i, (cell, width) in enumerate(zip(cells, widths)):
            self.cell(width, 7, str(cell), border=1, fill=header, align='C' if i > 0 else 'L')
        self.ln()


def generate_roadmap_pdf():
    """Generate the ROADMAP.pdf showing current progress."""
    pdf = RiskCorePDF()
    pdf.add_page()

    # Title
    pdf.title_section('RISKCORE Development Roadmap')
    pdf.body_text('Multi-manager risk aggregation platform - MVP Development Progress')
    pdf.ln(5)

    # Quick Status Table
    pdf.section_header('Overall Progress')
    pdf.ln(2)

    widths = [30, 50, 35, 75]
    pdf.table_row(['Week', 'Phase', 'Status', 'Summary'], widths, header=True)

    status_data = [
        ('1', 'Foundation', 'COMPLETE', 'Database, mock data, OpenFIGI, validation'),
        ('2', 'Data Ingestion', 'NOT STARTED', 'Position/trade API, FIX, CSV upload'),
        ('3', 'Risk Engine', 'NOT STARTED', 'Riskfolio-Lib, VaR, exposures'),
        ('4', 'Aggregation', 'NOT STARTED', 'Cross-PM netting, overlap detection'),
        ('5', 'Dashboard', 'NOT STARTED', 'React + Tailwind, real-time'),
        ('6', 'AI + Polish', 'NOT STARTED', 'Claude integration, documentation'),
    ]

    for row in status_data:
        pdf.table_row(row, widths)

    pdf.ln(10)

    # Week 1 - Complete
    pdf.section_header('Week 1: Foundation - COMPLETE')
    pdf.ln(2)

    pdf.set_font('Helvetica', 'B', 10)
    pdf.cell(0, 6, 'Milestones Achieved:', new_x='LMARGIN', new_y='NEXT')

    week1_milestones = [
        ('Database schema design (34 tables with RLS)', True),
        ('Schema improvements (convexity, pm_id, validation tables)', True),
        ('Mock data generator (realistic multi-PM hedge fund)', True),
        ('OpenFIGI integration (custom API v3 client)', True),
        ('Security master service (FIGI resolution + DB)', True),
        ('Data validation pipeline (11 rules, 5 rule types)', True),
        ('CI/CD workflow (GitHub Actions)', True),
    ]

    for item, checked in week1_milestones:
        pdf.bullet_item(item, checked)

    pdf.ln(5)
    pdf.set_font('Helvetica', 'B', 10)
    pdf.cell(0, 6, 'Artifacts Created:', new_x='LMARGIN', new_y='NEXT')
    pdf.set_font('Helvetica', '', 9)

    artifacts = [
        'backend/services/openfigi.py - OpenFIGI API client',
        'backend/services/security_master.py - Security resolution',
        'backend/services/validation.py - Data validation pipeline',
        'scripts/generate_mock_data.py - Test data generator',
        'scripts/test_validation.py - Validation tests',
        'supabase/migrations/*.sql - Database schema',
    ]

    for artifact in artifacts:
        pdf.set_x(20)
        pdf.cell(0, 5, f"- {artifact}", new_x='LMARGIN', new_y='NEXT')

    pdf.ln(10)

    # Weeks 2-6 Overview
    pdf.section_header('Upcoming: Weeks 2-6')
    pdf.ln(2)

    upcoming = [
        ('Week 2', 'Data Ingestion', 'FastAPI endpoints, FIX parser, CSV/Excel upload'),
        ('Week 3', 'Risk Engine', 'VaR, CVaR, exposures, Greeks calculations'),
        ('Week 4', 'Aggregation', 'Cross-PM netting, overlap detection, firm rollup'),
        ('Week 5', 'Dashboard', 'React UI, real-time updates, charts'),
        ('Week 6', 'AI Layer', 'Claude integration, natural language queries'),
    ]

    for week, phase, desc in upcoming:
        pdf.set_font('Helvetica', 'B', 10)
        pdf.cell(25, 6, week)
        pdf.set_font('Helvetica', '', 10)
        pdf.cell(0, 6, f"{phase}: {desc}", new_x='LMARGIN', new_y='NEXT')

    pdf.ln(10)

    # Success Metrics
    pdf.section_header('MVP Success Metrics')
    pdf.ln(2)

    metrics = [
        ('Upload 3 formats (CSV, Excel, FIX)', False),
        ('Firm-wide exposure view in dashboard', False),
        ('Cross-PM overlap detection working', False),
        ('Natural language query: "What\'s our net tech exposure?"', False),
        ('10-minute demo ready', False),
        ('Documentation complete', False),
    ]

    for metric, done in metrics:
        pdf.bullet_item(metric, done)

    # Save
    output_path = 'C:/Users/massi/Desktop/RISKCORE/ROADMAP.pdf'
    pdf.output(output_path)
    print(f"Generated: {output_path}")
    return output_path


def generate_agenda_pdf():
    """Generate the Agenda.pdf for Week 2."""
    pdf = RiskCorePDF()
    pdf.add_page()

    # Calculate dates for next week
    today = datetime.now()
    # Find next Monday
    days_until_monday = (7 - today.weekday()) % 7
    if days_until_monday == 0:
        days_until_monday = 7
    monday = today + timedelta(days=days_until_monday)

    # Title
    pdf.title_section('RISKCORE Week 2 Agenda')
    pdf.subtitle('Data Ingestion Layer')
    pdf.body_text(f"Week of {monday.strftime('%B %d, %Y')} - {(monday + timedelta(days=4)).strftime('%B %d, %Y')}")
    pdf.ln(5)

    # Goal
    pdf.section_header('Week Goal')
    pdf.body_text('Build the complete data ingestion layer: REST API endpoints for positions and trades, '
                  'file upload handling (CSV/Excel), and FIX protocol message parsing.')
    pdf.ln(5)

    # Daily breakdown
    days = [
        {
            'day': 'Monday',
            'date': monday,
            'focus': 'FastAPI Foundation',
            'tasks': [
                'Set up FastAPI application structure',
                'Create backend/main.py entry point',
                'Configure CORS, middleware, error handling',
                'Set up database connection pool',
                'Create Pydantic models for Position and Trade',
                'Write requirements.txt with all dependencies',
            ],
            'deliverable': 'Running FastAPI app at localhost:8000 with /docs',
        },
        {
            'day': 'Tuesday',
            'date': monday + timedelta(days=1),
            'focus': 'Position API',
            'tasks': [
                'Create POST /api/v1/positions endpoint',
                'Create GET /api/v1/positions endpoint (with filters)',
                'Integrate validation pipeline for input validation',
                'Integrate security master for identifier resolution',
                'Add position to database with proper tenant isolation',
                'Write unit tests for position endpoints',
            ],
            'deliverable': 'Position CRUD working with validation',
        },
        {
            'day': 'Wednesday',
            'date': monday + timedelta(days=2),
            'focus': 'Trade API + P&L',
            'tasks': [
                'Create POST /api/v1/trades endpoint',
                'Create GET /api/v1/trades endpoint (with filters)',
                'Implement P&L calculation service',
                'Calculate: (quantity x current_price) - (quantity x avg_cost)',
                'Update position from trade (quantity, avg_cost)',
                'Write unit tests for trade endpoints',
            ],
            'deliverable': 'Trade ingestion with automatic P&L calculation',
        },
        {
            'day': 'Thursday',
            'date': monday + timedelta(days=3),
            'focus': 'File Upload',
            'tasks': [
                'Create POST /api/v1/upload endpoint',
                'Implement CSV parser with column auto-detection',
                'Implement Excel parser (.xlsx, .xls support)',
                'Create upload preview response (first 10 rows)',
                'Create POST /api/v1/upload/confirm for batch import',
                'Write unit tests for file parsing',
            ],
            'deliverable': 'CSV/Excel upload with preview and batch import',
        },
        {
            'day': 'Friday',
            'date': monday + timedelta(days=4),
            'focus': 'FIX Protocol + Testing',
            'tasks': [
                'Implement FIX parser using simplefix library',
                'Parse ExecutionReport (tag 35=8) messages',
                'Parse PositionReport (tag 35=AP) messages',
                'Create POST /api/v1/fix endpoint',
                'Integration tests for all endpoints',
                'Documentation and code cleanup',
            ],
            'deliverable': 'Complete data ingestion layer ready for Week 3',
        },
    ]

    for day_info in days:
        pdf.section_header(f"{day_info['day']} - {day_info['date'].strftime('%b %d')}: {day_info['focus']}")
        pdf.ln(2)

        pdf.set_font('Helvetica', 'B', 10)
        pdf.cell(0, 6, 'Tasks:', new_x='LMARGIN', new_y='NEXT')

        for task in day_info['tasks']:
            pdf.bullet_item(task, checked=False)

        pdf.ln(2)
        pdf.set_font('Helvetica', 'I', 9)
        pdf.set_text_color(0, 100, 0)
        pdf.cell(0, 6, f"Deliverable: {day_info['deliverable']}", new_x='LMARGIN', new_y='NEXT')
        pdf.set_text_color(0, 0, 0)
        pdf.ln(5)

    # Add new page for technical details
    pdf.add_page()
    pdf.section_header('Technical Specifications')
    pdf.ln(3)

    # API Endpoints
    pdf.set_font('Helvetica', 'B', 11)
    pdf.cell(0, 7, 'API Endpoints to Build:', new_x='LMARGIN', new_y='NEXT')
    pdf.ln(2)

    endpoints = [
        ('POST', '/api/v1/positions', 'Create new position'),
        ('GET', '/api/v1/positions', 'List positions (filterable)'),
        ('GET', '/api/v1/positions/{id}', 'Get single position'),
        ('POST', '/api/v1/trades', 'Create new trade'),
        ('GET', '/api/v1/trades', 'List trades (filterable)'),
        ('POST', '/api/v1/upload', 'Upload file, get preview'),
        ('POST', '/api/v1/upload/confirm', 'Confirm batch import'),
        ('POST', '/api/v1/fix', 'Parse FIX message'),
    ]

    widths = [20, 55, 80]
    pdf.table_row(['Method', 'Endpoint', 'Description'], widths, header=True)
    for endpoint in endpoints:
        pdf.table_row(endpoint, widths)

    pdf.ln(8)

    # Files to create
    pdf.set_font('Helvetica', 'B', 11)
    pdf.cell(0, 7, 'Files to Create:', new_x='LMARGIN', new_y='NEXT')
    pdf.ln(2)

    files = [
        ('backend/main.py', 'FastAPI application entry point'),
        ('backend/api/__init__.py', 'API router initialization'),
        ('backend/api/positions.py', 'Position endpoints'),
        ('backend/api/trades.py', 'Trade endpoints'),
        ('backend/api/upload.py', 'File upload endpoint'),
        ('backend/api/fix.py', 'FIX message endpoint'),
        ('backend/models/position.py', 'Position Pydantic models'),
        ('backend/models/trade.py', 'Trade Pydantic models'),
        ('backend/services/file_parser.py', 'CSV/Excel parser'),
        ('backend/services/fix_parser.py', 'FIX message parser'),
        ('backend/services/pnl.py', 'P&L calculation'),
        ('requirements.txt', 'Python dependencies'),
    ]

    widths = [70, 85]
    pdf.table_row(['File', 'Purpose'], widths, header=True)
    for file_info in files:
        pdf.table_row(file_info, widths)

    pdf.ln(8)

    # Dependencies
    pdf.set_font('Helvetica', 'B', 11)
    pdf.cell(0, 7, 'Dependencies from Week 1:', new_x='LMARGIN', new_y='NEXT')
    pdf.set_font('Helvetica', '', 10)
    pdf.ln(2)

    deps = [
        'validation.py - For validating incoming position/trade data',
        'security_master.py - For resolving security identifiers',
        'openfigi.py - For looking up unknown securities',
        'Database schema - positions, trades, securities tables',
    ]

    for dep in deps:
        pdf.set_x(15)
        pdf.cell(0, 5, f"- {dep}", new_x='LMARGIN', new_y='NEXT')

    pdf.ln(8)

    # Acceptance Criteria
    pdf.section_header('Week 2 Acceptance Criteria')
    pdf.ln(2)

    criteria = [
        'POST /api/v1/positions accepts valid data, returns validation errors for bad data',
        'POST /api/v1/trades creates trade and updates position quantities',
        'P&L calculates correctly: (qty x price) - (qty x avg_cost)',
        'CSV upload auto-detects columns (ticker, quantity, price)',
        'Excel upload handles .xlsx and .xls formats',
        'FIX ExecutionReport (35=8) parses correctly',
        'FIX PositionReport (35=AP) parses correctly',
        'All endpoints return proper HTTP status codes',
        'OpenAPI docs available at /docs',
        '>80% test coverage on new code',
    ]

    for criterion in criteria:
        pdf.bullet_item(criterion, checked=False)

    # Save
    output_path = 'C:/Users/massi/Desktop/RISKCORE/Agenda.pdf'
    pdf.output(output_path)
    print(f"Generated: {output_path}")
    return output_path


if __name__ == '__main__':
    print("Generating RISKCORE PDFs...")
    print()
    generate_roadmap_pdf()
    generate_agenda_pdf()
    print()
    print("Done!")
