# FootprintIQ

Building footprint estimation and human QA for large retail and warehouse address corpora.

## Register

product

## Users

Bain analysts are the primary audience; client stakeholders may occasionally view results. They work in research and diligence contexts: large address lists arrive via CSV (thousands of rows), the pipeline produces estimates, and reviewers **spot-check** a sample of outputs rather than validating every row by hand. Sessions are investigative: open a location, compare satellite imagery and footprint geometry to the calc trace, record a judgment, move on. The interface should feel like a precision instrument, not a consumer app or a marketing site.

## Product Purpose

Estimate building square footage at scale for US retail and warehouse locations, then let humans verify whether the pipeline picked the right building and whether the sqft number is plausible. Success means analysts can quickly triage confidence, drill into outliers, and capture structured QA without leaving the tool. The visualizer exists to make spot-checking trustworthy and fast when the underlying dataset is huge.

## Brand Personality

Clean, minimalist, readable. Calm expert confidence: the UI stays out of the way so maps, numbers, and trace logic carry the weight. Voice is direct and factual; no hype, no decorative chrome. Emotional goal: **clarity and trust** — reviewers should feel they are looking at evidence, not a dashboard costume.

References: **Linear** (density without clutter, crisp hierarchy, purposeful color) and **Apple** (restraint, legibility, generous whitespace where it aids focus).

## Anti-references

- AI-generated UI slop: identical card grids, hero metrics, gradient text, glassmorphism, side-stripe accent borders, modal-first flows, generic SaaS landing patterns.
- Heavy "enterprise GIS" chrome: dense toolbars, ornamental panels, visual noise that competes with the map.
- Over-branded marketing surfaces inside the tool (this is research infrastructure, not a campaign).

## Design Principles

1. **Evidence first** — Map, footprint, and calculation trace are the hero; chrome and decoration are minimal.
2. **Scan, then drill** — List view supports fast triage across thousands of rows; detail view supports deep inspection of one location.
3. **Precision without theater** — Numbers, confidence, and flags are legible at a glance; no dashboard theatrics.
4. **Restraint is a feature** — Every control and label earns its place; prefer whitespace and typography over boxes and icons.
5. **Built for spot checks** — Flows optimize for sampling and recording judgment, not pretending every row gets full review.

## Accessibility & Inclusion

No specific WCAG level or accommodations mandated for v1. Default to semantic HTML, sufficient contrast for data-heavy UI, and respect for `prefers-reduced-motion` when adding motion later.
