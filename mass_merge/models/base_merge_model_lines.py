# Copyright 2020 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import fields, models


class BaseMergeModelLine(models.Model):

    _name = "base.merge.model.line"
    _description = "Base Merge Model Line"

    merge_model_id = fields.Many2one("base.merge.model", required=True)
    field_id = fields.Many2one(
        comodel_name="ir.model.fields", ondelete="cascade", required=True
    )
    # future extensions
    # operator = fields.Selected(
    # [('=', 'Strict equal'), ('=ilike', 'Case sensitive equal')])
    # domain = fields.Text()
