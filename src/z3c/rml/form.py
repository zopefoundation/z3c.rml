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
from z3c.rml import attrng, directive, interfaces

try:
    import reportlab.graphics.barcode
except ImportError:
    # barcode package has not been installed
    import types
    import reportlab.graphics
    reportlab.graphics.barcode = types.ModuleType('barcode')
    reportlab.graphics.barcode.getCodeNames = lambda : ()


class IBarCodeBase(interfaces.IRMLDirectiveSignature):
    """Create a bar code."""

    code = attrng.Choice(
        title=u'Code',
        description=u'The name of the type of code to use.',
        choices=reportlab.graphics.barcode.getCodeNames(),
        required=True)

    value = attrng.TextNode(
        title=u'Value',
        description=u'The value represented by the code.',
        required=True)

    width = attrng.Measurement(
        title=u'Width',
        description=u'The width of the barcode.',
        required=False)

    height = attrng.Measurement(
        title=u'Height',
        description=u'The height of the barcode.',
        required=False)

    strokeColor = attrng.Color(
        title=u'Stroke Color',
        description=(u'The color of the line strokes in the area.'),
        required=False)

    strokeWidth = attrng.Measurement(
        title=u'Stroke Width',
        description=u'The width of the line strokes in the area.',
        required=False)

    fillColor = attrng.Color(
        title=u'Fill Color',
        description=(u'The color of the filled shapes in the area.'),
        required=False)

    barStrokeColor = attrng.Color(
        title=u'Bar Stroke Color',
        description=(u'The color of the line strokes in the barcode.'),
        required=False)

    barStrokeWidth = attrng.Measurement(
        title=u'Bar Stroke Width',
        description=u'The width of the line strokes in the barcode.',
        required=False)

    barFillColor = attrng.Color(
        title=u'Bar Fill Color',
        description=(u'The color of the filled shapes in the barcode.'),
        required=False)

    gap = attrng.Measurement(
        title=u'Gap',
        description=u'The width of the inter-character gaps.',
        required=False)

    # Bar code dependent attributes
    # I2of5, Code128, Standard93, FIM, POSTNET, Ean13B
    barWidth = attrng.Measurement(
        title=u'Bar Width',
        description=u'The width of the smallest bar within the barcode',
        required=False)

    # I2of5, Code128, Standard93, FIM, POSTNET
    barHeight = attrng.Measurement(
        title=u'Bar Height',
        description=u'The height of the symbol.',
        required=False)

    # I2of5
    ratio = attrng.Float(
        title=u'Ratio',
        description=(u'The ratio of wide elements to narrow elements. '
                     u'Must be between 2.0 and 3.0 (or 2.2 and 3.0 if the '
                     u'barWidth is greater than 20 mils (.02 inch)).'),
        min=2.0,
        max=3.0,
        required=False)

    # I2of5
    # Should be boolean, but some code want it as int; will still work
    checksum = attrng.Integer(
        title=u'Ratio',
        description=(u'A flag that enables the computation and inclusion of '
                     u'the check digit.'),
        required=False)

    # I2of5
    bearers = attrng.Float(
        title=u'Bearers',
        description=(u'Height of bearer bars (horizontal bars along the top '
                     u'and bottom of the barcode). Default is 3 '
                     u'x-dimensions. Set to zero for no bearer bars.'
                     u'(Bearer bars help detect misscans, so it is '
                     u'suggested to leave them on).'),
        required=False)

    # I2of5, Code128, Standard93, FIM, Ean13
    quiet = attrng.Boolean(
        title=u'Quiet Zone',
        description=(u'A flag to include quiet zones in the symbol.'),
        required=False)

    # I2of5, Code128, Standard93, FIM, Ean13
    lquiet = attrng.Measurement(
        title=u'Left Quiet Zone',
        description=(u"Quiet zone size to the left of code, if quiet is "
                     u"true. Default is the greater of .25 inch or .15 times "
                     u"the symbol's length."),
        required=False)

    # I2of5, Code128, Standard93, FIM, Ean13
    rquiet = attrng.Measurement(
        title=u'Right Quiet Zone',
        description=(u"Quiet zone size to the right of code, if quiet is "
                     u"true. Default is the greater of .25 inch or .15 times "
                     u"the symbol's length."),
        required=False)

    # I2of5, Code128, Standard93, FIM, POSTNET, Ean13
    frontName = attrng.String(
        title=u'Font Name',
        description=(u'The font used to print the value.'),
        required=False)

    # I2of5, Code128, Standard93, FIM, POSTNET, Ean13
    frontSize = attrng.Measurement(
        title=u'Font Size',
        description=(u'The size of the value text.'),
        required=False)

    # I2of5, Code128, Standard93, FIM, POSTNET, Ean13
    humanReadable = attrng.Boolean(
        title=u'Human Readable',
        description=(u'A flag when set causes the value to be printed below '
                     u'the bar code.'),
        required=False)

    # I2of5, Standard93
    stop = attrng.Boolean(
        title=u'Show Start/Stop',
        description=(u'A flag to specify whether the start/stop symbols '
                     u'are to be shown.'),
        required=False)

    # FIM, POSTNET
    spaceWidth = attrng.Measurement(
        title=u'Space Width',
        description=u'The space of the inter-character gaps.',
        required=False)

    # POSTNET
    shortHeight = attrng.Measurement(
        title=u'Short Height',
        description=u'The height of the short bar.',
        required=False)

    # Ean13
    textColor = attrng.Color(
        title=u'Text Color',
        description=(u'The color of human readable text.'),
        required=False)


class IBarCode(IBarCodeBase):
    """A barcode graphic."""

    x = attrng.Measurement(
        title=u'X-Position',
        description=u'The x-position of the lower-left corner of the barcode.',
        default=0,
        required=False)

    y = attrng.Measurement(
        title=u'Y-Position',
        description=u'The y-position of the lower-left corner of the barcode.',
        default=0,
        required=False)



class BarCode(directive.RMLDirective):
    signature = IBarCode

    def process(self):
        kw = dict(self.getAttributeValues())
        name = kw.pop('code')
        kw['value'] = str(kw['value'])
        x = kw.pop('x', 0)
        y = kw.pop('y', 0)
        code = reportlab.graphics.barcode.createBarcodeDrawing(name, **kw)
        manager = attrng.getManager(self, interfaces.ICanvasManager)
        code.drawOn(manager.canvas, x, y)
