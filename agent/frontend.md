# FRONTEND

## Quick Context

This frontend starts scaffolded with:
- Vite + React 19 + TypeScript
- Tailwind CSS v4 for styling

Recommended additions depending on the project:
- Framer Motion for animation
- TanStack Query for server data
- Zustand for simple client-side app state and navigation
- TanStack Router only when URLs, browser history, or shareable routes are required

Use global theme tokens in `src/index.css`. Light / Dark / System support is expected from the start.

This file is the **first pass** frontend guide: make the product feel excellent first.
After the frontend is functional and the UI direction is approved, use `frontend_cleanup.md` to reorganize components, hooks, services, and state without changing the approved experience.

---

## Purpose

The priority is not frontend purity. The priority is a frontend with excellent UI and UX: clear, beautiful, app-like, and convincing from the first run.

---

## Core Rule

**The first frontend pass is allowed to be structurally messy if the user experience is strong.**

Do not spend early effort on splitting files, extracting tiny components, or enforcing frontend architecture purity if that weakens visual quality, usability, or product clarity.

First make it:
- functional
- visually strong
- easy to understand
- satisfying to interact with
- complete in all states

---

## Product Shape

Default to an **app-style frontend**:
- One screen mentality
- Avoid full page reloads
- Avoid long pages and unnecessary document scrolling
- Prefer keeping the main workflow visible in a single viewport
- Think in terms of workspace, panels, trays, inspectors, toolbars, and focused actions
- Avoid bloated content: overlong descriptions, redundant titles, repeated data, and overly granular detail
- Use modals, slide-over panels, and collapsible sections when they improve focus

If scrolling is needed, prefer a single clear scroll container for the main content. Use internal scrolling only for bounded regions such as tables, logs, chat transcripts, or side panels. Avoid stacked scroll areas unless there is a clear product reason.

The UI should feel like a product someone can use for hours, not like a generic landing page or a template demo.

---

## UX Priorities

Optimize for these in order:

1. Immediate clarity
2. Strong visual hierarchy
3. Fast task completion
4. Low cognitive load
5. Polished feedback during every interaction
6. Consistency between screens and states

Every screen should answer instantly:
- What is this?
- What can I do here?
- What matters most right now?
- What should I click next?

---

## Layout Direction

Default layout:
- Persistent theme toggle (system/dark/light)
- Optional side panel for secondary actions, settings, etc
- Optional footer only if it adds real value
- Use icons to support text, not replace it
- Keep shape language intentional and consistent across panels, buttons, inputs, and dialogs

The main workflow should remain visible without jumping between many screens.

Prefer:
- predictable panel behavior
- short travel distance between related actions
- keeping the primary controls and main task visible within the viewport whenever possible
- animated soft transitions
- aligned elements, compact controls, and a restrained visual rhythm

Avoid:
- hidden primary actions
- giant empty areas
- accidental scroll mazes or unnecessary nested scrolls
- dashboard clutter
- fake “premium” decoration with weak usability
- excessive margin or padding
- weak alignment or inconsistent spacing

---

## Theme System

**Light / Dark / System is mandatory from day 1.**

Requirements:
- Support `light`, `dark`, and `system`
- The toggle must always be reachable
- Use global design tokens in `src/index.css`
- Colors, surfaces, borders, spacing accents, shadows, and radii should be centrally controlled
- Be careful with color behavior on both dark and light backgrounds
- The UI must look intentionally designed in both light and dark

Do not build light mode well and let dark mode become an afterthought.

---

## Visual Quality

Aim for a frontend that feels:
- minimalist
- intentional
- modern
- calm
- sharp
- high trust
- product-grade

Strong aesthetic choices:
- a clear spacing rhythm
- a defined surface system
- a deliberate typography scale
- restrained but meaningful color accents
- visible states for hover, active, selected, loading, success, and error

Do not settle for:
- default Tailwind-looking UI
- random card grids
- generic centered forms
- “clean but empty” layouts

---

## Interaction Quality

Interactions should feel expensive in the good sense:
- smooth appearance and exit transitions
- no jarring layout jumps
- loading states that reassure instead of block
- empty states that teach
- error states that explain and recover
- disabled states that still look intentional

Use motion with discipline:
- small transitions
- purposeful panel movement
- soft fades and position shifts
- no decorative motion without UX value

---

## Information Design

The frontend must establish a clear hierarchy:
- one dominant primary area
- a visible current task
- a clear primary action
- secondary actions visually subordinate
- supporting information grouped near the thing it affects

If the UI shows data:
- summarize first
- detail second
- raw dumps last

If the UI shows forms:
- group fields by intent
- keep labels clear
- reduce noise
- show defaults and constraints early

---

## What “Good” Looks Like

A good V1 frontend should feel like:
- a real product, not a starter kit
- fast to scan
- hard to misuse
- easy to trust
- good on desktop, laptop and mobile

It should be possible for the user to open the app and immediately think:
"Yes, this already feels like software."

---

## Minimum Bar

Before calling the frontend good enough:
- the main task fits naturally in the viewport
- light mode looks finished
- dark mode looks finished
- system mode works
- loading, error, empty, and success states exist
- spacing is consistent
- the main action is obvious
- the visual style feels chosen, not accidental

---

## Do Not Optimize Yet

On the first frontend pass, do **not** obsess over:
- directory purity
- micro-component extraction
- aggressive file splitting
- abstracting every style decision
- generalized component systems

That comes later in the cleanup pass.
