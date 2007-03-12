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
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Page Drawing Related Element Processing

$Id$
"""
__docformat__ = "reStructuredText"
import types
from z3c.rml import attr, element

try:
    import reportlab.graphics.barcode
except ImportError:
    # barcode package has not been installed
    import reportlab.graphics
    reportlab.graphics.barcode = types.ModuleType('barcode')
    reportlab.graphics.barcode.getCodeNames = lambda : ()


class BarCode(element.FunctionElement):
    args = (
        attr.Choice('code', reportlab.graphics.barcode.getCodeNames()),
        attr.TextNode(),
        )
    kw = (
        ('x', attr.Measurement('x')),
        ('y', attr.Measurement('y')),
        ('strokeColor', attr.Color('strokeColor')),
        ('strokeWidth', attr.Measurement('strokeWidth')),
        ('fillColor', attr.Color('fillColor')),
        ('barStrokeColor', attr.Color('barStrokeColor')),
        ('barStrokeWidth', attr.Measurement('barStrokeWidth')),
        ('barFillColor', attr.Color('barFillColor')),
        ('gap', attr.Measurement('gap')),
        )

    def process(self):
        kw = self.getKeywordArguments()
        name, kw['value'] = self.getPositionalArguments()
        x = kw.pop('x', 0)
        y = kw.pop('y', 0)
        code = reportlab.graphics.barcode.createBarcodeDrawing(name, **kw)
        code.drawOn(self.context, x, y)
