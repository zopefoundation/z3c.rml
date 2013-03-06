##############################################################################
#
# Copyright (c) 2007 Zope Foundation and Contributors.
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
"""Testing all XML Locale functionality.
"""
import os
import unittest
import z3c.rml.tests
from z3c.rml import rml2pdfscript
from z3c.rml.tests.test_rml import ComparePDFTestCase
from z3c.rml.tests.test_rml import RMLRenderingTestCase


class RMLRenderingTestCase(RMLRenderingTestCase):

    def runTest(self):
        rml2pdfscript.goSubProcess(self._inPath, self._outPath, True)


def test_suite():
   suite = unittest.TestSuite()
   return suite
   inputDir = os.path.join(os.path.dirname(z3c.rml.tests.__file__), 'input')
   outputDir = os.path.join(os.path.dirname(z3c.rml.tests.__file__), 'output')
   expectDir = os.path.join(os.path.dirname(z3c.rml.tests.__file__), 'expected')
   for filename in os.listdir(inputDir):
       if not filename.endswith(".rml"):
           continue
       inPath = os.path.join(inputDir, filename)
       outPath = os.path.join(outputDir, filename[:-4] + '.pdf')
       expectPath = os.path.join(expectDir, filename[:-4] + '.pdf')

       # ** Test RML to PDF rendering **
       # Create new type, so that we can get test matching
       TestCase = type(filename[:-4], (RMLRenderingTestCase,), {})
       case = TestCase(inPath, outPath)
       suite.addTest(case)

       # ** Test PDF rendering correctness **
       TestCase = type('compare-'+filename[:-4], (ComparePDFTestCase,), {})
       case = TestCase(expectPath, outPath)
       suite.addTest(case)

   return suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
