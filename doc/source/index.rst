.. toctree::
   :maxdepth: 2

BuildStream-plugins-container Documentation
===========================================

This is a collection of plugins that are either tailored to a very specific use
case, or need to change faster than would be allowed by the long term stable
API guarantees that we expect of core BuildStream plugins.

To use one of these plugins in your project you need to have installed the
bst-external package and enabled it in your `project configuration file
<https://buildstream.gitlab.io/buildstream/projectconf.html#plugin-origins-and-versions>`_.

.. Commented-out because we don't have any elements yet
   .. toctree::
      :maxdepth: 1
      :caption: Contained Elements


.. toctree::
   :maxdepth: 1
   :caption: Contained Sources

   sources/docker
