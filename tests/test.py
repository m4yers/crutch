#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.abspath(os.path.dirname(__file__)), '..'))

import tests.core as core
import tests.cpp as cpp

SUITES = unittest.TestSuite([core.get_suite(), cpp.get_suite()])

if __name__ == '__main__':
  unittest.TextTestRunner(verbosity=2).run(SUITES)
