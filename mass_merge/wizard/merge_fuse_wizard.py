# coding: utf-8
#   OpenERP, Open Source Management Solution
#   Copyright (C) 2012 Serpent Consulting Services (<http://www.serpentcs.com>)
#   Copyright (C) 2010-Today OpenERP SA (<http://www.openerp.com>)
#   Copyright (C) 2019 Sunflower IT (<https://www.sunflower>)
#   License GNU General Public License see <http://www.gnu.org/licenses/>

from lxml import etree

from odoo import _, api, fields, models, tools
from odoo.fields import One2many, Many2many, Reference
from odoo.exceptions import ValidationError, AccessError, UserError

from ..tools import is_table
from odoo.tools import mute_logger
import datetime
import functools
import itertools
import logging
from ast import literal_eval

_logger = logging.getLogger("merge.fuse.wizard")

import psycopg2


class MergeDummy(models.TransientModel):
    _name = "merge.dummy"
    _description = "Merge Object Dummy"

    name = fields.Char()


class MergeFuseWizardLine(models.TransientModel):
    _name = 'merge.fuse.wizard.line'
    _order = 'sequence asc'

    wizard_id = fields.Many2one('merge.fuse.wizard')
    sequence = fields.Integer()
    ref = fields.Reference(selection='_reference_models', readonly=True)

    @api.model
    def _reference_models(self):
        models = self.env['ir.model'].sudo().search([('state', '!=', 'manual')])
        return [(model.model, model.name)
                for model in models
                if not model.model.startswith('ir.')]


