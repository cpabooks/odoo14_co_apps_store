# Release validation — 2026-11-02

Environment: Odoo 14 Community, Python 3.8.20, isolated PostgreSQL 16 on port
55439, disposable database `co_store_release`. Addons paths contained only
standard Community addons and this repository. No Enterprise or private
`cpabooks-custom` addons were loaded. No production database was changed.

## Passed

- All eight addon manifests, dependency allowlist, declared files, Python/XML
  syntax, local description images/icons, ACL packaging and old namespaces.
- Local inherited views and report actions resolve to packaged XML definitions.
- All addon JavaScript syntax and Git whitespace checks.
- All eight addons installed in the disposable database and upgraded together.
  Installation failures found during preparation were fixed and rerun.
- `scripts/smoke_release.py` passed with all writes rolled back:
  - All eight installed states and external identifier namespaces.
  - Automatic account numbering and duplication, including legacy account
    groups that previously triggered recursive cleanup.
  - Restored FSM forms and quotation defaults.
  - Material request creation, a completed two-unit stock issue and return
    picking defaults loaded from that issue.
  - Internal/customer job completion report HTML rendering.
  - CAFM contract/order creation and contract report HTML rendering using
    standard Odoo company layout.
  - Financial Audit dashboard data, full-report and quick-print HTML rendering.
  - Public-user write denial for CAFM records, material requests and invoice types.

## Scope and limitations

The addons were installed together, not each in its own isolated database.
These checks cover server-side behavior and report HTML, not browser interaction
or actual wkhtmltopdf output. Existing screenshots, every workflow,
multi-company isolation and every permission combination were not exhaustively
reviewed. Non-blocking duplicate-label/model-description/tracking warnings remain.

The missing private dependency shown in the screenshot is resolved in source.
No authenticated Odoo Apps scan was run; remote name ownership and final store
acceptance remain subject to Odoo's scanner/review. No commit or push was made.
The checkout is on `main`; publish the reviewed changes to `14.0`, the branch
configured in the dashboard. See PUBLISHING.md.

## Reproduce

Run `scripts/validate_release.py` with the configured Odoo Python interpreter.
Run `scripts/smoke_release.py` through `odoo-bin shell` on a disposable database
with all eight addons installed. The smoke script always rolls back its writes.
