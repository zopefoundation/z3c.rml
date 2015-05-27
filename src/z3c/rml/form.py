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
"""
import types
import reportlab.pdfbase.pdfform
from z3c.rml import attr, directive, interfaces, occurence

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

    code = attr.Choice(
        title=u'Code',
        description=u'The name of the type of code to use.',
        choices=reportlab.graphics.barcode.getCodeNames(),
        required=True)

    value = attr.TextNode(
        title=u'Value',
        description=u'The value represented by the code.',
        required=True)

    width = attr.Measurement(
        title=u'Width',
        description=u'The width of the barcode.',
        required=False)

    height = attr.Measurement(
        title=u'Height',
        description=u'The height of the barcode.',
        required=False)

    barStrokeColor = attr.Color(
        title=u'Bar Stroke Color',
        description=(u'The color of the line strokes in the barcode.'),
        required=False)

    barStrokeWidth = attr.Measurement(
        title=u'Bar Stroke Width',
        description=u'The width of the line strokes in the barcode.',
        required=False)

    barFillColor = attr.Color(
        title=u'Bar Fill Color',
        description=(u'The color of the filled shapes in the barcode.'),
        required=False)

    gap = attr.Measurement(
        title=u'Gap',
        description=u'The width of the inter-character gaps.',
        required=False)

    # Bar code dependent attributes
    # I2of5, Code128, Standard93, FIM, POSTNET, Ean13B
    barWidth = attr.Measurement(
        title=u'Bar Width',
        description=u'The width of the smallest bar within the barcode',
        required=False)

    # I2of5, Code128, Standard93, FIM, POSTNET
    barHeight = attr.Measurement(
        title=u'Bar Height',
        description=u'The height of the symbol.',
        required=False)

    # I2of5
    ratio = attr.Float(
        title=u'Ratio',
        description=(u'The ratio of wide elements to narrow elements. '
                     u'Must be between 2.0 and 3.0 (or 2.2 and 3.0 if the '
                     u'barWidth is greater than 20 mils (.02 inch)).'),
        min=2.0,
        max=3.0,
        required=False)

    # I2of5
    # Should be boolean, but some code want it as int; will still work
    checksum = attr.Integer(
        title=u'Ratio',
        description=(u'A flag that enables the computation and inclusion of '
                     u'the check digit.'),
        required=False)

    # I2of5
    bearers = attr.Float(
        title=u'Bearers',
        description=(u'Height of bearer bars (horizontal bars along the top '
                     u'and bottom of the barcode). Default is 3 '
                     u'x-dimensions. Set to zero for no bearer bars.'
                     u'(Bearer bars help detect misscans, so it is '
                     u'suggested to leave them on).'),
        required=False)

    # I2of5, Code128, Standard93, FIM, Ean13
    quiet = attr.Boolean(
        title=u'Quiet Zone',
        description=(u'A flag to include quiet zones in the symbol.'),
        required=False)

    # I2of5, Code128, Standard93, FIM, Ean13
    lquiet = attr.Measurement(
        title=u'Left Quiet Zone',
        description=(u"Quiet zone size to the left of code, if quiet is "
                     u"true. Default is the greater of .25 inch or .15 times "
                     u"the symbol's length."),
        required=False)

    # I2of5, Code128, Standard93, FIM, Ean13
    rquiet = attr.Measurement(
        title=u'Right Quiet Zone',
        description=(u"Quiet zone size to the right of code, if quiet is "
                     u"true. Default is the greater of .25 inch or .15 times "
                     u"the symbol's length."),
        required=False)

    # I2of5, Code128, Standard93, FIM, POSTNET, Ean13
    fontName = attr.String(
        title=u'Font Name',
        description=(u'The font used to print the value.'),
        required=False)

    # I2of5, Code128, Standard93, FIM, POSTNET, Ean13
    fontSize = attr.Measurement(
        title=u'Font Size',
        description=(u'The size of the value text.'),
        required=False)

    # I2of5, Code128, Standard93, FIM, POSTNET, Ean13
    humanReadable = attr.Boolean(
        title=u'Human Readable',
        description=(u'A flag when set causes the value to be printed below '
                     u'the bar code.'),
        required=False)

    # I2of5, Standard93
    stop = attr.Boolean(
        title=u'Show Start/Stop',
        description=(u'A flag to specify whether the start/stop symbols '
                     u'are to be shown.'),
        required=False)

    # FIM, POSTNET
    spaceWidth = attr.Measurement(
        title=u'Space Width',
        description=u'The space of the inter-character gaps.',
        required=False)

    # POSTNET
    shortHeight = attr.Measurement(
        title=u'Short Height',
        description=u'The height of the short bar.',
        required=False)

    # Ean13
    textColor = attr.Color(
        title=u'Text Color',
        description=(u'The color of human readable text.'),
        required=False)

    # USPS4S
    routing = attr.String(
        title=u'Routing',
        description=u'The routing information string.',
        required=False)

    # QR
    barLevel = attr.Choice(
        title=u'Bar Level',
        description=u'The error correction level for QR code',
        choices=['L', 'M', 'Q', 'H'],
        required=False)

    barBorder = attr.Measurement(
        title=u'Bar Border',
        description=u'The width of the border around a QR code.',
        required=False)


class IBarCode(IBarCodeBase):
    """A barcode graphic."""

    x = attr.Measurement(
        title=u'X-Position',
        description=u'The x-position of the lower-left corner of the barcode.',
        default=0,
        required=False)

    y = attr.Measurement(
        title=u'Y-Position',
        description=u'The y-position of the lower-left corner of the barcode.',
        default=0,
        required=False)

    isoScale = attr.Boolean(
        title=u'Isometric Scaling',
        description=u'When set, the aspect ration of the barcode is enforced.',
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
        manager = attr.getManager(self, interfaces.ICanvasManager)
        code.drawOn(manager.canvas, x, y)


class IField(interfaces.IRMLDirectiveSignature):
    """A field."""

    title = attr.Text(
        title=u'Title',
        description=u'The title of the field.',
        required=True)

    x = attr.Measurement(
        title=u'X-Position',
        description=u'The x-position of the lower-left corner of the field.',
        default=0,
        required=True)

    y = attr.Measurement(
        title=u'Y-Position',
        description=u'The y-position of the lower-left corner of the field.',
        default=0,
        required=True)


class Field(directive.RMLDirective):
    signature = IField
    callable = None
    attrMapping = {}

    def process(self):
        kwargs = dict(self.getAttributeValues(attrMapping=self.attrMapping))
        canvas = attr.getManager(self, interfaces.ICanvasManager).canvas
        getattr(reportlab.pdfbase.pdfform, self.callable)(canvas, **kwargs)


class ITextField(IField):
    """A text field within the PDF"""

    width = attr.Measurement(
        title=u'Width',
        description=u'The width of the text field.',
        required=True)

    height = attr.Measurement(
        title=u'Height',
        description=u'The height of the text field.',
        required=True)

    value = attr.Text(
        title=u'Value',
        description=u'The default text value of the field.',
        required=False)

    maxLength = attr.Integer(
        title=u'Maximum Length',
        description=u'The maximum amount of characters allowed in the field.',
        required=False)

    multiline = attr.Boolean(
        title=u'Multiline',
        description=u'A flag when set allows multiple lines within the field.',
        required=False)

class TextField(Field):
    signature = ITextField
    callable = 'textFieldAbsolute'
    attrMapping = {'maxLength': 'maxlen'}


class IButtonField(IField):
    """A button field within the PDF"""

    value = attr.Choice(
        title=u'Value',
        description=u'The value of the button.',
        choices=('Yes', 'Off'),
        required=True)

class ButtonField(Field):
    signature = IButtonField
    callable = 'buttonFieldAbsolute'


class IOption(interfaces.IRMLDirectiveSignature):
    """An option in the select field."""

    value = attr.TextNode(
        title=u'Value',
        description=u'The value of the option.',
        required=True)

class Option(directive.RMLDirective):
    signature = IOption

    def process(self):
        value = self.getAttributeValues(valuesOnly=True)[0]
        self.parent.options.append(value)


class ISelectField(IField):
    """A selection field within the PDF"""
    occurence.containing(
        occurence.ZeroOrMore('option', IOption))

    width = attr.Measurement(
        title=u'Width',
        description=u'The width of the select field.',
        required=True)

    height = attr.Measurement(
        title=u'Height',
        description=u'The height of the select field.',
        required=True)

    value = attr.Text(
        title=u'Value',
        description=u'The default value of the field.',
        required=False)

class SelectField(Field):
    signature = ISelectField
    callable = 'selectFieldAbsolute'
    factories = {'option': Option}

    def process(self):
        self.options = []
        self.processSubDirectives()
        kwargs = dict(self.getAttributeValues(attrMapping=self.attrMapping))
        kwargs['options'] = self.options
        canvas = attr.getManager(self, interfaces.ICanvasManager).canvas
        getattr(reportlab.pdfbase.pdfform, self.callable)(canvas, **kwargs)
