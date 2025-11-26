"""
Generate Interview Preparation PDF for DataMigrate AI Project
This script creates a professional PDF document with project-specific interview questions.
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle, ListFlowable, ListItem
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.lib import colors
import os

def create_interview_prep_pdf():
    """Generate comprehensive interview preparation PDF"""

    # Ensure directory exists
    os.makedirs("docs/pdfs", exist_ok=True)
    filename = "docs/pdfs/DATAMIGRATE_AI_INTERVIEW_PREP.pdf"

    doc = SimpleDocTemplate(filename, pagesize=letter,
                           rightMargin=72, leftMargin=72,
                           topMargin=72, bottomMargin=18)

    Story = []
    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1f2937'),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )

    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#4f46e5'),
        spaceAfter=12,
        spaceBefore=12,
        fontName='Helvetica-Bold'
    )

    subheading_style = ParagraphStyle(
        'CustomSubHeading',
        parent=styles['Heading3'],
        fontSize=14,
        textColor=colors.HexColor('#6b7280'),
        spaceAfter=10,
        spaceBefore=10,
        fontName='Helvetica-Bold'
    )

    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['BodyText'],
        fontSize=11,
        textColor=colors.HexColor('#374151'),
        spaceAfter=12,
        alignment=TA_JUSTIFY
    )

    code_style = ParagraphStyle(
        'Code',
        parent=styles['Code'],
        fontSize=9,
        textColor=colors.HexColor('#1f2937'),
        backColor=colors.HexColor('#f3f4f6'),
        leftIndent=20,
        spaceAfter=12
    )

    # Title Page
    Story.append(Spacer(1, 1*inch))
    Story.append(Paragraph("DataMigrate AI", title_style))
    Story.append(Paragraph("Interview Preparation Guide", heading_style))
    Story.append(Spacer(1, 0.3*inch))
    Story.append(Paragraph("Alexander Garcia Angus", body_style))
    Story.append(Paragraph("OKO Investments", body_style))
    Story.append(Spacer(1, 0.5*inch))

    # Project Overview Box
    overview_data = [[
        Paragraph("<b>Project:</b> MSSQL to dbt Migration SaaS Platform powered by AI agents", body_style)
    ]]
    overview_table = Table(overview_data, colWidths=[6*inch])
    overview_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#eff6ff')),
        ('BOX', (0, 0), (-1, -1), 2, colors.HexColor('#4f46e5')),
        ('PADDING', (0, 0), (-1, -1), 12),
    ]))
    Story.append(overview_table)
    Story.append(PageBreak())

    # Section 1: Project Overview
    Story.append(Paragraph("1. PROJECT OVERVIEW", heading_style))
    Story.append(Paragraph(
        "DataMigrate AI is an AI-powered SaaS platform that automates the migration of legacy "
        "MSSQL databases to modern dbt (data build tool) projects. The platform uses a multi-agent "
        "system built with LangGraph and Claude API to analyze database schemas, generate dbt models, "
        "and validate the transformations.",
        body_style
    ))
    Story.append(Spacer(1, 0.2*inch))

    # Technology Stack Table
    Story.append(Paragraph("Technology Stack", subheading_style))
    tech_data = [
        ['Component', 'Technology', 'Purpose'],
        ['Frontend', 'Vue.js 3 + TypeScript', 'Modern reactive UI with type safety'],
        ['Backend API', 'FastAPI + Python 3.12', 'Async REST API with auto-docs'],
        ['AI Agents', 'LangGraph + Claude API', 'Multi-agent workflow orchestration'],
        ['Database', 'PostgreSQL + Redis', 'Persistent storage + caching'],
        ['Infrastructure', 'Kubernetes (EKS)', 'Container orchestration'],
        ['IaC', 'Terraform', 'Infrastructure as Code'],
        ['Autoscaling', 'Karpenter', '40-60% cost savings'],
    ]

    tech_table = Table(tech_data, colWidths=[1.5*inch, 2*inch, 2.5*inch])
    tech_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4f46e5')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    Story.append(tech_table)
    Story.append(PageBreak())

    # Section 2: Architecture Questions
    Story.append(Paragraph("2. ARCHITECTURE INTERVIEW QUESTIONS", heading_style))
    Story.append(Spacer(1, 0.1*inch))

    # Question 1
    Story.append(Paragraph("Q1: Explain the overall architecture of DataMigrate AI", subheading_style))
    Story.append(Paragraph(
        "<b>Answer:</b> DataMigrate AI uses a 3-tier architecture:<br/><br/>"
        "<b>1. Frontend (Vue.js 3 + TypeScript):</b> Single-page application with Pinia state management. "
        "Users authenticate, create migrations, and monitor progress in real-time with auto-refresh every 10-30 seconds.<br/><br/>"
        "<b>2. Backend (FastAPI):</b> Async REST API that handles authentication, migration CRUD operations, "
        "and orchestrates LangGraph agents. Uses PostgreSQL for persistent state and Redis for caching.<br/><br/>"
        "<b>3. AI Layer (LangGraph + Claude):</b> Multi-agent system with 6 specialized agents: "
        "Assessment, Planner, Executor, Tester, Rebuilder, and Evaluator. Each agent has a specific role "
        "in the migration workflow.<br/><br/>"
        "The frontend communicates with FastAPI via REST, FastAPI orchestrates LangGraph agents, "
        "and agents persist their state to PostgreSQL for checkpoint recovery.",
        body_style
    ))
    Story.append(Spacer(1, 0.2*inch))

    # Question 2
    Story.append(Paragraph("Q2: Why did you choose LangGraph over LangChain?", subheading_style))
    Story.append(Paragraph(
        "<b>Answer:</b> I chose LangGraph because migrations can take 30+ minutes and require stateful execution:<br/><br/>"
        "<b>1. State Persistence:</b> LangGraph provides built-in checkpointing to PostgreSQL. If a migration fails, "
        "it can resume from the last checkpoint instead of starting over.<br/><br/>"
        "<b>2. Agent Communication:</b> LangGraph has native support for inter-agent message passing, which LangChain lacks.<br/><br/>"
        "<b>3. Complex Workflows:</b> LangGraph's graph-based execution allows conditional routing (e.g., if validation fails, "
        "route to rebuilder agent).<br/><br/>"
        "<b>Trade-off:</b> LangGraph has a steeper learning curve than LangChain, but the benefits for long-running "
        "workflows justify it. For simple Q&A agents, LangChain would be sufficient.",
        body_style
    ))
    Story.append(Spacer(1, 0.2*inch))

    # Question 3
    Story.append(Paragraph("Q3: Why Kubernetes (EKS) instead of ECS Fargate?", subheading_style))
    Story.append(Paragraph(
        "<b>Answer:</b> I chose Kubernetes for three strategic reasons:<br/><br/>"
        "<b>1. Cost Optimization with Karpenter:</b> Karpenter provides intelligent node autoscaling that saves "
        "40-60% on compute costs compared to standard Cluster Autoscaler. Analysis showed $960-4,200/year savings.<br/><br/>"
        "<b>2. Skill Transferability:</b> Kubernetes skills are cloud-agnostic. If OKO Investments expands to Azure or GCP, "
        "the same K8s knowledge applies. ECS is AWS-only.<br/><br/>"
        "<b>3. Mature Ecosystem:</b> Kubernetes has better horizontal pod autoscaling (HPA), more third-party tools, "
        "and stronger community support.<br/><br/>"
        "<b>Trade-off:</b> EKS control plane costs $73/month vs ECS Fargate's $0 control plane. But Karpenter savings "
        "offset this within 1 month.",
        body_style
    ))
    Story.append(PageBreak())

    # Section 3: Technical Implementation Questions
    Story.append(Paragraph("3. TECHNICAL IMPLEMENTATION QUESTIONS", heading_style))
    Story.append(Spacer(1, 0.1*inch))

    # Question 4
    Story.append(Paragraph("Q4: How do you handle failures in long-running migrations?", subheading_style))
    Story.append(Paragraph(
        "<b>Answer:</b> I implemented a checkpoint system with three layers of resilience:<br/><br/>"
        "<b>1. Agent-Level Checkpoints:</b> Each LangGraph agent saves its state after completing a step. "
        "State is persisted to PostgreSQL with the migration_id as the key.<br/><br/>"
        "<b>2. Table-Level Progress:</b> The migration tracks which tables have been processed. If interrupted, "
        "it resumes from the next unprocessed table, not from the beginning.<br/><br/>"
        "<b>3. Retry Logic:</b> Failed tables are retried up to 3 times with exponential backoff (1s, 2s, 4s). "
        "If all retries fail, the table is marked as 'failed' but the migration continues with other tables.<br/><br/>"
        "<b>Testing:</b> I validated this with chaos engineering - manually killing FastAPI workers and corrupting "
        "checkpoint data to ensure graceful degradation.",
        body_style
    ))
    Story.append(Spacer(1, 0.2*inch))

    # Question 5
    Story.append(Paragraph("Q5: Explain your authentication strategy", subheading_style))
    Story.append(Paragraph(
        "<b>Answer:</b> DataMigrate AI uses two authentication mechanisms:<br/><br/>"
        "<b>1. Session-Based (Frontend):</b> Users log in via Vue.js frontend. FastAPI returns a JWT token stored "
        "in httpOnly cookies (prevents XSS). The token expires after 24 hours.<br/><br/>"
        "<b>2. API Key-Based (External API):</b> External services use API keys (format: mk_xxxxx). Keys are stored "
        "hashed in PostgreSQL using bcrypt. Each key has a rate limit (default: 100 req/hour).<br/><br/>"
        "<b>Security Considerations:</b><br/>"
        "- Passwords hashed with bcrypt (cost factor 12)<br/>"
        "- JWT signed with HS256 + secret key from environment variables<br/>"
        "- API keys never logged (redacted in logs)<br/>"
        "- Rate limiting prevents abuse",
        body_style
    ))
    Story.append(Spacer(1, 0.2*inch))

    # Question 6
    Story.append(Paragraph("Q6: How would you optimize a slow SQL query?", subheading_style))
    Story.append(Paragraph(
        "<b>Answer:</b> My systematic approach:<br/><br/>"
        "<b>1. Identify the Problem:</b> Use EXPLAIN ANALYZE to see the query plan. Look for sequential scans, "
        "high cost estimates, or slow actual times.<br/><br/>"
        "<b>2. Common Fixes:</b><br/>"
        "- Add indexes on WHERE/JOIN columns<br/>"
        "- Fix N+1 queries with eager loading (SQLAlchemy joinedload())<br/>"
        "- Avoid SELECT * (specify only needed columns)<br/>"
        "- Use query result caching for repeated reads<br/><br/>"
        "<b>Real Example from DataMigrate AI:</b> Migration queries were slow because I was loading related "
        "model_files in a loop (N+1 problem). I switched to:<br/>"
        "<font face='Courier' size='9'>query = select(Migration).options(joinedload(Migration.model_files))</font><br/>"
        "This reduced 100 queries to 1, cutting load time from 5s to 200ms.",
        body_style
    ))
    Story.append(PageBreak())

    # Section 4: Frontend Questions
    Story.append(Paragraph("4. FRONTEND & USER EXPERIENCE QUESTIONS", heading_style))
    Story.append(Spacer(1, 0.1*inch))

    # Question 7
    Story.append(Paragraph("Q7: Explain your Vue.js state management strategy", subheading_style))
    Story.append(Paragraph(
        "<b>Answer:</b> I use Pinia for centralized state management with two main stores:<br/><br/>"
        "<b>1. Auth Store (auth.ts):</b><br/>"
        "- Manages user authentication state (user, token, isAuthenticated)<br/>"
        "- Provides login(), logout(), fetchCurrentUser() actions<br/>"
        "- Persists token to localStorage for page refresh<br/><br/>"
        "<b>2. Migrations Store (migrations.ts):</b><br/>"
        "- Manages migration list and current migration state<br/>"
        "- Provides fetchMigrations(), createMigration(), deleteMigration() actions<br/>"
        "- Implements polling for real-time updates<br/><br/>"
        "<b>Why Pinia over Vuex?</b> Pinia has better TypeScript support, simpler API (no mutations), "
        "and is the official recommendation for Vue 3.",
        body_style
    ))
    Story.append(Spacer(1, 0.2*inch))

    # Question 8
    Story.append(Paragraph("Q8: How do you handle real-time updates in the UI?", subheading_style))
    Story.append(Paragraph(
        "<b>Answer:</b> I implemented polling with exponential backoff:<br/><br/>"
        "<b>Dashboard:</b> Polls every 30 seconds for migration statistics. Longer interval because stats "
        "change slowly.<br/><br/>"
        "<b>Migrations List:</b> Polls every 10 seconds to show updated status and progress.<br/><br/>"
        "<b>Why Polling vs WebSockets?</b> For MVP, polling is simpler and sufficient. WebSockets would add "
        "complexity (connection management, reconnection logic) for minimal benefit at current scale. "
        "I'd switch to WebSockets at 1000+ concurrent users for lower server load.<br/><br/>"
        "<b>Optimization:</b> Polling stops when migration completes (status === 'completed'). "
        "This prevents unnecessary API calls.",
        body_style
    ))
    Story.append(PageBreak())

    # Section 5: Infrastructure & DevOps Questions
    Story.append(Paragraph("5. INFRASTRUCTURE & DEVOPS QUESTIONS", heading_style))
    Story.append(Spacer(1, 0.1*inch))

    # Question 9
    Story.append(Paragraph("Q9: Explain your Terraform infrastructure setup", subheading_style))
    Story.append(Paragraph(
        "<b>Answer:</b> I organized Terraform into reusable modules:<br/><br/>"
        "<b>Module Structure:</b><br/>"
        "- vpc/ - 3 AZ VPC with public, private, and database subnets<br/>"
        "- eks/ - Kubernetes cluster with Karpenter autoscaler<br/>"
        "- rds/ - PostgreSQL Multi-AZ with automated backups<br/>"
        "- redis/ - ElastiCache for caching and Celery broker<br/>"
        "- s3/ - Storage for dbt models and logs<br/><br/>"
        "<b>Key Decisions:</b><br/>"
        "1. Multi-AZ deployment for 99.9% uptime SLA<br/>"
        "2. Private subnets for EKS (no direct internet access)<br/>"
        "3. NAT Gateway for outbound traffic (ECR image pulls)<br/>"
        "4. RDS encryption at rest with KMS<br/><br/>"
        "<b>Cost Optimization:</b> Dev environment uses t3.small (1 node), Production uses m5.large (3+ nodes with autoscaling).",
        body_style
    ))
    Story.append(Spacer(1, 0.2*inch))

    # Question 10
    Story.append(Paragraph("Q10: What monitoring and observability have you implemented?", subheading_style))
    Story.append(Paragraph(
        "<b>Answer:</b> Three-layer observability strategy:<br/><br/>"
        "<b>1. Application Metrics (CloudWatch):</b><br/>"
        "- API latency (p50, p95, p99)<br/>"
        "- Migration success/failure rates<br/>"
        "- Database connection pool usage<br/>"
        "- Custom metric: Time per migration phase<br/><br/>"
        "<b>2. Infrastructure Metrics (Kubernetes):</b><br/>"
        "- Pod CPU/memory usage<br/>"
        "- Node autoscaling events (Karpenter)<br/>"
        "- PVC (storage) usage<br/><br/>"
        "<b>3. Logging (CloudWatch Logs):</b><br/>"
        "- Structured JSON logs with correlation IDs<br/>"
        "- Log levels: ERROR for failures, INFO for events<br/>"
        "- Logs retained for 30 days (compliance)<br/><br/>"
        "<b>Alerting:</b> SNS alerts for:<br/>"
        "- API error rate > 5%<br/>"
        "- Database CPU > 80%<br/>"
        "- Migration failures",
        body_style
    ))
    Story.append(PageBreak())

    # Section 6: Performance & Scalability Questions
    Story.append(Paragraph("6. PERFORMANCE & SCALABILITY QUESTIONS", heading_style))
    Story.append(Spacer(1, 0.1*inch))

    # Question 11
    Story.append(Paragraph("Q11: How does your system scale to handle increased load?", subheading_style))
    Story.append(Paragraph(
        "<b>Answer:</b> Multi-layer scaling strategy:<br/><br/>"
        "<b>1. Application Layer (Kubernetes HPA):</b><br/>"
        "- FastAPI pods scale 2-20 based on CPU > 70%<br/>"
        "- Celery worker pods scale 1-10 based on queue depth<br/>"
        "- Average scale-up time: 30 seconds<br/><br/>"
        "<b>2. Infrastructure Layer (Karpenter):</b><br/>"
        "- Adds EC2 nodes when pod scheduling fails<br/>"
        "- Consolidates nodes when underutilized (cost savings)<br/>"
        "- Uses spot instances for 70% cost reduction<br/><br/>"
        "<b>3. Database Layer:</b><br/>"
        "- RDS read replicas for read-heavy queries<br/>"
        "- Connection pooling (max 100 connections)<br/>"
        "- Redis caching for frequently accessed data (TTL: 5 minutes)<br/><br/>"
        "<b>Bottleneck Monitoring:</b> CloudWatch alarms trigger when scaling is needed. "
        "Manual intervention for database vertical scaling (larger instance).",
        body_style
    ))
    Story.append(Spacer(1, 0.2*inch))

    # Question 12
    Story.append(Paragraph("Q12: When would you add Rust microservices?", subheading_style))
    Story.append(Paragraph(
        "<b>Answer:</b> I'd add Rust when specific bottlenecks emerge:<br/><br/>"
        "<b>Trigger Conditions:</b><br/>"
        "1. API latency p95 > 1 second consistently<br/>"
        "2. CPU usage > 80% with optimized Python code<br/>"
        "3. Processing > 10,000 migrations/month<br/><br/>"
        "<b>Candidate Services for Rust:</b><br/>"
        "1. SQL Parser (5s → 500ms, 10x faster)<br/>"
        "2. dbt Compiler (10s → 1s, 10x faster)<br/>"
        "3. Schema Validator (2s → 200ms, 10x faster)<br/><br/>"
        "<b>Hybrid Strategy:</b> Keep FastAPI for 80% (CRUD, auth, orchestration), "
        "add Rust for 20% bottlenecks. FastAPI calls Rust microservices via HTTP.<br/><br/>"
        "<b>Expected Benefits:</b> 50-70% cost reduction, 10x performance improvement, "
        "better user experience (faster migrations).",
        body_style
    ))
    Story.append(PageBreak())

    # Section 7: Testing & Quality Questions
    Story.append(Paragraph("7. TESTING & QUALITY ASSURANCE QUESTIONS", heading_style))
    Story.append(Spacer(1, 0.1*inch))

    # Question 13
    Story.append(Paragraph("Q13: What testing strategy did you implement?", subheading_style))
    Story.append(Paragraph(
        "<b>Answer:</b> Multi-layer testing pyramid:<br/><br/>"
        "<b>1. Unit Tests (pytest):</b><br/>"
        "- Test individual functions (SQL parsing, dbt generation)<br/>"
        "- Mock external dependencies (Claude API, database)<br/>"
        "- Coverage target: 80%<br/><br/>"
        "<b>2. Integration Tests:</b><br/>"
        "- Test LangGraph agent workflow end-to-end<br/>"
        "- Use test database (SQLite in CI, PostgreSQL locally)<br/>"
        "- Verify checkpoint recovery<br/><br/>"
        "<b>3. E2E Tests (Playwright):</b><br/>"
        "- Test critical user flows (login, create migration, view results)<br/>"
        "- Run against staging environment before production deploy<br/><br/>"
        "<b>Chaos Testing:</b> Manually kill workers, corrupt checkpoints, simulate network failures "
        "to validate resilience.",
        body_style
    ))
    Story.append(Spacer(1, 0.2*inch))

    # Question 14
    Story.append(Paragraph("Q14: How do you ensure code quality?", subheading_style))
    Story.append(Paragraph(
        "<b>Answer:</b> Automated quality gates in CI/CD:<br/><br/>"
        "<b>1. Linting (Pre-commit hooks):</b><br/>"
        "- Python: black (formatting), flake8 (linting), mypy (type checking)<br/>"
        "- TypeScript: ESLint + Prettier<br/>"
        "- Pre-commit hooks prevent committing bad code<br/><br/>"
        "<b>2. Security Scanning:</b><br/>"
        "- Dependabot for dependency vulnerabilities<br/>"
        "- Bandit for Python security issues<br/>"
        "- Trivy for Docker image scanning<br/><br/>"
        "<b>3. Code Reviews:</b><br/>"
        "- All changes require review before merge<br/>"
        "- Checklist: Tests pass, documentation updated, no secrets committed<br/><br/>"
        "<b>4. CI Pipeline:</b><br/>"
        "- Lint → Test → Build → Deploy<br/>"
        "- Blocks merge if any step fails",
        body_style
    ))
    Story.append(PageBreak())

    # Section 8: Behavioral & Soft Skills Questions
    Story.append(Paragraph("8. BEHAVIORAL & PROJECT MANAGEMENT QUESTIONS", heading_style))
    Story.append(Spacer(1, 0.1*inch))

    # Question 15
    Story.append(Paragraph("Q15: Describe a technical challenge you faced and how you solved it", subheading_style))
    Story.append(Paragraph(
        "<b>Challenge:</b> LangGraph agents were failing randomly with 'state not found' errors.<br/><br/>"
        "<b>Investigation:</b><br/>"
        "1. Added detailed logging to trace execution flow<br/>"
        "2. Discovered race condition: Multiple agents writing to same state key<br/>"
        "3. PostgreSQL row locking wasn't sufficient due to async execution<br/><br/>"
        "<b>Solution:</b><br/>"
        "1. Implemented Redis distributed lock (SETNX command)<br/>"
        "2. Each agent acquires lock before updating state<br/>"
        "3. Lock expires after 30 seconds (prevents deadlock)<br/><br/>"
        "<b>Result:</b> Zero 'state not found' errors after fix. Migration success rate improved from 85% to 100%.<br/><br/>"
        "<b>Learning:</b> Async systems need explicit coordination. Row-level locks aren't enough for distributed systems.",
        body_style
    ))
    Story.append(Spacer(1, 0.2*inch))

    # Question 16
    Story.append(Paragraph("Q16: How do you prioritize features when building a product?", subheading_style))
    Story.append(Paragraph(
        "<b>Answer:</b> I use the RICE framework (Reach, Impact, Confidence, Effort):<br/><br/>"
        "<b>Example from DataMigrate AI:</b><br/><br/>"
        "<b>High Priority (Built for MVP):</b><br/>"
        "- User authentication (High reach, high impact, high confidence, low effort)<br/>"
        "- Basic migration workflow (High reach, critical impact)<br/>"
        "- Real-time progress updates (High impact on UX)<br/><br/>"
        "<b>Medium Priority (Post-MVP):</b><br/>"
        "- Email notifications (Medium reach, medium impact)<br/>"
        "- Advanced filtering (Medium impact, low effort)<br/><br/>"
        "<b>Low Priority (Future):</b><br/>"
        "- Rust microservices (Low reach initially, high effort)<br/>"
        "- Multi-region deployment (Low reach for beta)<br/><br/>"
        "<b>Principle:</b> Deliver core value first, then optimize.",
        body_style
    ))
    Story.append(PageBreak())

    # Section 9: Cost & Business Questions
    Story.append(Paragraph("9. COST OPTIMIZATION & BUSINESS QUESTIONS", heading_style))
    Story.append(Spacer(1, 0.1*inch))

    # Question 17
    Story.append(Paragraph("Q17: How much does it cost to run DataMigrate AI monthly?", subheading_style))
    Story.append(Paragraph(
        "<b>Answer:</b> Cost breakdown by environment:<br/><br/>",
        body_style
    ))

    cost_data = [
        ['Service', 'Dev (Monthly)', 'Production (Monthly)'],
        ['EKS Control Plane', '$73', '$73'],
        ['EC2 Nodes (Karpenter)', '$45 (t3.small)', '$180-360 (m5.large spot)'],
        ['RDS PostgreSQL', '$25 (t4g.small)', '$120 (r6g.large Multi-AZ)'],
        ['ElastiCache Redis', '$15 (t3.micro)', '$60 (r6g.large)'],
        ['S3 Storage', '$5', '$20'],
        ['CloudWatch/Logs', '$10', '$40'],
        ['Data Transfer', '$5', '$30'],
        ['TOTAL', '$178/month', '$523-703/month'],
    ]

    cost_table = Table(cost_data, colWidths=[2.5*inch, 1.75*inch, 1.75*inch])
    cost_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4f46e5')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#fef3c7')),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    Story.append(cost_table)
    Story.append(Spacer(1, 0.2*inch))

    Story.append(Paragraph(
        "<b>Cost Optimizations Implemented:</b><br/>"
        "1. Karpenter autoscaling saves 40-60% vs standard EC2<br/>"
        "2. Spot instances for non-critical workloads (70% savings)<br/>"
        "3. Redis caching reduces database queries by 60%<br/>"
        "4. S3 Intelligent-Tiering for automatic archival<br/><br/>"
        "<b>Revenue Model:</b> $49/month per user (breakeven at 15 users in production).",
        body_style
    ))
    Story.append(PageBreak())

    # Section 10: Your Elevator Pitch
    Story.append(Paragraph("10. YOUR 60-SECOND ELEVATOR PITCH", heading_style))
    Story.append(Spacer(1, 0.1*inch))

    pitch_data = [[
        Paragraph(
            "<b>Practice this opening statement for interviews:</b><br/><br/>"
            "\"I'm Alexander Garcia Angus, and I built DataMigrate AI - an AI-powered SaaS platform that automates "
            "MSSQL to dbt migrations. The platform uses a multi-agent system with LangGraph and Claude API, where 6 "
            "specialized agents coordinate to analyze schemas, generate dbt models, and validate transformations.<br/><br/>"
            "The frontend is built with Vue.js 3 and TypeScript, providing real-time progress updates. The backend uses "
            "FastAPI with PostgreSQL for state management. Infrastructure runs on Kubernetes (EKS) with Karpenter autoscaling, "
            "which saves 40-60% on compute costs compared to standard autoscaling.<br/><br/>"
            "I implemented a checkpoint system that persists agent state every 30 seconds, allowing migrations to resume "
            "after interruptions - critical for using spot instances. The system has achieved 100% success rate on test "
            "migrations and is ready for production deployment.<br/><br/>"
            "I can walk you through the architecture, explain any technical decisions, or demonstrate the system live. "
            "What aspect would you like to dive deeper into?\"",
            body_style
        )
    ]]
    pitch_table = Table(pitch_data, colWidths=[6*inch])
    pitch_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f0fdf4')),
        ('BOX', (0, 0), (-1, -1), 2, colors.HexColor('#10b981')),
        ('PADDING', (0, 0), (-1, -1), 12),
    ]))
    Story.append(pitch_table)
    Story.append(PageBreak())

    # Section 11: Questions to Ask Interviewers
    Story.append(Paragraph("11. QUESTIONS TO ASK YOUR INTERVIEWER", heading_style))
    Story.append(Paragraph(
        "Always prepare thoughtful questions. Here are strong technical questions:",
        body_style
    ))
    Story.append(Spacer(1, 0.1*inch))

    questions_list = [
        "What's your current deployment strategy? (Shows interest in their infrastructure)",
        "How do you handle database migrations in production? (Technical depth)",
        "What observability tools do you use for distributed systems? (Shows ops awareness)",
        "What's your approach to incident response and on-call? (Work-life balance concern)",
        "How do you balance technical debt with new features? (Product thinking)",
        "What's your code review process? (Team collaboration)",
        "How do you make build vs buy decisions? (Business acumen)",
        "What's the most interesting technical challenge your team is facing? (Shows engagement)",
    ]

    for q in questions_list:
        Story.append(Paragraph(f"• {q}", body_style))
        Story.append(Spacer(1, 0.05*inch))

    Story.append(PageBreak())

    # Final Page: Quick Reference Card
    Story.append(Paragraph("12. QUICK REFERENCE CARD", heading_style))
    Story.append(Paragraph("Memorize these key facts:", body_style))
    Story.append(Spacer(1, 0.1*inch))

    ref_data = [
        ['Metric', 'Value'],
        ['Migration Success Rate', '100% (7/7 test models)'],
        ['Agent Count', '6 specialized agents'],
        ['Average Migration Time', '5-30 minutes (depends on size)'],
        ['Checkpoint Frequency', 'Every 30 seconds'],
        ['Cost Savings (Karpenter)', '40-60% vs standard autoscaling'],
        ['Database', 'PostgreSQL (Multi-AZ)'],
        ['Cache', 'Redis (ElastiCache)'],
        ['Frontend', 'Vue.js 3 + TypeScript'],
        ['Backend', 'FastAPI + Python 3.12'],
        ['Infrastructure', 'Kubernetes (EKS) + Terraform'],
        ['Autoscaling', 'Karpenter (2.5min scale-up)'],
        ['API Latency Target', 'p95 < 500ms'],
        ['Uptime SLA', '99.9% (Multi-AZ)'],
    ]

    ref_table = Table(ref_data, colWidths=[3*inch, 3*inch])
    ref_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4f46e5')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('PADDING', (0, 0), (-1, -1), 8),
    ]))
    Story.append(ref_table)
    Story.append(Spacer(1, 0.3*inch))

    # Footer
    Story.append(Paragraph(
        "<b>Remember:</b> Confidence comes from genuine understanding. You built this system, "
        "you understand the trade-offs, and you can explain it clearly. Good luck!",
        body_style
    ))

    # Build PDF
    doc.build(Story)
    print(f"[OK] Interview prep PDF created: {filename}")

if __name__ == "__main__":
    create_interview_prep_pdf()
