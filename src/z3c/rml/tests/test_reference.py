##############################################################################
#
# Copyright (c) 2012 Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTLAR PURPOSE.
#
##############################################################################
"""Test generating reference.
"""
import os
import unittest
from z3c.rml import reference

class ReferenceTestCase(unittest.TestCase):

    level = 3

    def runTest(self):
        reference.main(
            os.path.join(os.path.dirname(reference.__file__),
                         'rml-reference.pdf'))


def test_suite():
   return unittest.TestSuite([ReferenceTestCase()])
