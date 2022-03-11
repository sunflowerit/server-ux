# coding: utf-8
#  Copyright (C) 2010-2019 Today OpenERP SA (<http://www.openerp.com>)
#  Sunflower IT (<https://www.sunflowerweb.nl>)
#  programmed by: Oscar Alcala: oscar@vauxoo.com
#  programmed by: Jose Morales: jose@vauxoo.com
#  programmed by: Sunflower IT: info@sunflowerweb.nl
#  License GNU General Public License see <http://www.gnu.org/licenses/>
{
    "name": "Mass Merge Records",
    "version": "14.0.1.0.1",
    "author": "Vauxoo",
    "category": "Tools",
    "website": "http://www.serpentcs.com",
    "license": "AGPL-3",
    'depends': [
        'base'
    ],
    'data': [
        'security/merge_security.xml',
        'security/ir.model.access.csv',
        'wizard/merge_fuse_wizard.xml',
        'views/merge_editing_view.xml',
    ],
    'installable': True,
    'application': True,
}
