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
import io
import os
import unittest

import lxml.etree

from z3c.rml import dtd


class DTDUnitTestCase(unittest.TestCase):

    def runTest(self):
        text = dtd.generate()
        et = lxml.etree.DTD(io.StringIO(text))
        self.assertIsNotNone(next(et.iterelements()))


class UpdateDTDTestCase(unittest.TestCase):

    level = 2

    def runTest(self):
        path = os.path.join(os.path.dirname(dtd.__file__), 'rml.dtd')
        # Write the file.
        with open(path, 'w') as file:
            file.write(dtd.generate())
        # Ensure we produced a processable DTD.
        try:
            lxml.etree.DTD(path)
        except BaseException:
            raise
