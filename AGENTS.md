# AGENTS.md

This file provides guidance to Codex (Codex.ai/code) when working with code in this repository.

## Project Overview

PayHRIS Payroll is a standalone Laravel 12 + Inertia.js + React payroll application for Philippine payroll processing. It mirrors employee data from a separate HRIS app via API and handles all payroll computation, deductions, bonuses, and multi-currency support independently.

**This is a documentation/planning repository** — it contains specs, database schemas, computation logic docs, user stories, and Jira ticket templates. No application code exists yet.

## Tech Stack

- **Backend:** Laravel 12, PHP 8.4+
- **Frontend:** Inertia.js v2, React 19, TypeScript, Tailwind CSS v4, Shadcn/ui, Zustand
- **Database:** MySQL with ULIDs as primary keys, no database-level FK constraints (app-layer integrity)
- **Cache/Queue:** Redis
- **Key packages:** spatie/laravel-permission, spatie/laravel-data, spatie/laravel-model-states, lorisleiva/laravel-actions, owen-it/laravel-auditing, barryvdh/laravel-dompdf, maatwebsite/laravel-excel, pestphp/pest

## Build & Development Commands

```bash
composer install && npm install
cp .env.example .env && php artisan key:generate
php artisan migrate && php artisan db:seed
npm run dev          # Vite dev server
npm run build        # Production build
php artisan serve    # Laravel dev server
php artisan queue:work
php artisan schedule:work
php artisan test     # Run Pest tests
php artisan test --filter=TestName  # Single test
```

## Architecture

### Domain-Driven Laravel Structure
```
app/
  {Domain}/Actions/       # Single-responsibility business logic (laravel-actions)
  {Domain}/Models/        # Eloquent models
  {Domain}/Policies/      # Authorization policies
  {Domain}/DTOs/          # Data transfer objects (spatie/laravel-data)
  {Domain}/Events/        # Domain events
  {Domain}/Listeners/     # Event listeners
  {Domain}/Jobs/          # Background jobs
  {Domain}/Queries/       # Complex query classes
  Http/Controllers/Web/   # Thin controllers returning Inertia responses
  Http/Requests/          # Form Request validation
  Http/Resources/         # API Resources for JSON shaping
```

### Frontend Structure
```
resources/js/
  pages/                  # Inertia page components (map 1:1 to Laravel routes)
  components/ui/          # Shadcn/ui base primitives
  components/layout/      # Shell components (sidebar, header)
  components/forms/       # Reusable form controls
  components/tables/      # Data grids, filters, pagination
  layouts/                # authenticated-layout.tsx, guest-layout.tsx
  hooks/                  # Custom React hooks
  types/                  # TypeScript type definitions
  lib/                    # Utilities
```

### Key Architectural Patterns

- **Controllers stay thin** — orchestrate request/auth/response only; business logic goes in Actions
- **Validation always via Form Requests** — Zod on frontend mirrors a subset for UX, never replaces server validation
- **Authorization is Laravel-first** — Gates/Policies enforce rules; frontend checks are UX-only
- **Inertia page props are the data contract** — keep props small and intentional, no raw model dumps
- **State machine for payroll runs** — `draft → submitted → under_review → finalized` (irreversible, via spatie/laravel-model-states)
- **All monetary computation in PHP (Philippine Peso)** — foreign currencies converted at snapshot rates

### Payroll Computation Engine

`ComputePayslipAction` runs a strict 10-step gross-to-net pipeline per employee:

1. **Gross Pay** (monthly salary or daily_rate × working_days)
2. **Add Bonuses** (fixed, percentage, or formula-based)
3. **Absent Deduction** (daily_rate_for_deduction × absent_days)
4. **SSS** (bracket-based lookup)
5. **PhilHealth** (2.5% employee share, salary floor/ceiling)
6. **Pag-IBIG** (fixed ₱100)
7. **HMO** (fixed per employee)
8. **Voluntary** (MP2, SSS WISP, Cash Advance recovery)
9. **BIR Withholding Tax** (TRAIN Law annual brackets, annualize → look up → divide by 12)
10. **Net Pay** (gross + bonuses − all deductions, floored at 0)

Steps 4-6 and 9 use **Step 1 gross_pay** (basic salary) as basis, not adjusted gross. External salary employees (`has_external_salary=true`) skip steps 3-9 entirely.

### Currency System

- PHP (₱) is immutable base currency (rate=1.0)
- Rates stored as `1 [FOREIGN] = X PHP`
- Rates snapshotted into `payroll_run_currency_snapshots` at run creation for historical integrity
- Use `DECIMAL` types and `decimal:6` casts, never floats

### Roles

| Role | Access |
|---|---|
| `owner` | Full access, finalizes runs, manages currencies/external salary flags |
| `payroll_officer` | Creates/manages runs through draft→submitted→under_review |
| `finance` | Reviews runs, transitions under_review→finalized |
| `employee` | Read-only access to own finalized payslips |

### HRIS Integration

- Daily sync via `SyncEmployeesFromHrisJob` calling `GET {HRIS_API_URL}/api/payroll/employees`
- Keyed on `hris_employee_id` (ULID from HRIS)
- Payroll-specific fields (`has_external_salary`, `has_mp2`, etc.) are local-only, never overwritten by sync

## Documentation Index

| File | Contents |
|---|---|
| `docs/01-database-schema.md` | All 16 tables, column types, indexes, relationships |
| `docs/02-payroll-computation.md` | 10-step computation, BIR tax brackets, SSS table |
| `docs/03-bonus-manager.md` | 4 built-in + custom bonus types, auto-trigger logic, exclusions |
| `docs/04-currency.md` | Rate management, snapshot strategy, conversion formulas |
| `docs/05-user-stories.md` | 46 user stories across owner/payroll_officer/finance/employee roles |
| `jira/acceptance-criteria.md` | Template for Jira ticket acceptance criteria |
| `jira/technical-implementation.md` | Template for Jira ticket technical implementation details |
