# Copyright (c) 2019-Today Sunflower IT (<https://www.sunflowerweb.nl>)
# License GNU General Public License see <http://www.gnu.org/licenses/>


def is_table(cr, table):
    """Check whether a certain table exists and is not a view"""
    cr.execute("SELECT 1 FROM pg_class WHERE relname = %s AND relkind = 'r'", (table,))
    return cr.fetchone()
