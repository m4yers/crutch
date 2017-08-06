============
STATUS/TODO
============

.. contents::

Interface
=========

Vim plugin
----------
Status: planned


Driver
======

Actions
-------

create
~~~~~~
Status: **Usable**

build
~~~~~
Status: **Usable**

test
~~~~
Status: **Planned**

add
~~~
Status: **Planned**

This action allows to add some new stuff, like a missed feature::

  $ crutch add feature doc

or maybe a file or test group::

  $ crutch add test <name>
  $ crutch add file <name>

and this should generate a new test folder and put newly generated files into
appropriate folders, e.g. ``*.hpp`` into ``/include/<project>`` and ``*.cpp``
into ``/src/<project>``

remove
~~~~~~
Status: **Planned**

The reverse of add, basically

clean
~~~~~
Status: **Planned**

Must delete all generated temporal files and folders, e.g build folder, docs,
etc

doc
~~~
Status: **Planned**


Core
====


Features
========


Project Types
=============

C++
---
Status: **Usable**

Python
------
Status: **Planned**

C#
--
Status: **Planned**

Java
----
Status: **Planned**

Vim
---
Status: **Planned**
