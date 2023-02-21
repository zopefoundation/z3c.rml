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
"""Test RML to PDF converter.
"""

import io
import unittest
from unittest import mock

from z3c.rml import rml2pdf


class RML2PDFTest(unittest.TestCase):

    @mock.patch("z3c.rml.rml2pdf.go")
    def test_main_minimal(self, go):
        rml2pdf.main(["input.rml", "output.pdf"])
        go.assert_called_with("input.rml", "output.pdf")

    @mock.patch("z3c.rml.rml2pdf.go")
    def test_main_all_args(self, go):
        rml2pdf.main(["input.rml", "output.pdf", "./out/pdf/", "./out/dtd/"])
        go.assert_called_with(
            "input.rml", "output.pdf", "./out/pdf/", "./out/dtd/"
        )

    def test_go(self):
        rml = """
            <!DOCTYPE document SYSTEM "rml_1_0.dtd">
            <document filename="test.pdf">
            </document>
        """
        rml2pdf.go(io.StringIO(rml))

    def test_parseString(self):
        rml = """
          <?xml version="1.0" encoding="UTF-8" ?>
          <!DOCTYPE document SYSTEM "rml_1_0.dtd">
          <document filename="test.pdf">
            <template>
              <pageTemplate id="main">
                <frame id="first" x1="1in" y1="1in"
                       width="7in" height="9in"/>
              </pageTemplate>
            </template>
            <story><para>Hello</para></story>
          </document>
        """.strip()
        stream = rml2pdf.parseString(rml)
        self.assertEqual(stream.read()[:8], b"%PDF-1.4")
