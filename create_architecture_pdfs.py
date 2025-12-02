"""
Generate PDF documents for Backend Language Comparison and Go+Python Architecture
"""

import os
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.units import inch


def create_backend_comparison_pdf(output_dir: str = "docs"):
    """Generate Backend Language Comparison PDF"""

    os.makedirs(output_dir, exist_ok=True)
    filename = f"{output_dir}/BACKEND_LANGUAGE_COMPARISON.pdf"

    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72
    )

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name='MainTitle',
        parent=styles['Heading1'],
        fontSize=24,
        alignment=TA_CENTER,
        spaceAfter=30,
        textColor=colors.HexColor('#1a365d')
    ))
    styles.add(ParagraphStyle(
        name='SectionTitle',
        parent=styles['Heading2'],
        fontSize=16,
        spaceBefore=20,
        spaceAfter=12,
        textColor=colors.HexColor('#2d3748')
    ))
    styles.add(ParagraphStyle(
        name='SubSection',
        parent=styles['Heading3'],
        fontSize=13,
        spaceBefore=15,
        spaceAfter=8,
        textColor=colors.HexColor('#4a5568')
    ))
    styles.add(ParagraphStyle(
        name='BodyCustom',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=8,
        leading=14,
        alignment=TA_JUSTIFY
    ))
    styles.add(ParagraphStyle(
        name='BulletText',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=4,
        leftIndent=20
    ))
    styles.add(ParagraphStyle(
        name='CodeText',
        fontName='Courier',
        fontSize=8,
        leftIndent=20,
        spaceAfter=4,
        backColor=colors.HexColor('#f7fafc')
    ))

    story = []

    # Title Page
    story.append(Spacer(1, 100))
    story.append(Paragraph("Backend Language Comparison", styles['MainTitle']))
    story.append(Paragraph("for DataMigrate AI", ParagraphStyle(
        name='Subtitle', fontSize=18, alignment=TA_CENTER, textColor=colors.HexColor('#4a5568')
    )))
    story.append(Spacer(1, 40))
    story.append(Paragraph("Author: Alexander Garcia Angus", ParagraphStyle(
        name='Author', fontSize=12, alignment=TA_CENTER
    )))
    story.append(Paragraph("Company: OKO Investments", ParagraphStyle(
        name='Company', fontSize=12, alignment=TA_CENTER
    )))
    story.append(Paragraph(f"Date: {datetime.now().strftime('%B %d, %Y')}", ParagraphStyle(
        name='Date', fontSize=12, alignment=TA_CENTER
    )))
    story.append(PageBreak())

    # Executive Summary
    story.append(Paragraph("Executive Summary", styles['SectionTitle']))
    story.append(Paragraph(
        "This document compares 6 backend language options for DataMigrate AI, analyzing development costs, "
        "AWS infrastructure costs, maintenance overhead, and total cost of ownership (TCO) over 2 years.",
        styles['BodyCustom']
    ))
    story.append(Spacer(1, 10))
    story.append(Paragraph(
        "<b>Key Finding:</b> Go + Python hybrid offers the best balance of performance, development speed, "
        "and cost ($31,624 TCO vs FastAPI's $29,670 with 5-10x performance improvement).",
        styles['BodyCustom']
    ))
    story.append(Spacer(1, 20))

    # Cost Analysis Methodology
    story.append(Paragraph("Cost Analysis Methodology", styles['SectionTitle']))
    story.append(Paragraph("Assumptions:", styles['SubSection']))
    assumptions = [
        "Developer hourly rate: $100/hour",
        "Developer weekly rate: $8,000/week (40 hours)",
        "AWS baseline: $600/month (FastAPI monolith on ECS)",
        "Evaluation period: 24 months (2 years)",
        "Project scope: 15 REST API endpoints + LangGraph agents integration"
    ]
    for item in assumptions:
        story.append(Paragraph(f"- {item}", styles['BulletText']))
    story.append(Spacer(1, 15))

    story.append(Paragraph("Cost Components:", styles['SubSection']))
    components = [
        "Initial Development: Time to build all endpoints + agent integration",
        "AWS Infrastructure: Monthly compute, database, networking costs",
        "Maintenance: Ongoing bug fixes, dependency updates, refactoring",
        "Total Cost of Ownership (TCO): Sum of all costs over 2 years"
    ]
    for i, item in enumerate(components, 1):
        story.append(Paragraph(f"{i}. {item}", styles['BulletText']))
    story.append(PageBreak())

    # Option 1: Python FastAPI
    story.append(Paragraph("Option 1: Python (FastAPI) - Current Stack", styles['SectionTitle']))
    story.append(Paragraph("Development Cost:", styles['SubSection']))
    story.append(Paragraph("- API endpoints: 15 endpoints x 30 min = 7.5 hours", styles['BulletText']))
    story.append(Paragraph("- LangGraph integration: Already built (0 hours)", styles['BulletText']))
    story.append(Paragraph("- Authentication/middleware: 8 hours", styles['BulletText']))
    story.append(Paragraph("- Testing: 10 hours", styles['BulletText']))
    story.append(Paragraph("- Total time: 25.5 hours (3.2 days)", styles['BulletText']))
    story.append(Paragraph("- Cost: $2,550", styles['BulletText']))
    story.append(Spacer(1, 10))

    story.append(Paragraph("AWS Infrastructure (Monthly):", styles['SubSection']))
    story.append(Paragraph("- ECS Fargate: $180/month", styles['BulletText']))
    story.append(Paragraph("- RDS PostgreSQL: $120/month", styles['BulletText']))
    story.append(Paragraph("- ElastiCache Redis: $60/month", styles['BulletText']))
    story.append(Paragraph("- Other (ALB, NAT, CloudWatch): $70/month", styles['BulletText']))
    story.append(Paragraph("- Monthly total: $430/month", styles['BulletText']))
    story.append(Paragraph("- 24-month cost: $10,320", styles['BulletText']))
    story.append(Spacer(1, 10))

    story.append(Paragraph("Maintenance: $16,800 (7 hours/month x 24 months)", styles['BodyCustom']))
    story.append(Paragraph("<b>Total 2-Year TCO: $29,670</b>", styles['BodyCustom']))
    story.append(Spacer(1, 10))

    story.append(Paragraph("Pros:", styles['SubSection']))
    pros = ["Fastest initial development", "LangGraph works natively", "Huge ecosystem", "Easy to hire developers"]
    for p in pros:
        story.append(Paragraph(f"+ {p}", styles['BulletText']))

    story.append(Paragraph("Cons:", styles['SubSection']))
    cons = ["Slower API performance (200-500ms latency)", "Higher memory usage (200MB+)", "GIL limits concurrency"]
    for c in cons:
        story.append(Paragraph(f"- {c}", styles['BulletText']))
    story.append(PageBreak())

    # Option 2: Go + Python
    story.append(Paragraph("Option 2: Go + Python Microservices (RECOMMENDED)", styles['SectionTitle']))
    story.append(Paragraph("Development Cost:", styles['SubSection']))
    story.append(Paragraph("- Go API endpoints: 15 endpoints x 20 min = 5 hours", styles['BulletText']))
    story.append(Paragraph("- Go authentication: 12 hours (JWT, middleware)", styles['BulletText']))
    story.append(Paragraph("- Go-Python HTTP integration: 8 hours", styles['BulletText']))
    story.append(Paragraph("- Python service extraction: 6 hours", styles['BulletText']))
    story.append(Paragraph("- Testing: 15 hours", styles['BulletText']))
    story.append(Paragraph("- Total time: 46 hours (5.75 days)", styles['BulletText']))
    story.append(Paragraph("- Cost: $4,600", styles['BulletText']))
    story.append(Spacer(1, 10))

    story.append(Paragraph("AWS Infrastructure (Monthly):", styles['SubSection']))
    story.append(Paragraph("- Go API (ECS): $90/month (50% less than Python)", styles['BulletText']))
    story.append(Paragraph("- Python Service (ECS): $90/month", styles['BulletText']))
    story.append(Paragraph("- RDS PostgreSQL: $120/month", styles['BulletText']))
    story.append(Paragraph("- ElastiCache Redis: $60/month", styles['BulletText']))
    story.append(Paragraph("- Other: $66/month", styles['BulletText']))
    story.append(Paragraph("- Monthly total: $426/month", styles['BulletText']))
    story.append(Paragraph("- 24-month cost: $10,224", styles['BulletText']))
    story.append(Spacer(1, 10))

    story.append(Paragraph("Maintenance: $16,800 (7 hours/month x 24 months)", styles['BodyCustom']))
    story.append(Paragraph("<b>Total 2-Year TCO: $31,624</b>", styles['BodyCustom']))
    story.append(Spacer(1, 10))

    story.append(Paragraph("Pros:", styles['SubSection']))
    pros = ["5-10x faster API responses (50-100ms)", "50% lower memory usage", "Keeps existing LangGraph code", "Better concurrency (goroutines)"]
    for p in pros:
        story.append(Paragraph(f"+ {p}", styles['BulletText']))

    story.append(Paragraph("Cons:", styles['SubSection']))
    cons = ["Slightly higher development time (+3 days)", "Two services to maintain", "HTTP latency between services (5-10ms)"]
    for c in cons:
        story.append(Paragraph(f"- {c}", styles['BulletText']))
    story.append(Paragraph("<b>Performance Improvement: 60-80% faster API responses</b>", styles['BodyCustom']))
    story.append(PageBreak())

    # Summary Comparison Table
    story.append(Paragraph("Summary Comparison Table", styles['SectionTitle']))

    table_data = [
        ['Language', 'Initial Dev', 'AWS (24mo)', 'Maintenance', 'Total TCO', 'Performance'],
        ['Python (FastAPI)', '$2,550', '$10,320', '$16,800', '$29,670', 'Baseline'],
        ['Go + Python', '$4,600', '$10,224', '$16,800', '$31,624', '5-10x faster'],
        ['TypeScript + Python', '$4,775', '$11,472', '$16,800', '$33,047', '~Python'],
        ['C# + Python', '$6,475', '$12,480', '$18,000', '$36,955', '4-6x faster'],
        ['Java + Python', '$7,125', '$13,560', '$19,200', '$39,885', '3-5x faster'],
        ['Rust + Python', '$8,800', '$9,456', '$24,000', '$42,256', '10-20x faster'],
    ]

    table = Table(table_data, colWidths=[1.3*inch, 0.8*inch, 0.9*inch, 0.9*inch, 0.9*inch, 1.0*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2d3748')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#e2e8f0')),
        ('BACKGROUND', (0, 2), (-1, 2), colors.HexColor('#c6f6d5')),  # Highlight Go option
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cbd5e0')),
    ]))
    story.append(table)
    story.append(Spacer(1, 20))

    # LangGraph Integration
    story.append(Paragraph("LangGraph Integration Explanation", styles['SectionTitle']))
    story.append(Paragraph(
        "The Critical Question: 'Does Go mean no Python agents?'",
        styles['SubSection']
    ))
    story.append(Paragraph(
        "<b>Answer: NO! LangGraph stays in Python, Go just handles the API.</b>",
        styles['BodyCustom']
    ))
    story.append(Spacer(1, 10))

    story.append(Paragraph("Why LangGraph Must Stay in Python:", styles['SubSection']))
    reasons = [
        "LangGraph is Python-only - No Go/Java/C# equivalent exists",
        "LangGraph dependencies: langchain, anthropic SDK, langgraph-checkpoint - all Python",
        "Your existing 6 agents are already built in Python - don't throw away your competitive advantage!"
    ]
    for r in reasons:
        story.append(Paragraph(f"- {r}", styles['BulletText']))
    story.append(Spacer(1, 15))

    story.append(Paragraph("Traffic Distribution:", styles['SubSection']))
    story.append(Paragraph("<b>95% of requests go to Go API:</b> login, list migrations, CRUD operations", styles['BodyCustom']))
    story.append(Paragraph("<b>5% of requests go to Python:</b> run-agents (only when creating new migration)", styles['BodyCustom']))
    story.append(PageBreak())

    # Final Recommendation
    story.append(Paragraph("Final Recommendation", styles['SectionTitle']))

    story.append(Paragraph("For Now (MVP Phase):", styles['SubSection']))
    story.append(Paragraph(
        "Keep Python (FastAPI) - Lowest TCO ($29,670), fastest development, everything works.",
        styles['BodyCustom']
    ))

    story.append(Paragraph("For Scale (1,000+ users):", styles['SubSection']))
    story.append(Paragraph(
        "Migrate to Go + Python - Small TCO increase (+$1,954), but 5-10x performance improvement "
        "justifies the investment when you have real traffic.",
        styles['BodyCustom']
    ))

    story.append(Paragraph("Avoid:", styles['SubSection']))
    story.append(Paragraph("- Java/C# - Only if mandated by enterprise requirements", styles['BulletText']))
    story.append(Paragraph("- Rust - Only if you need extreme performance (10,000+ migrations/day)", styles['BulletText']))

    # Footer
    story.append(Spacer(1, 40))
    story.append(Paragraph(
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | DataMigrate AI | OKO Investments",
        ParagraphStyle(name='Footer', fontSize=9, textColor=colors.grey, alignment=TA_CENTER)
    ))

    doc.build(story)
    print(f"[OK] Created: {filename}")


