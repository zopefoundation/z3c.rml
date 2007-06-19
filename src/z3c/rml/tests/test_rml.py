##############################################################################
#
# Copyright (c) 2007 Zope Corporation and Contributors.
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

$Id$
"""
import os
import PIL
import popen2
import unittest
import sys
import z3c.rml.tests
from z3c.rml import rml2pdf, attr

GS_COMMAND = ('gs -q -sNOPAUSE -sDEVICE=png256 -sOutputFile=%s[Page-%%d].png '
              '%s -c quit')

class RMLRenderingTestCase(unittest.TestCase):

    def __init__(self, inPath, outPath):
        self._inPath = inPath
        self._outPath = outPath
        unittest.TestCase.__init__(self)

    def setUp(self):
        # Switch file opener for Image attibute
        self._fileOpen = attr.File.open
        def testOpen(img, filename):
            path = os.path.join(os.path.dirname(self._inPath), filename)
            return open(path, 'rb')
        attr.File.open = testOpen
        import z3c.rml.tests.module
        sys.modules['module'] = z3c.rml.tests.module
        sys.modules['mymodule'] = z3c.rml.tests.module

    def tearDown(self):
        attr.File.open = self._fileOpen
        del sys.modules['module']
        del sys.modules['mymodule']

    def runTest(self):
        rml2pdf.go(self._inPath, self._outPath)


class ComparePDFTestCase(unittest.TestCase):

    level = 2

    def __init__(self, basePath, testPath):
        self._basePath = basePath
        self._testPath = testPath
        unittest.TestCase.__init__(self)

    def assertSameImage(self, baseImage, testImage):
        base = PIL.Image.open(baseImage).getdata()
        test = PIL.Image.open(testImage).getdata()
        for i in range(len(base)):
            if (base[i] - test[i]) != 0:
                self.fail('Image is not the same.')

    def runTest(self):
        # Convert the base PDF to image(s)
        status = popen2.Popen3(
            GS_COMMAND %(self._basePath[:-4], self._basePath), True).wait()
        if status:
            return
        # Convert the test PDF to image(s)
        status = popen2.Popen3(
            GS_COMMAND %(self._testPath[:-4], self._testPath), True).wait()
        if status:
            return
        # Go through all pages and ensure their equality
        n = 1
        while True:
            baseImage = self._basePath[:-4] + '[Page-%i].png' %n
            testImage = self._testPath[:-4] + '[Page-%i].png' %n
            if os.path.exists(baseImage) and os.path.exists(testImage):
                self.assertSameImage(baseImage, testImage)
            else:
                break
            n += 1


def test_suite():
   suite = unittest.TestSuite()
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