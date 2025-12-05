# DataMigrate AI - Sales Materials

Sales presentation materials in 5 languages for partners and sales teams.

## Contents

### PowerPoint Presentations (.pptx)
Professional sales decks with 10 slides covering:
- Problem & Solution
- How It Works
- AI Agents
- Warehouses & Security
- Customer Benefits
- Pricing Plans
- Partner Benefits

### Markdown Documents (.md)
Full sales documentation suitable for:
- PDF conversion
- Word document export
- Web publishing
- Email templates

## Languages

| Language | Folder | PowerPoint | Document |
|----------|--------|------------|----------|
| English | `/en` | DataMigrate-AI-Sales-EN.pptx | DataMigrate-AI-Sales-Presentation.md |
| Spanish | `/es` | DataMigrate-AI-Sales-ES.pptx | DataMigrate-AI-Presentacion-Ventas.md |
| Portuguese | `/pt` | DataMigrate-AI-Sales-PT.pptx | DataMigrate-AI-Apresentacao-Vendas.md |
| Danish | `/da` | DataMigrate-AI-Sales-DA.pptx | DataMigrate-AI-Salgs-Praesentation.md |
| German | `/de` | DataMigrate-AI-Sales-DE.pptx | DataMigrate-AI-Vertriebs-Praesentation.md |

## Pricing Summary

### Customer Plans
| Plan | Price | Tables | Best For |
|------|-------|--------|----------|
| Starter | $499/mo | 50 | Small teams, pilots |
| Professional | $1,499/mo | 200 | Growing data teams |
| Enterprise | Custom | Unlimited | Large organizations |

### Partner Commissions
| Tier | Revenue | Commission |
|------|---------|------------|
| Silver | $0-$50K | 15% |
| Gold | $50K-$200K | 18% |
| Platinum | $200K+ | 20% |

## Converting to PDF/Word

### Using Pandoc (recommended)
```bash
# Install pandoc: https://pandoc.org/installing.html

# Convert to PDF
pandoc en/DataMigrate-AI-Sales-Presentation.md -o en/DataMigrate-AI-Sales-EN.pdf

# Convert to Word
pandoc en/DataMigrate-AI-Sales-Presentation.md -o en/DataMigrate-AI-Sales-EN.docx
```

### Using VS Code
1. Install "Markdown PDF" extension
2. Open the .md file
3. Right-click > "Markdown PDF: Export (pdf)"

### Using Online Tools
- [Dillinger.io](https://dillinger.io/) - Export to PDF/HTML
- [StackEdit](https://stackedit.io/) - Export to PDF/Word

## Regenerating PowerPoints

To regenerate all PowerPoint files:

```bash
pip install python-pptx
python generate_presentations.py
```

## Contact

- Email: sales@datamigrate.ai
- Website: www.datamigrate.ai
