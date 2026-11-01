# Odoo Apps submission — Odoo 14

Repository: https://github.com/cpabooks/odoo14_co_apps_store.git
Register branch `14.0` as shown in the vendor dashboard.

## Names and contents

All eight modules use new technical names listed in `module_names.json`.
Display names, XML namespaces, module references, JavaScript identifiers,
asset paths and the internal fire-safety/sequence dependency were updated.
The old `cpabooks_chart_of_accounts` directory must not be re-added to this
repository: it causes the ownership conflict shown in the dashboard.
New names still require acceptance by the remote Apps scanner; availability
cannot be guaranteed by local validation.

Original author attribution and LGPL-3 licensing are retained. Existing
prices are configured in USD in each addon manifest. Store pages use local images; unverified ranking/partner
badges and the footer advertising other Odoo versions have been removed.
Existing image previews have not been recreated or independently verified.

## Required dependency before publishing Financial Audit Reports

`co_audited_financials` requires `project_dashboard_odoo`. This addon is not
included in the supplied source repository. Its report actions and templates
are used by Financial Audit Reports, so removing the dependency would break
functionality. Ensure the correct Odoo 14 dependency is available on Odoo Apps
and accessible to buyers before publishing this addon. This module is not
certified ready until dependency installation and its workflows are tested.

`co_cafm` and `co_fire_safety` depend on `co_document_sequences` in this repository.
`co_cafm` and `co_recipe_costing` require Python package `openpyxl`;
`co_audited_financials` requires `openpyxl` and `xlsxwriter`.
Additional runtime integrations must be checked in the target Odoo environment.

## Validation

Run `scripts/validate_release.py` with the configured Odoo Python 3.8 environment.
It validates all eight manifests, referenced files, Python syntax, XML,
description images and absence of old technical namespaces.
Check `RELEASE_VALIDATION.md` for the actual installation results.

Use a disposable database for install and upgrade testing. Do not install the
old and renamed versions together: they retain the same business model names.
Renaming creates new addons; this is not an in-place migration of existing
installed databases or their external identifiers.

## Publish

Review the diff, commit the prepared files and push the reviewed commit to
`14.0`. In the vendor dashboard scan:
`ssh://git@github.com/cpabooks/odoo14_co_apps_store.git#14.0`
For a private repository grant the Odoo Apps scanner repository read access.
No Git push, repository registration or remote scan was performed here.

Official submission and dependency rules:
https://apps.odoo.com/apps/upload
https://apps.odoo.com/apps/faq
https://apps.odoo.com/apps/vendor-guidelines

## Installation fixes found during preparation

- CAFM now declares its required dependency on `co_document_sequences`.
- Document numbering now declares `purchase`, whose views it extends.
- CAFM and Fire Safety source model XML IDs and SQL table references used
  obsolete `cafm_cpa_*` / `faff_cpa_*` identifiers. They now match the actual
  `cpabooks.cafm.*` / `cpabooks.faff.*` model names.
- Seven ungrouped CAFM ACLs are restricted to internal users (`base.group_user`).
- Recipe Costing and Financial Audit declare their spreadsheet Python dependencies.
- Development backup files are excluded from the distributable modules.

## Field Service publication blocker

`co_field_service` also requires `industry_fsm_report` (Enterprise worksheet
reports), `cpabooks_project_issue_note` (material request lines and issue picking
fields/views), and `all_in_one_schedule_activity_management` (inherited task
views). These existing code dependencies are now declared in the manifest.
They are not included in the supplied Apps Store source repository. Confirm
all dependency versions and their store availability before publishing.
The Enterprise report dependency means Community compatibility is not claimed.
A full installation of this addon remains unverified until those dependencies
are provided. The existing customer worksheet template is now loaded by the
manifest and also requires the Enterprise report dependency.
