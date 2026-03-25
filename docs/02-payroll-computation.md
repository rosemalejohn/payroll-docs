# Payroll Computation

This document describes the full gross-to-net computation logic for payroll payslips. All monetary values are computed and stored in **PHP (Philippine Peso)**.

---

## Table of Contents

1. [Overview](#overview)
2. [Pre-Computation: Employee Classification](#pre-computation-employee-classification)
3. [Pre-Computation: Currency Conversion](#pre-computation-currency-conversion)
4. [Regular Employee: 10-Step Computation](#regular-employee-10-step-computation)
   - [Step 1: Gross Pay](#step-1-gross-pay)
   - [Step 2: Add Bonuses](#step-2-add-bonuses)
   - [Step 3: Absent Deduction](#step-3-absent-deduction)
   - [Step 4: SSS Deduction](#step-4-sss-deduction)
   - [Step 5: PhilHealth Deduction](#step-5-philhealth-deduction)
   - [Step 6: Pag-IBIG Deduction](#step-6-pag-ibig-deduction)
   - [Step 7: HMO Deduction](#step-7-hmo-deduction)
   - [Step 8: Voluntary Deductions](#step-8-voluntary-deductions)
   - [Step 9: BIR Withholding Tax](#step-9-bir-withholding-tax)
   - [Step 10: Net Pay](#step-10-net-pay)
5. [External Salary Employee Computation](#external-salary-employee-computation)
6. [BIR Withholding Tax Brackets](#bir-withholding-tax-brackets)
7. [SSS Contribution Table](#sss-contribution-table)
8. [Computation Order and Immutability](#computation-order-and-immutability)
9. [Recalculation Rules](#recalculation-rules)

---

## Overview

When a payroll run moves from `draft` to any state, payslips are computed for all active employees in the company for the given payroll period.

The computation engine is implemented as a Laravel action: `ComputePayslipAction`.

Each payslip is idempotent: if the payroll run is still in `draft`, recomputing it will overwrite the previous result. Once the run is `finalized`, no recomputation is allowed.

---

## Pre-Computation: Employee Classification

Before running the 10-step process, the engine checks `employees.has_external_salary`.

```
if has_external_salary == true:
    → run External Salary computation (see section below)
else:
    → run 10-step Regular computation
```

Employees with `employment_status != 'active'` are **excluded** from the run unless manually re-included by `payroll_officer` or `owner`.

---

## Pre-Computation: Currency Conversion

If the employee's `employee_compensation.currency_id` is not PHP, the salary figures must be converted to PHP using the **snapshot rate** from `payroll_run_currency_snapshots`.

```
salary_in_php = salary_in_foreign_currency × snapshot_rate
```

Where `snapshot_rate` is the value of `payroll_run_currency_snapshots.rate` for the matching `currency_id` and `payroll_run_id`.

All subsequent computation steps operate on PHP values only.

---

## Regular Employee: 10-Step Computation

### Step 1: Gross Pay

Gross pay depends on `employees.pay_basis`.

**Monthly basis:**
```
gross_pay = employee_compensation.monthly_salary
```

**Daily basis:**
```
gross_pay = employee_compensation.daily_rate × payroll_periods.working_days
```

`working_days` is the value on the `payroll_periods` record for this run (set by the payroll officer before the run).

At this point, `gross_pay` is the **base gross** before bonuses, absent deductions, or any adjustments.

The `BASIC` line item is recorded:
```
line_item: { code: 'BASIC', type: 'earning', amount: gross_pay }
```

---

### Step 2: Add Bonuses

All `payroll_run_bonuses` records linked to this run and marked `is_active = 1` are evaluated.

For each active bonus:
1. Check if employee is in `payroll_run_bonus_exclusions` for this bonus → if yes, skip
2. Compute bonus amount based on `bonus_types.computation_type`:

**Fixed bonus:**
```
bonus_amount = payroll_run_bonuses.amount
```

**Percentage bonus:**
```
if percentage_basis == 'basic':
    basis = gross_pay (Step 1 result, pre-absent deduction)
else: (gross)
    basis = gross_pay
bonus_amount = basis × payroll_run_bonuses.rate
```

**Formula bonus (13th Month):**
```
bonus_amount = (employee annual basic salary) / 12
```
For the purposes of this computation, annual basic is derived as:
```
if pay_basis == 'monthly':
    annual_basic = monthly_salary × 12
else:
    annual_basic = daily_rate × total_working_days_in_year (default: 261)
bonus_amount = annual_basic / 12
```

**Formula bonus (June Special):**
```
bonus_amount = gross_pay × 1.0   (equivalent to one month's gross pay)
```
The June Special is a full month's gross equivalent. If a different rate is needed, it is configured as a custom `percentage` bonus instead.

Each bonus is recorded as a line item:
```
line_item: { code: bonus_type.code, type: 'bonus', amount: bonus_amount }
```

**Running total after Step 2:**
```
gross_with_bonuses = gross_pay + SUM(all bonus_amounts)
```

---

### Step 3: Absent Deduction

```
daily_rate_for_deduction = monthly_salary / 22
```

If `pay_basis == 'daily'`, the daily rate is already known.

If `pay_basis == 'monthly'`, the daily rate for deductions uses a divisor of **22** (standard working days per month):
```
daily_rate_for_deduction = monthly_salary / 22
```

```
absent_deduction = daily_rate_for_deduction × payslips.absent_days
```

`absent_days` is entered by the payroll officer per employee per payroll run before computation.

```
line_item: { code: 'ABSENT_DEDUCTION', type: 'deduction', amount: absent_deduction }
```

**Adjusted gross after Step 3:**
```
adjusted_gross = gross_with_bonuses - absent_deduction
```

The deduction computation steps (4–9) use the **original `gross_pay` (Step 1)** as the basis for percentage-based calculations (not the adjusted gross). This matches standard Philippine payroll practice where statutory deductions are based on basic salary, not reduced by absences.

---

### Step 4: SSS Deduction

SSS is bracket-based. The bracket is looked up from the SSS contribution table using **`gross_pay` (basic salary, Step 1 value)**.

See the [SSS Contribution Table](#sss-contribution-table) section below.

```
sss_deduction = sss_employee_share (from bracket table)
```

```
line_item: { code: 'SSS', type: 'deduction', amount: sss_deduction }
```

---

### Step 5: PhilHealth Deduction

```
philhealth_deduction = gross_pay × 0.05 / 2
```

**Explanation:**
- PhilHealth rate is **5% of basic monthly salary** (as of 2024 directive)
- Total 5% is shared equally: 2.5% employee, 2.5% employer
- Employee share = `gross_pay × 0.025`

```
philhealth_deduction = gross_pay × 0.025
```

PhilHealth has a monthly salary ceiling for contribution purposes. As of the current rate schedule:
- Minimum contribution: ₱500 (salary ≤ ₱10,000)
- Maximum contribution: ₱5,000 (salary ≥ ₱100,000)

```
philhealth_basis = MAX(10000, MIN(gross_pay, 100000))
philhealth_deduction = philhealth_basis × 0.025
```

```
line_item: { code: 'PHILHEALTH', type: 'deduction', amount: philhealth_deduction }
```

---

### Step 6: Pag-IBIG Deduction

Pag-IBIG (HDMF) employee contribution is a **fixed ₱100.00** for all employees.

```
pagibig_deduction = 100.00
```

```
line_item: { code: 'PAGIBIG', type: 'deduction', amount: pagibig_deduction }
```

---

### Step 7: HMO Deduction

HMO is a **fixed amount per employee**, stored on the `employees` record as `hmo_amount`.

```
hmo_deduction = employees.hmo_amount
```

If `hmo_amount = 0.00`, no line item is generated for HMO.

```
line_item: { code: 'HMO', type: 'deduction', amount: hmo_deduction }
```

---

### Step 8: Voluntary Deductions

Applied only if the corresponding opt-in flags are set on the employee record.

**MP2 (Pag-IBIG Fund II):**
```
if employees.has_mp2 == true:
    mp2_deduction = employee_compensation.mp2_amount
    line_item: { code: 'MP2', type: 'deduction', amount: mp2_deduction }
```

**SSS WISP (Workers' Investment and Savings Program):**
```
if employees.has_sss_wisp == true:
    sss_wisp_deduction = employee_compensation.sss_wisp_amount
    line_item: { code: 'SSS_WISP', type: 'deduction', amount: sss_wisp_deduction }
```

**Cash Advance Recovery:**

All `cash_advances` records for this employee with `status = 'active'` are summed:

```
cash_advance_deduction = SUM(cash_advances.balance) WHERE employee_id = ? AND status = 'active'
```

If `cash_advance_deduction > 0`:
```
line_item: { code: 'CASH_ADVANCE', type: 'deduction', amount: cash_advance_deduction }
```

After the payroll run is **finalized**, a post-finalization job updates each recovered cash advance:
```
cash_advances.amount_recovered += deduction_applied
cash_advances.balance -= deduction_applied
if cash_advances.balance <= 0: status = 'fully_recovered'
```

---

### Step 9: BIR Withholding Tax

BIR withholding tax is computed based on the employee's **annualized taxable income**.

**Taxable income basis for withholding:**
```
taxable_monthly_income = gross_pay
                       - sss_deduction
                       - philhealth_deduction
                       - pagibig_deduction
                       (absent_deduction is NOT subtracted for BIR basis)
```

**Annualize for tax bracket lookup:**
```
annual_taxable_income = taxable_monthly_income × 12
```

**Look up the BIR bracket** (see [BIR Withholding Tax Brackets](#bir-withholding-tax-brackets) below) to get:
- `base_tax` (fixed amount for the bracket)
- `excess_over` (lower bound of bracket)
- `marginal_rate` (percentage applied to excess)

```
tax_on_excess = (annual_taxable_income - excess_over) × marginal_rate
annual_tax = base_tax + tax_on_excess
monthly_bir_tax = annual_tax / 12
```

Round `monthly_bir_tax` to 2 decimal places.

```
line_item: { code: 'BIR_TAX', type: 'deduction', amount: monthly_bir_tax }
```

---

### Step 10: Net Pay

```
total_deductions = absent_deduction
                 + sss_deduction
                 + philhealth_deduction
                 + pagibig_deduction
                 + hmo_deduction
                 + mp2_deduction
                 + sss_wisp_deduction
                 + cash_advance_deduction
                 + bir_tax

net_pay = gross_pay + total_bonuses - total_deductions
```

Where:
```
total_bonuses = SUM(all bonus line items from Step 2)
```

The net pay **cannot go below zero**. If computed net pay would be negative:
```
net_pay = max(0.00, net_pay)
```

A flag or warning should be surfaced to the payroll officer when net pay is floored to zero.

---

## External Salary Employee Computation

Employees with `has_external_salary = 1` are treated as pass-through:

1. Gross pay is computed (same as Step 1 above, based on pay_basis)
2. Bonuses are applied (same as Step 2)
3. **All deductions are skipped** (Steps 3–9 are not executed)
4. Net pay = gross pay + bonuses

```
gross_pay = [monthly_salary or daily_rate × working_days]  -- Step 1
total_bonuses = [sum of applicable bonuses]                 -- Step 2
total_deductions = 0.00
net_pay = gross_pay + total_bonuses
```

Only the owner can set `has_external_salary = true` on an employee record. This flag is typically used for:
- Contractual workers billed via external payroll service
- Foreign employees whose tax and statutory contributions are handled outside the system
- Consultants and freelancers on fixed contracts

---

## BIR Withholding Tax Brackets

Based on the **TRAIN Law (Republic Act 10963)** rates effective January 1, 2023.

These are **annual** taxable income brackets:

| Annual Taxable Income | Base Tax | Marginal Rate | Excess Over |
|---|---|---|---|
| ≤ ₱250,000 | ₱0 | 0% | ₱0 |
| ₱250,001 – ₱400,000 | ₱0 | 15% | ₱250,000 |
| ₱400,001 – ₱800,000 | ₱22,500 | 20% | ₱400,000 |
| ₱800,001 – ₱2,000,000 | ₱102,500 | 25% | ₱800,000 |
| ₱2,000,001 – ₱8,000,000 | ₱402,500 | 30% | ₱2,000,000 |
| > ₱8,000,000 | ₱2,202,500 | 35% | ₱8,000,000 |

**Implementation example (₱50,000/month employee):**

```
taxable_monthly = 50,000 - SSS - PhilHealth - Pag-IBIG
               ≈ 50,000 - 1,125 - 1,250 - 100
               = 47,525

annual_taxable = 47,525 × 12 = 570,300

Bracket: ₱400,001 – ₱800,000
base_tax = 22,500
excess_over = 400,000
marginal_rate = 20%

tax_on_excess = (570,300 - 400,000) × 0.20 = 170,300 × 0.20 = 34,060
annual_tax = 22,500 + 34,060 = 56,560
monthly_bir_tax = 56,560 / 12 = 4,713.33
```

**Important implementation notes:**
- The BIR tax brackets in code should be stored as a configuration array (not a database table) since they change infrequently and require a code deployment when they do change
- Statutory deductions (SSS, PhilHealth, Pag-IBIG) used in the BIR basis calculation use the values computed in Steps 4–6, not pre-estimated values
- BIR calculation therefore depends on Steps 4–6 completing first

---

## SSS Contribution Table

SSS uses a **salary bracket** system. The table below reflects the SSS contribution schedule effective January 2024 (MSC = Monthly Salary Credit).

**Employee share only (Payroll deducts employee share):**

| Monthly Basic Salary Range | MSC | Employee Share |
|---|---|---|
| Below ₱4,250 | ₱4,000 | ₱180.00 |
| ₱4,250 – ₱4,749.99 | ₱4,500 | ₱202.50 |
| ₱4,750 – ₱5,249.99 | ₱5,000 | ₱225.00 |
| ₱5,250 – ₱5,749.99 | ₱5,500 | ₱247.50 |
| ₱5,750 – ₱6,249.99 | ₱6,000 | ₱270.00 |
| ₱6,250 – ₱6,749.99 | ₱6,500 | ₱292.50 |
| ₱6,750 – ₱7,249.99 | ₱7,000 | ₱315.00 |
| ₱7,250 – ₱7,749.99 | ₱7,500 | ₱337.50 |
| ₱7,750 – ₱8,249.99 | ₱8,000 | ₱360.00 |
| ₱8,250 – ₱8,749.99 | ₱8,500 | ₱382.50 |
| ₱8,750 – ₱9,249.99 | ₱9,000 | ₱405.00 |
| ₱9,250 – ₱9,749.99 | ₱9,500 | ₱427.50 |
| ₱9,750 – ₱10,249.99 | ₱10,000 | ₱450.00 |
| ₱10,250 – ₱10,749.99 | ₱10,500 | ₱472.50 |
| ₱10,750 – ₱11,249.99 | ₱11,000 | ₱495.00 |
| ₱11,250 – ₱11,749.99 | ₱11,500 | ₱517.50 |
| ₱11,750 – ₱12,249.99 | ₱12,000 | ₱540.00 |
| ₱12,250 – ₱12,749.99 | ₱12,500 | ₱562.50 |
| ₱12,750 – ₱13,249.99 | ₱13,000 | ₱585.00 |
| ₱13,250 – ₱13,749.99 | ₱13,500 | ₱607.50 |
| ₱13,750 – ₱14,249.99 | ₱14,000 | ₱630.00 |
| ₱14,250 – ₱14,749.99 | ₱14,500 | ₱652.50 |
| ₱14,750 – ₱15,249.99 | ₱15,000 | ₱675.00 |
| ₱15,250 – ₱15,749.99 | ₱15,500 | ₱697.50 |
| ₱15,750 – ₱16,249.99 | ₱16,000 | ₱720.00 |
| ₱16,250 – ₱16,749.99 | ₱16,500 | ₱742.50 |
| ₱16,750 – ₱17,249.99 | ₱17,000 | ₱765.00 |
| ₱17,250 – ₱17,749.99 | ₱17,500 | ₱787.50 |
| ₱17,750 – ₱18,249.99 | ₱18,000 | ₱810.00 |
| ₱18,250 – ₱18,749.99 | ₱18,500 | ₱832.50 |
| ₱18,750 – ₱19,249.99 | ₱19,000 | ₱855.00 |
| ₱19,250 – ₱19,749.99 | ₱19,500 | ₱877.50 |
| ₱19,750 and above | ₱20,000 | ₱900.00 |

**Implementation notes:**
- SSS brackets should be stored as a PHP config file or database-seeded lookup table that can be updated when SSS revises their schedule
- The lookup key is `gross_pay` (basic salary from Step 1)
- If `gross_pay < 4,250`, use the minimum bracket (₱180.00)
- If `gross_pay >= 19,750`, use the maximum bracket (₱900.00)

---

## Computation Order and Immutability

The 10 steps must execute in strict order because later steps depend on earlier results:

```
Step 1  → produces gross_pay
Step 2  → produces total_bonuses (depends on Step 1 basis for percentage bonuses)
Step 3  → produces absent_deduction (depends on Step 1 daily_rate_for_deduction)
Step 4  → produces sss_deduction (depends on Step 1 gross_pay for bracket lookup)
Step 5  → produces philhealth_deduction (depends on Step 1 gross_pay)
Step 6  → produces pagibig_deduction (fixed, no dependency)
Step 7  → produces hmo_deduction (fixed, no dependency)
Step 8  → produces voluntary deductions (depends on employee flags; cash advance from DB)
Step 9  → produces bir_tax (depends on Steps 1, 4, 5, 6 values)
Step 10 → produces net_pay (depends on all above)
```

---

## Recalculation Rules

| State | Can Recalculate? | Notes |
|---|---|---|
| `draft` | Yes | Full recomputation on every save or explicit trigger |
| `submitted` | No | Locked; changes require returning to draft (not supported) |
| `under_review` | No | Locked |
| `finalized` | No | Permanently locked |

When the payroll run is in `draft`, the payroll officer may:
- Update `absent_days` per employee
- Add or remove bonuses from the run
- Change bonus amounts for this run
- Update employee compensation (changes take effect on next computation)

After any such change, the payslip(s) must be recomputed via `ComputePayslipAction`.
