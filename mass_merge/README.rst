.. image:: https://img.shields.io/badge/license-LGPL--3-blue.png
   :target: https://www.gnu.org/licenses/lgpl
   :alt: License: LGPL-3

Mass Merge Records
==================
This module is a general purpose module that merges records that may be similar
or reflect similar properties when created.

Merges any number of records from any table. Similar to the base_partner_merge functionality,
but with any table and with an interfaces that permits partial merges.


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
Go to Settings - Manage user - Tick Mass Merge	boolean field to give access.
Go to Settings - Mass Merge - Mass Merge. Create merge for your chosen model.

Go to Settings - Technical - Merge records. There are two tools:

* Record Merge by ID: Given n ids from a table, merge them into a single record
* Record Merge by criteria: Given a filter/domain on a table and a criteria to group the filtered records, create the corresponding "Merge by ID" models

The Merge by ID is the basic tool, in "Draft" state you have to provide:

* The model
* N ids to merge and mark one of them as destiny (i.e. the record that the others will be merged upon)

Press Launch to get to the "In progress" state. Several new tabs appear:

* The first one is the Relation Fields, i.e. the fields that have a relationship with other tables (o2m and m2o), and should/could be considered for possible merging. The tree shows the number of records and a button to create a merge for those records (a Merge by Id in case of m2o relationship and a Merge by Criteria in case of o2m relationship).
* The next four tabs are the steps of the Merge in itself:

 * Data consolidation: Copying the data from the merged records to the destiny one. You can choose which fields to merge and the order of consolidation (i.e. which record data will take prevalence)
 * FKs merge: Changing all fks in the database pointing to the merged records to the destiny one. The code of the base_parter_merge is used. You can choose which fields to merge.
 * References merge: Changing all reference fields (e.g. field value = res.partner, 145) to the destiny one. You can choose which fields to merge.
 * Non-relational merge: Changing all reference fields (two fields, one with model = res.partner, other res_id = 145) to the destiny one. You can choose which fields to merge.

* The last two tabs are the steps to consider after the merge:

 * Recompute: List of computed fields that are stored and could need a recompute. You can choose which fields to recompute.
 * Delete merged: What to do with the merged records (not the destiny). You can delete (launch unlink), deactivate (write active False), recompute (all compute stored fields are recomputed), SQL delete (warning, just in case the ORM does not let us), or leave them (None).

A Merge Button is provided to launch everything in the correct order, getting to the Done state.

The Merge by Criteria is a process to generate the Merge by ID automatically. In "Draft" state you have to provide:

* The model
* A filter: A domain to get all records that will be merged
* A group key: A python expression that will give the key that groups the records resulting of the filter in different merges
* An order: an optional _order expression to apply in each merge group to determine the destiny one. If none is provided, the table _order is used

Press Start to get to the "In progress" state. Several new tabs appear:
* Merge groups: A list of all the merges that will be generated, presenting the destiny id. You can choose which groups will be merged
* The same six tabs that appear in the Merge by ID model, and that will be used as default values for the generated groups (i.e. you can configure all the mergings before they are created)

Press Create merges to generate all the Merge by IDs records and get to the Done state. Two buttons let you launch processes on all the groups:
* Merge all groups
* Cancel all groups

Be warned: This module is both dangerous and useful, you can solve big problems in a very small time but you can create bigger problems as easily. Test any merges in a duplicate database before doing anything in production.

Example: There are two projects that should be merged, as they are really the same project.

* We start creating the Merge by ID on the project.project model, providing the ids
* The relation fields tab warns us that we should consider many models:

 * Project.task: Both projects come from a template, so they each have 15 tasks that start with the same code. We press the button + in the task field lines to create a Merge by criteria. The filter is already filled, so we only need a group key. In this case the task should be merged two by two by the code (6 first letters of the name), so it would be: o.name[:6] . We launch all the merges
 * Other models: The analytic account / contract, sale order, sale order line...

With this module all this merge is done in minutes.

Also, this module could be inherited to create interfaces for the final user for a certain model (e.g. product merge).


Known issues / Roadmap
----------------------

- Tests: merge 2, 3 countries; check if partner countries have changed,
  check if ir_model_data was updated
- On merge wizard, show a visual link that opens the ref in a pop window
  (such as web_tree_many2one_clickable offers)
- Generic support for '_inherits' models: when one is merged, merge the other
  (now we only have specific support for product.product/product.template)
