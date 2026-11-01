# Release validation

Prepared for Odoo 14 using Python 3.8.20 and an isolated PostgreSQL 16 instance.
No production database or original source addon was changed.

## Passed

- All 8 addons: manifest, data/demo/QWeb paths, local description images, icon,
  Python syntax, XML syntax and technical namespace packaging checks.
- JavaScript syntax checks and Git whitespace check.
- The following 6 addons installed together on a disposable database, then
  upgraded successfully with standard Odoo Community addons:
  `co_chart_of_accounts`, `co_cafm`, `co_fire_safety`, `co_recipe_costing`,
  `co_document_sequences`, `co_switchgear`.
- ORM smoke check: all 6 installed namespaces have external identifiers;
  automatic account numbering and duplicate numbering work; the renamed COA
  setup action resolves; public users cannot write CAFM units or contracts.
  Smoke writes were rolled back.

## Remaining blockers

- `co_audited_financials`: requires `project_dashboard_odoo`, absent from the
  supplied Apps Store source. Installation and reporting are unverified.
- `co_field_service`: initial installation exposed undeclared dependencies on
  `industry_fsm_report`, `cpabooks_project_issue_note`, and
  `all_in_one_schedule_activity_management`. These are now declared, and the
  customer report template is now included. Installation with these
  dependencies remains unverified. Enterprise is required for the report.

The 6-addon test checks installation together, not each addon in a separate
database. Interactive workflows, report rendering, multi-company isolation,
all permission combinations and image accuracy were not exhaustively tested.
Existing non-blocking duplicate field-label/model-description warnings remain.

Reproduce packaging checks with your Odoo Python interpreter:

```sh
/path/to/odoo-python scripts/validate_release.py
```

Run `scripts/smoke_release.py` through `odoo-bin shell` on a disposable database
with the 6 addons installed. See PUBLISHING.md for submission details.

No commit, push or remote Odoo Apps scan was performed. Name ownership and
final acceptance can only be confirmed by the Apps Store scanner/review.
