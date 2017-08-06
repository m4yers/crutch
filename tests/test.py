#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import sys
import os

this_folder = os.path.abspath(os.path.dirname(__file__))
root_folder = os.path.join(this_folder, '..')
sys.path.insert(0, root_folder)

import tests.core as core

suites = unittest.TestSuite([core.suite])

if __name__ == '__main__':
  unittest.TextTestRunner(verbosity=2).run(suites)