class MergeFuseWizard(models.TransientModel):
    _name = 'merge.fuse.wizard'

    _model_merge = "merge.dummy"
    _table_merge = "merge_dummy"

    line_ids = fields.One2many('merge.fuse.wizard.line', 'wizard_id')

    object_ids = fields.Many2many(_model_merge, string="Objects")
    dst_object_id = fields.Many2one(_model_merge, string="Destination Object")

    @api.model
    def _assert_permissions(self):
        """ Raise if the current user doesn't have permissions to merge """

        if self.env.user.has_group('mass_merge.group_merge_editing'):
            return True
        else:
            raise AccessError(_("You don't have the access rights to do that"))

        # Below Worked on version 10, record returns None on version 14 thus fixed this with above code using groups

        # record = self.line_ids[1].ref
        # try:
        #     record.check_access_rights('unlink')
        # except AccessError:
        #     raise ValidationError(_(
        #         "You need 'delete' permissions on this object to do that."))

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
                'ref': '{},{}'.format(active_model, str(active_id))
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
        to_merge_records = records[1].ref
        self._merge(to_merge_records, base_record)
        return {'type': 'ir.actions.act_window_close'}

    def _merge(self, object_ids, dst_object=None, extra_checks=True):
        """private implementation of merge object
        :param object_ids : ids of object to merge
        :param dst_object : record of destination
        :param extra_checks: pass False to bypass extra sanity check (e.g. email address)
        """

        # call sub methods to do the merge
        self._update_foreign_keys(object_ids, dst_object)
        self._update_reference_fields(object_ids, dst_object)
        self._update_values(object_ids, dst_object)

        self._log_merge_operation(object_ids, dst_object)

        # delete source object, since they are merged
        object_ids.unlink()

    @api.model
    def _update_foreign_keys(self, src_objects, dst_object):
        """Update all foreign key from the src_object to dst_object. All many2one fields will be updated.
        :param src_objects : merge source res.object recordset (does not include destination one)
        :param dst_object : record of destination res.object
        """
        _logger.debug(
            "_update_foreign_keys for dst_object: %s for src_objects: %s", dst_object.id, str(src_objects.ids)
        )

        # find the many2one relation to a object
        Object = self.env[self._model_merge]
        relations = self._get_fk_on(self._table_merge)

        self.flush()

        for table, column in relations:
            if "merge_object_" in table:  # ignore two tables
                continue

            # get list of columns of current table (exept the current fk column)
            # pylint: disable=E8103
            query = "SELECT column_name FROM information_schema.columns WHERE table_name LIKE '%s'" % (table)
            self._cr.execute(query, ())
            columns = []
            for data in self._cr.fetchall():
                if data[0] != column:
                    columns.append(data[0])

            # do the update for the current table/column in SQL
            query_dic = {
                "table": table,
                "column": column,
                "value": columns[0],
            }
            if len(columns) <= 1:
                # unique key treated
                query = (
                    """
                    UPDATE "%(table)s" as ___tu
                    SET "%(column)s" = %%s
                    WHERE
                        "%(column)s" = %%s AND
                        NOT EXISTS (
                            SELECT 1
                            FROM "%(table)s" as ___tw
                            WHERE
                                "%(column)s" = %%s AND
                                ___tu.%(value)s = ___tw.%(value)s
                        )"""
                    % query_dic
                )
                for src_object in src_objects:
                    self._cr.execute(query, (dst_object.id, src_object.id, dst_object.id))
            else:
                try:
                    with mute_logger("odoo.sql_db"), self._cr.savepoint():
                        query = 'UPDATE "%(table)s" SET "%(column)s" = %%s WHERE "%(column)s" IN %%s' % query_dic
                        self._cr.execute(
                            query,
                            (
                                dst_object.id,
                                tuple(src_objects.ids),
                            ),
                        )

                        # handle the recursivity with parent relation
                        if column == Object._parent_name and table == self._table_merge:
                            query = (
                                """
                                WITH RECURSIVE cycle(id, parent_id) AS (
                                        SELECT id, parent_id FROM %(table)s
                                    UNION
                                        SELECT  cycle.id, %(table)s.parent_id
                                        FROM    %(table)s, cycle
                                        WHERE   %(table)s.id = cycle.parent_id AND
                                                cycle.id != cycle.parent_id
                                )
                                SELECT id FROM cycle WHERE id = parent_id AND id = %%s
                            """
                                % query_dic
                            )
                            self._cr.execute(query, (dst_object.id,))

                except psycopg2.Error:
                    # updating fails, most likely due to a violated unique constraint
                    # keeping record with nonexistent object_id is useless, better delete it
                    query = 'DELETE FROM "%(table)s" WHERE "%(column)s" IN %%s' % query_dic
                    self._cr.execute(query, (tuple(src_objects.ids),))

        self.invalidate_cache()
    def _get_summable_fields(self):
        """Returns the list of fields that should be summed when merging objects"""
        return []
    def _get_fk_on(self, table):
        """return a list of many2one relation with the given table.
        :param table : the name of the sql table to return relations
        :returns a list of tuple 'table name', 'column name'.
        """
        query = """
            SELECT cl1.relname as table, att1.attname as column
            FROM pg_constraint as con, pg_class as cl1, pg_class as cl2,
                 pg_attribute as att1, pg_attribute as att2
            WHERE con.conrelid = cl1.oid
                AND con.confrelid = cl2.oid
                AND array_lower(con.conkey, 1) = 1
                AND con.conkey[1] = att1.attnum
                AND att1.attrelid = cl1.oid
                AND cl2.relname = %s
                AND att2.attname = 'id'
                AND array_lower(con.confkey, 1) = 1
                AND con.confkey[1] = att2.attnum
                AND att2.attrelid = cl2.oid
                AND con.contype = 'f'
        """
        self._cr.execute(query, (table,))
        return self._cr.fetchall()

    @api.model
    def _update_reference_fields(self, src_objects, dst_object):
        """Update all reference fields from the src_object to dst_object.
        :param src_objects : merge source res.object recordset (does not include destination one)
        :param dst_object : record of destination res.object
        """
        _logger.debug("_update_reference_fields for dst_object: %s for src_objects: %r", dst_object.id, src_objects.ids)

        def update_records(model, src, field_model="model", field_id="res_id"):
            Model = self.env[model] if model in self.env else None
            if Model is None:
                return
            records = Model.sudo().search([(field_model, "=", self._model_merge), (field_id, "=", src.id)])
            try:
                with mute_logger("odoo.sql_db"), self._cr.savepoint(), self.env.clear_upon_failure():
                    records.sudo().write({field_id: dst_object.id})
                    records.flush()
            except psycopg2.Error:
                # updating fails, most likely due to a violated unique constraint
                # keeping record with nonexistent object_id is useless, better delete it
                records.sudo().unlink()

        update_records = functools.partial(update_records)

        for scr_object in src_objects:
            update_records("calendar.event", src=scr_object, field_model="res_model")
            update_records("ir.attachment", src=scr_object, field_model="res_model")
            update_records("mail.followers", src=scr_object, field_model="res_model")

            update_records("portal.share", src=scr_object, field_model="res_model")
            update_records("rating.rating", src=scr_object, field_model="res_model")
            update_records("mail.activity", src=scr_object, field_model="res_model")
            update_records("mail.message", src=scr_object)
            update_records("ir.model.data", src=scr_object)

        records = self.env["ir.model.fields"].search([("ttype", "=", "reference")])
        for record in records.sudo():
            try:
                Model = self.env[record.model]
                field = Model._fields[record.name]
            except KeyError:
                # unknown model or field => skip
                continue

            if field.compute is not None:
                continue

            for src_object in src_objects:
                records_ref = Model.sudo().search([(record.name, "=", "%s,%d" % (self._model_merge, src_object.id))])
                values = {
                    record.name: "%s,%d" % (self._model_merge, dst_object.id),
                }
                records_ref.sudo().write(values)

        self.flush()

    @api.model
    def _update_values(self, src_objects, dst_object):
        """Update values of dst_object with the ones from the src_objects.
        :param src_objects : recordset of source res.object
        :param dst_object : record of destination res.object
        """
        _logger.debug("_update_values for dst_object: %s for src_objects: %r", dst_object.id, src_objects.ids)

        model_fields = dst_object.fields_get().keys()
        summable_fields = self._get_summable_fields()

        def write_serializer(item):
            if isinstance(item, models.BaseModel):
                return item.id
            else:
                return item

        # get all fields that are not computed or x2many
        values = dict()
        for column in model_fields:
            field = dst_object._fields[column]
            if field.type not in ("many2many", "one2many") and field.compute is None:
                for item in itertools.chain(src_objects, [dst_object]):
                    if item[column]:
                        if column in summable_fields and values.get(column):
                            values[column] += write_serializer(item[column])
                        else:
                            values[column] = write_serializer(item[column])
        # remove fields that can not be updated (id and parent_id)
        values.pop("id", None)
        parent_id = values.pop("parent_id", None)
        dst_object.write(values)
        # try to update the parent_id
        if parent_id and parent_id != dst_object.id:
            try:
                dst_object.write({"parent_id": parent_id})
            except ValidationError:
                _logger.info(
                    "Skip recursive object hierarchies for parent_id %s of object: %s", parent_id, dst_object.id
                )

    def _log_merge_operation(self, src_objects, dst_object):
        _logger.info("(uid = %s) merged the objects %r with %s", self._uid, src_objects.ids, dst_object.id)

    @api.model
    def _do_sql_updates(self, table, ids, updates):

        query = 'UPDATE "%s" SET %s WHERE id IN %%s' % (
            table,
            ','.join('"%s"=%s' % (u[0], u[1]) for u in updates),
        )
        self.env.cr.execute(query, (tuple(ids),))
