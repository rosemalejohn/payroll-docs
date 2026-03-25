# PayHRIS Payroll

A standalone Laravel 12 + Inertia.js + React payroll application. It connects to the **PayHRIS HRIS app** via API to mirror employee data and handles all payroll computation, deduction management, bonus distribution, and multi-currency support independently.

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Roles and Permissions](#roles-and-permissions)
- [Currency Setup](#currency-setup)
- [HRIS Integration](#hris-integration)
- [Environment Variables](#environment-variables)
- [Installation](#installation)
- [Documentation Index](#documentation-index)

---

## Overview

PayHRIS Payroll is a self-contained payroll system that:

- Pulls employee data from the HRIS app and maintains a local mirror
- Computes payroll runs with a structured 10-step gross-to-net calculation
- Manages statutory deductions (SSS, PhilHealth, Pag-IBIG, BIR withholding tax)
- Applies bonuses through a configurable Bonus Manager
- Supports multi-currency payslips with manually maintained exchange rates
- Enforces a strict payroll run lifecycle: `draft → submitted → under_review → finalized`
- Generates payslips as PDF and exports payroll data to Excel

---

## Features

### Payroll
- Payroll period management (monthly, semi-monthly, etc.)
- Per-employee pay basis: **monthly salary** or **daily rate**
- 10-step gross-to-net computation for regular employees
- External salary employees: deductions and tax bypassed, net = gross
- Absent day deduction based on daily rate
- Payroll run state machine with role-gated transitions

### Deductions
- SSS (bracket-based)
- PhilHealth (5% of basic salary)
- Pag-IBIG (fixed ₱100)
- HMO (fixed per employee)
- Voluntary: MP2, SSS WISP (opt-in flags per employee)
- Cash advance recovery
- BIR withholding tax (annual income-based tax table)

### Bonus Manager
- Meal Allowance (fixed amount, all employees)
- Attendance Bonus (percentage-based, threshold-controlled)
- 13th Month Pay (auto-triggered in December)
- June Special Bonus (auto-triggered in June)
- Custom one-off bonuses

### Currency
- PHP as base currency (rate = 1.0, immutable)
- Manual exchange rate management — no external API dependency
- Rates stored in `currencies` table with `rate_updated_at` timestamp
- Rates snapshotted at payroll run creation to ensure historical integrity
- All computation in PHP; display conversion on payslips

### Reporting
- Per-employee payslip generation (PDF via barryvdh/laravel-dompdf)
- Payroll run export (Excel via maatwebsite/laravel-excel)
- Audit trail on all sensitive mutations (owen-it/laravel-auditing)

---

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | Laravel 12 |
| Frontend Bridge | Inertia.js v2 |
| Frontend | React 19, TypeScript |
| UI Components | Shadcn/ui |
| State Management | Zustand |
| Styling | Tailwind CSS v4 |
| Database | MySQL |
| Cache / Queue | Redis |
| Permissions | spatie/laravel-permission |
| Data Objects | spatie/laravel-data |
| Action Layer | lorisleiva/laravel-actions |
| Model States | spatie/laravel-model-states |
| PDF Generation | barryvdh/laravel-dompdf |
| Excel Export | maatwebsite/laravel-excel |
| Audit Logging | owen-it/laravel-auditing |
| Testing | pestphp/pest |

**Primary Keys:** ULIDs on all tables.
**Foreign Keys:** No database-level FK constraints. Referential integrity is enforced at the application layer.

---

## Roles and Permissions

Managed via `spatie/laravel-permission`. Four roles exist:

| Role | Description |
|---|---|
| `owner` | Full access to everything. Can manage currencies, toggle `has_external_salary`, configure all bonus types, and finalize payroll runs. |
| `payroll_officer` | Creates and manages payroll runs through `draft` → `submitted` → `under_review`. Manages employee compensation records and bonus applications. |
| `finance` | Reviews submitted runs. Transitions from `under_review` → `finalized`. Read-only access to compensation data. |
| `employee` | Read-only access to their own payslips. |

Role hierarchy for payroll run transitions:

```
draft        → submitted    (payroll_officer, owner)
submitted    → under_review (payroll_officer, owner)
under_review → finalized    (finance, owner)
finalized    → [terminal]   (no further transitions)
```

---

## Currency Setup

PHP (Philippine Peso) is the **base currency** with a fixed rate of `1.0`. It cannot be deleted or have its rate changed.

All other currencies are stored with the rate expressed as:

```
1 [FOREIGN_CURRENCY] = X PHP
```

Example: `1 USD = 60.41 PHP` → stored as `rate = 60.41`

**Rate Management:**
- Only the `owner` role can update exchange rates
- Rates are updated via a modal in **Settings → Currencies**
- Each update records `rate_updated_at` on the currency row
- There is no scheduled or external rate sync

**Rate Snapshotting:**
- When a payroll run is created, current rates for all active currencies are copied into `payroll_run_currency_snapshots`
- All payslip computations reference snapshot rates, not live rates
- This ensures historical payslips remain accurate after future rate changes

See `docs/04-currency.md` for full details.

---

## HRIS Integration

The Payroll app does not own employee data — it mirrors it from the HRIS app.

**Configuration (`.env`):**
```env
HRIS_API_URL=https://hris.yourdomain.com
HRIS_API_KEY=your-secret-key
```

**Sync Mechanism:**
- A daily scheduled job (`SyncEmployeesFromHrisJob`) calls the HRIS API and upserts the local `employees` table
- Sync is keyed on `hris_employee_id` (the ULID from the HRIS app)
- Fields synced: name, email, department, position, employment status, pay basis, employment type
- Payroll-specific fields (`has_external_salary`, `has_mp2`, `has_sss_wisp`, etc.) are managed locally and never overwritten by sync
- Manual sync can be triggered by `owner` from the Settings screen

**Sync Endpoint (HRIS side):**
```
GET {HRIS_API_URL}/api/payroll/employees
Authorization: Bearer {HRIS_API_KEY}
```

Returns a paginated list of active employees.

---

## Environment Variables

```env
APP_NAME="PayHRIS Payroll"
APP_ENV=production
APP_KEY=
APP_URL=https://payroll.yourdomain.com

DB_CONNECTION=mysql
DB_HOST=127.0.0.1
DB_PORT=3306
DB_DATABASE=payhris_payroll
DB_USERNAME=
DB_PASSWORD=

REDIS_HOST=127.0.0.1
REDIS_PASSWORD=null
REDIS_PORT=6379

QUEUE_CONNECTION=redis
CACHE_DRIVER=redis
SESSION_DRIVER=redis

# HRIS Integration
HRIS_API_URL=https://hris.yourdomain.com
HRIS_API_KEY=

# PDF / Excel
DOMPDF_PAPER_SIZE=A4
```

---

## Installation

```bash
git clone <repo>
cd payhris-payroll

composer install
npm install

cp .env.example .env
php artisan key:generate

php artisan migrate
php artisan db:seed

npm run build
php artisan queue:work
php artisan schedule:work
```

Seed creates the four base roles and an initial `owner` user. PHP (base currency) is seeded into the `currencies` table.

---

## Documentation Index

| File | Contents |
|---|---|
| `docs/01-database-schema.md` | All table definitions, column types, indexes |
| `docs/02-payroll-computation.md` | 10-step computation, deduction formulas, BIR tax brackets |
| `docs/03-bonus-manager.md` | Built-in and custom bonus types, auto-trigger logic |
| `docs/04-currency.md` | Currency system, rate management, snapshot strategy |
