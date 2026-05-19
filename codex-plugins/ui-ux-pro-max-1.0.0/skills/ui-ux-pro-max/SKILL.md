---
name: ui-ux-pro-max
description: Use before frontend UI work to analyze user flows, information architecture, interaction patterns, layout structure, responsive behavior, and state coverage.
---

# UI UX Pro Max

Use this skill before generating or changing frontend code for a page, interface, component workflow, or user interaction.

## When to Use

- The user asks to create a new page, app screen, dashboard, form, editor, game UI, or marketing page.
- The user asks to redesign, restyle, reorganize, or improve an existing interface.
- The request changes a user flow, navigation pattern, input flow, modal, empty state, loading state, or error state.
- The implementation affects responsive layout, accessibility, or repeated user actions.

## Design Pass

Before editing frontend code, briefly work through:

1. User story: state the target user and the task they are trying to complete in one sentence.
2. Core flow: list the path from entry point to successful completion, including key decisions.
3. Information architecture: identify primary information, secondary information, navigation, and data flow from input to feedback.
4. Interaction model: choose modal vs non-modal, inline vs separate editing, reversible actions, keyboard access, and state transitions.
5. Interface structure: describe the main layout regions, priority of each region, and responsive breakpoint behavior.
6. State coverage: account for empty, loading, success, error, disabled, and edge-case states.

## Output Format

Before implementation, provide a concise design note with:

1. User story
2. Core flow
3. Interface structure
4. Key interactions and states

Then proceed with the code changes unless the design reveals an important ambiguity or risk that must be clarified first.
