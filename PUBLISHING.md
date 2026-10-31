# Odoo Apps Store submission

## Repository

- Repository: `https://github.com/cpabooks/odoo14_co_apps_store.git`
- Current release branch: `main`
- Odoo series: `14.0`
- Module: `cpabooks_chart_of_accounts`
- Price: free, as configured in the original manifest.
- License: LGPL-3.

Commit and push the prepared changes from this directory:

```sh
git add .
git commit -m "Prepare chart of accounts module for Odoo Apps"
git push origin main
```

In your Odoo Apps vendor account, register this repository and select `main` as the branch if the submission form supports it, then scan/update the repository. The manifest version identifies Odoo 14. If your account requires a version-named branch, push the reviewed commit to `14.0` and register that branch:

```sh
git push origin HEAD:14.0
```

A Git push alone does not register a new repository with Odoo Apps. Vendor access, repository access and the store's scan/review remain external steps. For an already registered repository, request an update/scan after pushing when necessary.

## Release contents

The manifest, English description, local cover, icon, interface illustrations, support email and licenses are included. No activation key or third-party addon is required for core functionality. Images are illustrative previews, not evidence of live installation testing.

## Validate before each release

Run `python3 scripts/validate_release.py` using your Odoo Python environment. This validates packaging and source files; it does not replace installation testing.

On a disposable PostgreSQL database and a working Odoo 14 installation:

```sh
/path/to/odoo-python /path/to/odoo-bin \
  -c /path/to/test-odoo.conf \
  --addons-path=/path/to/odoo/addons,/path/to/standard/addons,/path/to/this/repository \
  -d coa_release_test -i cpabooks_chart_of_accounts \
  --without-demo=all --stop-after-init --no-http
```

Repeat with `-u cpabooks_chart_of_accounts` to check an upgrade. Use a test configuration and a disposable database; installation initializes account defaults and groups for all companies. Exercise recoding previews, account creation, opening balance entries, merge permissions and company isolation before production use.

Guidelines: https://apps.odoo.com/apps/vendor-guidelines
Submission: https://apps.odoo.com/apps/upload

## Verification performed for this preparation

- Odoo 14 / Python 3.8, standard Community addons only, disposable PostgreSQL 16 cluster.
- Fresh installation and module upgrade completed successfully.
- Fresh setup produced 141 accounts and 26 groups for the initial company.
- ORM smoke check passed: account creation without a code, duplicate code regeneration, preservation of manually supplied codes, batch code generation, setup action resolution and denial of public write access to setup models.
- Packaging validator, JavaScript syntax and Git whitespace checks passed.
- Non-blocking duplicate field-label warnings remain in the existing models.
- Enterprise-specific integrations and all interactive reset/merge/opening-balance workflows have not been exhaustively tested.

The reproducible ORM smoke check is in `scripts/smoke_odoo.py`. From the Odoo source directory, run it with the same test configuration and addons path used for installation:

```sh
/path/to/odoo-python odoo-bin shell -c /path/to/test-odoo.conf \
  -d coa_release_test --no-http \
  < /path/to/this/repository/scripts/smoke_odoo.py
```

It rolls back its changes and must only be run on a disposable database.
