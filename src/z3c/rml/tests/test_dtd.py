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
"""Test generating DTD
"""
import os
import unittest
from z3c.rml import dtd

class DTDTestCase(unittest.TestCase):

    level = 2

    def runTest(self):
        path = os.path.join(os.path.dirname(dtd.__file__), 'rml.dtd')
        with open(path, 'w') as file:
            file.write(dtd.generate())


def test_suite():
   return unittest.TestSuite([DTDTestCase()])
