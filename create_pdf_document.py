"""
Create SOLID Principles Study Guide in PDF format
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY

def create_pdf_document():
    """Create PDF document"""

    # Create PDF
    doc = SimpleDocTemplate(
        "SOLID_PRINCIPLES_STUDY_GUIDE.pdf",
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=18,
    )

    # Container for the 'Flowable' objects
    elements = []

    # Define styles
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Center', alignment=TA_CENTER))
    styles.add(ParagraphStyle(
        name='Justify',
        alignment=TA_JUSTIFY,
        fontSize=11,
        leading=14
    ))

    # Title
    title_text = '<font size=18><b>SOLID Principles</b></font><br/><font size=14>Complete Study Guide</font>'
    elements.append(Paragraph(title_text, styles['Center']))
    elements.append(Spacer(1, 0.2 * inch))

    # Metadata
    elements.append(Paragraph('<b>Author:</b> Study Guide for Software Engineering Principles', styles['Normal']))
    elements.append(Paragraph('<b>Date:</b> November 2025', styles['Normal']))
    elements.append(Paragraph('<b>Purpose:</b> Comprehensive guide to SOLID, DRY, KISS, and YAGNI principles', styles['Normal']))
    elements.append(Spacer(1, 0.3 * inch))

    # Introduction
    elements.append(Paragraph('<b><font size=14>Introduction</font></b>', styles['Heading1']))
    elements.append(Spacer(1, 0.1 * inch))

    intro_text = """
    SOLID is an acronym for five design principles intended to make software designs more
    <b>understandable</b>, <b>flexible</b>, and <b>maintainable</b>. These principles were
    introduced by Robert C. Martin (Uncle Bob) in the early 2000s and have become the foundation
    of professional object-oriented software development.
    """
    elements.append(Paragraph(intro_text, styles['Justify']))
    elements.append(Spacer(1, 0.2 * inch))

    # SOLID Principles Table
    elements.append(Paragraph('<b><font size=14>The Five SOLID Principles</font></b>', styles['Heading1']))
    elements.append(Spacer(1, 0.1 * inch))

    solid_data = [
        ['Principle', 'Acronym', 'Key Point'],
        ['Single Responsibility', 'SRP', 'One class, one job'],
        ['Open/Closed', 'OCP', 'Open for extension,\nclosed for modification'],
        ['Liskov Substitution', 'LSP', 'Subtypes must be substitutable'],
        ['Interface Segregation', 'ISP', 'Small, focused interfaces'],
        ['Dependency Inversion', 'DIP', 'Depend on abstractions,\nnot concretions']
    ]

    solid_table = Table(solid_data, colWidths=[2.5 * inch, 1.2 * inch, 2.5 * inch])
    solid_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))

    elements.append(solid_table)
    elements.append(Spacer(1, 0.3 * inch))

    # 1. Single Responsibility Principle
    elements.append(PageBreak())
    elements.append(Paragraph('<b><font size=14>1. Single Responsibility Principle (SRP)</font></b>', styles['Heading1']))
    elements.append(Spacer(1, 0.1 * inch))

    srp_def = '<i>"A class should have one, and only one, reason to change."</i>'
    elements.append(Paragraph(srp_def, styles['Justify']))
    elements.append(Spacer(1, 0.1 * inch))

    srp_text = """
    Each class or module should have <b>only one job</b> or <b>responsibility</b>. This makes
    the code easier to understand, maintain, and test. When a class has multiple responsibilities,
    changes to one responsibility can affect the others, making the code fragile and hard to maintain.
    """
    elements.append(Paragraph(srp_text, styles['Justify']))
    elements.append(Spacer(1, 0.2 * inch))

    elements.append(Paragraph('<b>Why It Matters:</b>', styles['Normal']))
    srp_benefits = [
        'Changes to one responsibility don\'t affect others',
        'Easier to understand and maintain',
        'Easier to test in isolation',
        'Easier to reuse'
    ]
    for benefit in srp_benefits:
        elements.append(Paragraph(f'• {benefit}', styles['Normal']))

    elements.append(Spacer(1, 0.2 * inch))

    # 2. Open/Closed Principle
    elements.append(PageBreak())
    elements.append(Paragraph('<b><font size=14>2. Open/Closed Principle (OCP)</font></b>', styles['Heading1']))
    elements.append(Spacer(1, 0.1 * inch))

    ocp_def = '<i>"Software entities should be open for extension, but closed for modification."</i>'
    elements.append(Paragraph(ocp_def, styles['Justify']))
    elements.append(Spacer(1, 0.1 * inch))

    ocp_text = """
    You should be able to <b>add new functionality</b> without <b>changing existing code</b>.
    This reduces the risk of breaking existing functionality and makes your codebase more maintainable
    as it grows.
    """
    elements.append(Paragraph(ocp_text, styles['Justify']))
    elements.append(Spacer(1, 0.2 * inch))

    # 3. Liskov Substitution Principle
    elements.append(PageBreak())
    elements.append(Paragraph('<b><font size=14>3. Liskov Substitution Principle (LSP)</font></b>', styles['Heading1']))
    elements.append(Spacer(1, 0.1 * inch))

    lsp_def = '<i>"Objects of a superclass should be replaceable with objects of a subclass without breaking the application."</i>'
    elements.append(Paragraph(lsp_def, styles['Justify']))
    elements.append(Spacer(1, 0.1 * inch))

    lsp_text = """
    If class B is a subtype of class A, you should be able to replace A with B <b>without the program breaking</b>.
    This ensures that inheritance is used correctly and prevents unexpected behavior.
    """
    elements.append(Paragraph(lsp_text, styles['Justify']))
    elements.append(Spacer(1, 0.2 * inch))

    # 4. Interface Segregation Principle
    elements.append(PageBreak())
    elements.append(Paragraph('<b><font size=14>4. Interface Segregation Principle (ISP)</font></b>', styles['Heading1']))
    elements.append(Spacer(1, 0.1 * inch))

    isp_def = '<i>"Clients should not be forced to depend on interfaces they don\'t use."</i>'
    elements.append(Paragraph(isp_def, styles['Justify']))
    elements.append(Spacer(1, 0.1 * inch))

    isp_text = """
    Create <b>small, focused interfaces</b> instead of large, "fat" interfaces. Classes should only
    implement the methods they actually need, not be forced to implement methods they don't use.
    """
    elements.append(Paragraph(isp_text, styles['Justify']))
    elements.append(Spacer(1, 0.2 * inch))

    # 5. Dependency Inversion Principle
    elements.append(PageBreak())
    elements.append(Paragraph('<b><font size=14>5. Dependency Inversion Principle (DIP)</font></b>', styles['Heading1']))
    elements.append(Spacer(1, 0.1 * inch))

    dip_def = '<i>"High-level modules should not depend on low-level modules. Both should depend on abstractions."</i>'
    elements.append(Paragraph(dip_def, styles['Justify']))
    elements.append(Spacer(1, 0.1 * inch))

    dip_text = """
    Depend on <b>interfaces</b> or <b>abstract classes</b>, not concrete implementations. Inject dependencies
    instead of creating them. This makes code more flexible and easier to test.
    """
    elements.append(Paragraph(dip_text, styles['Justify']))
    elements.append(Spacer(1, 0.2 * inch))

    # Additional Principles
    elements.append(PageBreak())
    elements.append(Paragraph('<b><font size=14>Additional Principles</font></b>', styles['Heading1']))
    elements.append(Spacer(1, 0.2 * inch))

    additional_data = [
        ['Principle', 'Acronym', 'Key Point'],
        ['Don\'t Repeat Yourself', 'DRY', 'One source of truth'],
        ['Keep It Simple, Stupid', 'KISS', 'Simple is better than complex'],
        ['You Aren\'t Gonna Need It', 'YAGNI', 'Build only what\'s needed']
    ]

    additional_table = Table(additional_data, colWidths=[2.5 * inch, 1.2 * inch, 2.5 * inch])
    additional_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))

    elements.append(additional_table)
    elements.append(Spacer(1, 0.3 * inch))

    # DRY
    elements.append(Paragraph('<b>DRY - Don\'t Repeat Yourself</b>', styles['Heading2']))
    dry_text = """
    Every piece of knowledge should have a <b>single, unambiguous representation</b> in the system.
    Don't duplicate code or logic. If you write the same code twice, extract it into a reusable function or class.
    """
    elements.append(Paragraph(dry_text, styles['Justify']))
    elements.append(Spacer(1, 0.2 * inch))

    # KISS
    elements.append(Paragraph('<b>KISS - Keep It Simple, Stupid</b>', styles['Heading2']))
    kiss_text = """
    Most systems work best if they are kept <b>simple rather than complicated</b>. Avoid unnecessary
    complexity. Simple solutions are better than clever ones. If it can be done simply, do it simply.
    """
    elements.append(Paragraph(kiss_text, styles['Justify']))
    elements.append(Spacer(1, 0.2 * inch))

    # YAGNI
    elements.append(Paragraph('<b>YAGNI - You Aren\'t Gonna Need It</b>', styles['Heading2']))
    yagni_text = """
    Don't implement something <b>until it is necessary</b>. Don't add features "just in case".
    Build for current requirements, not hypothetical future ones. Add complexity only when needed.
    """
    elements.append(Paragraph(yagni_text, styles['Justify']))
    elements.append(Spacer(1, 0.3 * inch))

    # Benefits
    elements.append(PageBreak())
    elements.append(Paragraph('<b><font size=14>Benefits of Following These Principles</font></b>', styles['Heading1']))
    elements.append(Spacer(1, 0.1 * inch))

    benefits = [
        '<b>Maintainable</b> - Easy to modify and extend',
        '<b>Testable</b> - Easy to write unit tests',
        '<b>Flexible</b> - Easy to adapt to changes',
        '<b>Scalable</b> - Can grow without breaking',
        '<b>Professional</b> - Industry-standard practices',
        '<b>Understandable</b> - Clear responsibilities and abstractions',
        '<b>Reliable</b> - Fewer bugs and side effects'
    ]

    for benefit in benefits:
        elements.append(Paragraph(f'✓ {benefit}', styles['Normal']))
        elements.append(Spacer(1, 0.1 * inch))

    # Recommended Reading
    elements.append(PageBreak())
    elements.append(Paragraph('<b><font size=14>Recommended Reading</font></b>', styles['Heading1']))
    elements.append(Spacer(1, 0.2 * inch))

    books = [
        ('<b>"Clean Code"</b> by Robert C. Martin', 'The classic on software craftsmanship'),
        ('<b>"Clean Architecture"</b> by Robert C. Martin', 'Deep dive into SOLID principles'),
        ('<b>"Design Patterns"</b> by Gang of Four', 'Classic patterns with SOLID principles'),
        ('<b>"Head First Design Patterns"</b>', 'More approachable introduction'),
        ('<b>"Refactoring"</b> by Martin Fowler', 'How to improve existing code')
    ]

    for book, description in books:
        elements.append(Paragraph(f'{book}<br/><i>{description}</i>', styles['Normal']))
        elements.append(Spacer(1, 0.15 * inch))

    # Conclusion
    elements.append(PageBreak())
    elements.append(Paragraph('<b><font size=14>Conclusion</font></b>', styles['Heading1']))
    elements.append(Spacer(1, 0.1 * inch))

    conclusion_text = """
    SOLID principles are the <b>foundation of professional software development</b>. They help you write
    code that is easy to understand, change, test, and extend. Start applying these principles today and
    you'll see immediate improvements in your code quality!
    """
    elements.append(Paragraph(conclusion_text, styles['Justify']))
    elements.append(Spacer(1, 0.2 * inch))

    elements.append(Paragraph('<b>Next Steps:</b>', styles['Normal']))
    next_steps = [
        'Review your current project and identify violations',
        'Refactor one violation at a time',
        'Practice with simple examples',
        'Read "Clean Code" by Robert C. Martin',
        'Apply these principles in all future projects'
    ]
    for step in next_steps:
        elements.append(Paragraph(f'1. {step}', styles['Normal']))

    elements.append(Spacer(1, 0.3 * inch))
    elements.append(Paragraph('<b><font size=12>Happy coding! 🚀</font></b>', styles['Center']))

    # Build PDF
    doc.build(elements)
    print("PDF created successfully: SOLID_PRINCIPLES_STUDY_GUIDE.pdf")

if __name__ == "__main__":
    print("=" * 60)
    print("Creating SOLID Principles PDF Document")
    print("=" * 60)
    create_pdf_document()
    print("\nDone! You can now open SOLID_PRINCIPLES_STUDY_GUIDE.pdf")
