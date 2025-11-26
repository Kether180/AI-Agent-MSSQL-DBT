"""
Generate PDFs for Technical Ownership Guide and Terraform Infrastructure Guide
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.lib import colors
import os


def create_technical_ownership_pdf():
    """Generate Technical Ownership Guide PDF"""

    os.makedirs("docs/pdfs", exist_ok=True)
    filename = "docs/pdfs/TECHNICAL_OWNERSHIP_GUIDE.pdf"

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

    # Title Page
    Story.append(Spacer(1, 1*inch))
    Story.append(Paragraph("Demonstrating Technical Ownership", title_style))
    Story.append(Paragraph("In Job Interviews", heading_style))
    Story.append(Spacer(1, 0.3*inch))
    Story.append(Paragraph("Alexander Garcia Angus", body_style))
    Story.append(Paragraph("OKO Investments", body_style))
    Story.append(PageBreak())

    # Your Concern
    Story.append(Paragraph("Your Concern: Will Interviewers Think This is AI-Generated?", heading_style))
    Story.append(Paragraph(
        "<b>Short Answer:</b> Only if you can't explain it. Here's how to demonstrate true ownership.",
        body_style
    ))
    Story.append(Spacer(1, 0.2*inch))

    # Reality of Modern Development
    Story.append(Paragraph("The Reality of Modern Development", subheading_style))
    Story.append(Paragraph(
        "<b>ALL professional developers use AI tools in 2025:</b><br/>"
        "- GitHub Copilot<br/>"
        "- ChatGPT / Claude<br/>"
        "- Cursor IDE<br/>"
        "- Tabnine<br/><br/>"
        "<b>Interviewers KNOW this and EXPECT this.</b>",
        body_style
    ))
    Story.append(Spacer(1, 0.2*inch))

    # What They're Testing
    Story.append(Paragraph("What Interviewers Are Actually Testing:", subheading_style))
    Story.append(Paragraph(
        "1. <b>NOT:</b> \"Did you write every line yourself?\" (Nobody cares)<br/>"
        "2. <b>YES:</b> \"Do you UNDERSTAND the architecture?\" (Critical!)<br/>"
        "3. <b>YES:</b> \"Can you EXPLAIN your design decisions?\" (Critical!)<br/>"
        "4. <b>YES:</b> \"Can you MODIFY and DEBUG it?\" (Critical!)",
        body_style
    ))
    Story.append(PageBreak())

    # How to Demonstrate Ownership
    Story.append(Paragraph("How to Demonstrate True Ownership", heading_style))
    Story.append(Spacer(1, 0.1*inch))

    # Strategy 1: Add Personal Comments
    Story.append(Paragraph("1. Add Personal Comments Explaining YOUR Decisions", subheading_style))
    Story.append(Paragraph(
        "<b>BEFORE (looks AI-generated):</b><br/>"
        "<font face='Courier' size='9'>module \"vpc\" {</font><br/>"
        "<font face='Courier' size='9'>  source = \"./modules/vpc\"</font><br/>"
        "<font face='Courier' size='9'>  vpc_cidr = var.vpc_cidr</font><br/>"
        "<font face='Courier' size='9'>}</font><br/><br/>"
        "<b>AFTER (shows your thinking):</b><br/>"
        "<font face='Courier' size='9'># VPC Architecture Decision (Alexander - Nov 2025)</font><br/>"
        "<font face='Courier' size='9'># I chose 3 availability zones for high availability because:</font><br/>"
        "<font face='Courier' size='9'># 1. DataMigrate AI needs 99.9% uptime (SLA requirement)</font><br/>"
        "<font face='Courier' size='9'># 2. AWS recommends multi-AZ for production workloads</font><br/>"
        "<font face='Courier' size='9'># 3. Cost: Only 30% more than single-AZ but 10x more reliable</font><br/>"
        "<font face='Courier' size='9'>module \"vpc\" {</font><br/>"
        "<font face='Courier' size='9'>  source = \"./modules/vpc\"</font><br/>"
        "<font face='Courier' size='9'>  vpc_cidr = var.vpc_cidr</font><br/>"
        "<font face='Courier' size='9'>}</font>",
        body_style
    ))
    Story.append(Spacer(1, 0.2*inch))

    # Strategy 2: Architecture Decision Records
    Story.append(Paragraph("2. Create Architecture Decision Records (ADR)", subheading_style))
    Story.append(Paragraph(
        "Document your technical decisions in an ADR file:<br/><br/>"
        "<b>Example ADR: Why LangGraph Instead of LangChain</b><br/>"
        "Date: November 2025<br/>"
        "Author: Alexander Garcia Angus<br/>"
        "Status: Accepted<br/><br/>"
        "<b>Context:</b> Need multi-agent system for MSSQL to dbt migrations.<br/><br/>"
        "<b>Decision:</b> Chose LangGraph because:<br/>"
        "- Migrations take 30+ minutes (need state persistence)<br/>"
        "- LangGraph provides built-in checkpointing<br/>"
        "- Can resume from failures (spot instance interruptions)<br/><br/>"
        "<b>Consequences:</b><br/>"
        "Positive: Recoverable from failures, agent state saved to PostgreSQL<br/>"
        "Negative: Steeper learning curve than LangChain<br/>"
        "Mitigation: Extensive documentation and unit tests",
        body_style
    ))
    Story.append(PageBreak())

    # Strategy 3: Write Tests
    Story.append(Paragraph("3. Write Tests That Show YOUR Custom Logic", subheading_style))
    Story.append(Paragraph(
        "<b>Example: Test checkpoint system you designed</b><br/><br/>"
        "<font face='Courier' size='9'>def test_resume_from_checkpoint_after_interruption():</font><br/>"
        "<font face='Courier' size='9'>    \"\"\"</font><br/>"
        "<font face='Courier' size='9'>    Test migration resumes from last checkpoint.</font><br/>"
        "<font face='Courier' size='9'>    This is MY CODE for handling spot interruptions.</font><br/>"
        "<font face='Courier' size='9'>    \"\"\"</font><br/>"
        "<font face='Courier' size='9'>    migration = create_test_migration(tables=100)</font><br/>"
        "<font face='Courier' size='9'>    save_checkpoint(migration_id=migration.id, last_table=50)</font><br/>"
        "<font face='Courier' size='9'>    </font><br/>"
        "<font face='Courier' size='9'>    result = run_migration(migration.id)</font><br/>"
        "<font face='Courier' size='9'>    </font><br/>"
        "<font face='Courier' size='9'>    assert result['tables_processed'] == 50  # Only remaining</font><br/>"
        "<font face='Courier' size='9'>    assert migration.status == 'completed'</font><br/><br/>"
        "<b>In Interview:</b> \"I wrote comprehensive tests for the checkpoint system, including "
        "edge cases I discovered through chaos testing. For example, I manually corrupted checkpoint "
        "data to ensure the system gracefully falls back to restarting the migration...\"",
        body_style
    ))
    Story.append(Spacer(1, 0.2*inch))

    # Strategy 4: Portfolio File
    Story.append(Paragraph("4. Create a PORTFOLIO.md File for Interviewers", subheading_style))
    Story.append(Paragraph(
        "Create a file specifically showcasing your key contributions:<br/><br/>"
        "<b>What I Built (Key Contributions)</b><br/><br/>"
        "1. <b>Multi-Agent AI System (LangGraph)</b><br/>"
        "   Problem: MSSQL to dbt migrations too complex for single-agent LLMs<br/>"
        "   Solution: Designed 5 specialized agents with state persistence<br/>"
        "   Results: 100% success rate (7/7 test models)<br/><br/>"
        "2. <b>Checkpoint System for Long-Running Migrations</b><br/>"
        "   Problem: Migrations take 30+ minutes, spot instances can be terminated<br/>"
        "   Solution: Save progress every 30 seconds to PostgreSQL<br/>"
        "   Results: Zero data loss, 70% cost savings using spot instances",
        body_style
    ))
    Story.append(PageBreak())

    # Strategy 5: Practice Explaining
    Story.append(Paragraph("5. Practice Explaining Your Code Live", subheading_style))
    Story.append(Paragraph(
        "<b>Prepare to:</b><br/>"
        "- Walk through code line by line<br/>"
        "- Modify code on the spot (add a new feature)<br/>"
        "- Debug a bug you introduce intentionally<br/>"
        "- Discuss trade-offs (why X over Y)<br/>"
        "- Show working demos<br/><br/>"
        "<b>If you can do these, NO interviewer will doubt your ownership!</b>",
        body_style
    ))
    Story.append(Spacer(1, 0.2*inch))

    # When Asked About AI Assistance
    Story.append(Paragraph("How to Handle: 'Did You Use AI to Build This?'", heading_style))
    Story.append(Paragraph(
        "<b>Interviewer:</b> \"Did you use AI to build this?\"<br/><br/>"
        "<b>You:</b> \"Absolutely. I use Claude Code and GitHub Copilot daily - every professional "
        "developer does in 2025. But what matters is that I can explain every architectural decision "
        "I made. For example, I chose LangGraph over LangChain because migrations take 30+ minutes "
        "and require state persistence. LangGraph provides built-in checkpointing to PostgreSQL. "
        "I designed the checkpoint system to handle spot interruptions - we save state every 30 seconds. "
        "I can walk you through the code, modify it live, or debug it - whatever you'd like to see.\"<br/><br/>"
        "<b>This shows:</b><br/>"
        "- Honesty about using tools<br/>"
        "- Deep understanding of decisions<br/>"
        "- Confidence in your knowledge",
        body_style
    ))
    Story.append(PageBreak())

    # Final Checklist
    Story.append(Paragraph("Final Checklist: Prove True Ownership", heading_style))
    Story.append(Paragraph(
        "Before your interview, make sure you can:<br/><br/>"
        "[ ] <b>Explain every architectural decision</b> (why Kubernetes? why LangGraph? why PostgreSQL?)<br/>"
        "[ ] <b>Walk through the code live</b> (open files and explain line by line)<br/>"
        "[ ] <b>Modify code on the spot</b> (add a new agent, change a checkpoint interval)<br/>"
        "[ ] <b>Debug a bug</b> (simulate a failure, show how you'd fix it)<br/>"
        "[ ] <b>Discuss trade-offs</b> (why you chose X over Y, what you'd do differently)<br/>"
        "[ ] <b>Show working demos</b> (run a migration, show Kubernetes dashboard)<br/><br/>"
        "<b>If you can do these, NO interviewer will doubt your ownership!</b>",
        body_style
    ))
    Story.append(Spacer(1, 0.5*inch))

    # Footer
    Story.append(Paragraph(
        "<b>Remember:</b> Modern development uses AI tools. What matters is understanding "
        "your architecture, explaining your decisions clearly, and demonstrating you can modify and debug the code. "
        "You built this system - show that you truly understand it.",
        body_style
    ))

    doc.build(Story)
    print(f"[OK] Technical Ownership PDF created: {filename}")


def create_terraform_infrastructure_pdf():
    """Generate Terraform Infrastructure Guide PDF"""

    os.makedirs("docs/pdfs", exist_ok=True)
    filename = "docs/pdfs/TERRAFORM_INFRASTRUCTURE_GUIDE.pdf"

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
        leftIndent=20,
        spaceAfter=12
    )

    # Title Page
    Story.append(Spacer(1, 1*inch))
    Story.append(Paragraph("Terraform Infrastructure Guide", title_style))
    Story.append(Paragraph("DataMigrate AI", heading_style))
    Story.append(Spacer(1, 0.3*inch))
    Story.append(Paragraph("Alexander Garcia Angus", body_style))
    Story.append(Paragraph("OKO Investments", body_style))
    Story.append(PageBreak())

    # Overview
    Story.append(Paragraph("Overview", heading_style))
    Story.append(Paragraph(
        "DataMigrate AI uses <b>Terraform</b> to manage all AWS infrastructure as code. "
        "This provides version control, reproducibility, and team collaboration for infrastructure changes.",
        body_style
    ))
    Story.append(Spacer(1, 0.2*inch))

    # Why Terraform
    Story.append(Paragraph("Why Terraform?", subheading_style))
    Story.append(Paragraph(
        "<b>1. Infrastructure as Code (IaC)</b><br/>"
        "- Infrastructure defined in version-controlled files<br/>"
        "- Track changes over time with Git<br/>"
        "- Review infrastructure changes like code reviews<br/><br/>"
        "<b>2. Reproducible Environments</b><br/>"
        "- Identical dev, staging, and production environments<br/>"
        "- No configuration drift<br/>"
        "- Easy disaster recovery<br/><br/>"
        "<b>3. Multi-Cloud Support</b><br/>"
        "- Works with AWS, Azure, GCP, and 100+ providers<br/>"
        "- Future flexibility for OKO Investments<br/><br/>"
        "<b>4. Team Collaboration</b><br/>"
        "- State managed in S3 + DynamoDB<br/>"
        "- Prevent concurrent modifications (state locking)<br/>"
        "- Clear ownership and change history<br/><br/>"
        "<b>5. Cost Transparency</b><br/>"
        "- See exactly what resources are deployed<br/>"
        "- Easy to tear down unused environments<br/>"
        "- Estimate costs before deployment",
        body_style
    ))
    Story.append(PageBreak())

    # Architecture
    Story.append(Paragraph("Architecture Deployed", heading_style))
    Story.append(Paragraph(
        "Terraform deploys a <b>production-ready, scalable architecture</b> with these components:",
        body_style
    ))
    Story.append(Spacer(1, 0.2*inch))

    arch_data = [
        ['Component', 'Technology', 'Purpose'],
        ['Frontend', 'S3 + CloudFront', 'Vue.js static hosting with CDN'],
        ['API Gateway', 'ALB (HTTPS)', 'Load balancing and SSL termination'],
        ['Backend', 'ECS Fargate', 'FastAPI containers with auto-scaling'],
        ['Database', 'RDS PostgreSQL 15', 'Multi-AZ, encrypted, automated backups'],
        ['Cache', 'ElastiCache Redis', 'Session storage and caching'],
        ['Network', 'VPC (3 AZs)', 'Public, private, and database subnets'],
    ]

    arch_table = Table(arch_data, colWidths=[1.5*inch, 2*inch, 2.5*inch])
    arch_table.setStyle(TableStyle([
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
    Story.append(arch_table)
    Story.append(Spacer(1, 0.2*inch))

    Story.append(Paragraph("<b>Network Architecture:</b>", body_style))
    Story.append(Paragraph(
        "- <b>VPC</b> with 3 availability zones for high availability<br/>"
        "- <b>Public Subnets:</b> ALB, NAT Gateways (internet-facing)<br/>"
        "- <b>Private Subnets:</b> ECS tasks (FastAPI containers, no direct internet)<br/>"
        "- <b>Database Subnets:</b> RDS (completely isolated, no internet)<br/>"
        "- <b>Security Groups:</b> Least privilege access control",
        body_style
    ))
    Story.append(PageBreak())

    # Quick Start
    Story.append(Paragraph("Quick Start", heading_style))
    Story.append(Paragraph("<b>1. Prerequisites</b>", subheading_style))
    Story.append(Paragraph(
        "<font face='Courier' size='9'># Install Terraform</font><br/>"
        "<font face='Courier' size='9'>brew install terraform  # macOS</font><br/>"
        "<font face='Courier' size='9'>choco install terraform # Windows</font><br/><br/>"
        "<font face='Courier' size='9'># Install AWS CLI</font><br/>"
        "<font face='Courier' size='9'>brew install awscli</font><br/><br/>"
        "<font face='Courier' size='9'># Configure AWS credentials</font><br/>"
        "<font face='Courier' size='9'>aws configure</font>",
        body_style
    ))
    Story.append(Spacer(1, 0.2*inch))

    Story.append(Paragraph("<b>2. Deploy Infrastructure</b>", subheading_style))
    Story.append(Paragraph(
        "<font face='Courier' size='9'>cd terraform</font><br/><br/>"
        "<font face='Courier' size='9'># Initialize Terraform</font><br/>"
        "<font face='Courier' size='9'>terraform init</font><br/><br/>"
        "<font face='Courier' size='9'># Preview changes</font><br/>"
        "<font face='Courier' size='9'>terraform plan</font><br/><br/>"
        "<font face='Courier' size='9'># Deploy (takes 15-20 minutes)</font><br/>"
        "<font face='Courier' size='9'>terraform apply</font><br/><br/>"
        "<font face='Courier' size='9'># Get outputs</font><br/>"
        "<font face='Courier' size='9'>terraform output</font>",
        body_style
    ))
    Story.append(PageBreak())

    # Modules
    Story.append(Paragraph("Terraform Modules", heading_style))
    Story.append(Paragraph(
        "Infrastructure is organized into reusable modules for maintainability:",
        body_style
    ))
    Story.append(Spacer(1, 0.2*inch))

    modules_data = [
        ['Module', 'Purpose', 'Resources Created'],
        ['vpc', 'Network infrastructure', 'VPC, Subnets, NAT Gateways, Route Tables'],
        ['security', 'Security groups', 'ALB SG, ECS SG, RDS SG'],
        ['rds', 'PostgreSQL database', 'RDS instance, Parameter group, Backups, Alarms'],
        ['ecs', 'FastAPI backend', 'ECS cluster, Service, Tasks, ALB, Auto-scaling'],
        ['s3_cloudfront', 'Vue.js frontend', 'S3 bucket, CloudFront CDN, SSL certificate'],
    ]

    modules_table = Table(modules_data, colWidths=[1.2*inch, 2*inch, 2.8*inch])
    modules_table.setStyle(TableStyle([
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
    Story.append(modules_table)
    Story.append(PageBreak())

    # Cost Breakdown
    Story.append(Paragraph("Cost Breakdown (Development Environment)", heading_style))

    cost_data = [
        ['Service', 'Monthly Cost', 'Notes'],
        ['NAT Gateways (3)', '$32.40', '3 AZs for high availability'],
        ['RDS PostgreSQL', '$14.00', 'db.t3.micro (free tier eligible)'],
        ['ECS Fargate', '$25.00', '2 tasks (0.5 vCPU, 1GB RAM)'],
        ['Application Load Balancer', '$16.00', 'HTTPS with SSL certificate'],
        ['S3 + CloudFront', '$10.50', 'Static hosting + CDN'],
        ['CloudWatch Logs', '$5.00', '30-day retention'],
        ['TOTAL', '$105/month', 'Development environment'],
    ]

    cost_table = Table(cost_data, colWidths=[2*inch, 1.5*inch, 2.5*inch])
    cost_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4f46e5')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
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

    Story.append(Paragraph("<b>Cost Optimization Tips:</b>", subheading_style))
    Story.append(Paragraph(
        "- Use VPC Endpoints instead of NAT Gateways (saves $32/month)<br/>"
        "- RDS Reserved Instances provide 40-60% savings<br/>"
        "- Scale down ECS tasks during off-hours (nights/weekends)<br/>"
        "- S3 Intelligent Tiering for automatic cost optimization",
        body_style
    ))
    Story.append(PageBreak())

    # Security
    Story.append(Paragraph("Security Features", heading_style))
    Story.append(Paragraph(
        "<b>Network Isolation</b><br/>"
        "- Database in private subnets (no internet access)<br/>"
        "- ECS tasks in private subnets<br/>"
        "- ALB in public subnets only<br/><br/>"
        "<b>Encryption</b><br/>"
        "- RDS storage encrypted with AES-256<br/>"
        "- S3 bucket encryption enabled<br/>"
        "- HTTPS only (CloudFront, ALB with SSL)<br/><br/>"
        "<b>Access Control</b><br/>"
        "- IAM roles (no hardcoded credentials)<br/>"
        "- Security groups with least privilege<br/>"
        "- VPC Flow Logs for network monitoring<br/><br/>"
        "<b>Compliance</b><br/>"
        "- Automated backups (7 days retention)<br/>"
        "- Multi-AZ deployment for high availability<br/>"
        "- Deletion protection on production resources<br/>"
        "- Audit logging with CloudTrail",
        body_style
    ))
    Story.append(PageBreak())

    # Common Commands
    Story.append(Paragraph("Common Terraform Commands", heading_style))
    Story.append(Paragraph(
        "<font face='Courier' size='9'># Initialize (first time or after adding modules)</font><br/>"
        "<font face='Courier' size='9'>terraform init</font><br/><br/>"
        "<font face='Courier' size='9'># Preview changes</font><br/>"
        "<font face='Courier' size='9'>terraform plan</font><br/><br/>"
        "<font face='Courier' size='9'># Apply changes</font><br/>"
        "<font face='Courier' size='9'>terraform apply</font><br/><br/>"
        "<font face='Courier' size='9'># Destroy all resources</font><br/>"
        "<font face='Courier' size='9'>terraform destroy</font><br/><br/>"
        "<font face='Courier' size='9'># Show current state</font><br/>"
        "<font face='Courier' size='9'>terraform show</font><br/><br/>"
        "<font face='Courier' size='9'># Get specific output</font><br/>"
        "<font face='Courier' size='9'>terraform output api_endpoint</font><br/><br/>"
        "<font face='Courier' size='9'># Format code</font><br/>"
        "<font face='Courier' size='9'>terraform fmt -recursive</font><br/><br/>"
        "<font face='Courier' size='9'># Validate configuration</font><br/>"
        "<font face='Courier' size='9'>terraform validate</font>",
        body_style
    ))
    Story.append(PageBreak())

    # Best Practices
    Story.append(Paragraph("Best Practices", heading_style))
    Story.append(Paragraph(
        "<b>1. Never Commit Secrets</b><br/>"
        "- Use AWS Secrets Manager for database passwords<br/>"
        "- Never put credentials in terraform.tfvars<br/>"
        "- .tfvars files are gitignored<br/><br/>"
        "<b>2. Use Remote State</b><br/>"
        "- State stored in S3 (team collaboration)<br/>"
        "- State locking with DynamoDB (prevent conflicts)<br/>"
        "- Versioning enabled on S3 bucket<br/><br/>"
        "<b>3. Test in Dev First</b><br/>"
        "- Always apply changes to dev environment first<br/>"
        "- Verify everything works before staging/prod<br/>"
        "- Use terraform plan to preview changes<br/><br/>"
        "<b>4. Tag Everything</b><br/>"
        "- All resources tagged with Environment, Project, Owner<br/>"
        "- Easy cost tracking and resource management<br/>"
        "- Automated tagging via default_tags<br/><br/>"
        "<b>5. Use Modules</b><br/>"
        "- DRY principle (Don't Repeat Yourself)<br/>"
        "- Reusable infrastructure components<br/>"
        "- Easier to maintain and update",
        body_style
    ))
    Story.append(PageBreak())

    # Deployment Integration
    Story.append(Paragraph("Integration with DataMigrate AI", heading_style))

    Story.append(Paragraph("<b>Frontend Deployment</b>", subheading_style))
    Story.append(Paragraph(
        "<font face='Courier' size='9'># Build Vue.js app</font><br/>"
        "<font face='Courier' size='9'>cd frontend</font><br/>"
        "<font face='Courier' size='9'>npm run build</font><br/><br/>"
        "<font face='Courier' size='9'># Deploy to S3</font><br/>"
        "<font face='Courier' size='9'>aws s3 sync dist/ s3://$(terraform output -raw frontend_bucket) --delete</font><br/><br/>"
        "<font face='Courier' size='9'># Invalidate CloudFront cache</font><br/>"
        "<font face='Courier' size='9'>aws cloudfront create-invalidation \\</font><br/>"
        "<font face='Courier' size='9'>  --distribution-id $(terraform output -raw cloudfront_distribution_id) \\</font><br/>"
        "<font face='Courier' size='9'>  --paths \"/*\"</font>",
        body_style
    ))
    Story.append(Spacer(1, 0.2*inch))

    Story.append(Paragraph("<b>Backend Deployment</b>", subheading_style))
    Story.append(Paragraph(
        "<font face='Courier' size='9'># Build and push Docker image</font><br/>"
        "<font face='Courier' size='9'>docker build -t datamigrate-ai/fastapi:latest .</font><br/>"
        "<font face='Courier' size='9'>docker tag datamigrate-ai/fastapi:latest <ecr-repo-url>:latest</font><br/>"
        "<font face='Courier' size='9'>docker push <ecr-repo-url>:latest</font><br/><br/>"
        "<font face='Courier' size='9'># ECS will auto-deploy new image</font><br/>"
        "<font face='Courier' size='9'>aws ecs update-service \\</font><br/>"
        "<font face='Courier' size='9'>  --cluster $(terraform output -raw ecs_cluster_name) \\</font><br/>"
        "<font face='Courier' size='9'>  --service $(terraform output -raw ecs_service_name) \\</font><br/>"
        "<font face='Courier' size='9'>  --force-new-deployment</font>",
        body_style
    ))
    Story.append(PageBreak())

    # Environments Comparison
    Story.append(Paragraph("Environment Configurations", heading_style))

    env_data = [
        ['Aspect', 'Development', 'Production'],
        ['Monthly Cost', '$105', '$500-1,000'],
        ['RDS Instance', 'db.t3.micro', 'db.t3.medium+ Multi-AZ'],
        ['ECS Tasks', '2 tasks', '4-20 tasks (auto-scaling)'],
        ['Backup Retention', '3 days', '7 days'],
        ['Features', 'Basic', 'Performance Insights, WAF'],
    ]

    env_table = Table(env_data, colWidths=[2*inch, 2*inch, 2*inch])
    env_table.setStyle(TableStyle([
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
    Story.append(env_table)
    Story.append(Spacer(1, 0.3*inch))

    # Footer
    Story.append(Paragraph(
        "<b>Next Steps:</b><br/>"
        "1. Review the Terraform code in the /terraform directory<br/>"
        "2. Customize terraform.tfvars for your environment<br/>"
        "3. Deploy to AWS with terraform apply<br/>"
        "4. Set up CI/CD pipeline for automated deployments",
        body_style
    ))

    doc.build(Story)
    print(f"[OK] Terraform Infrastructure PDF created: {filename}")


if __name__ == "__main__":
    create_technical_ownership_pdf()
    create_terraform_infrastructure_pdf()
