# Database Schema

All tables use **ULIDs** as primary keys. There are **no database-level foreign key constraints** — referential integrity is enforced at the application layer (Laravel actions, data objects, model observers).

---

## Table of Contents

1. [companies](#1-companies)
2. [users](#2-users)
3. [employees](#3-employees-hris-mirror)
4. [currencies](#4-currencies)
5. [payroll_run_currency_snapshots](#5-payroll_run_currency_snapshots)
6. [salary_components](#6-salary_components)
7. [employee_compensation](#7-employee_compensation)
8. [payroll_periods](#8-payroll_periods)
9. [payroll_runs](#9-payroll_runs)
10. [payslips](#10-payslips)
11. [payslip_line_items](#11-payslip_line_items)
12. [bonus_types](#12-bonus_types)
13. [payroll_run_bonuses](#13-payroll_run_bonuses)
14. [cash_advances](#14-cash_advances)
15. [audit_log (laravel-auditing)](#15-audit-log)
16. [Indexes Summary](#indexes-summary)

---

## 1. companies

Stores the company/tenant record. The system is designed for a single company per deployment, but this table supports future multi-tenancy.

```sql
CREATE TABLE companies (
    id            CHAR(26)     NOT NULL PRIMARY KEY,   -- ULID
    name          VARCHAR(255) NOT NULL,
    code          VARCHAR(50)  NOT NULL UNIQUE,
    address       TEXT         NULL,
    tin           VARCHAR(50)  NULL,                   -- Tax Identification Number
    sss_number    VARCHAR(50)  NULL,
    philhealth_no VARCHAR(50)  NULL,
    pagibig_no    VARCHAR(50)  NULL,
    logo_path     VARCHAR(500) NULL,
    is_active     TINYINT(1)   NOT NULL DEFAULT 1,
    created_at    TIMESTAMP    NULL,
    updated_at    TIMESTAMP    NULL
);
```

---

## 2. users

Application users. Each user is linked to a company and has one or more roles via `spatie/laravel-permission`.

```sql
CREATE TABLE users (
    id                CHAR(26)     NOT NULL PRIMARY KEY,   -- ULID
    company_id        CHAR(26)     NOT NULL,               -- ref: companies.id
    employee_id       CHAR(26)     NULL,                   -- ref: employees.id (nullable for admin-only users)
    name              VARCHAR(255) NOT NULL,
    email             VARCHAR(255) NOT NULL UNIQUE,
    email_verified_at TIMESTAMP    NULL,
    password          VARCHAR(255) NOT NULL,
    remember_token    VARCHAR(100) NULL,
    is_active         TINYINT(1)   NOT NULL DEFAULT 1,
    last_login_at     TIMESTAMP    NULL,
    created_at        TIMESTAMP    NULL,
    updated_at        TIMESTAMP    NULL
);
```

**Notes:**
- Roles assigned via `model_has_roles` (spatie/laravel-permission standard table)
- `employee_id` links a user account to their employee mirror record; nullable for users who are staff/admin but not employees

---

## 3. employees (HRIS mirror)

Local mirror of employee data pulled from the HRIS app. Synced daily. Payroll-specific fields are managed locally and are never overwritten by the sync job.

```sql
CREATE TABLE employees (
    id                  CHAR(26)        NOT NULL PRIMARY KEY,   -- ULID (local)
    company_id          CHAR(26)        NOT NULL,               -- ref: companies.id
    hris_employee_id    CHAR(26)        NOT NULL UNIQUE,        -- ULID from HRIS app (sync key)

    -- Synced from HRIS (overwritten on every sync)
    employee_number     VARCHAR(50)     NOT NULL,
    first_name          VARCHAR(150)    NOT NULL,
    last_name           VARCHAR(150)    NOT NULL,
    middle_name         VARCHAR(150)    NULL,
    email               VARCHAR(255)    NULL,
    department          VARCHAR(150)    NULL,
    position            VARCHAR(150)    NULL,
    employment_type     ENUM('regular','contractual','probationary') NOT NULL DEFAULT 'regular',
    employment_status   ENUM('active','inactive','on_leave','terminated') NOT NULL DEFAULT 'active',
    date_hired          DATE            NULL,

    -- Payroll-specific (managed locally, never overwritten by sync)
    pay_basis           ENUM('monthly','daily') NOT NULL DEFAULT 'monthly',
    has_external_salary TINYINT(1)      NOT NULL DEFAULT 0,   -- owner-only flag
    has_mp2             TINYINT(1)      NOT NULL DEFAULT 0,   -- MP2 voluntary deduction
    has_sss_wisp        TINYINT(1)      NOT NULL DEFAULT 0,   -- SSS WISP voluntary deduction
    hmo_amount          DECIMAL(12,2)   NOT NULL DEFAULT 0.00,-- fixed HMO deduction
    sss_number          VARCHAR(50)     NULL,
    philhealth_number   VARCHAR(50)     NULL,
    pagibig_number      VARCHAR(50)     NULL,
    bir_tin             VARCHAR(50)     NULL,

    last_synced_at      TIMESTAMP       NULL,
    created_at          TIMESTAMP       NULL,
    updated_at          TIMESTAMP       NULL
);
```

**Notes:**
- `hris_employee_id` is the sync anchor — never regenerated
- `has_external_salary = 1` means the employee's net pay equals gross pay; all deductions and tax steps are skipped
- `pay_basis` determines Step 1 of computation: monthly salary or `daily_rate × working_days`
- `hmo_amount` is stored here rather than in `employee_compensation` because it is a fixed personal deduction, not a salary component

---

## 4. currencies

All currencies available in the system. PHP is the base currency and always has `is_base = 1` and `rate = 1.000000`.

```sql
CREATE TABLE currencies (
    id              CHAR(26)        NOT NULL PRIMARY KEY,   -- ULID
    company_id      CHAR(26)        NOT NULL,               -- ref: companies.id
    code            VARCHAR(10)     NOT NULL,               -- ISO 4217 e.g. USD, EUR, PHP
    name            VARCHAR(100)    NOT NULL,               -- e.g. "Philippine Peso"
    symbol          VARCHAR(10)     NOT NULL,               -- e.g. ₱, $, €
    rate            DECIMAL(18,6)   NOT NULL DEFAULT 1.000000, -- 1 [code] = rate PHP
    is_base         TINYINT(1)      NOT NULL DEFAULT 0,     -- only PHP has this = 1
    is_active       TINYINT(1)      NOT NULL DEFAULT 1,
    rate_updated_at TIMESTAMP       NULL,                   -- last time rate was manually changed
    updated_by      CHAR(26)        NULL,                   -- ref: users.id
    created_at      TIMESTAMP       NULL,
    updated_at      TIMESTAMP       NULL,

    UNIQUE KEY uq_currencies_company_code (company_id, code)
);
```

**Notes:**
- Only `owner` can update `rate` and `is_active`
- `is_base` cannot be changed via the UI; PHP is seeded with this flag
- `rate_updated_at` is set to `NOW()` whenever `rate` changes, regardless of `updated_at`
- See `docs/04-currency.md` for full rate management logic

---

## 5. payroll_run_currency_snapshots

Captures all active currency rates at the moment a payroll run is created. Payslip calculations reference snapshot rates — not live rates — for historical accuracy.

```sql
CREATE TABLE payroll_run_currency_snapshots (
    id             CHAR(26)      NOT NULL PRIMARY KEY,   -- ULID
    payroll_run_id CHAR(26)      NOT NULL,               -- ref: payroll_runs.id
    currency_id    CHAR(26)      NOT NULL,               -- ref: currencies.id
    currency_code  VARCHAR(10)   NOT NULL,               -- denormalized for readability
    rate           DECIMAL(18,6) NOT NULL,               -- rate at time of payroll run creation
    snapshotted_at TIMESTAMP     NOT NULL,
    created_at     TIMESTAMP     NULL,
    updated_at     TIMESTAMP     NULL
);
```

---

## 6. salary_components

Defines reusable salary component types (e.g., "Basic Salary", "Daily Rate", "MP2 Contribution"). Used as a catalog — actual amounts per employee are in `employee_compensation`.

```sql
CREATE TABLE salary_components (
    id           CHAR(26)     NOT NULL PRIMARY KEY,   -- ULID
    company_id   CHAR(26)     NOT NULL,               -- ref: companies.id
    name         VARCHAR(150) NOT NULL,
    code         VARCHAR(50)  NOT NULL,               -- e.g. BASIC, DAILY_RATE, MP2
    type         ENUM('earning','deduction','benefit') NOT NULL,
    is_taxable   TINYINT(1)   NOT NULL DEFAULT 1,
    is_system    TINYINT(1)   NOT NULL DEFAULT 0,     -- system components cannot be deleted
    description  TEXT         NULL,
    sort_order   INT          NOT NULL DEFAULT 0,
    is_active    TINYINT(1)   NOT NULL DEFAULT 1,
    created_at   TIMESTAMP    NULL,
    updated_at   TIMESTAMP    NULL,

    UNIQUE KEY uq_salary_components_company_code (company_id, code)
);
```

**System components (seeded, `is_system = 1`):**

| code | name | type |
|---|---|---|
| `BASIC_MONTHLY` | Basic Monthly Salary | earning |
| `DAILY_RATE` | Daily Rate | earning |
| `SSS` | SSS Contribution | deduction |
| `PHILHEALTH` | PhilHealth Contribution | deduction |
| `PAGIBIG` | Pag-IBIG Contribution | deduction |
| `HMO` | HMO Deduction | deduction |
| `MP2` | MP2 Voluntary Contribution | deduction |
| `SSS_WISP` | SSS WISP Voluntary | deduction |
| `CASH_ADVANCE` | Cash Advance Recovery | deduction |
| `BIR_TAX` | BIR Withholding Tax | deduction |
| `ABSENT_DEDUCTION` | Absent Deduction | deduction |

---

## 7. employee_compensation

The active compensation record for each employee. One row per employee (current state). Historical changes are tracked via `owen-it/laravel-auditing`.

```sql
CREATE TABLE employee_compensation (
    id                  CHAR(26)      NOT NULL PRIMARY KEY,   -- ULID
    company_id          CHAR(26)      NOT NULL,               -- ref: companies.id
    employee_id         CHAR(26)      NOT NULL UNIQUE,        -- ref: employees.id
    currency_id         CHAR(26)      NOT NULL,               -- ref: currencies.id
    monthly_salary      DECIMAL(14,2) NULL,                   -- used when pay_basis = monthly
    daily_rate          DECIMAL(14,2) NULL,                   -- used when pay_basis = daily
    mp2_amount          DECIMAL(12,2) NOT NULL DEFAULT 0.00,  -- voluntary MP2 fixed amount
    sss_wisp_amount     DECIMAL(12,2) NOT NULL DEFAULT 0.00,  -- voluntary SSS WISP fixed amount
    effective_date      DATE          NOT NULL,
    notes               TEXT          NULL,
    created_by          CHAR(26)      NULL,                   -- ref: users.id
    updated_by          CHAR(26)      NULL,                   -- ref: users.id
    created_at          TIMESTAMP     NULL,
    updated_at          TIMESTAMP     NULL
);
```

**Notes:**
- `currency_id` identifies what currency the salary figures are stored in
- If `currency_id` is not PHP, gross pay is converted to PHP during payroll computation using the snapshot rate
- Either `monthly_salary` or `daily_rate` must be set depending on `employees.pay_basis`
- `mp2_amount` and `sss_wisp_amount` are applied only if `employees.has_mp2 = 1` and `employees.has_sss_wisp = 1` respectively

---

## 8. payroll_periods

Defines the time window for a payroll run (e.g., "March 2026", "March 1–15, 2026").

```sql
CREATE TABLE payroll_periods (
    id            CHAR(26)     NOT NULL PRIMARY KEY,   -- ULID
    company_id    CHAR(26)     NOT NULL,               -- ref: companies.id
    name          VARCHAR(150) NOT NULL,               -- e.g. "March 2026"
    period_type   ENUM('monthly','semi_monthly','weekly') NOT NULL DEFAULT 'monthly',
    start_date    DATE         NOT NULL,
    end_date      DATE         NOT NULL,
    working_days  INT          NOT NULL DEFAULT 22,    -- working days in the period
    is_locked     TINYINT(1)   NOT NULL DEFAULT 0,     -- set to 1 when a finalized run exists
    created_by    CHAR(26)     NULL,                   -- ref: users.id
    created_at    TIMESTAMP    NULL,
    updated_at    TIMESTAMP    NULL
);
```

**Notes:**
- `working_days` is editable before the payroll run is finalized; used in Step 1 for daily-rate employees
- `is_locked = 1` prevents creating a second payroll run for the same period

---

## 9. payroll_runs

The central record for a payroll processing run. Tracks state, currency snapshot reference, and totals.

```sql
CREATE TABLE payroll_runs (
    id                CHAR(26)      NOT NULL PRIMARY KEY,   -- ULID
    company_id        CHAR(26)      NOT NULL,               -- ref: companies.id
    payroll_period_id CHAR(26)      NOT NULL,               -- ref: payroll_periods.id
    name              VARCHAR(255)  NOT NULL,               -- e.g. "March 2026 Payroll"
    state             VARCHAR(50)   NOT NULL DEFAULT 'draft',
    -- States: draft, submitted, under_review, finalized

    -- Currency snapshot info
    base_currency_id  CHAR(26)      NOT NULL,               -- ref: currencies.id (always PHP)
    rates_snapshotted_at TIMESTAMP  NULL,                   -- when currency snapshot was taken

    -- Totals (computed, stored for reporting performance)
    total_gross       DECIMAL(16,2) NOT NULL DEFAULT 0.00,
    total_deductions  DECIMAL(16,2) NOT NULL DEFAULT 0.00,
    total_net         DECIMAL(16,2) NOT NULL DEFAULT 0.00,
    employee_count    INT           NOT NULL DEFAULT 0,

    -- Audit fields
    submitted_by      CHAR(26)      NULL,                   -- ref: users.id
    submitted_at      TIMESTAMP     NULL,
    reviewed_by       CHAR(26)      NULL,                   -- ref: users.id
    reviewed_at       TIMESTAMP     NULL,
    finalized_by      CHAR(26)      NULL,                   -- ref: users.id
    finalized_at      TIMESTAMP     NULL,

    notes             TEXT          NULL,
    created_by        CHAR(26)      NULL,                   -- ref: users.id
    created_at        TIMESTAMP     NULL,
    updated_at        TIMESTAMP     NULL
);
```

**State Machine** (enforced via `spatie/laravel-model-states`):

```
draft → submitted → under_review → finalized
```

- Transitions are irreversible
- Only `payroll_officer` or `owner` can move from `draft` → `submitted` → `under_review`
- Only `finance` or `owner` can move from `under_review` → `finalized`
- Payslips are recalculated on each `draft` save; locked after `finalized`

---

## 10. payslips

One payslip per employee per payroll run. Stores the computed gross, deduction, and net totals. Line-level breakdown is in `payslip_line_items`.

```sql
CREATE TABLE payslips (
    id                   CHAR(26)      NOT NULL PRIMARY KEY,   -- ULID
    company_id           CHAR(26)      NOT NULL,               -- ref: companies.id
    payroll_run_id       CHAR(26)      NOT NULL,               -- ref: payroll_runs.id
    employee_id          CHAR(26)      NOT NULL,               -- ref: employees.id
    payroll_period_id    CHAR(26)      NOT NULL,               -- ref: payroll_periods.id

    -- Computation flags snapshotted at time of calculation
    pay_basis            ENUM('monthly','daily') NOT NULL,
    has_external_salary  TINYINT(1)    NOT NULL DEFAULT 0,
    working_days         INT           NOT NULL DEFAULT 0,
    absent_days          INT           NOT NULL DEFAULT 0,

    -- Salary snapshot
    monthly_salary       DECIMAL(14,2) NULL,
    daily_rate           DECIMAL(14,2) NULL,
    salary_currency_id   CHAR(26)      NULL,                   -- ref: currencies.id (snapshot)
    salary_currency_code VARCHAR(10)   NULL,                   -- denormalized
    salary_exchange_rate DECIMAL(18,6) NULL,                   -- snapshot rate at run creation

    -- Computed totals (all in PHP)
    gross_pay            DECIMAL(14,2) NOT NULL DEFAULT 0.00,
    total_bonuses        DECIMAL(14,2) NOT NULL DEFAULT 0.00,
    total_deductions     DECIMAL(14,2) NOT NULL DEFAULT 0.00,
    net_pay              DECIMAL(14,2) NOT NULL DEFAULT 0.00,

    -- Individual deduction totals (denormalized for reporting)
    sss_deduction        DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    philhealth_deduction DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    pagibig_deduction    DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    hmo_deduction        DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    mp2_deduction        DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    sss_wisp_deduction   DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    cash_advance_deduction DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    absent_deduction     DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    bir_tax              DECIMAL(12,2) NOT NULL DEFAULT 0.00,

    pdf_path             VARCHAR(500)  NULL,                   -- generated PDF path
    generated_at         TIMESTAMP     NULL,
    created_at           TIMESTAMP     NULL,
    updated_at           TIMESTAMP     NULL,

    UNIQUE KEY uq_payslips_run_employee (payroll_run_id, employee_id)
);
```

**Notes:**
- All monetary values stored in PHP regardless of the employee's salary currency
- Salary currency and exchange rate are snapshotted from `payroll_run_currency_snapshots` at computation time
- `has_external_salary = 1` payslips will have `total_deductions = 0` and `net_pay = gross_pay + total_bonuses`

---

## 11. payslip_line_items

Individual line entries on a payslip (each earning, bonus, or deduction as a separate row). Powers the itemized payslip PDF.

```sql
CREATE TABLE payslip_line_items (
    id             CHAR(26)       NOT NULL PRIMARY KEY,   -- ULID
    payslip_id     CHAR(26)       NOT NULL,               -- ref: payslips.id
    component_code VARCHAR(50)    NOT NULL,               -- ref: salary_components.code or bonus type code
    component_name VARCHAR(150)   NOT NULL,               -- display name
    type           ENUM('earning','deduction','bonus') NOT NULL,
    amount         DECIMAL(14,2)  NOT NULL DEFAULT 0.00,  -- in PHP
    sort_order     INT            NOT NULL DEFAULT 0,
    notes          TEXT           NULL,
    created_at     TIMESTAMP      NULL,
    updated_at     TIMESTAMP      NULL
);
```

**Standard line item order (sort_order):**

| sort_order | code | type |
|---|---|---|
| 10 | BASIC | earning |
| 20 | MEAL_ALLOWANCE | bonus |
| 30 | ATTENDANCE_BONUS | bonus |
| 40 | 13TH_MONTH | bonus |
| 50 | JUNE_SPECIAL | bonus |
| 60+ | custom bonuses | bonus |
| 100 | ABSENT_DEDUCTION | deduction |
| 110 | SSS | deduction |
| 120 | PHILHEALTH | deduction |
| 130 | PAGIBIG | deduction |
| 140 | HMO | deduction |
| 150 | MP2 | deduction |
| 160 | SSS_WISP | deduction |
| 170 | CASH_ADVANCE | deduction |
| 180 | BIR_TAX | deduction |

---

## 12. bonus_types

Catalog of bonus definitions available to the company. Includes both built-in system types and custom types.

```sql
CREATE TABLE bonus_types (
    id              CHAR(26)      NOT NULL PRIMARY KEY,   -- ULID
    company_id      CHAR(26)      NOT NULL,               -- ref: companies.id
    code            VARCHAR(50)   NOT NULL,               -- e.g. MEAL_ALLOWANCE, 13TH_MONTH
    name            VARCHAR(150)  NOT NULL,
    is_system       TINYINT(1)    NOT NULL DEFAULT 0,     -- built-in bonus types; cannot be deleted
    computation_type ENUM('fixed','percentage','formula') NOT NULL DEFAULT 'fixed',
    -- fixed: flat amount per employee
    -- percentage: percentage of gross pay (or basic salary)
    -- formula: system-computed (13th month, June Special)

    default_amount    DECIMAL(12,2) NULL,                 -- for fixed type
    default_rate      DECIMAL(7,4)  NULL,                 -- percentage as decimal e.g. 0.1000 = 10%
    percentage_basis  ENUM('gross','basic') NULL DEFAULT 'gross',

    -- For attendance bonus
    attendance_threshold_days INT  NULL,                  -- minimum attended days to qualify
    attendance_threshold_type ENUM('days','percentage')  NULL,

    -- Auto-trigger config
    auto_trigger      TINYINT(1)   NOT NULL DEFAULT 0,    -- 1 = added automatically on run creation
    auto_trigger_month INT         NULL,                  -- 6 = June, 12 = December (NULL = all months)

    is_active         TINYINT(1)   NOT NULL DEFAULT 1,
    description       TEXT         NULL,
    sort_order        INT          NOT NULL DEFAULT 0,
    created_at        TIMESTAMP    NULL,
    updated_at        TIMESTAMP    NULL,

    UNIQUE KEY uq_bonus_types_company_code (company_id, code)
);
```

**Seeded system bonus types:**

| code | name | type | auto_trigger | auto_trigger_month |
|---|---|---|---|---|
| `MEAL_ALLOWANCE` | Meal Allowance | fixed | 1 | NULL (all months) |
| `ATTENDANCE_BONUS` | Attendance Bonus | percentage | 0 | NULL |
| `13TH_MONTH` | 13th Month Pay | formula | 1 | 12 |
| `JUNE_SPECIAL` | June Special Bonus | formula | 1 | 6 |

---

## 13. payroll_run_bonuses

Links a bonus type to a payroll run with the configured amount/rate for that run. Each active employee in the run will receive the bonus unless individually excluded.

```sql
CREATE TABLE payroll_run_bonuses (
    id                 CHAR(26)      NOT NULL PRIMARY KEY,   -- ULID
    payroll_run_id     CHAR(26)      NOT NULL,               -- ref: payroll_runs.id
    bonus_type_id      CHAR(26)      NOT NULL,               -- ref: bonus_types.id
    bonus_code         VARCHAR(50)   NOT NULL,               -- denormalized
    bonus_name         VARCHAR(150)  NOT NULL,               -- denormalized

    -- Override amount/rate for this specific run
    amount             DECIMAL(12,2) NULL,
    rate               DECIMAL(7,4)  NULL,
    percentage_basis   ENUM('gross','basic') NULL,

    -- Attendance bonus config override
    attendance_threshold_days INT    NULL,

    apply_to_all       TINYINT(1)    NOT NULL DEFAULT 1,     -- 0 = per-employee exclusions in payroll_run_bonus_exclusions
    is_active          TINYINT(1)    NOT NULL DEFAULT 1,
    added_by           CHAR(26)      NULL,                   -- ref: users.id
    created_at         TIMESTAMP     NULL,
    updated_at         TIMESTAMP     NULL,

    UNIQUE KEY uq_payroll_run_bonuses_run_type (payroll_run_id, bonus_type_id)
);
```

---

## 14. payroll_run_bonus_exclusions

Records which employees are excluded from a specific bonus in a specific payroll run (when `apply_to_all = 0`).

```sql
CREATE TABLE payroll_run_bonus_exclusions (
    id                   CHAR(26)  NOT NULL PRIMARY KEY,   -- ULID
    payroll_run_bonus_id CHAR(26)  NOT NULL,               -- ref: payroll_run_bonuses.id
    employee_id          CHAR(26)  NOT NULL,               -- ref: employees.id
    reason               TEXT      NULL,
    created_at           TIMESTAMP NULL,
    updated_at           TIMESTAMP NULL,

    UNIQUE KEY uq_exclusions_bonus_employee (payroll_run_bonus_id, employee_id)
);
```

---

## 15. cash_advances

Tracks cash advance issuance and recovery per employee.

```sql
CREATE TABLE cash_advances (
    id               CHAR(26)      NOT NULL PRIMARY KEY,   -- ULID
    company_id       CHAR(26)      NOT NULL,               -- ref: companies.id
    employee_id      CHAR(26)      NOT NULL,               -- ref: employees.id
    amount           DECIMAL(12,2) NOT NULL,
    amount_recovered DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    balance          DECIMAL(12,2) NOT NULL,               -- amount - amount_recovered
    issued_date      DATE          NOT NULL,
    status           ENUM('active','fully_recovered','cancelled') NOT NULL DEFAULT 'active',
    notes            TEXT          NULL,
    created_by       CHAR(26)      NULL,                   -- ref: users.id
    created_at       TIMESTAMP     NULL,
    updated_at       TIMESTAMP     NULL
);
```

**Notes:**
- On payroll computation (Step 8), all `active` cash advances for the employee are summed to produce the `CASH_ADVANCE` deduction line item
- After finalization, the payroll officer marks advances as recovered (updating `amount_recovered` and `balance`)

---

## 16. Audit Log (laravel-auditing)

Managed by `owen-it/laravel-auditing`. Standard `audits` table. Models that implement `Auditable`:

- `PayrollRun` (state transitions, total updates)
- `Payslip` (any recalculation)
- `EmployeeCompensation` (salary changes)
- `Currency` (rate changes)
- `Employee` (payroll flag changes: `has_external_salary`, `has_mp2`, `has_sss_wisp`, `hmo_amount`)

---

## Indexes Summary

```sql
-- employees
CREATE INDEX idx_employees_company      ON employees (company_id);
CREATE INDEX idx_employees_hris_id      ON employees (hris_employee_id);
CREATE INDEX idx_employees_status       ON employees (employment_status);

-- employee_compensation
CREATE INDEX idx_emp_comp_employee      ON employee_compensation (employee_id);
CREATE INDEX idx_emp_comp_company       ON employee_compensation (company_id);

-- payroll_runs
CREATE INDEX idx_payroll_runs_company   ON payroll_runs (company_id);
CREATE INDEX idx_payroll_runs_period    ON payroll_runs (payroll_period_id);
CREATE INDEX idx_payroll_runs_state     ON payroll_runs (state);

-- payslips
CREATE INDEX idx_payslips_run           ON payslips (payroll_run_id);
CREATE INDEX idx_payslips_employee      ON payslips (employee_id);
CREATE INDEX idx_payslips_run_emp       ON payslips (payroll_run_id, employee_id);

-- payslip_line_items
CREATE INDEX idx_line_items_payslip     ON payslip_line_items (payslip_id);

-- payroll_run_bonuses
CREATE INDEX idx_run_bonuses_run        ON payroll_run_bonuses (payroll_run_id);

-- payroll_run_currency_snapshots
CREATE INDEX idx_currency_snapshots_run ON payroll_run_currency_snapshots (payroll_run_id);

-- cash_advances
CREATE INDEX idx_cash_advances_employee ON cash_advances (employee_id, status);

-- currencies
CREATE INDEX idx_currencies_company     ON currencies (company_id);
```
