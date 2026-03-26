# Prompt: Restructure Tickets to Be Feature-Focused

You will restructure tickets so that every ticket describes a **user-facing feature**, not a technical implementation artifact.

Before starting, ask me which epic(s) and/or specific ticket files to work on. Do not touch any files outside of what I specify.

## The Problem

Our current tickets are sliced by technical artifacts — actions, CRUD operations, pipeline steps, state machines — instead of by deliverable features. This makes tickets feel like implementation tasks ("create an action class") rather than product features ("manage currencies in settings").

## Rules

Apply these rules to every ticket in your assigned epic:

### 1. Merge technical slices of the same feature into one ticket

If multiple tickets exist for what is clearly one feature (e.g., a settings page and its individual CRUD operations), merge them into a single feature ticket.

**Signals to merge:**
- Tickets named after individual actions (e.g., "Add X Action", "Update X Action", "Delete X Action") that all operate on the same page or entity
- Tickets that split a single pipeline or workflow into implementation steps (e.g., "Step 1", "Step 2")
- A "setup" ticket (migrations/models) plus separate tickets for each operation on those models

**How to merge:**
- Pick the most natural ticket as the base (usually the one with the page/UI or the broadest scope)
- Combine all Technical Implementation sections (migrations, models, actions, routes, tests, edge cases) into the base ticket
- Combine all Acceptance Criteria (client-side and server-side) into the base ticket
- Delete the absorbed ticket files
- No information should be lost — every test, edge case, and detail must be preserved

### 2. Absorb infrastructure tickets into the features they serve

If a ticket describes pure technical infrastructure (state machine setup, auto-triggered background logic, recomputation actions) that isn't a standalone user-facing feature, absorb it into the feature ticket that uses it.

**Signals to absorb:**
- The ticket has no client-side acceptance criteria (it's invisible to users)
- The ticket is named after a class or pattern, not a feature (e.g., "AutoAttachBonusesToRunAction", "State Transitions")
- The ticket's logic is triggered automatically as part of another feature's flow

**How to absorb:**
- Identify which feature ticket triggers or depends on this infrastructure
- Move the actions, tests, and edge cases into that feature ticket
- If the infrastructure serves multiple features, put it in the most natural home (usually where the infrastructure is first created) and note the cross-references

### 3. Rename remaining tickets to use feature language

If a ticket is already a reasonable standalone feature but uses technical naming, rename it.

**Rename patterns:**
- "X CRUD" → "X Management" (e.g., "Cash Advance CRUD" → "Cash Advance Management")
- "X Action" → just "X" (e.g., "Create Payroll Run Action" → "Create Payroll Run")
- "X UI" → just "X" (features inherently include UI)
- Keep the `# [GW] Payroll - ` prefix in the markdown title

### 4. Update the EPIC.md

After restructuring, update the epic's `EPIC.md`:
- Remove deleted tickets from the table
- Update renamed ticket titles in the table
- Update the Epic Summary if needed to reflect the new structure

### 5. Rewrite acceptance criteria to be concise

Keep the existing section structure intact (Client-side → Layout/Behavior/Validation, Server-side → Side-effects). Do not add, remove, or reorganize sections. But rewrite each bullet point to be **straightforward and max 10 words**.

**Before:**
```
- The currency list displays each currency's code, name, symbol, exchange rate (with 6 decimal places), relative "last updated" timestamp, and active status
- An "Add Currency" button is available on the currency settings page (Owner only)
- If deactivation is blocked due to active employees, an error message states how many employees still use the currency
- Currency rate changes are tracked in the audit trail with old and new values
```

**After:**
```
- List shows code, name, symbol, rate, updated, status
- "Add Currency" button visible to Owner only
- Blocked deactivation shows affected employee count
- Audit trail tracks rate changes with old/new values
```

**Guidelines:**
- Cut filler words ("is available", "is shown", "there is a")
- Drop obvious context (don't say "on the currency settings page" if the ticket is about the currency settings page)
- One idea per bullet — split compound bullets if needed
- Keep technical specifics that matter (field names, role names, format strings)
- Do this for ALL sections: Layout, Behavior, Validation, and Side-effects

## What NOT to do

- Don't change ticket IDs (PAY-XXX) — keep the original ID even when merging
- Don't rewrite content that's already feature-focused — if a ticket is fine, leave it alone
- Don't lose any technical details — every migration, action, test, edge case, and acceptance criterion from deleted tickets must appear in the merged ticket
- Don't create new tickets — only merge, absorb, rename, or keep

## Examples From EP-06 to EP-10

Here's what was already done for reference:

**Merge example (EP-06):**
- PAY-033 "Currency Management Page (Settings)" + PAY-034 "Add New Currency Action" + PAY-035 "Update Currency Rate Action" + PAY-036 "Deactivate Currency with Safety Checks" → **PAY-033 "Currency Management Settings"**
- Why: Add, edit rate, and deactivate are all CRUD operations on the same settings page — one feature.

**Merge example (EP-08):**
- PAY-044 through PAY-050 (6 computation pipeline steps + batch recompute) → **PAY-044 "Payslip Computation Engine"**
- Why: Steps 1-10 of the pipeline are one feature, not 6 separate features. Batch recompute is just "re-run the pipeline."

**Absorb example (EP-07/EP-09):**
- PAY-041 "Payroll Run State Transitions" → absorbed into PAY-038 "Create Payroll Run" (state machine setup) and the feature tickets that perform transitions (Submit, Review, Finalize)
- PAY-052 "AutoAttachBonusesToRunAction" → absorbed into PAY-038 "Create Payroll Run" (auto-attach runs during run creation)
- Why: These were invisible infrastructure, not user-facing features.

**Rename examples:**
- PAY-037 "Payroll Period CRUD" → "Payroll Period Management"
- PAY-038 "Create Payroll Run Action" → "Create Payroll Run"
- PAY-051 "Bonus Types CRUD in Settings" → "Bonus Type Management Settings"
- PAY-053 "Per-Run Bonus Configuration UI" → "Payroll Run Bonus Configuration"
- PAY-055 "Cash Advance CRUD" → "Cash Advance Management"

## Checklist Before Submitting

- [ ] Every remaining ticket describes a user-facing feature (not a technical artifact)
- [ ] No information was lost from deleted/merged tickets
- [ ] EPIC.md ticket table matches the actual files in the directory
- [ ] Ticket titles use feature language, not technical language
- [ ] The `# [GW] Payroll - ` prefix is preserved in all ticket titles
- [ ] Every acceptance criteria bullet is max 10 words
- [ ] Acceptance criteria sections (Layout/Behavior/Validation/Side-effects) are unchanged
