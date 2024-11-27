#  Copyright (C) 2010-2019 Today OpenERP SA (<http://www.openerp.com>)
#  Sunflower IT (<https://www.sunflowerweb.nl>)
#  programmed by: Oscar Alcala: oscar@vauxoo.com
#  programmed by: Jose Morales: jose@vauxoo.com
#  programmed by: Sunflower IT: info@sunflowerweb.nl
#  License GNU General Public License see <http://www.gnu.org/licenses/>
{
    "name": "Mass Merge Records - lite version",
    "version": "14.0.1.0.0",
    "author": "Vauxoo, Odoo Community Association (OCA)",
    "category": "Tools",
    "website": "https://github.com/OCA/server-ux",
    "license": "AGPL-3",
    "depends": ["base"],
    "data": [
        "security/merge_security.xml",
        "security/ir.model.access.csv",
        "views/record_merge_id.xml",
        "views/record_merge_criteria.xml",
    ],
    "installable": True,
    "application": True,
}
