# Bonus Manager

The Bonus Manager controls which bonuses are applied to a payroll run, how they are computed, and which employees receive them. Bonuses are applied in **Step 2** of the payroll computation, after gross pay is established but before any deductions.

---

## Table of Contents

1. [Overview](#overview)
2. [Data Model Summary](#data-model-summary)
3. [Built-in Bonus Types](#built-in-bonus-types)
   - [Meal Allowance](#1-meal-allowance)
   - [Attendance Bonus](#2-attendance-bonus)
   - [13th Month Pay](#3-13th-month-pay)
   - [June Special Bonus](#4-june-special-bonus)
4. [Custom Bonuses](#custom-bonuses)
5. [Auto-Trigger Logic](#auto-trigger-logic)
6. [Per-Run Bonus Configuration](#per-run-bonus-configuration)
7. [Per-Employee Exclusions](#per-employee-exclusions)
8. [Bonus Application Order](#bonus-application-order)
9. [Bonus and External Salary Employees](#bonus-and-external-salary-employees)
10. [UI Flow](#ui-flow)

---

## Overview

A bonus is not applied globally — it is attached to a specific **payroll run** via a `payroll_run_bonuses` record. This means:

- The same bonus type can have different amounts in different payroll runs
- Bonuses can be added, removed, or adjusted per run while the run is in `draft`
- Auto-trigger bonuses are attached automatically when the payroll run is created
- Once the run is `submitted`, bonuses are locked and cannot be changed

All bonus amounts in payslip line items are in **PHP**.

---

## Data Model Summary

```
bonus_types
    ↓ (one per company catalog)
payroll_run_bonuses
    ↓ (one per active bonus per payroll run)
payroll_run_bonus_exclusions
    ↓ (optional, per employee exclusion)
payslip_line_items
    ↓ (one line per bonus per employee payslip)
```

---

## Built-in Bonus Types

These four bonus types are seeded with `is_system = 1` and cannot be deleted. They can be deactivated (`is_active = 0`) on a per-run basis.

---

### 1. Meal Allowance

| Property | Value |
|---|---|
| Code | `MEAL_ALLOWANCE` |
| Computation Type | `fixed` |
| Auto-trigger | Yes (every month) |
| Applies To | All employees (unless excluded) |

**Behavior:**
- A fixed PHP amount distributed to every employee every payroll run
- The default amount is configured on `bonus_types.default_amount`
- The amount can be overridden per payroll run in `payroll_run_bonuses.amount`
- The payroll officer can adjust the per-run amount before submitting

**Computation:**
```
meal_allowance_amount = payroll_run_bonuses.amount
```

**Payslip line item:**
```
{ code: 'MEAL_ALLOWANCE', type: 'bonus', amount: meal_allowance_amount }
```

---

### 2. Attendance Bonus

| Property | Value |
|---|---|
| Code | `ATTENDANCE_BONUS` |
| Computation Type | `percentage` |
| Auto-trigger | No (manually added per run) |
| Applies To | Employees meeting attendance threshold |

**Behavior:**
- Awards a percentage of gross basic salary to employees who met the attendance threshold for the payroll period
- Threshold is the minimum number of days present (days worked) to qualify
- The percentage and threshold are configurable per payroll run

**Configuration per run (stored in `payroll_run_bonuses`):**
- `rate`: decimal percentage (e.g., `0.1000` = 10%)
- `percentage_basis`: `'basic'` (uses `gross_pay` from Step 1)
- `attendance_threshold_days`: minimum days attended to qualify

**Computation:**
```
if employee_attended_days >= attendance_threshold_days:
    attendance_bonus = gross_pay × rate
else:
    attendance_bonus = 0 (no line item generated)
```

`employee_attended_days` is calculated as:
```
employee_attended_days = payroll_periods.working_days - payslips.absent_days
```

**Payslip line item (only if qualified):**
```
{ code: 'ATTENDANCE_BONUS', type: 'bonus', amount: attendance_bonus }
```

**Notes:**
- If `absent_days` has not been entered for an employee yet, the bonus defaults to 0 until `absent_days` is set
- The payroll officer enters `absent_days` per employee in the payroll run UI before finalizing

---

### 3. 13th Month Pay

| Property | Value |
|---|---|
| Code | `13TH_MONTH` |
| Computation Type | `formula` |
| Auto-trigger | Yes (December only) |
| Applies To | All employees (unless excluded) |

**Behavior:**
- Automatically added to payroll runs in December
- Based on Republic Act 6686 (13th Month Pay Law)
- Computed per employee based on their annual basic salary

**Computation:**
```
if pay_basis == 'monthly':
    annual_basic = monthly_salary × 12

if pay_basis == 'daily':
    annual_basic = daily_rate × 261  -- standard annual working days
                                     -- configurable as company setting

thirteenth_month = annual_basic / 12
```

The divisor `12` is fixed. `261` working days per year is the default and can be overridden at the company level if needed.

**Payslip line item:**
```
{ code: '13TH_MONTH', type: 'bonus', amount: thirteenth_month }
```

**Notes:**
- The 13th Month Pay is **non-taxable up to ₱90,000** under TRAIN Law. The BIR computation in Step 9 should exclude the 13th month amount from taxable income up to this threshold. The implementation should track this separately.
- If the company pays 13th month in partial installments (e.g., half in June, half in December), this must be configured using Custom Bonuses with manual amounts; the built-in formula always computes the full month

---

### 4. June Special Bonus

| Property | Value |
|---|---|
| Code | `JUNE_SPECIAL` |
| Computation Type | `formula` |
| Auto-trigger | Yes (June only) |
| Applies To | All employees (unless excluded) |

**Behavior:**
- Automatically added to payroll runs in June
- Awards one month's equivalent of gross basic pay

**Computation:**
```
june_special = gross_pay   -- equals the Step 1 gross pay (one full month equivalent)
```

For daily-rate employees:
```
june_special = daily_rate × payroll_periods.working_days
```
This is the same as their monthly gross pay for that period.

**Payslip line item:**
```
{ code: 'JUNE_SPECIAL', type: 'bonus', amount: june_special }
```

**Notes:**
- If the company calculates June Special differently (e.g., a percentage, or a flat amount), disable the auto-trigger on this bonus and create a Custom Bonus with the desired configuration

---

## Custom Bonuses

Custom bonuses can be created by the `owner` or `payroll_officer` role via **Settings → Bonuses** or directly from the payroll run bonus management screen.

**Creating a custom bonus:**
1. Give it a name and code (auto-generated from name but editable)
2. Choose computation type: `fixed` or `percentage`
3. Set default amount or rate
4. Set `auto_trigger = false` (custom bonuses are manually added to runs)
5. Optionally set `auto_trigger_month` if it should auto-apply in a specific month

**Custom bonus examples:**

| Name | Type | Details |
|---|---|---|
| Anniversary Bonus | fixed | ₱5,000 to specific employees |
| Performance Bonus Q1 | percentage | 15% of gross to eligible employees |
| Transportation Allowance | fixed | ₱2,500 to field employees |
| Hazard Pay | fixed | ₱3,000 for designated departments |

Custom bonuses with `is_system = 0` can be deleted by `owner` only if they are not referenced by any `payroll_run_bonuses` record (i.e., never used in a run).

---

## Auto-Trigger Logic

When a `PayrollRun` is created, the system automatically attaches applicable bonuses via `AutoAttachBonusesToRunAction`.

**Trigger condition:**
```php
foreach bonus_types where is_system = true and auto_trigger = true:
    if auto_trigger_month is null:
        attach to this run (applies every month)
    elseif auto_trigger_month == month(payroll_periods.start_date):
        attach to this run
    else:
        skip
```

**Example for a December 2026 payroll run:**
- `MEAL_ALLOWANCE` → attached (auto_trigger = true, auto_trigger_month = null)
- `ATTENDANCE_BONUS` → not attached (auto_trigger = false)
- `13TH_MONTH` → attached (auto_trigger = true, auto_trigger_month = 12)
- `JUNE_SPECIAL` → not attached (auto_trigger_month = 6, run is December)

**Custom bonuses with auto_trigger:**
If a custom bonus has `auto_trigger = true` and optionally `auto_trigger_month`, it follows the same logic and will be auto-attached when the run is created.

**Attached bonus defaults:**
When a bonus is auto-attached, the `payroll_run_bonuses` record is created using the values from `bonus_types`:
- `amount` ← `bonus_types.default_amount`
- `rate` ← `bonus_types.default_rate`
- `percentage_basis` ← `bonus_types.percentage_basis`
- `attendance_threshold_days` ← `bonus_types.attendance_threshold_days`
- `apply_to_all = 1`
- `is_active = 1`

The payroll officer can override these values before the run is submitted.

---

## Per-Run Bonus Configuration

While the payroll run is in `draft`, the payroll officer (or owner) can:

1. **View attached bonuses** on the payroll run detail screen
2. **Add a bonus** manually from the catalog (any active `bonus_types`)
3. **Remove a bonus** (sets `is_active = 0` on `payroll_run_bonuses`)
4. **Override the amount or rate** for a bonus in this specific run
5. **Toggle `apply_to_all`** to enable per-employee exclusions

Changes to bonuses in a `draft` run trigger recomputation of all payslips via `RecomputePayrollRunAction`.

---

## Per-Employee Exclusions

When `payroll_run_bonuses.apply_to_all = 0`, specific employees can be excluded from receiving that bonus.

Exclusions are stored in `payroll_run_bonus_exclusions`:
```
payroll_run_bonus_exclusions:
    payroll_run_bonus_id → which bonus+run combination
    employee_id          → which employee is excluded
    reason               → optional text note
```

**UI flow:**
1. Payroll officer opens bonus detail on the run
2. Toggles off `Apply to All`
3. A list of all employees in the run appears with checkboxes
4. Unchecked employees are added to exclusions
5. On save, payslips for excluded employees are recomputed without that bonus

**Computation check (Step 2):**
```php
foreach employee in payroll_run:
    foreach bonus in payroll_run_bonuses where is_active = 1:
        excluded = payroll_run_bonus_exclusions
                   .where('payroll_run_bonus_id', bonus.id)
                   .where('employee_id', employee.id)
                   .exists()
        if not excluded:
            apply bonus to payslip
```

---

## Bonus Application Order

Bonuses are applied and listed on the payslip in `sort_order` sequence from `bonus_types`. The default order is:

| sort_order | Code | Name |
|---|---|---|
| 10 | `MEAL_ALLOWANCE` | Meal Allowance |
| 20 | `ATTENDANCE_BONUS` | Attendance Bonus |
| 30 | `13TH_MONTH` | 13th Month Pay |
| 40 | `JUNE_SPECIAL` | June Special Bonus |
| 50+ | custom codes | Custom Bonuses (in creation order) |

All bonus amounts feed into the `total_bonuses` aggregate on the `payslips` record.

---

## Bonus and External Salary Employees

Employees with `has_external_salary = true` **do receive bonuses**. The bonus computation in Step 2 applies to them normally.

The only difference for external salary employees is that deductions (Steps 3–9) are skipped. Their net pay is:

```
net_pay = gross_pay + total_bonuses
```

If the business intent is to also exclude external salary employees from bonuses, they should be added to `payroll_run_bonus_exclusions` manually.

---

## UI Flow

### Settings → Bonuses

- Lists all `bonus_types` for the company
- Owner can create, edit, or deactivate custom bonuses
- System bonuses (`is_system = 1`) can have their `default_amount` and `default_rate` updated but cannot be deleted or have their `code` changed

### Payroll Run → Bonuses Tab

- Lists all bonuses attached to the current run (`payroll_run_bonuses`)
- Payroll officer can:
  - Add bonuses from catalog (opens a modal with available bonus types not already attached)
  - Edit amount/rate for the run (opens an inline edit or modal)
  - Toggle active/inactive per bonus
  - Manage exclusions per bonus
- Any change triggers background recomputation of affected payslips
- When the run is moved out of `draft`, this tab becomes read-only
