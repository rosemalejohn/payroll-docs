# User Stories — Payroll Standalone App

**Stack:** Laravel 12 + Inertia + React
**Roles:** `owner`, `payroll_officer`, `finance`, `employee`
**Base Currency:** PHP (manual exchange rates)

---

## Table of Contents

1. [Owner Stories](#owner-stories)
2. [Payroll Officer Stories](#payroll-officer-stories)
3. [Finance Stories](#finance-stories)
4. [Employee Stories](#employee-stories)
5. [Edge Case Stories](#edge-case-stories)

---

## Owner Stories

---

### US-01 — Manage Employee Roster

**As an owner, I want to add, edit, and deactivate employees so that the payroll roster stays accurate and up to date.**

**Acceptance Criteria:**
- Owner can create an employee with fields: name, email, role, pay basis (monthly/daily), base rate, and currency.
- Owner can toggle `has_external_salary` on any employee at any time.
- Deactivated employees are excluded from future payroll runs but their historical payslips remain accessible.
- Changing an employee's pay basis takes effect on the next payroll run, not the current open run.
- A confirmation prompt is shown before deactivating an employee who is included in an open payroll run.

---

### US-02 — Set Employee Pay Basis

**As an owner, I want to assign either a monthly salary or a daily rate to each employee so that payroll is computed correctly based on their employment type.**

**Acceptance Criteria:**
- Pay basis defaults to `monthly` on employee creation.
- Selecting `daily` exposes a daily rate field; selecting `monthly` exposes a monthly salary field.
- Monthly salary employees have their gross pay set to the fixed monthly amount.
- Daily rate employees have their gross pay computed as `daily_rate × working_days_in_period`.
- Both pay basis types participate in deductions and tax unless `has_external_salary` is true.

---

### US-03 — Mark Employee as External Salary

**As an owner, I want to flag an employee as having an external salary so that deductions and taxes are not applied to their payslip.**

**Acceptance Criteria:**
- A toggle `has_external_salary` is available on the employee profile.
- When enabled, the system skips SSS, PhilHealth, Pag-IBIG, HMO, MP2, SSS WISP, Absent Deduction, and BIR Withholding Tax for that employee.
- The gross pay for an external salary employee is recorded as-is with no net pay computation.
- The payslip for an external salary employee shows a note: "External Salary — No Deductions Applied."
- The flag can be changed by the owner only; payroll officers cannot modify it.

---

### US-04 — Configure Currency Exchange Rates

**As an owner, I want to set and update manual exchange rates (e.g., 1 USD = 60.41 PHP) via the Settings modal so that salaries denominated in foreign currencies are converted correctly to PHP.**

**Acceptance Criteria:**
- The Settings modal lists all active currency pairs with current rates and a last-updated timestamp.
- Owner enters the new rate and saves; the rate takes effect immediately for any open or future runs.
- Historical payslips retain the rate that was active at the time the run was finalized.
- If a rate is updated while a run is in `under_review` status, a warning banner is shown on the run detail page.
- A rate of zero or a negative value is rejected with a validation error.

---

### US-05 — Assign Roles to Users

**As an owner, I want to assign the `payroll_officer`, `finance`, or `employee` role to each user so that access is restricted to appropriate features.**

**Acceptance Criteria:**
- Only the owner can assign or change roles.
- A user cannot hold more than one non-owner role unless explicitly permitted.
- Changing a user's role takes effect immediately without requiring re-login.
- Role assignments are logged in the audit trail with timestamp and actor.
- Attempting to remove the last owner account is blocked with an error message.

---

### US-06 — View Payroll Audit Trail

**As an owner, I want to view a complete audit trail for every payroll run so that I can track who made changes and when.**

**Acceptance Criteria:**
- The audit trail records every status transition (draft → submitted → under_review → finalized) with actor and timestamp.
- Any edit to a payroll line item (bonus, deduction override) is captured with old and new values.
- Currency rate changes that overlap with an active run are noted in the audit trail for that run.
- The owner can filter the audit trail by run, date range, or user.
- The audit trail is read-only and cannot be deleted or edited.

---

### US-07 — Finalize a Payroll Run

**As an owner, I want to finalize a payroll run so that payslips are locked, made available for download, and no further changes can be made.**

**Acceptance Criteria:**
- Only runs in `under_review` status can be finalized.
- Finalization locks all payslip line items; no edits are permitted after this point.
- All employee payslips are generated as downloadable PDFs upon finalization.
- A finalized run displays the total net payroll amount, total deductions, and total tax withheld.
- Attempting to finalize a run with missing mandatory deduction configurations shows a blocking error.

---

### US-08 — Configure Mandatory Deductions

**As an owner, I want to configure the rates and caps for mandatory deductions (SSS, PhilHealth, Pag-IBIG, HMO) so that they are applied consistently across all eligible employees.**

**Acceptance Criteria:**
- Owner can set employee share and employer share percentages and caps per deduction type.
- Changes to rates apply to the next payroll run; runs already in progress use the rates active at the time the run was created.
- Each deduction can be individually enabled or disabled for the company.
- Disabling a mandatory deduction logs a warning in the audit trail.
- Validation prevents saving a rate that exceeds 100% or a cap below zero.

---

### US-09 — Configure Voluntary Deductions

**As an owner, I want to configure voluntary deductions (MP2, SSS WISP) and their default enrollment status so that eligible employees are enrolled correctly.**

**Acceptance Criteria:**
- Owner can set a fixed amount or percentage for MP2 and SSS WISP per employee.
- Default enrollment status can be set globally (opt-in or opt-out).
- Individual employee enrollment can be overridden on the employee profile.
- Voluntary deductions are shown separately from mandatory deductions on the payslip.
- Removing a voluntary deduction mid-run prompts the owner to confirm the change.

---

### US-10 — Generate Company Payroll Summary Report

**As an owner, I want to generate a summary report for a finalized payroll run so that I have an overview of total payroll costs, taxes, and deductions.**

**Acceptance Criteria:**
- The summary report shows total gross pay, total deductions by type, total BIR withheld, and total net pay.
- The report can be filtered by department or pay basis.
- The report is exportable as CSV and PDF.
- Summary figures include employer contribution amounts for SSS, PhilHealth, and Pag-IBIG.
- Reports are available only for finalized runs.

---

## Payroll Officer Stories

---

### US-11 — Create a Payroll Run

**As a payroll_officer, I want to create a new payroll run for a specific period so that I can begin computing employee salaries.**

**Acceptance Criteria:**
- A payroll run requires a period label (e.g., "March 2026"), start date, and end date.
- Only one run per period can exist in `draft`, `submitted`, or `under_review` status at a time.
- The system auto-populates the run with all active employees at the time of creation.
- Employees added after the run is created must be manually added to that run.
- The run is created in `draft` status and is editable by the payroll_officer.

---

### US-12 — Add Employees to a Draft Run

**As a payroll_officer, I want to add or remove employees from a draft payroll run so that the correct roster is included before submission.**

**Acceptance Criteria:**
- Payroll officer can add any active employee not already in the run.
- Payroll officer can remove an employee from a draft run; this does not deactivate them globally.
- Removing an employee prompts for a reason (e.g., terminated, on leave without pay).
- The run cannot be submitted if it contains zero employees.
- Addition/removal of employees in a draft run is recorded in the audit trail.

---

### US-13 — Apply Bonus to Employees in a Run

**As a payroll_officer, I want to apply bonuses (Meal Allowance, Attendance Bonus, 13th Month, June Special, Custom) to employees in a run so that additional compensation is included in their payslip.**

**Acceptance Criteria:**
- Meal Allowance is a fixed PHP amount entered per employee or applied in bulk.
- Attendance Bonus is a percentage of gross pay, configurable per run.
- 13th Month and June Special bonuses can be manually triggered; they also auto-trigger for the appropriate run months (see US-30 and US-31).
- Custom bonuses require a label, amount, and taxability flag.
- All bonuses are itemized on the payslip.

---

### US-14 — Record Cash Advance Deduction

**As a payroll_officer, I want to enter a cash advance deduction for an employee so that the amount disbursed to them earlier is recovered via payroll.**

**Acceptance Criteria:**
- Cash advance deductions are entered with an amount and optional note.
- Multiple cash advance entries can be added per employee per run.
- The total cash advance deduction is itemized as a single line on the payslip showing the total amount.
- Cash advance deductions are included in net pay computation after all other deductions.
- If the cash advance amount exceeds net pay, the system shows a warning but does not block submission.

---

### US-15 — Record Absent Deduction

**As a payroll_officer, I want to enter absent day deductions for an employee so that unpaid absences are reflected in their net pay.**

**Acceptance Criteria:**
- Absent deductions are entered as a number of days; the system computes the deduction amount based on daily rate (or monthly salary divided by working days).
- The number of absent days cannot exceed the total working days in the run period.
- Absent deductions are listed separately on the payslip.
- A note field is available to record the reason for absence.
- Absent deductions apply to both monthly and daily rate employees.

---

### US-16 — Submit a Payroll Run for Review

**As a payroll_officer, I want to submit a completed draft run for review so that the finance team can verify it before finalization.**

**Acceptance Criteria:**
- Only draft runs can be submitted.
- Submission transitions the run to `submitted` status.
- The payroll_officer cannot edit the run after submission without it being returned to draft.
- A submission confirmation dialog summarizes the number of employees, total gross, and total net.
- An in-app notification is sent to users with the `finance` role upon submission.

---

### US-17 — Return a Run to Draft

**As a payroll_officer, I want to return a submitted or under_review run to draft so that I can correct errors identified during review.**

**Acceptance Criteria:**
- Returning a run to draft requires a reason comment.
- Only the payroll_officer or owner can initiate the return to draft action.
- Returning a run from `under_review` also notifies the finance user who placed it under review.
- All edits made after returning to draft are logged in the audit trail.
- A run cannot be returned to draft once it is finalized.

---

### US-18 — View Employee Payslip Preview

**As a payroll_officer, I want to preview an employee's payslip before the run is finalized so that I can verify the computation before submission.**

**Acceptance Criteria:**
- Payslip preview is available for any run in draft or submitted status.
- The preview shows gross pay, all deductions itemized, BIR withheld, bonuses, and net pay.
- The preview is marked with a "DRAFT" watermark so it is not mistaken for a finalized document.
- The preview accurately reflects any unsaved changes in the current editing session.
- The preview is accessible without leaving the current payroll run page.

---

### US-19 — Bulk Apply Deductions

**As a payroll_officer, I want to apply a deduction to all eligible employees in a run at once so that I do not have to enter repetitive data per employee.**

**Acceptance Criteria:**
- Bulk apply is available for SSS, PhilHealth, Pag-IBIG, HMO, MP2, and SSS WISP.
- The system uses each employee's configured rate or bracket to compute individual amounts.
- Employees with `has_external_salary=true` are automatically excluded from bulk deduction application.
- A summary shows how many employees were affected and the total deduction amount.
- Individual employee deduction amounts can still be overridden after bulk application.

---

### US-20 — View Run History

**As a payroll_officer, I want to view a list of all previous payroll runs and their statuses so that I can track payroll history.**

**Acceptance Criteria:**
- The run list shows period, status, created date, total employees, and total net pay for each run.
- Runs can be filtered by status (draft, submitted, under_review, finalized) and date range.
- Clicking a run opens its detail page in read-only mode if finalized, or editable mode if in draft.
- The run list is paginated and defaults to most recent first.
- Finalized runs show a "Download Summary" action button.

---

### US-21 — Handle BIR Withholding Tax

**As a payroll_officer, I want the system to automatically compute BIR withholding tax for each employee so that tax compliance is maintained without manual calculation.**

**Acceptance Criteria:**
- BIR tax is computed based on the applicable TRAIN Law brackets applied to the employee's taxable income for the period.
- Taxable income excludes non-taxable bonuses and mandated benefit contributions up to statutory limits.
- The computed BIR amount is shown per employee before submission.
- External salary employees (`has_external_salary=true`) have zero BIR computed.
- The payroll_officer can override the computed BIR for a specific employee with a note; the override is logged.

---

## Finance Stories

---

### US-22 — Review a Submitted Payroll Run

**As a finance user, I want to review a submitted payroll run so that I can verify all figures before it proceeds to finalization.**

**Acceptance Criteria:**
- Finance can view all payslip details for a submitted run in read-only mode.
- Finance can place the run `under_review` to signal active verification is in progress.
- Finance can add comments or flags on individual employee payslip lines.
- Finance cannot edit payslip figures directly; they must return the run to the payroll_officer.
- The run can be approved (moved to owner queue for finalization) or returned to draft by finance.

---

### US-23 — Flag Discrepancies in a Run

**As a finance user, I want to flag individual employee payslip lines with a discrepancy note so that the payroll_officer can investigate and correct them.**

**Acceptance Criteria:**
- Finance can add a flag with a text note on any payslip line item (deduction, bonus, gross pay).
- Flagged items are highlighted in the run detail view for all authorized users.
- Flags are visible to the payroll_officer when the run is returned to draft.
- Resolving a flag requires the payroll_officer to mark it as resolved with a comment.
- All unresolved flags block re-submission.

---

### US-24 — Approve a Run for Finalization

**As a finance user, I want to approve a reviewed run so that the owner can proceed to finalize it.**

**Acceptance Criteria:**
- Approval is only available when the run is in `under_review` status.
- Approving a run transitions it to a "pending finalization" state visible to the owner.
- An in-app notification is sent to the owner upon approval.
- Finance approval is logged with timestamp in the audit trail.
- Finance cannot finalize the run themselves; finalization is exclusively the owner's action.

---

### US-25 — Export Payroll Data for Accounting

**As a finance user, I want to export finalized payroll data so that I can import it into the accounting system.**

**Acceptance Criteria:**
- Export is available only for finalized runs.
- Export formats include CSV (detailed per-employee) and PDF (summary).
- The CSV includes: employee name, gross pay, each deduction type, BIR withheld, bonuses, and net pay.
- Amounts in foreign currencies are exported in both the original currency and PHP equivalent.
- The export file name includes the run period (e.g., `payroll-march-2026.csv`).

---

### US-26 — View Deduction Remittance Report

**As a finance user, I want to view a deduction remittance report for a finalized run so that I know the total amounts to remit to SSS, PhilHealth, Pag-IBIG, and BIR.**

**Acceptance Criteria:**
- The remittance report groups deductions by agency (SSS, PhilHealth, Pag-IBIG, BIR) with employee and employer shares.
- Per-employee breakdowns are available within each agency grouping.
- The report is downloadable as PDF.
- Totals match the figures in the finalized payslips.
- The report includes the run period and date of finalization as header metadata.

---

### US-27 — View Currency Conversion Details

**As a finance user, I want to view the exchange rates applied to each finalized run so that I can reconcile PHP amounts against original foreign currency salaries.**

**Acceptance Criteria:**
- The run detail page shows the exchange rate used for each currency pair present in the run.
- If a rate was updated mid-run (between run creation and finalization), both the original and updated rates are shown with their effective dates.
- Finance can see which employees had salaries converted and at what rate.
- Currency details are included in the CSV export.
- Historical rates cannot be changed retroactively on a finalized run.

---

## Employee Stories

---

### US-28 — View My Payslips

**As an employee, I want to view a list of my finalized payslips so that I can track my compensation history.**

**Acceptance Criteria:**
- The employee can view payslips only for runs that have been finalized.
- The list shows period, gross pay, total deductions, and net pay for each payslip.
- Draft and in-progress payslip data is not visible to the employee.
- The list is sorted by period, most recent first.
- The employee can only see their own payslips, not those of other employees.

---

### US-29 — Download My Payslip as PDF

**As an employee, I want to download my payslip as a PDF so that I have an official record of my compensation for a given period.**

**Acceptance Criteria:**
- A "Download PDF" button is available on each finalized payslip.
- The PDF includes: employee name, period, gross pay, itemized deductions, bonuses, BIR withheld, and net pay.
- The PDF includes the company name, payroll period, and date of finalization.
- External salary employees receive a simplified payslip with no deduction section.
- The PDF is generated server-side and is identical every time it is downloaded.

---

### US-30 — View My Deduction Breakdown

**As an employee, I want to see a breakdown of all deductions applied to my payslip so that I understand how my net pay was computed.**

**Acceptance Criteria:**
- Deductions are listed individually: SSS, PhilHealth, Pag-IBIG, HMO, MP2, SSS WISP, Cash Advance, Absent Deduction.
- Each deduction shows the basis (e.g., "SSS: 4.5% of gross up to bracket cap") alongside the PHP amount.
- Voluntary deductions are labeled as such.
- If a deduction was overridden by the payroll_officer, it is shown with an asterisk and a note.
- Total deductions are summed at the bottom with a clear net pay figure.

---

### US-31 — View My Bonus Details

**As an employee, I want to see the bonuses applied to my payslip so that I understand all components of my total compensation.**

**Acceptance Criteria:**
- Each bonus is listed by name (Meal Allowance, Attendance Bonus, 13th Month Pay, June Special, or custom label).
- The computation basis is shown (e.g., "Attendance Bonus: 5% of gross = PHP 1,500").
- Auto-triggered bonuses (13th Month in December, June Special in June) are labeled "Auto" in the payslip.
- Custom bonuses show the label provided by the payroll_officer.
- Total bonuses are summed and added to gross pay before deductions.

---

---

## Edge Case Stories

---

### US-32 — Payroll Run for an External Salary Employee

**As a payroll_officer, I want the system to skip all deductions and tax for an external salary employee in a run so that their payslip only reflects the gross amount without any computed deductions.**

**Acceptance Criteria:**
- When computing pay for an employee with `has_external_salary=true`, the system sets all deduction fields to zero.
- BIR withholding tax is also set to zero for this employee.
- The payslip PDF for the employee shows gross pay and net pay as the same amount.
- A visible label "External Salary — No Deductions Applied" appears on the payslip.
- Bulk deduction application skips this employee automatically and shows a count of how many external salary employees were skipped.

---

### US-33 — December Run Auto-Triggers 13th Month Pay

**As a payroll_officer, I want the system to automatically include 13th Month Pay for all eligible employees in a December payroll run so that I do not have to manually apply it.**

**Acceptance Criteria:**
- When a payroll run is created with a period that falls in December, the system auto-adds a 13th Month Pay bonus for all eligible employees.
- 13th Month Pay is computed as 1/12 of the employee's total basic salary earned during the calendar year.
- The auto-trigger shows a confirmation prompt informing the payroll_officer that 13th Month Pay will be added.
- The payroll_officer can adjust the amount per employee before submission if corrections are needed.
- External salary employees are excluded from the auto-trigger.

---

### US-34 — June Run Auto-Triggers June Special Bonus

**As a payroll_officer, I want the system to automatically include the June Special Bonus for all eligible employees in a June payroll run so that the mid-year bonus is not missed.**

**Acceptance Criteria:**
- When a payroll run period falls in June, the system auto-adds the June Special Bonus for all configured employees.
- The June Special Bonus amount or rate is configurable by the owner in the Bonus Manager settings.
- The auto-trigger shows a confirmation prompt before adding the bonus.
- The payroll_officer can remove or adjust the bonus per employee before submission.
- If the June Special Bonus has not been configured, a warning is shown rather than a silent skip.

---

### US-35 — Mid-Month Employee Termination in an Open Run

**As a payroll_officer, I want to handle mid-month termination of an employee included in an open run so that their final pay is computed accurately for the days they actually worked.**

**Acceptance Criteria:**
- When an employee is marked as terminated with an effective date within the run period, the system prompts the payroll_officer to specify the last working day.
- Gross pay for a monthly employee is prorated: `(salary / working_days_in_period) × days_worked`.
- Gross pay for a daily rate employee uses actual days worked up to the termination date.
- All applicable deductions are recomputed based on the prorated gross.
- The payslip notes the termination effective date and the proration basis used.

---

### US-36 — Updating Currency Rate Mid-Run

**As an owner, I want to understand the impact of updating an exchange rate while a payroll run is in progress so that I can decide whether to update now or wait for the next run.**

**Acceptance Criteria:**
- When the owner updates a rate and one or more runs are in `draft`, `submitted`, or `under_review` status, the system shows a warning listing the affected runs.
- After confirmation, the new rate is applied to the in-progress run immediately; all affected employee pay figures are recomputed.
- The run detail page shows a banner: "Currency rate was updated [date/time]. Figures have been recomputed."
- The audit trail records the old rate, new rate, timestamp, and which run was affected.
- If the owner chooses not to apply the new rate to the current run, the update is queued for the next run and the current run retains the original rate.

---

### US-37 — Employee with Cash Advance Balance

**As a payroll_officer, I want to deduct an outstanding cash advance from an employee's net pay so that the company can recover disbursed funds.**

**Acceptance Criteria:**
- The payroll_officer enters the cash advance amount to recover in the current run.
- The system warns if the cash advance deduction exceeds the employee's net pay after all other deductions.
- If net pay would go negative, the system blocks submission and prompts the payroll_officer to reduce the cash advance amount or split it across multiple runs.
- The cash advance deduction is shown as a line item on the payslip.
- Partial recovery is supported; the remaining balance can be recorded for future runs via a note.

---

### US-38 — Daily Rate Employee with Absences

**As a payroll_officer, I want the system to compute the gross pay for a daily rate employee accounting for their absent days so that they are only paid for the days they actually worked.**

**Acceptance Criteria:**
- Gross pay for a daily rate employee is computed as `daily_rate × (working_days_in_period − absent_days)`.
- The payslip shows total working days, absent days, days paid, daily rate, and resulting gross pay.
- Absent days cannot exceed the total working days in the period; the system rejects values that do.
- Absent deduction is shown as a line item reflecting the value of the days not worked.
- All other deductions (SSS, PhilHealth, etc.) are based on the prorated gross after absent deductions.

---

### US-39 — Attempting to Submit a Run with Unresolved Flags

**As a payroll_officer, I want the system to block re-submission of a run that has unresolved finance flags so that I am forced to address all discrepancies before resubmitting.**

**Acceptance Criteria:**
- Attempting to submit a run returned from review with unresolved flags shows a blocking validation error.
- The error lists each unresolved flag by employee name and line item.
- Once all flags are marked resolved (with a comment), the submission button becomes active.
- Resolved flags remain visible in the audit trail as resolved, with the resolver's name and timestamp.
- The finance user can see resolved flags when the run returns to `submitted` or `under_review`.

---

### US-40 — Finance User Detects Currency Mismatch

**As a finance user, I want to be alerted when an employee's salary currency differs from the base currency and no exchange rate is configured so that I can flag the run before incorrect amounts are submitted.**

**Acceptance Criteria:**
- If an employee's salary is in a currency for which no exchange rate exists in Settings, a warning is shown on the run detail page.
- The affected employee's pay line is highlighted with a "Missing Rate" indicator.
- The run cannot be moved from `submitted` to `under_review` until all currency rates are configured.
- Finance can navigate directly from the warning to the Settings modal to prompt the owner to set the rate.
- Once the rate is set, the run figures are recomputed and the warning is dismissed automatically.

---

### US-41 — Employee Views Payslip in Their Salary Currency

**As an employee, I want my payslip to show my salary in both my original currency and PHP so that I can understand the conversion applied.**

**Acceptance Criteria:**
- If the employee's base salary is in a foreign currency (e.g., USD), the payslip shows both the original amount and the PHP equivalent.
- The exchange rate used and the date it was set are displayed on the payslip.
- Net pay is always displayed in PHP as the primary figure.
- Deductions are shown in PHP, with a note indicating they are computed on the PHP-converted gross.
- If the employee's currency is PHP, no conversion section is shown on the payslip.

---

### US-42 — Owner Prevents Double Payroll Run for Same Period

**As an owner, I want the system to prevent creating a duplicate payroll run for a period that already has an active or finalized run so that payroll is not accidentally processed twice.**

**Acceptance Criteria:**
- Attempting to create a run for a period that overlaps with an existing non-cancelled run triggers a validation error.
- The error message names the existing run and its current status.
- A finalized run for a period cannot be superseded without explicit owner confirmation and a documented reason.
- If the existing run was cancelled, a new run for the same period can be created without restriction.
- The run creation form shows a list of recent runs to help the payroll_officer avoid duplicates.

---

### US-43 — Handling HMO Deduction for New Employee Mid-Period

**As a payroll_officer, I want to prorate the HMO deduction for a new employee who joined mid-period so that they are not charged a full month's HMO in their first partial payroll.**

**Acceptance Criteria:**
- When a new employee is added to a run with a start date within the run period, the HMO deduction is prorated based on days worked.
- The prorated amount is computed as `(HMO_monthly / working_days_in_period) × days_worked`.
- The payslip notes the pro-ration basis and the employee's start date.
- The payroll_officer can override the prorated amount if a different arrangement applies.
- Other mandatory deductions (SSS, PhilHealth, Pag-IBIG) follow the same prorated logic for the first partial period.

---

### US-44 — Payroll Officer Cannot Finalize a Run

**As a payroll_officer, I want to be prevented from finalizing a run so that finalization remains exclusively within the owner's authority and unauthorized pay releases are blocked.**

**Acceptance Criteria:**
- The "Finalize" button is not visible to users with the `payroll_officer` role.
- Any direct API call to finalize a run by a payroll_officer returns a 403 Forbidden response.
- The payroll_officer can see the run status and know it is pending owner finalization.
- The payroll_officer receives an in-app notification when a run they submitted is finalized.
- This access control is enforced at the backend policy layer, not only in the UI.

---

### US-45 — Employee Cannot View Draft or In-Progress Payslips

**As an employee, I want to be restricted from seeing my payslip data until the run is finalized so that I do not see unverified or incomplete pay information.**

**Acceptance Criteria:**
- The employee's payslip list page does not show any entry for runs in `draft`, `submitted`, or `under_review` status.
- Direct URL navigation to a draft payslip by an employee returns a 403 Forbidden response.
- Once a run is finalized, the payslip appears on the employee's list within one minute.
- No partial or preview payslip data is exposed through any API endpoint to the employee role.
- The employee receives an in-app notification when a new finalized payslip is available.

---

### US-46 — Payroll Run Summary Includes Employer Contributions

**As an owner, I want to see employer-side contributions (SSS, PhilHealth, Pag-IBIG) included in the run summary so that I have full visibility into the total cost of payroll beyond just net pay.**

**Acceptance Criteria:**
- The run summary page shows employee contributions and employer contributions separately for each benefit.
- Total employer cost is computed as: `sum of net pay + sum of employer contributions`.
- Employer contributions are not deducted from employee net pay but are listed for cost accounting.
- The CSV export includes employer contribution columns.
- Employer contribution figures are based on the same brackets used for employee deductions.

---

*End of User Stories — 46 stories across 5 categories.*
