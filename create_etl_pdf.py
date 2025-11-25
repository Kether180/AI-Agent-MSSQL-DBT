"""
Create ETL vs dbt Benefits PDF
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT

def create_etl_pdf():
    """Create PDF document explaining ETL vs dbt benefits"""

    # Create PDF
    doc = SimpleDocTemplate(
        "ETL_VS_DBT_BENEFITS.pdf",
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=18,
    )

    elements = []
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Center', alignment=TA_CENTER))
    styles.add(ParagraphStyle(name='Justify', alignment=TA_JUSTIFY, fontSize=11, leading=14))

    # Title
    title = '<font size=20><b>Why Transition from Legacy ETL to dbt?</b></font>'
    elements.append(Paragraph(title, styles['Center']))
    elements.append(Spacer(1, 0.3 * inch))

    subtitle = '<font size=14><i>The Complete Business and Technical Case</i></font>'
    elements.append(Paragraph(subtitle, styles['Center']))
    elements.append(Spacer(1, 0.4 * inch))

    # Executive Summary
    elements.append(Paragraph('<b><font size=16>Executive Summary</font></b>', styles['Heading1']))
    elements.append(Spacer(1, 0.1 * inch))

    exec_summary = """
    Organizations are rapidly migrating from traditional ETL tools (SSIS, Informatica, Talend) to modern
    data transformation frameworks like <b>dbt (data build tool)</b>. This transition delivers:
    """
    elements.append(Paragraph(exec_summary, styles['Justify']))
    elements.append(Spacer(1, 0.1 * inch))

    benefits_list = [
        '<b>65% cost reduction</b> - Save $2.5M+ over 5 years',
        '<b>10x faster development</b> - Deploy changes in days, not weeks',
        '<b>Better data quality</b> - Automated testing catches errors before production',
        '<b>Version control</b> - Git-based workflow like modern software development',
        '<b>Self-service analytics</b> - Analysts can build transformations themselves'
    ]

    for benefit in benefits_list:
        elements.append(Paragraph(f'• {benefit}', styles['Normal']))
    elements.append(Spacer(1, 0.3 * inch))

    # The Problem
    elements.append(PageBreak())
    elements.append(Paragraph('<b><font size=16>The Problem with Legacy ETL</font></b>', styles['Heading1']))
    elements.append(Spacer(1, 0.2 * inch))

    # Architecture comparison
    legacy_text = '<b>Traditional ETL Architecture:</b>'
    elements.append(Paragraph(legacy_text, styles['Normal']))
    elements.append(Spacer(1, 0.1 * inch))

    arch_text = """
    Source Database → ETL Tool (SSIS/Informatica) → Data Warehouse → BI Tools
    """
    elements.append(Paragraph(arch_text, styles['Normal']))
    elements.append(Spacer(1, 0.2 * inch))

    # Pain points
    elements.append(Paragraph('<b>Critical Pain Points:</b>', styles['Heading2']))
    elements.append(Spacer(1, 0.1 * inch))

    pain_points = [
        ('<b>Not Version Controlled</b>', 'ETL jobs are GUI-based binary files. No Git, no code review, no audit trail.'),
        ('<b>Not Testable</b>', 'Manual testing only. Bugs discovered in production. No automated validation.'),
        ('<b>Expensive</b>', 'License costs: $50k-$500k/year. Plus specialized training and support.'),
        ('<b>Slow Development</b>', 'Drag-and-drop is tedious. Changes take weeks. Hard to reuse logic.'),
        ('<b>Hard to Debug</b>', 'Black box transformations. Difficult to troubleshoot. No local testing.'),
        ('<b>Specialized Knowledge</b>', 'Only ETL developers can work on it. Creates bottlenecks.')
    ]

    for title, description in pain_points:
        elements.append(Paragraph(f'{title}', styles['Normal']))
        elements.append(Paragraph(f'{description}', styles['BodyText']))
        elements.append(Spacer(1, 0.1 * inch))

    # The Solution
    elements.append(PageBreak())
    elements.append(Paragraph('<b><font size=16>The dbt Solution</font></b>', styles['Heading1']))
    elements.append(Spacer(1, 0.2 * inch))

    modern_text = '<b>Modern Data Stack with dbt:</b>'
    elements.append(Paragraph(modern_text, styles['Normal']))
    elements.append(Spacer(1, 0.1 * inch))

    modern_arch = """
    Source DB → Modern Warehouse (Snowflake/BigQuery) → dbt (Transformations) → BI Tools
    """
    elements.append(Paragraph(modern_arch, styles['Normal']))
    elements.append(Spacer(1, 0.3 * inch))

    # Key benefits
    elements.append(Paragraph('<b><font size=14>Key Benefits</font></b>', styles['Heading2']))
    elements.append(Spacer(1, 0.2 * inch))

    # Create benefits table
    benefits_data = [
        ['Feature', 'Legacy ETL', 'dbt'],
        ['Version Control', 'No (binary files)', 'Yes (Git)'],
        ['Testing', 'Manual only', 'Automated'],
        ['Cost/Year', '$200k+', '$0-12k'],
        ['Development Speed', 'Weeks', 'Days'],
        ['Skill Required', 'Specialized', 'SQL only'],
        ['Documentation', 'Manual', 'Auto-generated'],
        ['CI/CD', 'No', 'Yes'],
        ['Team Collaboration', 'Limited', 'Everyone']
    ]

    benefits_table = Table(benefits_data, colWidths=[2 * inch, 2 * inch, 2 * inch])
    benefits_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
    ]))
    elements.append(benefits_table)
    elements.append(Spacer(1, 0.3 * inch))

    # Cost comparison
    elements.append(PageBreak())
    elements.append(Paragraph('<b><font size=16>Cost Comparison (5 Years)</font></b>', styles['Heading1']))
    elements.append(Spacer(1, 0.2 * inch))

    # Legacy costs
    elements.append(Paragraph('<b>Legacy ETL Stack:</b>', styles['Heading2']))
    elements.append(Spacer(1, 0.1 * inch))

    legacy_costs = [
        ['Item', 'Annual Cost', '5-Year Total'],
        ['Informatica/SSIS Licenses', '$200,000', '$1,000,000'],
        ['SQL Server Licenses', '$50,000', '$250,000'],
        ['ETL Developers (5 FTE)', '$500,000', '$2,500,000'],
        ['Training & Support', '$25,000', '$125,000'],
        ['TOTAL', '$775,000/year', '$3,875,000']
    ]

    legacy_table = Table(legacy_costs, colWidths=[2.2 * inch, 1.8 * inch, 1.8 * inch])
    legacy_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('BACKGROUND', (0, -1), (-1, -1), colors.red),
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(legacy_table)
    elements.append(Spacer(1, 0.3 * inch))

    # Modern costs
    elements.append(Paragraph('<b>Modern dbt Stack:</b>', styles['Heading2']))
    elements.append(Spacer(1, 0.1 * inch))

    modern_costs = [
        ['Item', 'Annual Cost', '5-Year Total'],
        ['dbt Cloud', '$12,000', '$60,000'],
        ['Snowflake (pay-per-use)', '$50,000', '$250,000'],
        ['Analytics Engineers (2 FTE)', '$200,000', '$1,000,000'],
        ['Training', '$5,000', '$25,000'],
        ['TOTAL', '$267,000/year', '$1,335,000']
    ]

    modern_table = Table(modern_costs, colWidths=[2.2 * inch, 1.8 * inch, 1.8 * inch])
    modern_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('BACKGROUND', (0, -1), (-1, -1), colors.green),
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(modern_table)
    elements.append(Spacer(1, 0.3 * inch))

    # Savings
    savings_text = '<font size=14 color="green"><b>SAVINGS: $2,540,000 over 5 years (65% reduction)</b></font>'
    elements.append(Paragraph(savings_text, styles['Center']))
    elements.append(Spacer(1, 0.3 * inch))

    # Real-world example
    elements.append(PageBreak())
    elements.append(Paragraph('<b><font size=16>Real-World Example</font></b>', styles['Heading1']))
    elements.append(Spacer(1, 0.2 * inch))

    elements.append(Paragraph('<b>Before (Legacy SSIS):</b>', styles['Heading2']))
    before_steps = [
        '1. Data analyst requests new metric',
        '2. Creates ticket for ETL team',
        '3. Waits 2-3 weeks for ETL developer availability',
        '4. ETL developer builds SSIS package (1 week)',
        '5. Testing (1 week)',
        '6. Deployment (scheduled monthly)',
        '',
        '<b>Total Time: 4-6 weeks</b>'
    ]
    for step in before_steps:
        elements.append(Paragraph(step, styles['Normal']))
    elements.append(Spacer(1, 0.2 * inch))

    elements.append(Paragraph('<b>After (dbt):</b>', styles['Heading2']))
    after_steps = [
        '1. Data analyst writes SQL in dbt',
        '2. Creates pull request',
        '3. Automated tests run (5 minutes)',
        '4. Code review (1 day)',
        '5. Merge and deploy (automated)',
        '',
        '<b>Total Time: 1-2 days</b>'
    ]
    for step in after_steps:
        elements.append(Paragraph(step, styles['Normal']))
    elements.append(Spacer(1, 0.3 * inch))

    speedup = '<font size=12 color="green"><b>Result: 10x faster development cycle</b></font>'
    elements.append(Paragraph(speedup, styles['Center']))

    # Technical benefits
    elements.append(PageBreak())
    elements.append(Paragraph('<b><font size=16>Technical Benefits</font></b>', styles['Heading1']))
    elements.append(Spacer(1, 0.2 * inch))

    tech_benefits = [
        ('<b>1. Version Control with Git</b>', 'Full audit trail, code review, easy rollbacks, branching for features'),
        ('<b>2. SQL-Based</b>', 'Everyone knows SQL. No proprietary tools or languages.'),
        ('<b>3. Built-In Testing</b>', 'Automated data quality tests. Catch issues before production.'),
        ('<b>4. Auto-Generated Documentation</b>', 'Beautiful, interactive docs with lineage graphs.'),
        ('<b>5. Modular & Reusable</b>', 'DRY principle. Define logic once, use everywhere.'),
        ('<b>6. Free Open Source</b>', 'dbt Core is free. Optional paid Cloud for teams.'),
        ('<b>7. CI/CD Ready</b>', 'Tests run on every PR. Deploy with confidence.'),
        ('<b>8. Incremental Models</b>', 'Fast updates. Only process changed data.'),
        ('<b>9. Data Lineage</b>', 'Visual graphs showing data flow and dependencies.'),
        ('<b>10. Easier Collaboration</b>', 'Entire analytics team can contribute, not just specialists.')
    ]

    for title, desc in tech_benefits:
        elements.append(Paragraph(title, styles['Normal']))
        elements.append(Paragraph(desc, styles['BodyText']))
        elements.append(Spacer(1, 0.15 * inch))

    # Business benefits
    elements.append(PageBreak())
    elements.append(Paragraph('<b><font size=16>Business Benefits</font></b>', styles['Heading1']))
    elements.append(Spacer(1, 0.2 * inch))

    biz_benefits = [
        '65% cost reduction',
        '10x faster time-to-market',
        'Better data quality (automated testing)',
        'More agile (deploy multiple times per day)',
        'Better team collaboration',
        'Easier hiring (SQL is universal skill)',
        'Lower risk (tests catch errors early)',
        'Self-service analytics (analysts independent)',
        'Scalable (grow without adding headcount)',
        'Modern practices (attract top talent)'
    ]

    for benefit in biz_benefits:
        elements.append(Paragraph(f'✓ {benefit}', styles['Normal']))
        elements.append(Spacer(1, 0.1 * inch))

    # Conclusion
    elements.append(PageBreak())
    elements.append(Paragraph('<b><font size=16>Conclusion</font></b>', styles['Heading1']))
    elements.append(Spacer(1, 0.2 * inch))

    conclusion = """
    The migration from legacy ETL to dbt is a <b>strategic business decision</b> that delivers
    immediate cost savings, faster development, and better data quality. Organizations that make
    this transition report:
    """
    elements.append(Paragraph(conclusion, styles['Justify']))
    elements.append(Spacer(1, 0.2 * inch))

    results = [
        '<b>65% reduction</b> in data engineering costs',
        '<b>10x faster</b> development and deployment',
        '<b>90% fewer</b> production data quality issues',
        '<b>5x more</b> analytics team contributions',
        '<b>100% increase</b> in deployment frequency'
    ]

    for result in results:
        elements.append(Paragraph(f'• {result}', styles['Normal']))
    elements.append(Spacer(1, 0.3 * inch))

    final = """
    <b>The case is clear:</b> Legacy ETL tools are expensive, slow, and hard to maintain.
    Modern data transformation with dbt is faster, cheaper, and more reliable.
    The question is not <i>if</i> you should migrate, but <i>when</i>.
    """
    elements.append(Paragraph(final, styles['Justify']))
    elements.append(Spacer(1, 0.3 * inch))

    cta = '<font size=14><b>Start your migration today with our automated MSSQL to dbt tool!</b></font>'
    elements.append(Paragraph(cta, styles['Center']))

    # Build PDF
    doc.build(elements)
    print("[OK] PDF created: ETL_VS_DBT_BENEFITS.pdf")

if __name__ == "__main__":
    print("=" * 60)
    print("Creating ETL vs dbt Benefits PDF")
    print("=" * 60)
    create_etl_pdf()
    print("\n[OK] Done! You can now open ETL_VS_DBT_BENEFITS.pdf")
