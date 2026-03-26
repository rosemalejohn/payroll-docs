# EP-08: Payroll Computation Engine

## Epic Summary

Implement the 10-step gross-to-net ComputePayslipAction pipeline: gross pay calculation, bonus application, absent deduction, SSS/PhilHealth/Pag-IBIG statutory deductions, HMO, voluntary deductions, cash advance recovery, BIR withholding tax (TRAIN Law), net pay with external salary path, batch recomputation, bulk deduction application, and per-employee BIR tax overrides.

## Tickets

| Ticket | Title |
|--------|-------|
| PAY-044 | ComputePayslipAction - Gross Pay Calculation (Step 1) |
| PAY-045 | ComputePayslipAction - Bonus Application (Step 2) |
| PAY-046 | ComputePayslipAction - Absent and Statutory Deductions (Steps 3-6) |
| PAY-047 | ComputePayslipAction - HMO, Voluntary Deductions, Cash Advance (Steps 7-8) |
| PAY-048 | ComputePayslipAction - BIR Withholding Tax (Step 9) |
| PAY-049 | ComputePayslipAction - Net Pay and External Salary Path (Step 10) |
| PAY-050 | RecomputePayrollRunAction - Batch Recompute All Payslips |
| PAY-084 | Bulk Apply Deductions to Payroll Run |
| PAY-085 | BIR Tax Override Per Employee |