def create_go_python_architecture_pdf(output_dir: str = "docs"):
    """Generate Go + Python Architecture PDF"""

    os.makedirs(output_dir, exist_ok=True)
    filename = f"{output_dir}/GO_PYTHON_ARCHITECTURE.pdf"

    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72
    )

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name='MainTitle',
        parent=styles['Heading1'],
        fontSize=24,
        alignment=TA_CENTER,
        spaceAfter=30,
        textColor=colors.HexColor('#1a365d')
    ))
    styles.add(ParagraphStyle(
        name='SectionTitle',
        parent=styles['Heading2'],
        fontSize=16,
        spaceBefore=20,
        spaceAfter=12,
        textColor=colors.HexColor('#2d3748')
    ))
    styles.add(ParagraphStyle(
        name='SubSection',
        parent=styles['Heading3'],
        fontSize=13,
        spaceBefore=15,
        spaceAfter=8,
        textColor=colors.HexColor('#4a5568')
    ))
    styles.add(ParagraphStyle(
        name='BodyCustom',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=8,
        leading=14,
        alignment=TA_JUSTIFY
    ))
    styles.add(ParagraphStyle(
        name='BulletText',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=4,
        leftIndent=20
    ))

    story = []

    # Title Page
    story.append(Spacer(1, 100))
    story.append(Paragraph("Go + Python Hybrid Architecture", styles['MainTitle']))
    story.append(Paragraph("DataMigrate AI", ParagraphStyle(
        name='Subtitle', fontSize=18, alignment=TA_CENTER, textColor=colors.HexColor('#4a5568')
    )))
    story.append(Spacer(1, 40))
    story.append(Paragraph("Author: Alexander Garcia Angus", ParagraphStyle(
        name='Author', fontSize=12, alignment=TA_CENTER
    )))
    story.append(Paragraph("Company: OKO Investments", ParagraphStyle(
        name='Company', fontSize=12, alignment=TA_CENTER
    )))
    story.append(Paragraph(f"Date: {datetime.now().strftime('%B %d, %Y')}", ParagraphStyle(
        name='Date', fontSize=12, alignment=TA_CENTER
    )))
    story.append(PageBreak())

    # Architecture Overview
    story.append(Paragraph("Architecture Overview", styles['SectionTitle']))
    story.append(Paragraph(
        "DataMigrate AI uses a hybrid microservices architecture where Go handles high-frequency API "
        "operations (95% of requests) and Python handles AI agent orchestration (5% of requests).",
        styles['BodyCustom']
    ))
    story.append(Spacer(1, 15))

    # Architecture Components
    story.append(Paragraph("Architecture Components", styles['SubSection']))

    components_table = [
        ['Component', 'Technology', 'Port', 'Responsibility'],
        ['Frontend', 'Vue.js 3 + TypeScript', '443', 'User interface'],
        ['Load Balancer', 'AWS ALB', '443', 'SSL termination, routing'],
        ['Go API Service', 'Gin Framework', '8000', '95% of traffic - CRUD, auth'],
        ['Python Service', 'FastAPI + LangGraph', '8001', '5% of traffic - AI agents'],
        ['Database', 'PostgreSQL RDS', '5432', 'Data persistence'],
        ['Cache', 'Redis ElastiCache', '6379', 'Sessions, rate limiting'],
    ]

    table = Table(components_table, colWidths=[1.2*inch, 1.5*inch, 0.6*inch, 2.2*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2d3748')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cbd5e0')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f7fafc')]),
    ]))
    story.append(table)
    story.append(PageBreak())

    # Request Flow
    story.append(Paragraph("Request Flow Examples", styles['SectionTitle']))

    story.append(Paragraph("Example 1: User Login (Go handles 100%)", styles['SubSection']))
    login_steps = [
        "1. POST /api/v1/login received by Go API (8ms)",
        "2. Query PostgreSQL for user (15ms)",
        "3. Verify password with bcrypt (30ms)",
        "4. Generate JWT token (5ms)",
        "5. Return token to user (2ms)",
        "Total: 60ms (vs Python's 200ms)"
    ]
    for step in login_steps:
        story.append(Paragraph(step, styles['BulletText']))
    story.append(Spacer(1, 15))

    story.append(Paragraph("Example 2: List Migrations (Go handles 100%)", styles['SubSection']))
    list_steps = [
        "1. GET /api/v1/migrations received (5ms)",
        "2. Go API validates JWT (5ms)",
        "3. Query PostgreSQL with pagination (20ms)",
        "4. Serialize to JSON (5ms)",
        "5. Return to user (2ms)",
        "Total: 32ms (vs Python's 150ms)"
    ]
    for step in list_steps:
        story.append(Paragraph(step, styles['BulletText']))
    story.append(Spacer(1, 15))

    story.append(Paragraph("Example 3: Create Migration (Go 90% + Python 10%)", styles['SubSection']))
    story.append(Paragraph(
        "This is the key example showing how Go and Python work together:",
        styles['BodyCustom']
    ))
    create_steps = [
        "1. POST /api/v1/migrations received by Go (5ms)",
        "2. Validate input (8ms)",
        "3. Save to PostgreSQL (15ms)",
        "4. Return migration object to user immediately (2ms)",
        "   User sees response: 30ms [checkmark]",
        "",
        "Meanwhile (async, in background):",
        "5. Go spawns goroutine to call Python service",
        "6. HTTP POST to python-service:8001/run-agents",
        "7. Python initializes LangGraph state",
        "8. Run 6-agent workflow (24 minutes total):",
        "   - Assessment Agent (2 min)",
        "   - Planner Agent (3 min)",
        "   - Executor Agent (8 min)",
        "   - Tester Agent (5 min)",
        "   - Rebuilder Agent (4 min)",
        "   - Evaluator Agent (2 min)",
        "9. Save generated dbt models to PostgreSQL",
        "10. Update migration status to 'completed'"
    ]
    for step in create_steps:
        story.append(Paragraph(step, styles['BulletText']))
    story.append(Spacer(1, 10))
    story.append(Paragraph(
        "<b>Key Point:</b> User gets response in 30ms, not 24 minutes!",
        styles['BodyCustom']
    ))
    story.append(PageBreak())

    # Service Communication
    story.append(Paragraph("Service Communication", styles['SectionTitle']))
    story.append(Paragraph(
        "Go and Python services communicate via HTTP. Go calls Python asynchronously using goroutines, "
        "so the user doesn't wait for AI processing to complete.",
        styles['BodyCustom']
    ))
    story.append(Spacer(1, 15))

    story.append(Paragraph("Go to Python Communication:", styles['SubSection']))
    story.append(Paragraph("- Go API receives user request", styles['BulletText']))
    story.append(Paragraph("- Go saves initial data to PostgreSQL", styles['BulletText']))
    story.append(Paragraph("- Go returns response to user immediately", styles['BulletText']))
    story.append(Paragraph("- Go spawns goroutine to call Python service", styles['BulletText']))
    story.append(Paragraph("- Python service processes AI workflow", styles['BulletText']))
    story.append(Paragraph("- Python updates database with results", styles['BulletText']))
    story.append(Spacer(1, 15))

    story.append(Paragraph("Database Access Pattern:", styles['SubSection']))
    story.append(Paragraph(
        "Both services access the same PostgreSQL database but for different purposes:",
        styles['BodyCustom']
    ))
    story.append(Paragraph("- Go: Fast CRUD operations (99% reads, 1% writes) - 5-20ms queries", styles['BulletText']))
    story.append(Paragraph("- Python: Complex state updates during AI workflow - multiple writes", styles['BulletText']))
    story.append(PageBreak())

    # Performance Comparison
    story.append(Paragraph("Performance Comparison", styles['SectionTitle']))

    perf_table = [
        ['Metric', 'Python Monolith', 'Go + Python Hybrid'],
        ['API Latency (p50)', '200ms', '50ms (4x faster)'],
        ['API Latency (p95)', '500ms', '100ms (5x faster)'],
        ['Memory per Pod', '200MB', 'Go: 50MB, Python: 200MB'],
        ['Concurrent Requests', '1,000 req/s', '10,000 req/s (10x better)'],
        ['Startup Time', '3 seconds', 'Go: 100ms, Python: 3s'],
        ['Container Size', '400MB', 'Go: 20MB, Python: 400MB'],
    ]

    perf_table_obj = Table(perf_table, colWidths=[1.8*inch, 1.8*inch, 2.2*inch])
    perf_table_obj.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2d3748')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cbd5e0')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f7fafc')]),
    ]))
    story.append(perf_table_obj)
    story.append(PageBreak())

    # Benefits Summary
    story.append(Paragraph("Benefits Summary", styles['SectionTitle']))

    story.append(Paragraph("Performance Benefits:", styles['SubSection']))
    perf_benefits = [
        "4-5x faster API response times",
        "10x higher concurrent request capacity",
        "50% lower memory usage for API pods"
    ]
    for b in perf_benefits:
        story.append(Paragraph(f"+ {b}", styles['BulletText']))

    story.append(Paragraph("Cost Benefits:", styles['SubSection']))
    cost_benefits = [
        "Fewer replicas needed (Go handles more traffic per pod)",
        "Smaller container images (Go binaries are tiny)",
        "Lower AWS costs due to resource efficiency"
    ]
    for b in cost_benefits:
        story.append(Paragraph(f"+ {b}", styles['BulletText']))

    story.append(Paragraph("Development Benefits:", styles['SubSection']))
    dev_benefits = [
        "Keep existing Python LangGraph code (no rewrite!)",
        "Go is easier to learn than Rust (1-2 weeks)",
        "Clear separation of concerns (API vs agents)"
    ]
    for b in dev_benefits:
        story.append(Paragraph(f"+ {b}", styles['BulletText']))

    story.append(Paragraph("Operational Benefits:", styles['SubSection']))
    ops_benefits = [
        "Independent scaling (scale API and agents separately)",
        "Independent deployment (deploy Go without touching Python)",
        "Easier debugging (logs separated by service)"
    ]
    for b in ops_benefits:
        story.append(Paragraph(f"+ {b}", styles['BulletText']))

    # Footer
    story.append(Spacer(1, 40))
    story.append(Paragraph(
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | DataMigrate AI | OKO Investments",
        ParagraphStyle(name='Footer', fontSize=9, textColor=colors.grey, alignment=TA_CENTER)
    ))

    doc.build(story)
    print(f"[OK] Created: {filename}")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("DataMigrate AI - Architecture Documentation Generator")
    print("=" * 60)

    print("\nGenerating PDF documents...")
    create_backend_comparison_pdf()
    create_go_python_architecture_pdf()

    print("\n" + "=" * 60)
    print("Documentation generation complete!")
    print("=" * 60)

    print("\nGenerated files:")
    print("  - docs/BACKEND_LANGUAGE_COMPARISON.pdf")
    print("  - docs/GO_PYTHON_ARCHITECTURE.pdf")
