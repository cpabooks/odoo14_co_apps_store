# -*- coding: utf-8 -*-
from . import models
from . import account_move
from . import ir_sequences
from . import sale_order
from . import purchase_order
from . import stock_picking
from . import stock_inventory
from . import account_full_reconcile
from . import account_payment
# from . import crm
from . import project
# from . import quality_chk
# pdc.wizard lives in paid sh_pdc; do not load it or Apps adds that price to the cart.
from . import res_company
from . import set_company_prefix
# from . import helpdesk_ticket
from . import common_method
