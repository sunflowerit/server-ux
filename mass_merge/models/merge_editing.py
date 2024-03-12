# License GNU General Public License see <http://www.gnu.org/licenses/>
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class MergeObject(models.Model):
    _name = "merge.object"
    _description = "Merge Object"

    name = fields.Char("Name", required=True, index=True)
    model_id = fields.Many2one(
        "ir.model", "Model", required=True, index=True, ondelete="cascade"
    )
    ref_ir_act_server_fuse = fields.Many2one(
        "ir.actions.server",
        "Sidebar fuse server action",
        readonly=True,
        help="Sidebar action to make this template\
        available on records of the related document\
        model",
    )
    model_list = fields.Char("Model List", size=256)

    @api.onchange("model_id")
    def onchange_model(self):
        if self.model_id:
            model_obj = self.env["ir.model"]
            model_data = model_obj.browse(self.model_id.id)
            self.model_list = "[" + str(self.model_id) + ""
            active_model_obj = self.env[model_data.model]
            if active_model_obj._inherits:
                for key, _val in active_model_obj._inherits.items():
                    model_ids = model_obj.search([("model", "=", key)])
                    if model_ids:
                        self.model_list += "," + str(model_ids[0]) + ""
            self.model_list += "]"

    def create_action_fuse(self):
        vals = {}
        action_obj = self.env["ir.actions.server"]
        for data in self:
            button_name = _("Mass Fuse (%s)") % data.name
            vals["ref_ir_act_server_fuse"] = action_obj.create(
                {
                    "name": button_name,
                    "type": "ir.actions.server",
                    "model_id": self.env.ref("mass_merge.model_merge_fuse_wizard").id,
                    "state": "code",
                    "code": "action = model._get_wizard_action()",
                    "binding_model_id": self.env.ref(
                        "mass_merge.model_merge_fuse_wizard"
                    ).id,
                    "binding_type": "report",
                }
            )
        self.write(
            {"ref_ir_act_server_fuse": vals.get("ref_ir_act_server_fuse", False).id}
        )
        return True

    def unlink_fuse_action(self):
        for template in self:
            try:
                if template.ref_ir_act_server_fuse:
                    self.env["ir.actions.server"].search(
                        [("id", "=", template.ref_ir_act_server_fuse.id)]
                    ).unlink()
            except Exception:
                raise UserError(_("Deletion of the action record failed."))
        return True
