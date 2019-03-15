BuildStream Container Plugins
*****************************

.. image:: https://gitlab.com/BuildStream/bst-plugins-container/badges/master/pipeline.svg
   :target: https://gitlab.com/BuildStream/bst-plugins-container/commits/master

.. image:: https://img.shields.io/pypi/v/bst-plugins-container.svg
   :target: https://pypi.org/project/bst-plugins-container

.. image:: https://img.shields.io/pypi/pyversions/bst-plugins-container.svg
   :target: https://pypi.org/project/bst-plugins-container

.. image:: https://img.shields.io/badge/Documentation-yellow.svg?logo=gitlab&labelColor=grey
   :target: https://buildstream.gitlab.io/bst-plugins-container

.. image:: https://img.shields.io/badge/Source-teal.svg?logo=gitlab&labelColor=grey
   :target: https://gitlab.com/BuildStream/bst-plugins-container

A collection of plugins for `BuildStream <https://BuildStream.build>`_ that are
related to containers.

Usage
=====

There are two ways to use external BuildStream plugins, either as a submodule,
or as a Python package. See BuildStream's
`External plugin documentation <https://docs.buildstream.build/format_project.html#external-plugins>`_
for more details.

Using the plugins as a Python package
-------------------------------------
To use the container plugins as a Python package within a BuildStream project,
you will first need to install bst-plugins-container via pip::

   pip install bst-plugins-container

The plugins must be declared in *project.conf*. To do this, please refer
to BuildStream's
`Local plugins documentation <https://buildstream.gitlab.io/buildstream/format_project.html#local-plugins>`_.

Using the plugins locally within a project
------------------------------------------
To use the container plugins locally within a
BuildStream project, you will first need to clone the repo to a location
**within your project**::

    git clone https://gitlab.com/BuildStream/bst-plugins-container.git

The plugins must be declared in *project.conf*. To do this, please refer
to BuildStream's
`Pip plugins documentation <https://buildstream.gitlab.io/buildstream/format_project.html#pip-plugins>`_.
