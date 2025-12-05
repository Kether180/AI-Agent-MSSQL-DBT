# Documentation Agent

## Status: Coming Soon (20%)

## Overview
The Documentation Agent auto-generates comprehensive documentation including column descriptions, table overviews, data lineage diagrams, and ERD visualizations.

## File Locations
- Main: Not yet created
- Templates: Not yet created

## Planned Capabilities
- [ ] Auto-generate column descriptions using AI
- [ ] Create table documentation
- [ ] Generate ERD diagrams
- [ ] Build data lineage maps
- [ ] Create data dictionary
- [ ] Generate business glossary
- [ ] Export to multiple formats (MD, HTML, PDF)

## Current Implementation
- No backend implementation
- Concept only

## TODO - LOW PRIORITY
1. [ ] Design documentation templates
2. [ ] Implement AI description generator
3. [ ] Build ERD generator (Mermaid.js)
4. [ ] Create lineage tracking
5. [ ] Add export functionality

## Technical Design
```
Schema Metadata -> AI Analysis -> Template Rendering -> Output Formats
```

## Planned AI Integration
- Use OpenAI/Claude for description generation
- Context: column names, types, sample data
- Output: business-friendly descriptions

## Planned Dependencies
- OpenAI API
- Mermaid.js
- Markdown
- WeasyPrint (for PDF)

## Integration Requirements
1. Hook into post-generation pipeline
2. Add documentation viewer to frontend
3. Allow manual edits to AI suggestions
4. Version documentation with migrations

## Estimated Effort
- 2-3 sprints for basic implementation
- AI descriptions: high quality depends on training

---
Last Updated: 2024-12-05
