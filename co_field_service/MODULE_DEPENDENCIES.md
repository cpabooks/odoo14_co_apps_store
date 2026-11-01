# Field Service dependencies

The authoritative list is `__manifest__.py`. This store build depends only on
standard Odoo 14 Community addons: Project, Sales, Inventory, Purchase,
Accounting, Mail, Employees, Timesheets and Sales Timesheets.

Material requests, material issue/return views, stock picking extensions and
internal/customer job completion reports are included in `co_field_service`.
The private `cpabooks_project_issue_note` addon, customized activity addon and
Enterprise worksheet addon are no longer required.

The legacy activity-page hiding view was removed because its target page
belongs to a separate activity extension. Existing optional approval hooks
remain conditional on that integration being present.

Do not install the old and renamed addons together: they share model names.
