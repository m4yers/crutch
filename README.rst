======
CRUTCH
======

.. image:: https://img.shields.io/pypi/status/crutch.svg
   :target: https://pypi.python.org/pypi/crutch
   :alt: PyPi Status

.. image:: https://img.shields.io/pypi/v/crutch.svg
   :target: https://pypi.python.org/pypi/crutch
   :alt: PyPi Version

.. image:: https://img.shields.io/pypi/pyversions/crutch.svg
   :target: https://pypi.python.org/pypi/crutch
   :alt: Python Versions

.. image:: https://travis-ci.org/m4yers/crutch.svg?branch=master
   :target: https://travis-ci.org/m4yers/crutch
   :alt: Build Status

.. image:: https://coveralls.io/repos/github/m4yers/crutch/badge.svg?branch=master
   :target: https://coveralls.io/github/m4yers/crutch?branch=master
   :alt: Test Coverage

.. image:: https://landscape.io/github/m4yers/crutch/master/landscape.svg?style=flat
   :target: https://landscape.io/github/m4yers/crutch/master
   :alt: Code Health

Have you ever had this moment when you wanted to write a small tool or just try
out some new algorithm but the thought of assembling proper project folder
structure spoiled the desire...

CRUTCH is a console development environment, though its definition sounds a bit
weird it does allow you to create a fully customized project, manage its
lifecycle, including `configure`, `build`, `test`, `clean` `add/remove
files/features/tests`, plus language specific features. Also you can extend its
functionality by writing a language module or a feature for already existing
one.

.. contents::

Installation
============

From pip::

  $ pip install crutch


Usage
=====

In its simplest form you interact with CRUTCH via two commands::

  $ crutch new <type>
  $ crutch

Those two lines create a project and `build`, `test`, `run` or whatever default
action is configured for this type of project... that is all you need to get
things going. The default project configuration supposed to provide you with
things necessary to just start writing stuff, but if you need more you can add
features to your projects.

Features
-------------

Feature is something that extends CRUTCH capabilities and specifically adds
functionality to your projects's runner. CRUTCH itself has only one feature,
which is called `new`, that all it does: *create a new project*, and it will
stay this way forever. Additional functionality will be added via language
extensions and features for them.

From user perspective feature is an action keyword that follows `crutch`
command, akin to `new`. For example compile-time projects normally will include
`build` feature, most projects will include `clean` and `test` features. Nice
features to have are: `install`, `publish`, `debug` etc.

Feature allows for a second cli parameters parsing, thus you can invoke an
action for a feature::

  $ crutch test add core/runner

This line invokes `test` feature of the current project with `add` action that
allows you to add a test file in one go(assuming you are not wearing yours
smart ass hat and not trying to modify configuration files manually). The
symmetrical operation would be::

  $ crutch test remove core/runner

This will remove the test files and do cleanup afterwards. Using `test` feature
to manage test files is WAY better than doing this manually...


So, how do you add features? One way is to stay with default provided features,
another is to specify a list of features with `new` action::

  $ crutch new cpp -f xcode gtest

This line forces `cpp` extension to generate `xcode` build project using `cmake`
and add `gtest` based `test` feature.

What if you want to add a feature after you've already created a project? What
might be the way? Just guess... The `feature` feature of course::

  $ crutch feature add doxygen

This line adds `doxygen` based `doc` feature to the project.

The last thing... a feature has a default action, normally it is associated
with its essence, invoking this::

  $ crutch doxygen

Naturally will build documentation, and by invoking this::

  $ crutch doc

You achieve the same, because `doxygen` feature belongs to `doc` feature
category...


Feature Category
----------------

Feature categories is something that is not really reflected in CLI, but
nonetheless is very important concept. Every feature belongs to a category,
duh... This means that at the very least you can invoke an action on a feature
by providing its category name instead. This is very true for categories that
can have only `one` active feature at a time. BUT, if category can have
multiple active features it can modify or even add new actions you can invoke::

  $ crutch lint

This `lint` category has several features: `pep8`, `pylint`, `flake8` etc. So
by invoking category's default action you run all those linter features one
after another to verify your code, alternatively you can run them separately::

  $ crutch pep8
  $ crutch pylint

This opens door for a very complex scenarios, like running custom test server
bench that is basically a tech-stack that needs to be managed. So you can
provide a custom category `bench` that contains multitude of optional features,
like `mysql`, `maria`, `couchbase`, `apache`, etc. And this category provides
few actions like `start`, `stop`, `publish` etc that you can invoke to run all
this madness...Anyway this multi-category is a far feature, and I am writing
this here so I won't forget it later

Types
-------------

In Progress::

  cpp
  python

In Future::

  c#
  java
  vim
  ...


Links
=====

* PyPI_
* GitHub_
* `Travis CI`_
* Coveralls_

.. _PyPI: https://pypi.python.org/pypi/crutch/
.. _GitHub: https://github.com/m4yers/crutch
.. _`Travis CI`: https://travis-ci.org/m4yers/crutch
.. _`Coveralls`: https://coveralls.io/r/m4yers/crutch
