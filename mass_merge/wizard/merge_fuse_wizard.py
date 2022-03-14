# coding: utf-8
#   OpenERP, Open Source Management Solution
#   Copyright (C) 2012 Serpent Consulting Services (<http://www.serpentcs.com>)
#   Copyright (C) 2010-Today OpenERP SA (<http://www.openerp.com>)
#   Copyright (C) 2019 Sunflower IT (<https://www.sunflower>)
#   License GNU General Public License see <http://www.gnu.org/licenses/>

from lxml import etree

from odoo import _, api, fields, models, tools
from odoo.fields import One2many, Many2many, Reference
from odoo.exceptions import ValidationError, AccessError

from ..tools import is_table


class MergeFuseWizardLine(models.TransientModel):
    _name = 'merge.fuse.wizard.line'
    _order = 'sequence asc'

    wizard_id = fields.Many2one('merge.fuse.wizard')
    sequence = fields.Integer()
    ref = fields.Reference(selection=[], readonly=True)


class MergeFuseWizard(models.TransientModel):
    _name = 'merge.fuse.wizard'

    line_ids = fields.One2many('merge.fuse.wizard.line', 'wizard_id')

    @api.model
    def _assert_permissions(self):
        """ Raise if the current user doesn't have permissions to merge """
        record = self.line_ids[:1].ref
        record.ensure_one()
        try:
            record.check_access_rights('unlink')
        except AccessError:
            raise ValidationError(_(
                "You need 'delete' permissions on this object to do that."))

    @api.model
    def _get_wizard_action(self):
        """ Action that opens a merge wizard for active_model/active_ids """
        active_model = self.env.context.get('active_model')
        active_ids = self.env.context.get('active_ids')
        if not active_model or not active_ids or len(active_ids) < 2:
            raise ValidationError(
                'You must choose at least two records.')
        line_vals = []
        for i, active_id in enumerate(active_ids):
            line_vals.append((0, False, {
                'sequence': i,
                'ref': '{},{}'.format(active_model, active_id)
            }))
        res = self.create({'line_ids': line_vals})
        res._assert_permissions()
        return {
            'name': _('Merge records ({})').format(active_model),
            'type': 'ir.actions.act_window',
            'res_model': 'merge.fuse.wizard',
            'res_id': res.id,
            'src_model': active_model,
            'view_type': 'form',
            'view_mode': 'form,tree',
            'target': 'new',
            'flags': {'action_buttons': False},
        }

    def action_apply(self):
        """ Perform the merge when 'Merge' button is pressed """
        self.ensure_one()
        self._assert_permissions()
        records = self.line_ids.sorted(lambda a: a.sequence)
        base_record = records[0].ref
        to_merge_records = records[1:].mapped('ref')
        self._do_merge(base_record, to_merge_records)
        self.env.invalidate_all()
        return {'type': 'ir.actions.act_window_close'}

    @api.model
    def _do_sql_updates(self, table, ids, updates):
        query = 'UPDATE "%s" SET %s WHERE id IN %%s' % (
            table,
            ','.join('"%s"=%s' % (u[0], u[1]) for u in updates),
        )
        self.env.cr.execute(query, (tuple(ids),))

    @api.model
    def _do_merge(self, base_record, to_merge_records):
        """ Perform the actual merge of records """
        active_model = base_record._name
        if active_model != to_merge_records._name:
            raise ValidationError(_('Cannot merge apples and oranges.'))

        # deal with ir_model_data
        query = '''
            UPDATE ir_model_data
            SET res_id = %s
            WHERE res_id IN %s
            AND model = %s
        '''
        self.env.cr.execute(query, (
            base_record.id,
            tuple(to_merge_records.ids),
            active_model))

        # deal with related fields
        base_ref = '%s,%s' % (active_model, base_record.id)
        base_model = self.env[active_model]
        inherits_field = base_model._inherits and base_model._inherits.values()[0]
        inherits_model = base_model._inherits and base_model._inherits.keys()[0]
        merged_refs = to_merge_records.mapped(
            lambda rec: '%s,%s' % (active_model, rec.id))
        related_fields = self.env['ir.model.fields'].search([
            '|',
            ('ttype', '=', 'reference'),
            '&',
            ('ttype', 'in', ('many2one', 'one2many', 'many2many')),
            ('relation', '=', active_model),
        ])
        for related_field in related_fields:
            try:
                target_model = self.env[related_field.model]
            except KeyError:
                continue
            target_field_name = related_field.name
            target_field = target_model._fields.get(target_field_name)
            if target_field:
                # skip the _inherits field, its not necessary to follow and will also lead to locks
                # we handle that field in merge_editing_product for now
                # TODO: in future handle this generically
                if related_field.model == inherits_model and related_field.relation_field == inherits_field:
                    continue

                # deal with ir.property
                if target_field.company_dependent:
                    self.env['ir.property'].sudo().search([
                        ('fields_id', '=', related_field.id),
                        ('value_reference', 'in', merged_refs)
                    ]).write(dict(value_reference=base_ref))
                    continue

                # skip any non-stored field, it will not have a db column
                # not only computed and related fields can have this:
                # https://github.com/OCA/OCB/blob/10.0/odoo/models.py#L3666
                elif not target_field.store:
                    continue

                # skip if the target table does not exist or is in fact a view
                elif not is_table(self.env.cr, target_model._table):
                    continue

                # deal with reference fields
                elif isinstance(target_field, Reference):
                    target_records = target_model.search([
                        (target_field_name, 'in', merged_refs)])
                    if not target_records:
                        continue
                    updates = {(target_field_name, "'{}'".format(base_ref))}
                    self._do_sql_updates(
                        target_model._table, target_records.ids, updates)

                # all other fields
                else:
                    target_records = target_model.search([
                        (target_field_name, 'in', to_merge_records.ids)])
                    if not target_records:
                        continue

                    if isinstance(target_field, (One2many, Many2many)):
                        target_records[0].sudo().write({
                            target_field_name: [(4, base_record.id)]})
                    else:
                        updates = {(target_field_name, base_record.id)}
                        self._do_sql_updates(
                            target_model._table, target_records.ids, updates)

        # delete records
        self.env.invalidate_all()
        to_merge_records.unlink()
