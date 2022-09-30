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
"""Tests for SVG to reportlab graphics conversion.
"""

import unittest

import reportlab.lib.colors as colors

from z3c.rml import svg2rlg


class SVG2RLGTestCase(unittest.TestCase):
    def test_parseLength(self):
        self.assertEqual(svg2rlg.parseLength("1"), 1.0)
        self.assertEqual(svg2rlg.parseLength("1.25"), 1.25)
        self.assertEqual(svg2rlg.parseLength("5px"), 5.0)
        self.assertEqual(svg2rlg.parseLength("2em"), 2.0)
        self.assertEqual(svg2rlg.parseLength("25%"), 25.0)
        self.assertEqual(svg2rlg.parseLength("4pc"), 48.0)
        self.assertEqual(svg2rlg.parseLength("1in"), 72.0)
        self.assertEqual(svg2rlg.parseLength("3.5e+5"), 350000.0)
        self.assertEqual(svg2rlg.parseLength("e3"), 1000.0)
        with self.assertRaises(svg2rlg.SVGError):
            svg2rlg.parseLength("furlong")
        with self.assertRaises(svg2rlg.SVGError):
            svg2rlg.parseLength("in")
        with self.assertRaises(svg2rlg.SVGError):
            svg2rlg.parseLength("1AU")

    def test_parseColor(self):
        self.assertEqual(svg2rlg.parseColor("none"), None)
        self.assertEqual(svg2rlg.parseColor("currentColor"), "currentColor")
        self.assertEqual(
            svg2rlg.parseColor("transparent"), colors.Color(0.0, 0.0, 0.0, 0.0)
        )
        with self.assertRaises(svg2rlg.SVGError):
            svg2rlg.parseColor("Ceci n'est pas une couleur")
        self.assertEqual(
            svg2rlg.parseColor("wheat"),
            colors.HexColor("#f5deb3")
        )
        with self.assertRaises(svg2rlg.SVGError):
            svg2rlg.parseColor("octarine")
        self.assertEqual(
            svg2rlg.parseColor("#87cefa"),
            colors.HexColor("#87cefa")
        )
        self.assertEqual(
            svg2rlg.parseColor("#1fa"),
            colors.HexColor("#11ffaa")
        )
        self.assertEqual(
            svg2rlg.parseColor("RGB(128,10,255)"), colors.HexColor("#800aff")
        )
        self.assertEqual(
            svg2rlg.parseColor("rgb(128,10,255)"), colors.HexColor("#800aff")
        )
        with self.assertRaises(svg2rlg.SVGError):
            svg2rlg.parseColor("RGB(912,260,525)")
        self.assertEqual(
            svg2rlg.parseColor("RGB(50%,0%,12.25%)"),
            colors.Color(0.5, 0.0, 0.1225, 1.0),
        )
        with self.assertRaises(svg2rlg.SVGError):
            svg2rlg.parseColor("RGB(200%,300%,1225%)")

    def test_parseDashArray(self):
        self.assertEqual(svg2rlg.parseDashArray("none"), None)
        self.assertEqual(
            list(svg2rlg.parseDashArray("1.25,  0.5in,1pc")),
            [1.25, 36.0, 12.0]
        )

    def test_parseOpacity(self):
        self.assertEqual(svg2rlg.parseOpacity("0.5"), 0.5)
        self.assertEqual(svg2rlg.parseOpacity(0.25), 0.25)
        self.assertEqual(svg2rlg.parseOpacity(42), 1.0)
        self.assertEqual(svg2rlg.parseOpacity(-1), 0.0)
        with self.assertRaises(svg2rlg.SVGError):
            svg2rlg.parseOpacity("opaque")

    def test_parseAnchor(self):
        self.assertEqual(svg2rlg.parseAnchor(None), "start")
        self.assertEqual(svg2rlg.parseAnchor("none"), "start")
        self.assertEqual(svg2rlg.parseAnchor("middle"), "middle")
        with self.assertRaises(svg2rlg.SVGError):
            svg2rlg.parseAnchor("somewhere")
