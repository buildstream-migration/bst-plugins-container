Contributing to BuildStream Container Plugins
*********************************************
Thank you very much for choosing to contribute to this project. In this
document, you will find instructions on interacting with our issue queue,
submitting merge requests, testing locally etc. These guidelines apply to all
parts of this project, including this document, so if you notice anything
missing here, please create a merge request or open an issue.


Submitting issues
=================
In general, we encourage you to check the list of `open issues
<https://gitlab.com/BuildStream/bst-plugins-container/issues>`_ before opening
a new one. If you do not find an existing issue that matches yours,
please create a `new issue
<https://gitlab.com/BuildStream/bst-plugins-container/issues/new>`_.

Bug reports
-----------
If you are experiencing any issues with any of the plugins provided by this
repository, create a new issue and add the ``bug`` label.

New features
------------
If you would like to add any new plugins, or add new features to existing
plugins, please open an issue first. Depending on the nature of the work, we
might also suggest to propose it on the `BuildStream mailing list
<https://mail.gnome.org/mailman/listinfo/buildstream-list>`_ but in any case,
opening an issue on this repository should be the first step.

For such issues, please use the ``enhancement`` label.


Submitting patches
==================
Once it has been agreed on an issue or mailing list that something needs doing,
the next step is to create a merge request for it.

For small things like fixing a typo, minor refactoring, or minor formatting
changes, you do not need to enter an issue first. You can directly submit a
merge request in these cases.

Merge requests
--------------
You can submit a merge request to this project either from your fork or from a
feature branch in this repository. In either case, it is recommended to use
descriptive names for your branches, like ``username/add-shiny-feature-x``. The
``username`` part helps in identifying which branch belong to whom.

In general, we expect open merge requests to be ready to be landed. This means
that you should verify beforehand that the tests are all passing, have tidied
up the commit history etc.

One exception to that rule is WIP (Work in Progress) merge requests. Such merge
requests are useful to surface any potential issues sooner rather than later.
To mark a merge request as WIP, simply prefix the title with ``WIP:``
identifier. GitLab `treats this specially
<https://docs.gitlab.com/ee/user/project/merge_requests/work_in_progress_merge_requests.html>`_
which helps reviewers.

Commit history
--------------
Submitted merge requests should have a clean commit history. Ensure that you
do not include fixup commits or merge commits in your merge request.

Try to ensure that every commit in a series passes the test suite. This is
important when tracking down regressions.

If you add or update any tests, we prefer that you include the testsuite in the
same commit as the code changes.

Commit messages
---------------
Please read Chris Beams' excellent advice on `how to write a Git commit message
<https://chris.beams.io/posts/git-commit/>`_. As a rule of thumb, follow that
guide while working on this project. There are some slight differences that are
mentioned below:

* We are a bit more relaxed about the length of the subject line. But, you
  should still try to not make it bigger than 72 characters.
* Try to prefix the subject line with the name of the component that is being
  modified. For example, ``doc: Fix link to BuildStream docs``.


Testing
=======
We use `tox <https://tox.readthedocs.io>`_ as the frontend for running all our
tests, which are implemented using `pytest <https://docs.pytest.org>`_.

To run the tests, simply run::

    tox

By default, this will try to run the tests against all supported versions of
Python that is available on your machine. If you have multiple versions
installed and would like to run the tests against only one version, you can do
that using the ``-e`` option of ``tox``::

    tox -e py37

Linting
-------
We use `flake8 <http://flake8.pycqa.org>`_ to lint our code. You can run the
linter like so::

    tox -e flake8

To ensure that our reStructuredText (``.rst``) files (like this document) are
syntactically correct, we use a tool called `restructuredtext-lint
<https://github.com/twolfson/restructuredtext-lint>`_. If you are editing any
reStructuredText files, please verify that their formatting is correct by
running::

    tox -e rst-lint


Documentation
=============
The source for the documentation is located in the ``doc/source`` directory.

Whenever a change is merged to ``master``, GitLab CI is configured to rebuild
and publish the docs.

Building docs locally
---------------------
Although GitLab CI will build and publish the docs automatically, it can be
useful to build them locally to verify that everything looks and behaves as
expected. To do so, simply run::

    tox -e docs

This will produce the generated docs in ``doc/build/html`` directory. You can
then launch any simple webserver to view the docs in your browser. For example,
you can do so with the following commands::

    cd doc/build/html
    python3 -m http.server

This will launch a webserver on port 8000 and you should be able to browse the
docs at http://localhost:8000.


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
