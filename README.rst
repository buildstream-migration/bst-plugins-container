BuildStream Container Plugins
*****************************

.. image:: https://gitlab.com/BuildStream/bst-plugins-container/badges/master/pipeline.svg
   :target: https://gitlab.com/BuildStream/bst-plugins-container/commits/master

A collection of plugins for BuildStream that are related to containers.

How to use this repo
====================

There are two ways to use external buildstream plugins, either as a submodule, or as
a Python package.

Using the plugins locally within a project
------------------------------------------
To use the container plugins locally within a
`BuildStream <https://gitlab.com/BuildStream/buildstream>`_
project, you will first need to clone the repo to a location **within your
project**::

    git clone https://gitlab.com/BuildStream/bst-plugins-container.git

The plugins must be declared in *project.conf*. To do this, please refer
to BuildStream's
`Local plugins documentation <https://buildstream.gitlab.io/buildstream/format_project.html#local-plugins>`_.

Using the plugins as a Python package
-------------------------------------
To use the container plugins as a Python package within a
`BuildStream <https://gitlab.com/BuildStream/buildstream>`_
project, you will first need to install bst-plugins-container via pip::

    git clone https://gitlab.com/BuildStream/bst-plugins-container.git
    cd bst-plugins-container
    pip install --user -e .

To ensure it's installed, try: ``pip show bst-plugins-container``,
this should show information about the package.

.. note::
   The -e option ensures that changes made to the git repository are reflected
   in the Python package's behaviour.

Then, the plugins must be declared in the *project.conf*. The implementation of
this is explained in BuildStream's
`Pip plugins documentation <https://buildstream.gitlab.io/buildstream/format_project.html#pip-plugins>`_

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
5. Update the variables ``version`` and ``release`` in ``doc/source/conf.py``
6. Create and push an annotated tag for this version, containing all the
   items from the latest NEWS entry.
