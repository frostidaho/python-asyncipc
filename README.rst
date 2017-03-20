========
Overview
========

.. start-badges

.. list-table::
    :stub-columns: 1

    * - docs
      - |docs|
    * - tests
      - | |travis|
        | |coveralls|
    * - package
      - | |version| |wheel| |supported-versions| |supported-implementations|
        | |commits-since|

.. |docs| image:: https://readthedocs.org/projects/python-asyncipc/badge/?style=flat
    :target: https://readthedocs.org/projects/python-asyncipc
    :alt: Documentation Status

.. |travis| image:: https://travis-ci.org/frostidaho/python-asyncipc.svg?branch=master
    :alt: Travis-CI Build Status
    :target: https://travis-ci.org/frostidaho/python-asyncipc

.. |coveralls| image:: https://coveralls.io/repos/frostidaho/python-asyncipc/badge.svg?branch=master&service=github
    :alt: Coverage Status
    :target: https://coveralls.io/r/frostidaho/python-asyncipc

.. |version| image:: https://img.shields.io/pypi/v/asyncipc.svg
    :alt: PyPI Package latest release
    :target: https://pypi.python.org/pypi/asyncipc

.. |commits-since| image:: https://img.shields.io/github/commits-since/frostidaho/python-asyncipc/v0.1.0.svg
    :alt: Commits since latest release
    :target: https://github.com/frostidaho/python-asyncipc/compare/v0.1.0...master

.. |wheel| image:: https://img.shields.io/pypi/wheel/asyncipc.svg
    :alt: PyPI Wheel
    :target: https://pypi.python.org/pypi/asyncipc

.. |supported-versions| image:: https://img.shields.io/pypi/pyversions/asyncipc.svg
    :alt: Supported versions
    :target: https://pypi.python.org/pypi/asyncipc

.. |supported-implementations| image:: https://img.shields.io/pypi/implementation/asyncipc.svg
    :alt: Supported implementations
    :target: https://pypi.python.org/pypi/asyncipc


.. end-badges

An example package. Generated with cookiecutter-pylibrary.

* Free software: BSD license

Installation
============

::

    pip install asyncipc

Documentation
=============

https://python-asyncipc.readthedocs.io/

Development
===========

To run the all tests run::

    tox

Note, to combine the coverage data from all the tox environments run:

.. list-table::
    :widths: 10 90
    :stub-columns: 1

    - - Windows
      - ::

            set PYTEST_ADDOPTS=--cov-append
            tox

    - - Other
      - ::

            PYTEST_ADDOPTS=--cov-append tox
