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

from z3c.rml import attr
from z3c.rml import directive
from z3c.rml import interfaces
from z3c.rml import occurence


try:
    import reportlab.graphics.barcode
except ImportError:
    # barcode package has not been installed

    import reportlab.graphics
    reportlab.graphics.barcode = types.ModuleType('barcode')
    reportlab.graphics.barcode.getCodeNames = lambda: ()


class IBarCodeBase(interfaces.IRMLDirectiveSignature):
    """Create a bar code."""

    code = attr.Choice(
        title='Code',
        description='The name of the type of code to use.',
        choices=reportlab.graphics.barcode.getCodeNames(),
        required=True)

    value = attr.TextNode(
        title='Value',
        description='The value represented by the code.',
        required=True)

    width = attr.Measurement(
        title='Width',
        description='The width of the barcode.',
        required=False)

    height = attr.Measurement(
        title='Height',
        description='The height of the barcode.',
        required=False)

    barStrokeColor = attr.Color(
        title='Bar Stroke Color',
        description=('The color of the line strokes in the barcode.'),
        required=False)

    barStrokeWidth = attr.Measurement(
        title='Bar Stroke Width',
        description='The width of the line strokes in the barcode.',
        required=False)

    barFillColor = attr.Color(
        title='Bar Fill Color',
        description=('The color of the filled shapes in the barcode.'),
        required=False)

    gap = attr.Measurement(
        title='Gap',
        description='The width of the inter-character gaps.',
        required=False)

    # Bar code dependent attributes
    # I2of5, Code128, Standard93, FIM, POSTNET, Ean13B
    barWidth = attr.Measurement(
        title='Bar Width',
        description='The width of the smallest bar within the barcode',
        required=False)

    # I2of5, Code128, Standard93, FIM, POSTNET
    barHeight = attr.Measurement(
        title='Bar Height',
        description='The height of the symbol.',
        required=False)

    # I2of5
    ratio = attr.Float(
        title='Ratio',
        description=('The ratio of wide elements to narrow elements. '
                     'Must be between 2.0 and 3.0 (or 2.2 and 3.0 if the '
                     'barWidth is greater than 20 mils (.02 inch)).'),
        min=2.0,
        max=3.0,
        required=False)

    # I2of5
    # Should be boolean, but some code want it as int; will still work
    checksum = attr.Integer(
        title='Ratio',
        description=('A flag that enables the computation and inclusion of '
                     'the check digit.'),
        required=False)

    # I2of5
    bearers = attr.Float(
        title='Bearers',
        description=('Height of bearer bars (horizontal bars along the top '
                     'and bottom of the barcode). Default is 3 '
                     'x-dimensions. Set to zero for no bearer bars.'
                     '(Bearer bars help detect misscans, so it is '
                     'suggested to leave them on).'),
        required=False)

    # I2of5, Code128, Standard93, FIM, Ean13
    quiet = attr.Boolean(
        title='Quiet Zone',
        description=('A flag to include quiet zones in the symbol.'),
        required=False)

    # I2of5, Code128, Standard93, FIM, Ean13
    lquiet = attr.Measurement(
        title='Left Quiet Zone',
        description=("Quiet zone size to the left of code, if quiet is "
                     "true. Default is the greater of .25 inch or .15 times "
                     "the symbol's length."),
        required=False)

    # I2of5, Code128, Standard93, FIM, Ean13
    rquiet = attr.Measurement(
        title='Right Quiet Zone',
        description=("Quiet zone size to the right of code, if quiet is "
                     "true. Default is the greater of .25 inch or .15 times "
                     "the symbol's length."),
        required=False)

    # I2of5, Code128, Standard93, FIM, POSTNET, Ean13
    fontName = attr.Text(
        title='Font Name',
        description=('The font used to print the value.'),
        required=False)

    # I2of5, Code128, Standard93, FIM, POSTNET, Ean13
    fontSize = attr.Measurement(
        title='Font Size',
        description=('The size of the value text.'),
        required=False)

    # I2of5, Code128, Standard93, FIM, POSTNET, Ean13
    humanReadable = attr.Boolean(
        title='Human Readable',
        description=('A flag when set causes the value to be printed below '
                     'the bar code.'),
        required=False)

    # I2of5, Standard93
    stop = attr.Boolean(
        title='Show Start/Stop',
        description=('A flag to specify whether the start/stop symbols '
                     'are to be shown.'),
        required=False)

    # FIM, POSTNET
    spaceWidth = attr.Measurement(
        title='Space Width',
        description='The space of the inter-character gaps.',
        required=False)

    # POSTNET
    shortHeight = attr.Measurement(
        title='Short Height',
        description='The height of the short bar.',
        required=False)

    # Ean13
    textColor = attr.Color(
        title='Text Color',
        description=('The color of human readable text.'),
        required=False)

    # USPS4S
    routing = attr.Text(
        title='Routing',
        description='The routing information string.',
        required=False)

    # QR
    barLevel = attr.Choice(
        title='Bar Level',
        description='The error correction level for QR code',
        choices=['L', 'M', 'Q', 'H'],
        required=False)

    barBorder = attr.Measurement(
        title='Bar Border',
        description='The width of the border around a QR code.',
        required=False)


class IBarCode(IBarCodeBase):
    """A barcode graphic."""

    x = attr.Measurement(
        title='X-Position',
        description='The x-position of the lower-left corner of the barcode.',
        default=0,
        required=False)

    y = attr.Measurement(
        title='Y-Position',
        description='The y-position of the lower-left corner of the barcode.',
        default=0,
        required=False)

    isoScale = attr.Boolean(
        title='Isometric Scaling',
        description='When set, the aspect ration of the barcode is enforced.',
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
        title='Title',
        description='The title of the field.',
        required=True)

    x = attr.Measurement(
        title='X-Position',
        description='The x-position of the lower-left corner of the field.',
        default=0,
        required=True)

    y = attr.Measurement(
        title='Y-Position',
        description='The y-position of the lower-left corner of the field.',
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
        title='Width',
        description='The width of the text field.',
        required=True)

    height = attr.Measurement(
        title='Height',
        description='The height of the text field.',
        required=True)

    value = attr.Text(
        title='Value',
        description='The default text value of the field.',
        required=False)

    maxLength = attr.Integer(
        title='Maximum Length',
        description='The maximum amount of characters allowed in the field.',
        required=False)

    multiline = attr.Boolean(
        title='Multiline',
        description='A flag when set allows multiple lines within the field.',
        required=False)


class TextField(Field):
    signature = ITextField
    callable = 'textFieldAbsolute'
    attrMapping = {'maxLength': 'maxlen'}


class IButtonField(IField):
    """A button field within the PDF"""

    value = attr.Choice(
        title='Value',
        description='The value of the button.',
        choices=('Yes', 'Off'),
        required=True)


class ButtonField(Field):
    signature = IButtonField
    callable = 'buttonFieldAbsolute'


class IOption(interfaces.IRMLDirectiveSignature):
    """An option in the select field."""

    value = attr.TextNode(
        title='Value',
        description='The value of the option.',
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
        title='Width',
        description='The width of the select field.',
        required=True)

    height = attr.Measurement(
        title='Height',
        description='The height of the select field.',
        required=True)

    value = attr.Text(
        title='Value',
        description='The default value of the field.',
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
