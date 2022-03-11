.. image:: https://img.shields.io/badge/license-LGPL--3-blue.png
   :target: https://www.gnu.org/licenses/lgpl
   :alt: License: LGPL-3

Mass Merge Records
==================
This module is a general purpose module that merges records that may be similar
or reflect similar properties when created.

Considerations
--------------

Technical Explanation
---------------------
For demonstration there can exist a customer with two or more record entries that
are same apart from difference in names. Among the records there could be caps
in the name characters. e.g
** 1.) Paul
** 2.) PAul
** 3.) pAuL
the above records are just one "__Paul__" so in this case you can merge the
records into one.

Functional Usage
----------------

TODO: Put here some functional examples.

Known issues / Roadmap
----------------------

- Tests: merge 2, 3 countries; check if partner countries have changed,
  check if ir_model_data was updated
- On merge wizard, show a visual link that opens the ref in a pop window
  (such as web_tree_many2one_clickable offers)
- Generic support for '_inherits' models: when one is merged, merge the other
  (now we only have specific support for product.product/product.template)
