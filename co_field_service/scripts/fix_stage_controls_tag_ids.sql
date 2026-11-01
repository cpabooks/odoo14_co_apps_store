UPDATE ir_ui_view
SET arch_db = REPLACE(
    arch_db,
    E'                <xpath expr="//group[@class=''cpabooks_fsm_overview'']/group[1]//field[@name=''tag_ids'']" position="attributes">\n                    <attribute name="attrs">{\'readonly\': [(\'fsm_stage_4_readonly\', \'=\', True)]}</attribute>\n                </xpath>\n\n',
    ''
)
WHERE id = 5402 AND arch_db LIKE '%tag_ids%';
