"""
Create Word documents for SOC 2 and GDPR/Privacy compliance findings
"""
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.table import WD_TABLE_ALIGNMENT


def create_soc2_document():
    """Create SOC 2 findings and recommendations document"""
    doc = Document()

    # Title
    title = doc.add_heading('RISKCORE SOC 2 Compliance', 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER

    # Subtitle
    subtitle = doc.add_paragraph('Findings, Recommendations, and Implementation Strategy')
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER

    doc.add_paragraph()

    # Executive Summary
    doc.add_heading('Executive Summary', level=1)
    doc.add_paragraph(
        "This document outlines RISKCORE's approach to SOC 2 compliance. As a self-hosted, "
        "on-premises risk analytics platform, RISKCORE has a unique compliance posture that "
        "differs significantly from traditional cloud SaaS providers."
    )

    doc.add_paragraph()
    summary = doc.add_paragraph()
    summary.add_run('Key Strategic Decision: ').bold = True
    summary.add_run(
        "Build RISKCORE following all SOC 2 Trust Services Criteria from day 1, "
        "but pursue formal certification only after achieving sufficient revenue ($500K+ ARR) "
        "to justify the $55K-90K annual certification cost."
    )

    # What is SOC 2
    doc.add_heading('What is SOC 2?', level=1)
    doc.add_paragraph(
        "SOC 2 (System and Organization Controls 2) is an auditing framework developed by the "
        "American Institute of CPAs (AICPA) that evaluates how organizations manage customer data "
        "based on five Trust Services Criteria."
    )

    # Trust Services Criteria Table
    doc.add_heading('The 5 Trust Services Criteria', level=2)
    table = doc.add_table(rows=6, cols=3)
    table.style = 'Table Grid'

    # Header row
    headers = ['Criteria', 'Description', 'Required for RISKCORE?']
    for i, header in enumerate(headers):
        cell = table.rows[0].cells[i]
        cell.text = header
        cell.paragraphs[0].runs[0].bold = True

    # Data rows
    data = [
        ('Security', 'Protection against unauthorized access', 'YES (Required)'),
        ('Availability', 'System availability for operation', 'YES (Enterprise SLA)'),
        ('Processing Integrity', 'System processing is complete, accurate, timely', 'YES (Risk calculations)'),
        ('Confidentiality', 'Information designated confidential is protected', 'YES (Position/trade data)'),
        ('Privacy', 'Personal information collection, use, retention', 'Optional (B2B focus)')
    ]

    for row_idx, row_data in enumerate(data, start=1):
        for col_idx, value in enumerate(row_data):
            table.rows[row_idx].cells[col_idx].text = value

    doc.add_paragraph()

    # Key Finding 1
    doc.add_heading('Key Finding #1: SOC 2 Requires External Audit', level=1)
    finding1 = doc.add_paragraph()
    finding1.add_run('You cannot self-certify SOC 2. ').bold = True
    finding1.add_run(
        "Unlike GDPR compliance (which is a set of regulations you follow), SOC 2 requires "
        "an independent audit by a licensed CPA firm. Without an official audit report, "
        'you cannot claim "SOC 2 compliant" status.'
    )

    doc.add_paragraph()
    doc.add_paragraph('The audit process:')
    bullets = [
        'AICPA sets the standards',
        'Licensed CPA firms perform audits (Schellman, A-LIGN, Coalfire, etc.)',
        'Audits cost $15K-50K+ depending on scope',
        'Type I: Point-in-time assessment of control design',
        'Type II: Operating effectiveness over 6+ months (more valuable)'
    ]
    for bullet in bullets:
        doc.add_paragraph(bullet, style='List Bullet')

    # Key Finding 2
    doc.add_heading("Key Finding #2: RISKCORE's Self-Hosted Model is an Advantage", level=1)
    doc.add_paragraph(
        "RISKCORE's on-premises architecture fundamentally changes our compliance posture:"
    )

    table2 = doc.add_table(rows=5, cols=2)
    table2.style = 'Table Grid'
    advantages = [
        ('Data Location', "Client's infrastructure - not our servers"),
        ('Data Ownership', "Client owns all data - we're not a data controller"),
        ('Network Access', 'Air-gapped option available - reduced attack surface'),
        ('Data Transmission', 'No data leaves client network - no cross-border issues'),
        ('RISKCORE Access', 'Zero access to client position/trade data')
    ]
    for row_idx, (aspect, detail) in enumerate(advantages):
        table2.rows[row_idx].cells[0].text = aspect
        table2.rows[row_idx].cells[1].text = detail

    doc.add_paragraph()
    doc.add_paragraph(
        "This architecture means RISKCORE faces fewer compliance burdens than cloud SaaS providers. "
        "Clients are responsible for their own data security, and we provide the tools to help them."
    )

    # Cost Analysis
    doc.add_heading('Cost Analysis: SOC 2 Certification', level=1)

    table3 = doc.add_table(rows=10, cols=3)
    table3.style = 'Table Grid'
    costs_header = ['Item', 'Low Estimate', 'High Estimate']
    for i, h in enumerate(costs_header):
        table3.rows[0].cells[i].text = h
        table3.rows[0].cells[i].paragraphs[0].runs[0].bold = True

    costs = [
        ('Type I Audit', '$15,000', '$25,000'),
        ('Type II Audit', '$20,000', '$35,000'),
        ('SIEM/Logging Tools', '$5,000', '$10,000'),
        ('Vulnerability Scanner', '$3,000', '$5,000'),
        ('MFA Solution', '$2,000', '$5,000'),
        ('GRC Platform (Vanta/Drata)', '$8,000', '$15,000'),
        ('Security Training', '$1,000', '$2,000'),
        ('Penetration Testing', '$5,000', '$10,000'),
        ('TOTAL YEAR 1', '$59,000', '$107,000')
    ]

    for row_idx, row_data in enumerate(costs, start=1):
        for col_idx, value in enumerate(row_data):
            cell = table3.rows[row_idx].cells[col_idx]
            cell.text = value
            if row_idx == len(costs):
                cell.paragraphs[0].runs[0].bold = True

    # Recommendations
    doc.add_heading('Recommendations', level=1)

    doc.add_heading('1. Build Compliant from Day 1', level=2)
    doc.add_paragraph(
        "Implement all SOC 2 controls in RISKCORE's architecture even without formal certification. "
        "This approach:"
    )
    rec1_bullets = [
        'Creates a strong security foundation',
        'Makes future certification easier',
        'Allows us to say "built following SOC 2 principles"',
        'Provides real security benefits to customers'
    ]
    for bullet in rec1_bullets:
        doc.add_paragraph(bullet, style='List Bullet')

    doc.add_heading('2. Certify After Revenue Threshold', level=2)
    doc.add_paragraph(
        'Pursue formal SOC 2 certification when ARR exceeds $500K. At this point:'
    )
    rec2_bullets = [
        'Revenue can absorb $55K-90K annual cost',
        'Enterprise customers requiring SOC 2 reports are more likely',
        'Certification becomes a competitive advantage'
    ]
    for bullet in rec2_bullets:
        doc.add_paragraph(bullet, style='List Bullet')

    doc.add_heading('3. Tier-Specific Security Marketing', level=2)
    doc.add_paragraph(
        'Update pricing pages and documentation to clearly show security features by tier:'
    )
    rec3_bullets = [
        'Free: Enterprise-grade security foundations (RBAC, RLS, encryption)',
        'Pro: + MFA, extended audit logs, security questionnaire',
        'Enterprise: + SSO/SAML, penetration test report, SOC 2 report (when available)'
    ]
    for bullet in rec3_bullets:
        doc.add_paragraph(bullet, style='List Bullet')

    doc.add_heading('4. Use GRC Platform for Efficiency', level=2)
    doc.add_paragraph(
        'When ready for certification, use a GRC platform like Vanta or Drata ($10K/year) to:'
    )
    rec4_bullets = [
        'Automate evidence collection',
        'Continuously monitor compliance',
        'Streamline audit process',
        'Reduce manual documentation effort'
    ]
    for bullet in rec4_bullets:
        doc.add_paragraph(bullet, style='List Bullet')

    # Implementation Timeline
    doc.add_heading('Implementation Timeline', level=1)

    timeline_table = doc.add_table(rows=5, cols=3)
    timeline_table.style = 'Table Grid'
    timeline_header = ['Phase', 'Timing', 'Activities']
    for i, h in enumerate(timeline_header):
        timeline_table.rows[0].cells[i].text = h
        timeline_table.rows[0].cells[i].paragraphs[0].runs[0].bold = True

    timeline_data = [
        ('Foundation', 'Now (MVP)', 'Build with SOC 2 controls, document security'),
        ('Documentation', '$0-100K ARR', 'Security whitepaper, DPA template, IR plan'),
        ('Validation', '$100K-500K ARR', 'Penetration test, SOC 2 readiness assessment'),
        ('Certification', '$500K+ ARR', 'SOC 2 Type I, then Type II audit')
    ]

    for row_idx, row_data in enumerate(timeline_data, start=1):
        for col_idx, value in enumerate(row_data):
            timeline_table.rows[row_idx].cells[col_idx].text = value

    # Conclusion
    doc.add_heading('Conclusion', level=1)
    doc.add_paragraph(
        "SOC 2 certification is valuable but expensive. For RISKCORE, the optimal strategy is to "
        "build with all SOC 2 principles from day 1 while deferring formal certification until "
        "revenue justifies the cost. Our self-hosted architecture provides inherent security advantages "
        "that we should highlight in marketing materials."
    )

    doc.add_paragraph()
    action = doc.add_paragraph()
    action.add_run('Immediate Action Items:').bold = True

    action_items = [
        'Implement MFA for Pro/Enterprise tiers',
        'Create security whitepaper for website',
        'Update pricing page with security feature matrix',
        'Draft incident response plan',
        'Prepare security questionnaire responses'
    ]
    for item in action_items:
        doc.add_paragraph(item, style='List Bullet')

    # Save
    doc.save('docs/SOC2_Findings_and_Recommendations.docx')
    print('SOC 2 document created: docs/SOC2_Findings_and_Recommendations.docx')


def create_gdpr_privacy_document():
    """Create GDPR and Privacy findings document"""
    doc = Document()

    # Title
    title = doc.add_heading('RISKCORE GDPR & Privacy Compliance', 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER

    subtitle = doc.add_paragraph('Findings, Analysis, and Recommendations for Self-Hosted Software')
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER

    doc.add_paragraph()

    # Executive Summary
    doc.add_heading('Executive Summary', level=1)

    key_finding = doc.add_paragraph()
    key_finding.add_run('Key Finding: ').bold = True
    key_finding.add_run(
        "RISKCORE's self-hosted, on-premises architecture fundamentally changes GDPR applicability. "
        "Since we never store or access client position/trade data, we face minimal GDPR obligations "
        "compared to cloud SaaS providers."
    )

    doc.add_paragraph()
    doc.add_paragraph(
        "This document analyzes GDPR, CCPA, and global privacy regulations as they apply to "
        "RISKCORE's unique deployment model."
    )

    # RISKCORE's Data Model
    doc.add_heading("Understanding RISKCORE's Data Model", level=1)

    doc.add_heading('What Data Does RISKCORE Process?', level=2)

    data_table = doc.add_table(rows=7, cols=4)
    data_table.style = 'Table Grid'

    headers = ['Data Type', 'Location', 'Personal Data?', 'GDPR Applies to RISKCORE?']
    for i, h in enumerate(headers):
        data_table.rows[0].cells[i].text = h
        data_table.rows[0].cells[i].paragraphs[0].runs[0].bold = True

    data_rows = [
        ('Position data', "Client's servers", 'No', 'No'),
        ('Trade records', "Client's servers", 'No', 'No'),
        ('Risk metrics', "Client's servers", 'No', 'No'),
        ('User accounts', "Client's servers", 'Yes (email, name)', 'No (client controls)'),
        ('License validation', 'Our servers', 'Yes (company info)', 'Yes'),
        ('Support tickets', 'Our systems', 'Yes (contact info)', 'Yes')
    ]

    for row_idx, row_data in enumerate(data_rows, start=1):
        for col_idx, value in enumerate(row_data):
            data_table.rows[row_idx].cells[col_idx].text = value

    doc.add_paragraph()

    # Key Finding: Not a Traditional Data Processor
    doc.add_heading('Key Finding: RISKCORE is NOT a Traditional Data Processor', level=1)

    doc.add_paragraph(
        "In traditional SaaS, the vendor is a 'Data Processor' under GDPR because they store "
        "and process client data on their servers. RISKCORE's model is different:"
    )

    doc.add_paragraph()
    doc.add_heading('Traditional SaaS Model', level=2)
    doc.add_paragraph('SaaS Vendor = Data Processor (holds client data)', style='List Bullet')
    doc.add_paragraph('Uses sub-processors (AWS, etc.)', style='List Bullet')
    doc.add_paragraph('Must comply with GDPR as processor', style='List Bullet')

    doc.add_heading('RISKCORE Model (Self-Hosted)', level=2)
    doc.add_paragraph('Client = Data Controller AND Processor (owns their data)', style='List Bullet')
    doc.add_paragraph('RISKCORE = Software Provider (no data access)', style='List Bullet')
    doc.add_paragraph('RISKCORE is NOT a data processor for client position data', style='List Bullet')

    doc.add_paragraph()
    implication = doc.add_paragraph()
    implication.add_run('Implication: ').bold = True
    implication.add_run(
        "We do NOT need a Data Processing Agreement (DPA) with clients for their position/trade data "
        "because we never process it. The client handles all GDPR obligations for their own data."
    )

    # What RISKCORE Must Do
    doc.add_heading("What RISKCORE Must Do for GDPR", level=1)

    doc.add_heading('For Our Own Systems (License, Support, Marketing)', level=2)

    our_obligations = doc.add_table(rows=7, cols=3)
    our_obligations.style = 'Table Grid'

    headers = ['Requirement', 'Implementation', 'Status']
    for i, h in enumerate(headers):
        our_obligations.rows[0].cells[i].text = h
        our_obligations.rows[0].cells[i].paragraphs[0].runs[0].bold = True

    obligations_data = [
        ('Legal basis for processing', 'Legitimate interest, contract, consent', 'Planned'),
        ('Privacy policy', 'Website, clear language', 'Planned'),
        ('Data subject rights', 'Delete account, export data', 'Planned'),
        ('Breach notification', '72-hour notification process', 'Planned'),
        ('Records of processing', 'Processing activities log', 'Planned'),
        ('DPO appointment', 'Not required (< 250 employees)', 'N/A')
    ]

    for row_idx, row_data in enumerate(obligations_data, start=1):
        for col_idx, value in enumerate(row_data):
            our_obligations.rows[row_idx].cells[col_idx].text = value

    doc.add_paragraph()

    doc.add_heading('For Client Deployments', level=2)
    doc.add_paragraph(
        "Since we don't access client data, our obligations are limited to providing tools and documentation:"
    )
    client_support = [
        'Data subject access request functionality (export)',
        'Right to erasure functionality (delete)',
        'DPIA template (if clients need it)',
        'Security documentation for their compliance',
        'Incident response template'
    ]
    for item in client_support:
        doc.add_paragraph(item, style='List Bullet')

    # Global Privacy Landscape
    doc.add_heading('Global Privacy Regulations', level=1)

    doc.add_paragraph(
        "Beyond GDPR, other privacy regulations may apply depending on client location:"
    )

    regulations_table = doc.add_table(rows=8, cols=3)
    regulations_table.style = 'Table Grid'

    headers = ['Regulation', 'Jurisdiction', 'RISKCORE Applicability']
    for i, h in enumerate(headers):
        regulations_table.rows[0].cells[i].text = h
        regulations_table.rows[0].cells[i].paragraphs[0].runs[0].bold = True

    regulations_data = [
        ('GDPR', 'EU/EEA', 'License system, support only'),
        ('CCPA/CPRA', 'California', 'If CA users use license system'),
        ('UK GDPR', 'United Kingdom', 'UK customers'),
        ('LGPD', 'Brazil', 'Brazilian customers'),
        ('POPIA', 'South Africa', 'SA customers'),
        ('PDPA', 'Singapore', 'Singapore customers'),
        ('Privacy Act', 'Australia', 'Australian customers')
    ]

    for row_idx, row_data in enumerate(regulations_data, start=1):
        for col_idx, value in enumerate(row_data):
            regulations_table.rows[row_idx].cells[col_idx].text = value

    doc.add_paragraph()

    universal = doc.add_paragraph()
    universal.add_run('Universal Principles: ').bold = True
    universal.add_run(
        "All major privacy laws share common principles: lawfulness, purpose limitation, "
        "data minimization, accuracy, storage limitation, security, and accountability. "
        "RISKCORE implements all of these."
    )

    # Financial Services Specific
    doc.add_heading('Financial Services Regulations', level=1)

    doc.add_paragraph(
        "Beyond general privacy, financial services have specific requirements:"
    )

    fin_regs = doc.add_table(rows=4, cols=3)
    fin_regs.style = 'Table Grid'

    headers = ['Regulation', 'Requirement', 'RISKCORE Support']
    for i, h in enumerate(headers):
        fin_regs.rows[0].cells[i].text = h
        fin_regs.rows[0].cells[i].paragraphs[0].runs[0].bold = True

    fin_data = [
        ('SEC/FINRA', 'Books & records retention', '5-year position history, audit logs'),
        ('MiFID II', 'Trade reporting, best execution', 'Export functionality, trade capture'),
        ('AIFMD', 'Risk management, disclosure', 'VaR, CVaR, exposure reporting')
    ]

    for row_idx, row_data in enumerate(fin_data, start=1):
        for col_idx, value in enumerate(row_data):
            fin_regs.rows[row_idx].cells[col_idx].text = value

    # Recommendations
    doc.add_heading('Recommendations', level=1)

    doc.add_heading('1. Emphasize Self-Hosted Advantage', level=2)
    doc.add_paragraph(
        "Our self-hosted model is a significant privacy advantage. Marketing should emphasize:"
    )
    marketing_points = [
        "Your data never leaves your network",
        "RISKCORE has zero access to your positions",
        "You control your own GDPR compliance",
        "Air-gapped deployment available",
        "No cross-border data transfer concerns"
    ]
    for point in marketing_points:
        doc.add_paragraph(point, style='List Bullet')

    doc.add_heading('2. Create Privacy Documentation', level=2)
    doc.add_paragraph('Develop the following documents:')
    docs_needed = [
        'Privacy policy for RISKCORE website/license system',
        'Data processing information for marketing',
        'Security whitepaper for client compliance teams',
        'DPIA template for client use',
        'Data subject request procedures'
    ]
    for d in docs_needed:
        doc.add_paragraph(d, style='List Bullet')

    doc.add_heading('3. Implement Privacy Features', level=2)
    doc.add_paragraph('Build privacy-supporting features into RISKCORE:')
    features = [
        'User data export (for DSAR compliance)',
        'User data deletion (for right to erasure)',
        'Audit logging (for accountability)',
        'Consent management (for terms acceptance)',
        'Data retention controls (configurable for Enterprise)'
    ]
    for f in features:
        doc.add_paragraph(f, style='List Bullet')

    doc.add_heading('4. DPA Only When Needed', level=2)
    doc.add_paragraph(
        "Only provide a Data Processing Agreement in scenarios where RISKCORE actually "
        "accesses client data (e.g., support/debugging sessions). For standard self-hosted "
        "deployments, a DPA is not required."
    )

    # Conclusion
    doc.add_heading('Conclusion', level=1)
    doc.add_paragraph(
        "RISKCORE's self-hosted architecture provides significant privacy advantages. "
        "Unlike cloud SaaS providers, we do not store or access client position/trade data, "
        "which means our GDPR obligations are minimal. Clients are responsible for their "
        "own data protection compliance, and we provide the tools to support them."
    )

    doc.add_paragraph()
    actions = doc.add_paragraph()
    actions.add_run('Immediate Action Items:').bold = True

    action_items = [
        'Draft privacy policy for website',
        'Create security whitepaper highlighting self-hosted benefits',
        'Implement user data export functionality',
        'Implement user account deletion',
        'Document data retention policies'
    ]
    for item in action_items:
        doc.add_paragraph(item, style='List Bullet')

    # Save
    doc.save('docs/GDPR_Privacy_Findings_and_Recommendations.docx')
    print('GDPR/Privacy document created: docs/GDPR_Privacy_Findings_and_Recommendations.docx')


if __name__ == '__main__':
    create_soc2_document()
    create_gdpr_privacy_document()
    print('Both documents created successfully!')
