# FRONTEND CLEANUP

## Purpose

Use this file only after the frontend already works and the UI direction is approved.

This is the structural pass:
- clean the code
- organize the folders
- extract reusable UI
- move logic to the right layer
- keep the approved experience intact

Do not redesign the product during this pass.

---

## Core Rule

Keep the same:
- behavior
- visual result
- theme behavior
- motion behavior
- loading, error, empty, and success states
- primary user flows

The UI should feel the same after cleanup. Only the implementation should become easier to maintain.

---

## Structure Target

Use this structure when it improves clarity:

```text
frontend/src/
  components/
    ui/
    features/
  hooks/
  services/
  stores/
  lib/
  types/
```

This is a target, not a religion. Reduce chaos, do not create ceremony.

---

## UI Components

Clean up the UI by extracting reusable pieces into `components/ui/`:
- buttons
- inputs
- cards
- badges
- dialogs
- panels
- tables
- common empty/error/loading blocks

Feature-specific blocks belong in `components/features/`.

Do not extract tiny fragments that make the code harder to understand.

---

## Hooks

Use hooks for stateful orchestration when it improves clarity:
- query orchestration
- streaming state
- form workflows
- keyboard shortcuts
- panel and modal behavior
- reusable interaction logic

Hooks should not render UI.
Presentational components should not own network orchestration.

---

## Services

Move API and transport logic into `services/`:
- REST calls
- SSE handling
- request shaping
- response normalization
- error normalization

Services return data, promises, async iterators, or callback-style interfaces.
Services should not return React components or hooks.

---

## State Management

Use the right tool for the right state:
- TanStack Query for server data
- Zustand for simple client-side app state
- `useState` or `useReducer` for local component state

Good Zustand use cases:
- current view
- open panels
- modal state
- local filters
- client-only preferences

Do not mirror server data into Zustand.

---

## Theming And Styling

During cleanup:
- keep theme tokens centralized
- remove dead classes
- consolidate repeated utility patterns
- preserve the approved light / dark / system behavior
- keep animation rules consistent

Do not flatten the final design into generic utility soup.

---

## Semantic Markup

If the working frontend ended up too messy:
- replace meaningless wrappers with semantic tags where appropriate
- keep a single clear `<main>` area
- use `<section>` only for meaningful content groups
- keep `<dialog>` for modals

Do not refactor markup just to satisfy a style preference if the current structure is readable and stable.

---

## Refactor Strategy

Refactor in small steps:
1. keep the app runnable
2. extract repeated UI
3. separate feature blocks from reusable UI
4. move API logic into services
5. move stateful orchestration into hooks
6. simplify stores
7. remove duplication

Do not mix structural refactors with visual redesign.

---

## Verification

After cleanup, verify:
- the UI still looks the same
- the main flows still work
- theme switching still works
- responsive behavior still works
- no state handling regressed
- no loading/error/empty state disappeared

If the user experience changed, the cleanup went too far.
