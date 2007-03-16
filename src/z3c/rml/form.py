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
        ('width', attr.Measurement('width')),
        ('height', attr.Measurement('height')),
        ('strokeColor', attr.Color('strokeColor')),
        ('strokeWidth', attr.Measurement('strokeWidth')),
        ('fillColor', attr.Color('fillColor')),
        ('barStrokeColor', attr.Color('barStrokeColor')),
        ('barStrokeWidth', attr.Measurement('barStrokeWidth')),
        ('barFillColor', attr.Color('barFillColor')),
        ('gap', attr.Measurement('gap')),
        # Bar code dependent attributes
        # I2of5, Code128, Standard93, FIM, POSTNET, Ean13B
        ('barWidth', attr.Measurement('barWidth')),
        # I2of5, Code128, Standard93, FIM, POSTNET
        ('barHeight', attr.Measurement('barHeight')),
        # I2of5
        ('ratio', attr.Float('ratio')),
        # I2of5
        # Should be boolean, but some code want it as int; will still work
        ('checksum', attr.Int('checksum')),
        # I2of5
        ('bearers', attr.Float('bearers')),
        # I2of5, Code128, Standard93, FIM, Ean13
        ('quiet', attr.Bool('quiet')),
        # I2of5, Code128, Standard93, FIM, Ean13
        ('lquiet', attr.Measurement('lquiet')),
        # I2of5, Code128, Standard93, FIM, Ean13
        ('rquiet', attr.Measurement('rquiet')),
        # I2of5, Code128, Standard93, FIM, POSTNET, Ean13
        ('fontName', attr.Text('fontName')),
        # I2of5, Code128, Standard93, FIM, POSTNET, Ean13
        ('fontSize', attr.Measurement('fontSize')),
        # I2of5, Code128, Standard93, FIM, POSTNET, Ean13
        ('humanReadable', attr.Bool('humanReadable')),
        # I2of5, Standard93
        ('stop', attr.Bool('atop')),
        # FIM, POSTNET
        ('spaceWidth', attr.Measurement('spaceWidth')),
        # POSTNET
        ('shortHeight', attr.Measurement('shortHeight')),
        # Ean13
        ('textColor', attr.Color('textColor')),
        )

    def process(self):
        kw = self.getKeywordArguments()
        name, value = self.getPositionalArguments()
        kw['value'] = str(value)
        x = kw.pop('x', 0)
        y = kw.pop('y', 0)
        code = reportlab.graphics.barcode.createBarcodeDrawing(name, **kw)
        code.drawOn(self.context, x, y)
