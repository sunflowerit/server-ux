# Copyright 2020 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import models


class View(models.Model):
    _inherit = "ir.ui.view"

    def postprocess(self, node, current_node_path, editable, name_manager):

        result = super(View, self).postprocess(
            node=node,
            current_node_path=current_node_path,
            editable=editable,
            name_manager=name_manager,
        )
        return result
