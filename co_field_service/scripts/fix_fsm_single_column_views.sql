-- Pre-upgrade fix: child inherits still pointed at overview group[2] in DB.
UPDATE ir_ui_view
SET arch_db = REPLACE(
    arch_db,
    '//group[@class=''cpabooks_fsm_overview'']/group[2]',
    '//group[@class=''cpabooks_fsm_overview'']/group[1]'
)
WHERE id IN (5402, 5456, 5458);

-- Merge fields 20+ into the same column as 1-19 in the base inherit arch.
UPDATE ir_ui_view
SET arch_db = REPLACE(
    arch_db,
    E'</group>\n                        <group>\n                            <field name="create_date"',
    E'<field name="create_date"'
)
WHERE id = 5048
  AND arch_db LIKE '%total_print_row%'
  AND arch_db LIKE '%<group>%create_date%';
