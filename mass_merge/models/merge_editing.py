# coding: utf-8
# License GNU General Public License see <http://www.gnu.org/licenses/>
from odoo import fields, models, api, _
from odoo.exceptions import UserError


class MergeObject(models.Model):
    _name = "merge.object"

    name = fields.Char("Name", size=64, required=True, index=True)
    model_id = fields.Many2one('ir.model', 'Model', required=True, index=True, ondelete='cascade')
    model_id = fields.Many2one('ir.model', 'Model', required=True, index=True)
    ref_ir_act_server_fuse = fields.Many2one(
        'ir.actions.server',
        'Sidebar fuse server action', readonly=True,
        help="Sidebar action to make this template\
        available on records of the related document\
        model")
    ref_ir_value_fuse = fields.Many2one(
        'ir.values', 'Sidebar fuse button',
        readonly=True, help="Sidebar button to\
        open the sidebar action")
    model_list = fields.Char('Model List', size=256)

    @api.onchange('model_id')
    def onchange_model(self):
        if self.model_id:
            model_obj = self.env['ir.model']
            model_data = model_obj.browse(self.model_id.id)
            self.model_list = "[" + str(self.model_id) + ""
            active_model_obj = self.env[model_data.model]
            if active_model_obj._inherits:
                for key, val in active_model_obj._inherits.items():
                    model_ids = model_obj.search([('model', '=', key)])
                    if model_ids:
                        self.model_list += "," + str(model_ids[0]) + ""
            self.model_list += "]"


    @api.multi
    def create_action_fuse(self):
        vals = {}
        action_obj = self.env['ir.actions.server']
        for data in self:
            src_obj = data.model_id.model
            button_name = _('Mass Fuse (%s)') % data.name
            vals['ref_ir_act_server_fuse'] = action_obj.create({
                'name': button_name,
                'type': 'ir.actions.server',
                'model_id': self.env.ref(
                    'merge_editing.model_merge_fuse_wizard').id,
                'state': 'code',
                'code': 'action = model._get_wizard_action()',
                'condition': True,
            })
            vals['ref_ir_value_fuse'] = self.env['ir.values'].create({
                'name': button_name,
                'model': src_obj,
                'key': 'action',
                'key2': 'client_action_multi',
                'value': "ir.actions.server," + str(
                    vals['ref_ir_act_server_fuse'].id),
            })
        self.write({
            'ref_ir_act_server_fuse': vals.get('ref_ir_act_server_fuse', False).id,
            'ref_ir_value_fuse': vals.get('ref_ir_value_fuse', False).id,
        })
        return True

    @api.multi
    def unlink_fuse_action(self):
        for template in self:
            try:
                if template.ref_ir_act_server_fuse:
                    self.env['ir.actions.server'].search(
                        [('id', '=', template.ref_ir_act_server_fuse.id)]).unlink()
                if template.ref_ir_value_fuse:
                    ir_values_obj = self.env['ir.values']
                    ir_values_obj.search(
                        [('id', '=', template.ref_ir_value_fuse.id)]).unlink()
            except:
                raise UserError(_("Deletion of the action record failed."))
        return True
