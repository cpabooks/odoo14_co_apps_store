# Odoo Apps submission — Odoo 14

Repository: https://github.com/cpabooks/odoo14_co_apps_store.git
Scanner URL: `ssh://git@github.com/cpabooks/odoo14_co_apps_store.git#14.0`

## Resolved scanner blocker

The scanner reported `co_field_service: unmet dependency
cpabooks_project_issue_note for series 14.0`. The required material request,
issue/return picking implementation and views are now bundled in
`co_field_service`, with references changed to that namespace.

The private activity extension is no longer a dependency. Views whose only
purpose was hiding pages from that extension were removed. The existing JCR
page now has its own report wrapper and renderers, so it does not require the
Enterprise worksheet addon. The original CRN and internal timesheet forms
were restored from the supplied source and adapted to Community views.
Invoice type, guaranteed invoice lines, invoice/project links, the quotation
creation action and valid security/menu references are provided locally.

`co_audited_financials` now owns its AFG dashboard assets, PDF templates,
renderers and paperformat support. Its required dependency on the customized
`project_dashboard_odoo` has been removed. P&L and balance sheet actions open
the built-in AFG dashboard. Legacy dashboard integration is optional.
See THIRD_PARTY_NOTICES.md for source attribution.

All required addon dependencies are now standard Odoo 14 Community modules
or one of the eight bundled modules. CAFM and Fire Safety depend on
`co_document_sequences`. Spreadsheet exports require `openpyxl` and, for
Financial Audit, `xlsxwriter`; these are declared in the manifests.

## Validation

Run `scripts/validate_release.py` with the configured Odoo Python interpreter.
It checks manifests, dependency availability against the Community allowlist,
source/XML syntax, declared files, icons, local page images, ACL packaging and
technical namespaces. GitHub Actions also checks every addon JavaScript file.
See RELEASE_VALIDATION.md for database testing and remaining limitations.

## Publish the corrected branch

The working checkout was on `main`, while the dashboard scans `14.0`.
Commit the reviewed changes, then merge that commit into `14.0` and push
`14.0` to the repository above. Pushing only `main` will not update the branch
shown in the screenshot. After pushing, click **Scan** in the Apps dashboard.
For a private repository the Odoo scanner needs repository read access.

No commit, push, repository registration or authenticated remote scan was
performed by this preparation. Remote technical-name ownership and final
acceptance can only be confirmed by the Apps scanner/review.

## Compatibility

Do not install old and renamed versions together: they share business model
names. These renamed addons are not an in-place migration for databases using
the original module namespaces. Test upgrades on a copy of an existing database.
Existing prices and LGPL-3 licensing are retained. Existing screenshots were
not recreated or independently checked against every workflow.

Official rules:
- https://apps.odoo.com/apps/upload
- https://apps.odoo.com/apps/faq
- https://apps.odoo.com/apps/vendor-guidelines

## Additional runtime fixes

CAFM contract reports now use standard Odoo company headers/footers instead of
an undeclared private Professional Templates style model. The old report-style
selector is removed from this store build. Contract order creation and HTML
printing were tested. Account group cleanup now guards nested legacy-group
reassignment, fixing recursion during account creation when all apps coexist.
All eight manifests retain the original repository's `live_test_url`:
`https://cpabooks.org/contactus?debug=1`. This restores the metadata for the
Apps Store's **Live Preview** button and opens the existing contact/demo-request
page. It is not a hosted interactive Odoo demo. Prices are unchanged.

The Download/Buy and Deploy on Odoo.sh buttons are rendered by Odoo Apps,
not by `static/description/index.html`. Their availability and labels depend on
the published listing, price, purchase status and Odoo's platform behavior.
After publishing the updated `14.0` branch, rescan the repository to refresh
the listing metadata. Remote button visibility has not been verified here.
