# Chart of Accounts Manager

Technical name: `co_chart_of_accounts` · Odoo 14 · LGPL-3

Standalone chart-of-accounts module. It depends only on standard Odoo modules:
`base`, `web`, `mail`, `product`, `account`, `purchase`.

## Features

- **L1 Type** (1 digit): 1 Assets · 2 Liabilities · 3 Equity · 4 Income · 5 Expense
- **L2 Group** (2 digits): IFRS reporting groups (e.g. 11 Fixed Assets, 15 Cash and Bank)
- **L3 Ledger** (company-configured digits): type + rolling number, independent of the group
- Automatic ledger code on create/duplicate; changing the group never changes the code
- COA list actions: Reset All, Factory Reset, merge, delete unused, regroup
- **Reset & Regenerate COA Codes** wizard with preview
- IFRS coding wizard for types, groups and ledgers
- Correspondent debit/credit ledgers
- Opening balance journal with automatic offset
- Create bank/cash journals from COA ledgers
- COA seed data under `data/coa_seed/`

## Optional integrations

These work automatically when the related app is installed, and are skipped otherwise:

- **Inventory** (`stock`): seeded products use the storable product type.
- **Employees** (`hr`): visa analytic accounts per employee.
- **Assets** (`account_asset`, Enterprise): deferred expense models.

## Upgrading from `co_chart_of_accounts` 0.3.x

The `14.0.1.0.0` migration re-activates the module views and re-runs the COA setup.
Do not install this module together with `co_chart_of_accounts_v1` in the same database.

## Installation

Add the repository root to `addons_path`, restart Odoo, update the Apps list,
clear the default Apps filter and search for **Chart of Accounts Manager**.
Install `co_chart_of_accounts`. The module extends Accounting rather than
adding a separate application tile.

Open **Accounting → Configuration → Chart of Accounts**. Accounting Managers
can use the setup and maintenance tools. Some administrative wizards also
require Settings access.

## Existing databases

Installation creates account defaults and resets account groups across companies.
It removes the standard per-company unique account-code constraint so mirrored
or duplicate ledger codes can be used. Review the resulting chart before posting
transactions. Always evaluate installation, reset, merge and code regeneration on
a backup copy first. Uninstalling does not undo accounting setup changes.

Company settings support four or six digit code preferences. The IFRS-oriented
structure is a setup aid; it is not a certification of regulatory compliance.

## Support and license

Support: info@cpabooks.org. Licensed under LGPL-3; the repository includes the
GPL-3 text and LGPL-3 additional permissions. Core features require no activation
key or third-party addon. Optional Enterprise integrations require their own
Odoo licenses.
