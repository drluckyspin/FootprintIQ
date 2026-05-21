---
name: FootprintIQ
description: Minimal research UI for spot-checking building footprint estimates at scale
colors:
  background-dark: "#0a0a0a"
  foreground-dark: "#ededed"
  muted-dark: "#1a1a1a"
  border-dark: "#2a2a2a"
  background-light: "#fafafa"
  foreground-light: "#0a0a0a"
  muted-light: "#f4f4f5"
  border-light: "#e4e4e7"
  primary: "#3b82f6"
  confidence-high: "#16a34a"
  confidence-medium: "#ca8a04"
  confidence-low: "#ea580c"
  confidence-unmatched: "#dc2626"
  action-blue: "#2563eb"
  action-blue-hover: "#1d4ed8"
typography:
  body:
    fontFamily: "ui-sans-serif, system-ui, -apple-system, sans-serif"
    fontSize: "1rem"
    fontWeight: 400
    lineHeight: 1.5
  title:
    fontFamily: "ui-sans-serif, system-ui, -apple-system, sans-serif"
    fontSize: "1.5rem"
    fontWeight: 700
    lineHeight: 1.25
  display:
    fontFamily: "ui-sans-serif, system-ui, -apple-system, sans-serif"
    fontSize: "1.875rem"
    fontWeight: 700
    lineHeight: 1.2
  label:
    fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace"
    fontSize: "0.75rem"
    fontWeight: 400
    lineHeight: 1.4
rounded:
  sm: "4px"
  md: "6px"
spacing:
  page: "32px"
  section: "24px"
  control: "12px"
components:
  input-default:
    backgroundColor: "transparent"
    textColor: "{colors.foreground-dark}"
    rounded: "{rounded.sm}"
    padding: "8px 12px"
  button-primary:
    backgroundColor: "{colors.action-blue}"
    textColor: "#ffffff"
    rounded: "{rounded.sm}"
    padding: "6px 12px"
  panel-bordered:
    backgroundColor: "transparent"
    textColor: "{colors.foreground-dark}"
    rounded: "{rounded.sm}"
    padding: "16px"
---

# Design System: FootprintIQ

## Overview

**Creative North Star: "The Field Instrument"**

A restrained research console: map and numbers first, chrome second. Density follows Linear (compact tables, clear hierarchy); calm and legibility follow Apple (system type, neutral surfaces, color only where it signals meaning). The system rejects dashboard theater, decorative cards, and anything that reads as generic AI UI.

**Key characteristics:**

- System-native sans and mono; no display marketing typefaces
- Dark default with `prefers-color-scheme: light` parity via CSS variables
- Flat surfaces: borders and tonal contrast, not drop shadows
- Semantic confidence colors reserved for data status, not decoration
- Max content width ~72rem (`max-w-6xl`) for readable line length on prose

## Colors

A **restrained** palette: tinted neutrals carry the UI; blue is the sole interactive accent; green–amber–orange–red encode pipeline confidence only.

### Primary

- **Signal Blue** (`#3b82f6`): Links, focus, and primary actions. Defined as `--primary` in `globals.css`. Submit buttons currently use a sibling shade (`#2563eb` / `#1d4ed8` on hover); align new work to `--primary` when refactoring.

### Neutral

- **Obsidian Canvas** (`#0a0a0a` / `#fafafa`): Page background (dark / light).
- **Soft Ink** (`#ededed` / `#0a0a0a`): Body text.
- **Quiet Surface** (`#1a1a1a` / `#f4f4f5`): Muted fills (table header wash uses `bg-black/5` in dark).
- **Hairline Rule** (`#2a2a2a` / `#e4e4e7`): Borders on tables, inputs, QA panels.

### Tertiary (semantic data only)

- **Verified Green** (`#16a34a`): High confidence
- **Caution Amber** (`#ca8a04`): Medium confidence
- **Review Orange** (`#ea580c`): Low confidence
- **Unmatched Red** (`#dc2626`): Unmatched / error states

### Named Rules

**The Evidence Accent Rule.** Blue and confidence hues appear only on data, controls, or status. Never as page-wide gradients or decorative fills.

**The No Slop Rule.** No gradient text, glass cards, side-stripe callouts, or identical icon-card grids. If a pattern appears on a SaaS landing template, it does not belong here.

## Typography

**Display / Title / Body Font:** System UI sans (`ui-sans-serif, system-ui, -apple-system, sans-serif`)

**Data / ID Font:** System monospace (`ui-monospace`, `font-mono text-xs`) for location IDs, trace values, and tabular numbers (`tabular-nums`)

**Character:** Neutral, highly legible, zero brand flourish. Hierarchy is weight and size, not color.

### Hierarchy

- **Display** (700, `text-3xl` / 1.875rem): Home page title ("FootprintIQ")
- **Title** (700, `text-2xl` / 1.5rem): Location detail heading (`location_id`)
- **Section** (600, `text-lg`): "Calculation trace", "QA review"
- **Body** (400, `text-sm`–`text-base`, opacity 70–80 for secondary copy): Descriptions, table cells, form labels
- **Label / Mono** (400, `text-xs` mono): IDs, trace `dd` values, sqft columns

### Named Rules

**The 65ch Rule.** Prose and long address strings truncate or wrap; main column stays within `max-w-6xl` so reading does not sprawl edge-to-edge on wide monitors.

## Elevation

Flat-by-default. Depth is conveyed with 1px borders (`border-[var(--border)]`), subtle background washes (`bg-black/5`, `bg-amber-500/5` for test rows), and spacing—not box shadows. MapLibre canvas is the one "lifted" surface; UI chrome stays flush with the page.

**The Flat Instrument Rule.** Do not add shadows to tables, forms, or cards unless introducing a true overlay (dialog, popover). Prefer border + padding over card elevation.

## Components

### Search input

Single full-width field: transparent background, `border-[var(--border)]`, `rounded`, `text-sm`, `px-3 py-2`. Placeholder-driven; no icon adornment.

### Data table

`min-w-full text-left text-sm` inside `overflow-x-auto` + bordered container. Header row: bottom border + light muted wash. Body rows: hairline separators; test fixtures (`TEST_*` ids) get amber tint, not a second card layer.

### Links

Underlined `text-sm`; test rows use amber link color in dark/light. No button-styled links in tables.

### QA form panel

`rounded border border-[var(--border)] p-4` — a bordered panel, not a floating card. Native `<select>` and `<textarea>` match input styling (transparent bg, border token). Primary submit: filled blue button, `text-sm`.

### Calculation trace

Definition list (`dl` / `dt` / `dd`): labels at 70% opacity, values in mono `text-xs`. Flags as simple disc list—no badge components unless encoding status.

### Map (MapLibre)

Full-width in grid column; no decorative frame. Respect `maplibregl-canvas { outline: none }`.

### Location navigation

Compact prev/next between locations; text links, not pill buttons.

## Do's and Don'ts

**Do**

- Use CSS variables from `:root` for background, foreground, border, and confidence colors
- Keep tables scannable: tabular nums, mono IDs, capitalize confidence in cells until badge tokens exist
- Preserve keyboard-friendly native controls (`select`, `textarea`, `button`)
- Let the satellite map dominate the detail layout (`lg:grid-cols-2`)

**Don't**

- Introduce shadcn card grids, hero metrics, or icon+heading feature tiles
- Hardcode new blues outside the `--primary` / action pair without updating this file
- Add modal-first QA flows; inline forms and navigation are sufficient
- Use em dashes in UI copy; prefer commas or periods
- Animate layout properties; if motion is added later, ease-out only and honor `prefers-reduced-motion`
