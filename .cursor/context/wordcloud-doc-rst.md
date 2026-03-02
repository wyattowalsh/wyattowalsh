This file is a merged representation of a subset of the codebase, containing specifically included files, combined into a single document by Repomix.

# File Summary

## Purpose
This file contains a packed representation of the entire repository's contents.
It is designed to be easily consumable by AI systems for analysis, code review,
or other automated processes.

## File Format
The content is organized as follows:
1. This summary section
2. Repository information
3. Directory structure
4. Repository files (if enabled)
5. Multiple file entries, each consisting of:
  a. A header with the file path (## File: path/to/file)
  b. The full contents of the file in a code block

## Usage Guidelines
- This file should be treated as read-only. Any changes should be made to the
  original repository files, not this packed version.
- When processing this file, use the file path to distinguish
  between different files in the repository.
- Be aware that this file may contain sensitive information. Handle it with
  the same level of security as you would the original repository.

## Notes
- Some files may have been excluded based on .gitignore rules and Repomix's configuration
- Binary files are not included in this packed representation. Please refer to the Repository Structure section for a complete list of file paths, including binary files
- Only files matching these patterns are included: doc/**/*.rst
- Files matching patterns in .gitignore are excluded
- Files matching default ignore patterns are excluded
- Files are sorted by Git change count (files with more changes are at the bottom)

# Directory Structure
```
doc/
  _templates/
    class_with_call.rst
    class.rst
    function.rst
  changelog.rst
  cli.rst
  index.rst
  make_a_release.rst
  references.rst
```

# Files

## File: doc/_templates/class_with_call.rst
```
{{ fullname }}
{{ underline }}

.. currentmodule:: {{ module }}

.. autoclass:: {{ objname }}

   {% block methods %}
   .. automethod:: __init__
   .. automethod:: __call__
   {% endblock %}
```

## File: doc/_templates/class.rst
```
{{ fullname }}
{{ underline }}

.. currentmodule:: {{ module }}

.. autoclass:: {{ objname }}

   {% block methods %}
   .. automethod:: __init__
   {% endblock %}
```

## File: doc/_templates/function.rst
```
{{ fullname }}
{{ underline }}

.. currentmodule:: {{ module }}

.. autofunction:: {{ objname }}
```

## File: doc/changelog.rst
```
.. _changelog:

=========
Changelog
=========

This is the list of changes to wordcloud between each release. For full
details, see the commit logs at https://github.com/amueller/word_cloud

Next Release
==============

WordCloud 1.9.1
===============
Release Date 4/27/2023

Wheels
------
* Added wheels for Python 3.10 and 3.11

WordCloud 1.8.1
===============
Release Date 11/11/2020

Wheels
------
* Added wheels for Python 3.9.


WordCloud 1.8.0
===============

Wheels
------

* Add support for building wheels for Python 3.8 for all platforms and 32-bit wheels for windows **only**.
  See :issue:`547` and :issue:`549`. Contributed by :user:`amueller` and :user:`jcfr`.

Test
----

* Update CircleCI configuration to use `dockcross/manylinux1-x64 <https://github.com/dockcross/dockcross#cross-compilers>`_
  image instead of obsolete `dockcross/manylinux-x64` one. See :issue:`548`. Contributed by :user:`jcfr`.

WordCloud 1.7.0
===============

Features
--------
* Add export of SVG files using :func:`WordCloud.to_svg` by :user:`jojolebarjos` .
* Add missing options to the command line interface, `PR #527 <https://github.com/amueller/word_cloud/pull/527>`_ by :user:`dm-logv`.

Bug fixes
---------
* Make bigrams stopword aware, `PR #528<https://github.com/amueller/word_cloud/pull/529>`_ by :user:`carlgieringer`.


WordCloud 1.6.0
===============

Features
--------

* Add support to render numbers and single letters using the
  ``include_numbers`` and ``min_word_length`` arguments.

Examples
--------
* Add :ref:`phx_glr_auto_examples_parrot.py` example showing another example of
  image-based coloring and masks.

WordCloud 1.5.0
===============

Examples
--------

* Add :ref:`sphx_glr_auto_examples_frequency.py` example for understanding how
  to generate a wordcloud using a dictionary of word frequency.
  Contributed by :user:`yoonsubKim`.

* Add :ref:`sphx_glr_auto_examples_wordcloud_cn.py` example.
  Contributed by :user:`FontTian` and improved by :user:`duohappy`.

Features
--------

* Add support for mask contour. Contributed by :user:`jsmedmar`.

  * Improve :ref:`wordcloud_cli` adding support for ``--contour_width``
    and ``--contour_color`` named arguments.

  * Improve :class:`wordcloud.WordCloud` API adding support for
    ``contour_width`` and ``contour_color`` keyword arguments.

  * Update :ref:`sphx_glr_auto_examples_masked.py` example.

* Update :class:`wordcloud.WordCloud` to support ``repeat`` keyword argument.
  If set to True, indicates whether to repeat words and phrases until ``max_words``
  or ``min_font_size`` is reached. Contributed by :user:`amueller`.

Wheels
------

* Support installation on Linux, macOS and Windows for Python 2.7, 3.4, 3.5, 3.6 and 3.7 by
  updating the Continuous Integration (CI) infrastructure and support the automatic creation
  and upload of wheels to `PyPI`_. Contributed by :user:`jcfr`.

  * Use `scikit-ci`_  to simplify and centralize the CI configuration. By having ``appveyor.yml``,
    ``.circleci/config.yml`` and ``.travis.yml`` calling the scikit-ci command-line executable,
    all the CI steps for all service are described in one `scikit-ci.yml`_ configuration file.

  * Use `scikit-ci-addons`_ to provide a set of scripts useful to help drive CI.

  * Simplify release process using `versioneer`_. Release process is now as simple as
    tagging a release, there is no need to manually update version in ``__init__.py``.

  * Remove use of miniconda and instead use `manylinux`_ docker images.

* Fix installation of the cli on all platforms leveraging `entry_points`_.
  See :issue:`420`. Contributed by :user:`jcfr`.

.. _manylinux: https://www.python.org/dev/peps/pep-0571/
.. _PyPI: https://pypi.org/project/wordcloud
.. _scikit-ci: http://scikit-ci.readthedocs.io
.. _scikit-ci-addons: http://scikit-ci-addons.readthedocs.io
.. _scikit-ci.yml: https://github.com/amueller/word_cloud/blob/master/scikit-ci.yml
.. _versioneer: https://github.com/warner/python-versioneer/
.. _entry_points: https://setuptools.readthedocs.io/en/latest/setuptools.html#automatic-script-creation

Bug fixes
---------

* :class:`wordcloud.WordCloud` API

  * Fix coloring with black image. Contributed by :user:`amueller`.

  * Improve error message when there is no space on canvas. Contributed by  :user:`amueller`.

* :ref:`wordcloud_cli`

  * Fix handling of invalid `regexp` parameter. Contributed by :user:`jcfr`.

Documentation
-------------

* Update :class:`wordcloud.WordCloud` ``color_func`` keyword argument documentation
  explaining how to create single color word cloud.
  Fix :issue:`185`. Contributed by :user:`maifeng`.

* Simplify and improve `README <https://github.com/amueller/word_cloud#readme>`_.
  Contributed by :user:`amueller`.

* Add :ref:`wordcloud_cli` document. Contributed by :user:`amueller`.

* Add :ref:`making_a_release` and :ref:`changelog` documents. Contributed by :user:`jcfr`.

* Improve sphinx gallery integration. Contributed by :user:`jcfr`.

Website
-------

* Setup automatic deployment of the website each time the `master` branch is updated.
  Contributed by :user:`jcfr`.

* Update `website <https://amueller.github.io/word_cloud>`_ to use `Read the Docs Sphinx Theme`.
  Contributed by :user:`amueller`.

Test
----

* Update testing infrastructure. Contributed by :user:`jcfr`.

  * Switch testing framework from nose to `pytest <https://docs.pytest.org>`_.

  * Enforce coding style by running `flake8 <http://flake8.pycqa.org/en/latest/index.html>`_
    each time a Pull Request is proposed or the `master` branch updated.

  * Support generating html coverage report locally running ``pytest``, ``coverage html`` and
    opening ``htmlcov/index.html`` document.


WordCloud 1.4.1
===============

Bug fixes
---------

* Improve stopwords list. Contributed by :user:`xuhdev`.


Test
----

* Remove outdated channel and use conda-forge. Contributed by :user:`amueller`.

* Add test for the command line utility. Contributed by :user:`xuhdev`.


WordCloud 1.4.0
===============

See https://github.com/amueller/word_cloud/compare/1.3.3...1.4


WordCloud 1.3.3
===============

See https://github.com/amueller/word_cloud/compare/1.3.2...1.3.3


WordCloud 1.3.2
===============

See https://github.com/amueller/word_cloud/compare/1.2.2...1.3.2


WordCloud 1.2.2
===============

See https://github.com/amueller/word_cloud/compare/1.2.1...1.2.2


WordCloud 1.2.1
===============

See https://github.com/amueller/word_cloud/compare/4c7ebf81...1.2.1
```

## File: doc/cli.rst
```
.. _wordcloud_cli:

Command Line Interface
======================

.. argparse::
   :module: wordcloud.wordcloud_cli
   :func: make_parser
   :prog: wordcloud_cli
```

## File: doc/index.rst
```
WordCloud for Python documentation
==================================

Here you find instructions on how to create wordclouds with my Python wordcloud project. 
Compared to other wordclouds, my algorithm has the advantage of

* filling all available space.
* being able to use arbitrary masks.
* having a stupid simple algorithm (with an efficient implementation) that can be easily modified.
* being in Python

Check out the :ref:`example_gallery`.

The code of the project is on Github: `word_cloud <https://github.com/amueller/word_cloud>`_

  .. figure:: images/a_new_hope.png
     :width: 300px
     :target: auto_examples/a_new_hope.html
     :align: center

.. toctree::
    :hidden:
    :caption: User Documentation
    
    references
    cli
    auto_examples/index
    changelog

.. toctree::
    :hidden:
    :caption: Contributor Documentation

    make_a_release
```

## File: doc/make_a_release.rst
```
.. _making_a_release:

================
Making a release
================

This document guides a contributor through creating a release of the wordcloud
python packages.

A core developer should follow these steps to trigger the creation and upload of
a release `X.Y.Z` of **wordcloud** on `PyPI`_..

-------------------------
Documentation conventions
-------------------------

The commands reported below should be evaluated in the same terminal session.

Commands to evaluate starts with a dollar sign. For example::

  $ echo "Hello"
  Hello

means that ``echo "Hello"`` should be copied and evaluated in the terminal.

----------------------
Setting up environment
----------------------

1. First, `register for an account on PyPI <https://pypi.org>`_.


2. If not already the case, ask to be added as a ``Package Index Maintainer``.


3. Create a ``~/.pypirc`` file with your login credentials::

    [distutils]
    index-servers =
      pypi
      pypitest

    [pypi]
    username=<your-username>
    password=<your-password>

    [pypitest]
    repository=https://test.pypi.org/legacy/
    username=<your-username>
    password=<your-password>

  where ``<your-username>`` and ``<your-password>`` correspond to your PyPI account.


---------------------
`PyPI`_: Step-by-step
---------------------

1. Make sure that all CI tests are passing: `AppVeyor`_, `CircleCI`_ and `Travis CI`_.


2. List all tags sorted by version

  .. code::

    $ git tag -l | sort -V


3. Choose the next release version number

  .. code::

    release=X.Y.Z

  .. warning::

    To ensure the packages are uploaded on `PyPI`_, tags must match this regular
    expression: ``^[0-9]+(\.[0-9]+)*(\.post[0-9]+)?$``.


4. Download latest sources

  .. code::

    cd /tmp && git clone git@github.com:amueller/word_cloud && cd word_cloud


5. In `doc/changelog.rst` change ``Next Release`` section header with
   ``WordCloud X.Y.Z`` and commit the changes using the same title

  .. code::

    $ git add doc/changelog.rst
    $ git commit -m "WordCloud ${release}"


6. Tag the release

  .. code::

    $ git tag --sign -m "WordCloud ${release}" ${release} master

  .. note::

      We recommend using a GPG key to sign the tag.

7. Publish the tag

  .. code::

    $ git push origin ${release}

  .. note:: This will trigger builds on each CI services and automatically upload the wheels \
            and source distribution on `PyPI`_.

8. Check the status of the builds on `AppVeyor`_, `CircleCI`_ and `Travis CI`_.

9. Once the builds are completed, check that the distributions are available on `PyPI`_.


10. Create a clean testing environment to test the installation

  .. code::

    $ mkvirtualenv wordcloud-${release}-install-test && \
      pip install wordcloud && \
      python -c "import wordcloud;print(wordcloud.__version__)"

  .. note::

      If the ``mkvirtualenv`` is not available, this means you do not have `virtualenvwrapper`_
      installed, in that case, you could either install it or directly use `virtualenv`_ or `venv`_.

11. Cleanup

  .. code::

    $ deactivate  && \
      rm -rf dist/* && \
      rmvirtualenv wordcloud-${release}-install-test


12. Add a ``Next Release`` section back in `doc/changelog.rst`, merge the result
    and push local changes::

    $ git push origin master


.. _virtualenvwrapper: https://virtualenvwrapper.readthedocs.io/
.. _virtualenv: http://virtualenv.readthedocs.io
.. _venv: https://docs.python.org/3/library/venv.html

.. _AppVeyor: https://ci.appveyor.com/project/amueller/word-cloud/history
.. _CircleCI: https://circleci.com/gh/amueller/word_cloud
.. _Travis CI: https://travis-ci.org/amueller/word_cloud/pull_requests

.. _PyPI: https://pypi.org/project/wordcloud
```

## File: doc/references.rst
```
API Reference
=============
All functionality is encapsulated in the WordCloud class.

.. toctree::
   :maxdepth: 2

.. automodule:: wordcloud
   :no-members:
   :no-inherited-members:

.. currentmodule:: wordcloud

.. autosummary::
   :toctree: generated/
   :template: class.rst

    WordCloud
    ImageColorGenerator

   :template: function.rst
   
   random_color_func
   colormap_color_func
   get_single_color_func
```
