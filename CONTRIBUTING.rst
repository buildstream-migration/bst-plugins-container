Contributing to BuildStream Container Plugins
*********************************************

Pre-merge checklist
===================

Before merging changes, please check the following:

1. Any new plugins have:

   * A copyright statement attached.
   * An entry point defined in setup.py.
   * Been added to the list in ``doc/source/index.rst``

2. Any non-trivial change that is visible to the user should have a note
   in NEWS describing the change.

   Typical changes that do not require NEWS entries:

   * Typo fixes
   * Formatting changes
   * Internal Refactoring

   Typical changes that do require NEWS entries:

   * Bug fixes
   * New features

Pre-release checklist
=====================

1. Check any changes between releases that do not yet have a NEWS entry.
2. Check any new plugins have an entrypoint in setup.py.
3. Create a new release number in NEWS.
4. Update the version in setup.py
5. Update the ``version`` variable in ``doc/source/conf.py``
6. Create and push an annotated tag for this version, containing all the
   items from the latest NEWS entry.
