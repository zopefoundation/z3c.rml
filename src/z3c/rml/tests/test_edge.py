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
"""Testing edge cases.
"""
import logging
import os
import unittest
import sys
import z3c.rml.tests
from PyPDF2.utils import PdfReadError
from z3c.rml import rml2pdf
from z3c.rml import pdfinclude

HERE = os.path.dirname(z3c.rml.tests.__file__)
LOG_FILE = os.path.join(os.path.dirname(__file__), 'render.log')


class RMLEdgeTests(unittest.TestCase):

    def setUp(self):
        import z3c.rml.tests.module
        sys.modules['module'] = z3c.rml.tests.module
        sys.modules['mymodule'] = z3c.rml.tests.module

    def tearDown(self):
        del sys.modules['module']
        del sys.modules['mymodule']

        from z3c.rml.document import LOGGER_NAME
        for handler in logging.getLogger(LOGGER_NAME).handlers:
            if handler.baseFilename == LOG_FILE:
                handler.close()

        if os.path.exists(LOG_FILE):
            os.remove(LOG_FILE)

    def test_duplicate_key(self):
        save_strict = pdfinclude.STRICT
        inpath = os.path.join(HERE, 'input', 'data',
                              'tag-includePdfPages-edge-dupekey.rml')
        outpath = os.path.join(HERE, 'output',
                               'tag-includePdfPages-edge-dupekey.pdf')

        # in strict mode include will fail because the PDF is bad
        pdfinclude.STRICT = True
        with self.assertRaises(PdfReadError):
            rml2pdf.go(inpath, outpath)

        # in non strict mode such errors are demoted to warnings
        pdfinclude.STRICT = False
        rml2pdf.go(inpath, outpath)

        pdfinclude.STRICT = save_strict


def test_suite():
    suite = unittest.TestSuite([unittest.makeSuite(RMLEdgeTests)])
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
