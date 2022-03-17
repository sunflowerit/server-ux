# -*- coding: utf-8 -*-
# Copyright 2019 Sunflower IT <http://sunflowerweb.nl>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, SUPERUSER_ID


def post_init_hook(cr, pool):
    create_product_merge_action(cr)


def create_product_merge_action(cr):
    env = api.Environment(cr, SUPERUSER_ID, {})
    merge_obj = env['merge.object']

    # Create product.product merge action
    wizard = merge_obj.new()
    wizard.name = 'Merge product.product';
    wizard.model_id = env.ref('product.model_product_product')
    wizard.onchange_model()
    ppmerge = merge_obj.create(wizard._convert_to_write(wizard._cache))
    ppmerge.create_action_fuse()

    # create product.template merge action
    wizard = merge_obj.new()
    wizard.name = 'Merge product.template';
    wizard.model_id = env.ref('product.model_product_template')
    wizard.onchange_model()
    ptmerge = merge_obj.create(wizard._convert_to_write(wizard._cache))
    ptmerge.create_action_fuse()
