# Currency System

This document covers the currency management system: how currencies are stored, how rates are maintained manually, how rates are snapshotted at payroll run creation, and how conversions are applied during payslip computation.

---

## Table of Contents

1. [Overview](#overview)
2. [Base Currency](#base-currency)
3. [currencies Table](#currencies-table)
4. [Rate Format Convention](#rate-format-convention)
5. [Rate Management](#rate-management)
   - [Who Can Update Rates](#who-can-update-rates)
   - [Rate Update Modal Flow](#rate-update-modal-flow)
   - [rate_updated_at Tracking](#rate_updated_at-tracking)
6. [Currency Snapshot Strategy](#currency-snapshot-strategy)
   - [When Snapshots Are Created](#when-snapshots-are-created)
   - [payroll_run_currency_snapshots Table](#payroll_run_currency_snapshots-table)
   - [Why Snapshots Are Essential](#why-snapshots-are-essential)
7. [Conversion Formulas](#conversion-formulas)
   - [Foreign Currency to PHP](#foreign-currency-to-php)
   - [PHP to Foreign Currency (Display)](#php-to-foreign-currency-display)
8. [Multi-Currency Employee Compensation](#multi-currency-employee-compensation)
9. [Payslip Currency Display](#payslip-currency-display)
10. [Adding a New Currency](#adding-a-new-currency)
11. [Deactivating a Currency](#deactivating-a-currency)
12. [Implementation Notes](#implementation-notes)

---

## Overview

The currency system allows employees to have their compensation recorded in any active currency (e.g., USD, EUR, SGD). All payroll computations are performed in **PHP (Philippine Peso)**. Conversion happens once — at computation time — using the exchange rate snapshotted when the payroll run was created.

There is **no external rate API integration**. Rates are entered and maintained manually by the `owner`.

---

## Base Currency

PHP (Philippine Peso) is the base currency.

| Property | Value |
|---|---|
| Code | `PHP` |
| Name | Philippine Peso |
| Symbol | ₱ |
| Rate | `1.000000` (immutable) |
| `is_base` | `1` |

**Rules for the base currency:**
- `is_base` cannot be changed via the UI
- `rate` is permanently `1.000000` and cannot be edited
- The PHP currency record cannot be deleted or deactivated
- It is seeded during application setup

All other currencies are denominated **relative to PHP**.

---

## currencies Table

```
currencies
├── id              CHAR(26)       ULID
├── company_id      CHAR(26)
├── code            VARCHAR(10)    ISO 4217 e.g. USD, EUR, SGD
├── name            VARCHAR(100)   e.g. "US Dollar"
├── symbol          VARCHAR(10)    e.g. $, €, S$
├── rate            DECIMAL(18,6)  1 [code] = rate PHP
├── is_base         TINYINT(1)     1 = PHP only
├── is_active       TINYINT(1)
├── rate_updated_at TIMESTAMP      updated when rate changes
└── updated_by      CHAR(26)       ref: users.id
```

See `docs/01-database-schema.md` for the full DDL.

---

## Rate Format Convention

Rates are stored and interpreted as:

```
1 [FOREIGN_CURRENCY] = [rate] PHP
```

**Examples:**

| Currency | Rate | Meaning |
|---|---|---|
| USD | 60.410000 | 1 USD = ₱60.41 |
| EUR | 65.230000 | 1 EUR = ₱65.23 |
| SGD | 44.800000 | 1 SGD = ₱44.80 |
| JPY | 0.390000 | 1 JPY = ₱0.39 |

This means a **higher rate = stronger foreign currency** relative to PHP.

The rate is stored with 6 decimal places to support currencies like JPY (where 1 JPY ≈ 0.39 PHP) and other low-denomination currencies.

---

## Rate Management

### Who Can Update Rates

Only users with the `owner` role can update exchange rates. The `payroll_officer` and `finance` roles have read-only access to the currency list.

### Rate Update Modal Flow

**Navigation:** Settings → Currencies → [Edit icon on a currency row]

The owner sees a modal with:

1. Currency name and code (read-only)
2. Symbol (read-only)
3. Current rate field (editable, numeric input with 6 decimal precision)
4. Last updated info: `"Last updated on [date] at [time]"` (pulled from `rate_updated_at`)
5. Save and Cancel buttons

**On save (`UpdateCurrencyRateAction`):**

```php
public function handle(Currency $currency, float $newRate, User $updatedBy): Currency
{
    $currency->update([
        'rate'            => $newRate,
        'rate_updated_at' => now(),
        'updated_by'      => $updatedBy->id,
    ]);

    return $currency;
}
```

The action:
1. Validates `$newRate > 0`
2. Prevents updating a currency with `is_base = 1` (throws exception)
3. Updates `rate`, `rate_updated_at`, and `updated_by`
4. The audit log (laravel-auditing) records the old and new rate values

**Frontend validation:**
- Rate must be a positive number greater than 0
- Rate input is formatted with comma grouping and up to 6 decimal places
- Display shows the live formula as the user types: `"1 [CODE] = ₱[rate]"`

### rate_updated_at Tracking

`rate_updated_at` is distinct from `updated_at`. It is only updated when the `rate` value itself changes:

```php
// Only set rate_updated_at if rate is actually changing
if ($currency->isDirty('rate')) {
    $currency->rate_updated_at = now();
}
```

This allows the UI to show "Rate last updated on [date]" without confusing it with other metadata changes (e.g., updating the currency name or symbol).

---

## Currency Snapshot Strategy

### When Snapshots Are Created

Snapshots are created **once**, at the moment a `PayrollRun` is created, via `SnapshotCurrencyRatesAction`.

```php
public function handle(PayrollRun $payrollRun): void
{
    $currencies = Currency::where('company_id', $payrollRun->company_id)
                          ->where('is_active', 1)
                          ->get();

    foreach ($currencies as $currency) {
        PayrollRunCurrencySnapshot::create([
            'payroll_run_id' => $payrollRun->id,
            'currency_id'    => $currency->id,
            'currency_code'  => $currency->code,
            'rate'           => $currency->rate,
            'snapshotted_at' => now(),
        ]);
    }

    $payrollRun->update(['rates_snapshotted_at' => now()]);
}
```

**Only active currencies** (`is_active = 1`) are snapshotted. If a currency is deactivated after a payroll run is created but before computation, it is excluded from the snapshot — which means no employee should be compensated in that currency at the time of the run.

### payroll_run_currency_snapshots Table

```
payroll_run_currency_snapshots
├── id             CHAR(26)       ULID
├── payroll_run_id CHAR(26)       ref: payroll_runs.id
├── currency_id    CHAR(26)       ref: currencies.id
├── currency_code  VARCHAR(10)    denormalized for readability
├── rate           DECIMAL(18,6)  rate at snapshot time
└── snapshotted_at TIMESTAMP
```

Lookup in computation:

```php
$snapshotRate = PayrollRunCurrencySnapshot::where('payroll_run_id', $run->id)
    ->where('currency_id', $employee->compensation->currency_id)
    ->value('rate');
```

### Why Snapshots Are Essential

Without snapshotting, updating an exchange rate after a payroll run is created would retroactively change the computed PHP amounts on payslips, violating payroll integrity.

**Scenario without snapshots:**
1. Payroll run created for March 2026. USD = 60.00 PHP.
2. Payroll officer computes payslips for a USD-salaried employee.
3. Owner updates USD rate to 62.00 PHP on March 28 (before run is finalized).
4. Without snapshots, the USD employee's PHP gross changes silently.

**With snapshots:**
- The USD employee's payslip always uses 60.00 PHP (the rate at payroll run creation).
- The rate change only affects **future** payroll runs created after the update.

This guarantees that a finalized payslip is immutable and reflects the economic conditions at the time of the run.

---

## Conversion Formulas

### Foreign Currency to PHP

Used during payslip computation (Step 1 and Step 2):

```
amount_in_php = amount_in_foreign_currency × snapshot_rate
```

**Example:**
```
Employee salary: 2,000 USD
Snapshot rate:   60.41 PHP per USD
PHP gross:       2,000 × 60.41 = ₱120,820.00
```

### PHP to Foreign Currency (Display)

Used when displaying payslip amounts in the employee's salary currency (for the PDF):

```
amount_in_foreign = amount_in_php / snapshot_rate
```

**Example:**
```
Net pay (PHP):       ₱105,000.00
Snapshot rate:       60.41 PHP per USD
Net pay (USD):       105,000 / 60.41 = $1,737.63
```

Rounding: round to 2 decimal places using PHP's `round()` with `PHP_ROUND_HALF_UP` mode.

---

## Multi-Currency Employee Compensation

Each employee has a `currency_id` on their `employee_compensation` record, indicating what currency their salary is stored in.

**Possible states:**

| Scenario | currency_id | Handling |
|---|---|---|
| PHP employee | PHP currency ID | No conversion needed; rate = 1.0 |
| USD employee | USD currency ID | Convert using snapshot rate |
| SGD employee | SGD currency ID | Convert using snapshot rate |

**Computation path:**

```php
if ($compensation->currency_id === $phpCurrencyId) {
    $grossPayPhp = $compensation->monthly_salary; // or daily_rate × working_days
} else {
    $snapshotRate = $this->getSnapshotRate($run, $compensation->currency_id);
    $grossPayForeign = $compensation->monthly_salary; // or daily_rate × working_days
    $grossPayPhp = $grossPayForeign * $snapshotRate;
}
```

The `salary_exchange_rate` and `salary_currency_code` are stored denormalized on the `payslips` record for auditing and display purposes.

---

## Payslip Currency Display

The payslip PDF shows amounts in two ways depending on the employee's salary currency:

**PHP employee:**
- All amounts shown in PHP only: `₱ 45,000.00`

**Foreign currency employee:**
- Primary amounts shown in PHP (required for statutory deductions which are always in PHP)
- A secondary column or footer section shows the gross and net pay in the employee's original currency, labeled with the snapshot rate:

```
Gross Pay:   ₱ 120,820.00   (USD 2,000.00 × 60.4100)
Net Pay:     ₱ 105,340.00   (USD 1,743.96)
Rate used:   1 USD = ₱ 60.4100 (as of March 1, 2026)
```

The rate shown is pulled from `payslips.salary_exchange_rate` (the snapshot rate, not the live rate).

---

## Adding a New Currency

**Navigation:** Settings → Currencies → Add Currency

The owner fills out:
- Code (ISO 4217, e.g., `EUR`)
- Name (e.g., `Euro`)
- Symbol (e.g., `€`)
- Current rate (e.g., `65.23` meaning 1 EUR = ₱65.23)

On save (`CreateCurrencyAction`):
1. Validates `code` is unique within the company
2. Validates `rate > 0`
3. Creates the `currencies` record with `is_base = 0`, `is_active = 1`
4. Sets `rate_updated_at = now()`

The currency is immediately available for assignment to employee compensation records.

---

## Deactivating a Currency

**Navigation:** Settings → Currencies → Toggle active/inactive

When a currency is deactivated (`is_active = 0`):
- It no longer appears in the currency selector when editing `employee_compensation`
- It is **not** included in future payroll run currency snapshots
- Existing payslips that reference it are unaffected (they use the snapshot, not the live record)

**Guard:** If any `employee_compensation` records still reference this currency with active employees, the system should warn the owner before deactivating. Deactivating a currency currently assigned to active employees will cause a computation error on the next payroll run.

A safe deactivation flow:
1. Check for `employee_compensation` records with `currency_id = ?` linked to active employees
2. If found, show a warning: "X employees still have compensation in [CURRENCY]. Please reassign before deactivating."
3. Block deactivation until all references are updated

---

## Implementation Notes

### Precision

All rate and monetary calculations use PHP's `DECIMAL` types in MySQL (never FLOAT). In application code, use Laravel's `decimal:6` cast for rate fields and `decimal:2` for monetary fields:

```php
// In Currency model
protected $casts = [
    'rate' => 'decimal:6',
];

// In EmployeeCompensation model
protected $casts = [
    'monthly_salary' => 'decimal:2',
    'daily_rate'     => 'decimal:2',
];
```

Avoid floating-point arithmetic. For currency multiplication, use BC Math or a money library if precision issues arise in edge cases.

### Seeding

The database seeder creates the PHP base currency:

```php
Currency::create([
    'id'             => Str::ulid(),
    'company_id'     => $company->id,
    'code'           => 'PHP',
    'name'           => 'Philippine Peso',
    'symbol'         => '₱',
    'rate'           => '1.000000',
    'is_base'        => true,
    'is_active'      => true,
    'rate_updated_at'=> now(),
]);
```

### Rate Update Audit Trail

All rate changes are captured by `owen-it/laravel-auditing` on the `Currency` model. The audit log stores the old and new values:

```json
{
  "old_values": { "rate": "60.000000", "rate_updated_at": "2026-02-01 08:00:00" },
  "new_values": { "rate": "60.410000", "rate_updated_at": "2026-03-01 09:15:00" }
}
```

The Settings → Currencies screen shows the audit log for each currency, allowing the owner to see the full rate history.
