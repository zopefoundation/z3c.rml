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
"""Flowable Element Processing
"""
import copy
import logging
import re
from xml.sax.saxutils import unescape

import reportlab.lib.styles
import reportlab.platypus
import reportlab.platypus.doctemplate
import reportlab.platypus.flowables
import reportlab.platypus.tables
import zope.schema
from reportlab.lib import styles  # noqa: F401 imported but unused
from reportlab.lib import utils

from z3c.rml import SampleStyleSheet
from z3c.rml import attr
from z3c.rml import directive
from z3c.rml import form
from z3c.rml import interfaces
from z3c.rml import occurence
from z3c.rml import paraparser
from z3c.rml import platypus
from z3c.rml import special
from z3c.rml import stylesheet


try:
    import reportlab.graphics.barcode
except ImportError:
    # barcode package has not been installed
    import types

    import reportlab.graphics
    reportlab.graphics.barcode = types.ModuleType('barcode')
    reportlab.graphics.barcode.createBarcodeDrawing = None

# XXX:Copy of reportlab.lib.pygments2xpre.pygments2xpre to fix bug in Python 2.


def pygments2xpre(s, language="python"):
    "Return markup suitable for XPreformatted"
    try:
        from pygments import highlight
        from pygments.formatters import HtmlFormatter
    except ImportError:
        return s

    from pygments.lexers import get_lexer_by_name

    l_ = get_lexer_by_name(language)

    h = HtmlFormatter()
    from io import StringIO
    out = StringIO()
    highlight(s, l_, h, out)
    styles_ = [(cls, style.split(';')[0].split(':')[1].strip())
               for cls, (style, ttype, level) in h.class2style.items()
               if cls and style and style.startswith('color:')]
    from reportlab.lib.pygments2xpre import _2xpre
    return _2xpre(out.getvalue(), styles_)


class Flowable(directive.RMLDirective):
    klass = None
    attrMapping = None

    def process(self):
        args = dict(self.getAttributeValues(attrMapping=self.attrMapping))
        self.parent.flow.append(self.klass(**args))


class ISpacer(interfaces.IRMLDirectiveSignature):
    """Creates a vertical space in the flow."""

    width = attr.Measurement(
        title='Width',
        description='The width of the spacer. Currently not implemented.',
        default=100,
        required=False)

    length = attr.Measurement(
        title='Length',
        description='The height of the spacer.',
        required=True)


class Spacer(Flowable):
    signature = ISpacer
    klass = reportlab.platypus.Spacer
    attrMapping = {'length': 'height'}


class IIllustration(interfaces.IRMLDirectiveSignature):
    """Inserts an illustration with graphics elements."""

    width = attr.Measurement(
        title='Width',
        description='The width of the illustration.',
        required=True)

    height = attr.Measurement(
        title='Height',
        description='The height of the illustration.',
        default=100,
        required=True)


class Illustration(Flowable):
    signature = IIllustration
    klass = platypus.Illustration

    def process(self):
        args = dict(self.getAttributeValues())
        self.parent.flow.append(self.klass(self, **args))


class IBarCodeFlowable(form.IBarCodeBase):
    """Creates a bar code as a flowable."""

    value = attr.Text(
        title='Value',
        description='The value represented by the code.',
        required=True)


class BarCodeFlowable(Flowable):
    signature = IBarCodeFlowable
    klass = staticmethod(reportlab.graphics.barcode.createBarcodeDrawing)
    attrMapping = {'code': 'codeName'}


class IPluginFlowable(interfaces.IRMLDirectiveSignature):
    """Inserts a custom flowable developed in Python."""

    module = attr.Text(
        title='Module',
        description='The Python module in which the flowable is located.',
        required=True)

    function = attr.Text(
        title='Function',
        description=('The name of the factory function within the module '
                     'that returns the custom flowable.'),
        required=True)

    params = attr.TextNode(
        title='Parameters',
        description=('A list of parameters encoded as a long string.'),
        required=False)


class PluginFlowable(Flowable):
    signature = IPluginFlowable

    def process(self):
        modulePath, functionName, text = self.getAttributeValues(
            valuesOnly=True)
        module = __import__(modulePath, {}, {}, [modulePath])
        function = getattr(module, functionName)
        flowables = function(text)
        if not isinstance(flowables, (tuple, list)):
            flowables = [flowables]
        self.parent.flow += list(flowables)


class IMinimalParagraphBase(interfaces.IRMLDirectiveSignature):

    style = attr.Style(
        title='Style',
        description=('The paragraph style that is applied to the paragraph. '
                     'See the ``paraStyle`` tag for creating a paragraph '
                     'style.'),
        required=False)

    bulletText = attr.Text(
        title='Bullet Character',
        description=('The bullet character is the ASCII representation of '
                     'the symbol making up the bullet in a listing.'),
        required=False)

    dedent = attr.Integer(
        title='Dedent',
        description=('Number of characters to be removed in front of every '
                     'line of the text.'),
        required=False)


class IBold(interfaces.IRMLDirectiveSignature):
    """Renders the text inside as bold."""


class IItalic(interfaces.IRMLDirectiveSignature):
    """Renders the text inside as italic."""


class IUnderLine(interfaces.IRMLDirectiveSignature):
    """Underlines the contained text."""


class IBreak(interfaces.IRMLDirectiveSignature):
    """Inserts a line break in the paragraph."""


class IPageNumber(interfaces.IRMLDirectiveSignature):
    """Inserts the current page number into the text."""


class IParagraphBase(IMinimalParagraphBase):
    occurence.containing(
        occurence.ZeroOrMore('b', IBold),
        occurence.ZeroOrMore('i', IItalic),
        occurence.ZeroOrMore('u', IUnderLine),
        occurence.ZeroOrMore('br', IBreak,
                             condition=occurence.laterThanReportlab21),
        occurence.ZeroOrMore('pageNumber', IPageNumber)
    )


class IPreformatted(IMinimalParagraphBase):
    """A preformatted text, similar to the <pre> tag in HTML."""

    style = attr.Style(
        title='Style',
        description=('The paragraph style that is applied to the paragraph. '
                     'See the ``paraStyle`` tag for creating a paragraph '
                     'style.'),
        default=SampleStyleSheet['Code'],
        required=False)

    text = attr.RawXMLContent(
        title='Text',
        description=('The text that will be layed out.'),
        required=True)

    maxLineLength = attr.Integer(
        title='Max Line Length',
        description=('The maximum number of characters on one line.'),
        required=False)

    newLineChars = attr.Text(
        title='New Line Characters',
        description='The characters placed at the beginning of a wrapped line',
        required=False)


class Preformatted(Flowable):
    signature = IPreformatted
    klass = reportlab.platypus.Preformatted


class IXPreformatted(IParagraphBase):
    """A preformatted text that allows paragraph markup."""

    style = attr.Style(
        title='Style',
        description=('The paragraph style that is applied to the paragraph. '
                     'See the ``paraStyle`` tag for creating a paragraph '
                     'style.'),
        default=SampleStyleSheet['Normal'],
        required=False)

    text = attr.RawXMLContent(
        title='Text',
        description=('The text that will be layed out.'),
        required=True)


class XPreformatted(Flowable):
    signature = IXPreformatted
    klass = reportlab.platypus.XPreformatted


class ICodeSnippet(IXPreformatted):
    """A code snippet with text highlighting."""

    style = attr.Style(
        title='Style',
        description=('The paragraph style that is applied to the paragraph. '
                     'See the ``paraStyle`` tag for creating a paragraph '
                     'style.'),
        required=False)

    language = attr.Text(
        title='Language',
        description='The language the code snippet is written in.',
        required=False)


class CodeSnippet(XPreformatted):
    signature = ICodeSnippet

    def process(self):
        args = dict(self.getAttributeValues())
        lang = args.pop('language', None)
        args['text'] = unescape(args['text'])
        if lang is not None:
            args['text'] = pygments2xpre(args['text'], lang.lower())
        if 'style' not in args:
            args['style'] = attr._getStyle(self, 'Code')
        self.parent.flow.append(self.klass(**args))


class IParagraph(IParagraphBase, stylesheet.IBaseParagraphStyle):
    """Lays out an entire paragraph."""

    text = attr.XMLContent(
        title='Text',
        description=('The text that will be layed out.'),
        required=True)


class Paragraph(Flowable):
    signature = IParagraph
    klass = paraparser.Z3CParagraph
    defaultStyle = 'Normal'

    styleAttributes = zope.schema.getFieldNames(stylesheet.IBaseParagraphStyle)

    def processStyle(self, style):
        attrs = []
        for attrName in self.styleAttributes:
            if self.element.get(attrName) is not None:
                attrs.append(attrName)
        attrs = self.getAttributeValues(select=attrs)
        if attrs:
            style = copy.deepcopy(style)
            for name, value in attrs:
                setattr(style, name, value)
        return style

    def process(self):
        args = dict(self.getAttributeValues(ignore=self.styleAttributes))
        if 'style' not in args:
            args['style'] = attr._getStyle(self, self.defaultStyle)
        args['style'] = self.processStyle(args['style'])
        args['manager'] = attr.getManager(self)
        self.parent.flow.append(self.klass(**args))


class ITitle(IParagraph):
    """The title is a simple paragraph with a special title style."""


class Title(Paragraph):
    signature = ITitle
    defaultStyle = 'Title'


class IHeading1(IParagraph):
    """Heading 1 is a simple paragraph with a special heading 1 style."""


class Heading1(Paragraph):
    signature = IHeading1
    defaultStyle = 'Heading1'


class IHeading2(IParagraph):
    """Heading 2 is a simple paragraph with a special heading 2 style."""


class Heading2(Paragraph):
    signature = IHeading2
    defaultStyle = 'Heading2'


class IHeading3(IParagraph):
    """Heading 3 is a simple paragraph with a special heading 3 style."""


class Heading3(Paragraph):
    signature = IHeading3
    defaultStyle = 'Heading3'


class IHeading4(IParagraph):
    """Heading 4 is a simple paragraph with a special heading 4 style."""


class Heading4(Paragraph):
    signature = IHeading4
    defaultStyle = 'Heading4'


class IHeading5(IParagraph):
    """Heading 5 is a simple paragraph with a special heading 5 style."""


class Heading5(Paragraph):
    signature = IHeading5
    defaultStyle = 'Heading5'


class IHeading6(IParagraph):
    """Heading 6 is a simple paragraph with a special heading 6 style."""


class Heading6(Paragraph):
    signature = IHeading6
    defaultStyle = 'Heading6'


class ITableCell(interfaces.IRMLDirectiveSignature):
    """A table cell within a table."""

    content = attr.RawXMLContent(
        title='Content',
        description=('The content of the cell; can be text or any flowable.'),
        required=True)

    fontName = attr.Text(
        title='Font Name',
        description='The name of the font for the cell.',
        required=False)

    fontSize = attr.Measurement(
        title='Font Size',
        description='The font size for the text of the cell.',
        required=False)

    leading = attr.Measurement(
        title='Leading',
        description=('The height of a single text line. It includes '
                     'character height.'),
        required=False)

    fontColor = attr.Color(
        title='Font Color',
        description='The color in which the text will appear.',
        required=False)

    leftPadding = attr.Measurement(
        title='Left Padding',
        description='The size of the padding on the left side.',
        required=False)

    rightPadding = attr.Measurement(
        title='Right Padding',
        description='The size of the padding on the right side.',
        required=False)

    topPadding = attr.Measurement(
        title='Top Padding',
        description='The size of the padding on the top.',
        required=False)

    bottomPadding = attr.Measurement(
        title='Bottom Padding',
        description='The size of the padding on the bottom.',
        required=False)

    background = attr.Color(
        title='Background Color',
        description='The color to use as the background for the cell.',
        required=False)

    align = attr.Choice(
        title='Text Alignment',
        description='The text alignment within the cell.',
        choices=interfaces.ALIGN_TEXT_CHOICES,
        required=False)

    vAlign = attr.Choice(
        title='Vertical Alignment',
        description='The vertical alignment of the text within the cell.',
        choices=interfaces.VALIGN_TEXT_CHOICES,
        required=False)

    lineBelowThickness = attr.Measurement(
        title='Line Below Thickness',
        description='The thickness of the line below the cell.',
        required=False)

    lineBelowColor = attr.Color(
        title='Line Below Color',
        description='The color of the line below the cell.',
        required=False)

    lineBelowCap = attr.Choice(
        title='Line Below Cap',
        description='The cap at the end of the line below the cell.',
        choices=interfaces.CAP_CHOICES,
        required=False)

    lineBelowCount = attr.Integer(
        title='Line Below Count',
        description=('Describes whether the line below is a single (1) or '
                     'double (2) line.'),
        required=False)

    lineBelowDash = attr.Sequence(
        title='Line Below Dash',
        description='The dash-pattern of a line.',
        value_type=attr.Measurement(),
        default=None,
        required=False)

    lineBelowSpace = attr.Measurement(
        title='Line Below Space',
        description='The space of the line below the cell.',
        required=False)

    lineAboveThickness = attr.Measurement(
        title='Line Above Thickness',
        description='The thickness of the line above the cell.',
        required=False)

    lineAboveColor = attr.Color(
        title='Line Above Color',
        description='The color of the line above the cell.',
        required=False)

    lineAboveCap = attr.Choice(
        title='Line Above Cap',
        description='The cap at the end of the line above the cell.',
        choices=interfaces.CAP_CHOICES,
        required=False)

    lineAboveCount = attr.Integer(
        title='Line Above Count',
        description=('Describes whether the line above is a single (1) or '
                     'double (2) line.'),
        required=False)

    lineAboveDash = attr.Sequence(
        title='Line Above Dash',
        description='The dash-pattern of a line.',
        value_type=attr.Measurement(),
        default=None,
        required=False)

    lineAboveSpace = attr.Measurement(
        title='Line Above Space',
        description='The space of the line above the cell.',
        required=False)

    lineLeftThickness = attr.Measurement(
        title='Left Line Thickness',
        description='The thickness of the line left of the cell.',
        required=False)

    lineLeftColor = attr.Color(
        title='Left Line Color',
        description='The color of the line left of the cell.',
        required=False)

    lineLeftCap = attr.Choice(
        title='Line Left Cap',
        description='The cap at the end of the line left of the cell.',
        choices=interfaces.CAP_CHOICES,
        required=False)

    lineLeftCount = attr.Integer(
        title='Line Left Count',
        description=('Describes whether the left line is a single (1) or '
                     'double (2) line.'),
        required=False)

    lineLeftDash = attr.Sequence(
        title='Line Left Dash',
        description='The dash-pattern of a line.',
        value_type=attr.Measurement(),
        default=None,
        required=False)

    lineLeftSpace = attr.Measurement(
        title='Line Left Space',
        description='The space of the line left of the cell.',
        required=False)

    lineRightThickness = attr.Measurement(
        title='Right Line Thickness',
        description='The thickness of the line right of the cell.',
        required=False)

    lineRightColor = attr.Color(
        title='Right Line Color',
        description='The color of the line right of the cell.',
        required=False)

    lineRightCap = attr.Choice(
        title='Line Right Cap',
        description='The cap at the end of the line right of the cell.',
        choices=interfaces.CAP_CHOICES,
        required=False)

    lineRightCount = attr.Integer(
        title='Line Right Count',
        description=('Describes whether the right line is a single (1) or '
                     'double (2) line.'),
        required=False)

    lineRightDash = attr.Sequence(
        title='Line Right Dash',
        description='The dash-pattern of a line.',
        value_type=attr.Measurement(),
        default=None,
        required=False)

    lineRightSpace = attr.Measurement(
        title='Line Right Space',
        description='The space of the line right of the cell.',
        required=False)

    href = attr.Text(
        title='Link URL',
        description='When specified, the cell becomes a link to that URL.',
        required=False)

    destination = attr.Text(
        title='Link Destination',
        description=('When specified, the cell becomes a link to that '
                     'destination.'),
        required=False)


class TableCell(directive.RMLDirective):
    signature = ITableCell
    styleAttributesMapping = (
        ('FONTNAME', ('fontName',)),
        ('FONTSIZE', ('fontSize',)),
        ('TEXTCOLOR', ('fontColor',)),
        ('LEADING', ('leading',)),
        ('LEFTPADDING', ('leftPadding',)),
        ('RIGHTPADDING', ('rightPadding',)),
        ('TOPPADDING', ('topPadding',)),
        ('BOTTOMPADDING', ('bottomPadding',)),
        ('BACKGROUND', ('background',)),
        ('ALIGNMENT', ('align',)),
        ('VALIGN', ('vAlign',)),
        ('LINEBELOW', ('lineBelowThickness', 'lineBelowColor',
                       'lineBelowCap', 'lineBelowCount',
                       'lineBelowDash', 'lineBelowSpace')),
        ('LINEABOVE', ('lineAboveThickness', 'lineAboveColor',
                       'lineAboveCap', 'lineAboveCount',
                       'lineAboveDash', 'lineAboveSpace')),
        ('LINEBEFORE', ('lineLeftThickness', 'lineLeftColor',
                        'lineLeftCap', 'lineLeftCount',
                        'lineLeftDash', 'lineLeftSpace')),
        ('LINEAFTER', ('lineRightThickness', 'lineRightColor',
                       'lineRightCap', 'lineRightCount',
                       'lineRightDash', 'lineRightSpace')),
        ('HREF', ('href',)),
        ('DESTINATION', ('destination',)),
    )

    def processStyle(self):
        row = len(self.parent.parent.rows)
        col = len(self.parent.cols)
        for styleAction, attrNames in self.styleAttributesMapping:
            attrs = []
            for attrName in attrNames:
                if self.element.get(attrName) is not None:
                    attrs.append(attrName)
            if not attrs:
                continue
            args = self.getAttributeValues(select=attrs, valuesOnly=True)
            if args:
                self.parent.parent.style.add(
                    styleAction, [col, row], [col, row], *args)

    def process(self):
        # Produce style
        self.processStyle()
        # Produce cell data
        flow = Flow(self.element, self.parent)
        flow.process()
        content = flow.flow
        if len(content) == 0:
            content = self.getAttributeValues(
                select=('content',), valuesOnly=True)[0]
        self.parent.cols.append(content)


class ITableRow(interfaces.IRMLDirectiveSignature):
    """A table row in the block table."""
    occurence.containing(
        occurence.OneOrMore('td', ITableCell),
    )


class TableRow(directive.RMLDirective):
    signature = ITableRow
    factories = {'td': TableCell}

    def process(self):
        self.cols = []
        self.processSubDirectives()
        self.parent.rows.append(self.cols)


class ITableBulkData(interfaces.IRMLDirectiveSignature):
    """Bulk Data allows one to quickly create a table."""

    content = attr.TextNodeSequence(
        title='Content',
        description='The bulk data.',
        splitre=re.compile('\n'),
        value_type=attr.Sequence(splitre=re.compile(','),
                                 value_type=attr.Text())
    )


class TableBulkData(directive.RMLDirective):
    signature = ITableBulkData

    def process(self):
        self.parent.rows = self.getAttributeValues(valuesOnly=True)[0]


class BlockTableStyle(stylesheet.BlockTableStyle):

    def process(self):
        self.style = copy.deepcopy(self.parent.style)
        attrs = self.getAttributeValues()
        for name, value in attrs:
            setattr(self.style, name, value)
        self.processSubDirectives()
        self.parent.style = self.style


class IBlockTable(interfaces.IRMLDirectiveSignature):
    """A typical block table."""
    occurence.containing(
        occurence.ZeroOrMore('tr', ITableRow),
        occurence.ZeroOrOne('bulkData', ITableBulkData),
        occurence.ZeroOrMore('blockTableStyle', stylesheet.IBlockTableStyle),
    )

    style = attr.Style(
        title='Style',
        description=('The table style that is applied to the table. '),
        required=False)

    rowHeights = attr.Sequence(
        title='Row Heights',
        description='A list of row heights in the table.',
        value_type=attr.Measurement(),
        required=False)

    colWidths = attr.Sequence(
        title='Column Widths',
        description='A list of column widths in the table.',
        value_type=attr.Measurement(allowPercentage=True, allowStar=True),
        required=False)

    repeatRows = attr.Integer(
        title='Repeat Rows',
        description='A flag to repeat rows upon table splits.',
        required=False)

    alignment = attr.Choice(
        title='Alignment',
        description='The alignment of whole table.',
        choices=interfaces.ALIGN_TEXT_CHOICES,
        required=False)

    splitByRow = attr.Boolean(
        title='Split table between rows',
        description='Allow tables to span multiple pages',
        required=False)

    splitInRow = attr.Boolean(
        title='Split table in rows',
        description='Allow table rows to span multiple pages',
        required=False)


class BlockTable(Flowable):
    signature = IBlockTable
    klass = reportlab.platypus.Table
    factories = {
        'tr': TableRow,
        'bulkData': TableBulkData,
        'blockTableStyle': BlockTableStyle}

    def process(self):
        attrs = dict(self.getAttributeValues())
        # Get the table style; create a new one, if none is found
        style = attrs.pop('style', None)
        if style is None:
            self.style = reportlab.platypus.tables.TableStyle()
        else:
            self.style = copy.deepcopy(style)
        hAlign = attrs.pop('alignment', None)
        # Extract all table rows and cells
        self.rows = []
        self.processSubDirectives(None)
        # Create the table
        repeatRows = attrs.pop('repeatRows', None)
        table = self.klass(self.rows, style=self.style, **attrs)
        if repeatRows:
            table.repeatRows = repeatRows
        if hAlign:
            table.hAlign = hAlign
        # Must set keepWithNext on table, since the style is not stored corr.
        if hasattr(self.style, 'keepWithNext'):
            table.keepWithNext = self.style.keepWithNext
        self.parent.flow.append(table)


class INextFrame(interfaces.IRMLDirectiveSignature):
    """Switch to the next frame."""
    name = attr.StringOrInt(
        title='Name',
        description=('The name or index of the next frame.'),
        required=False)


class NextFrame(Flowable):
    signature = INextFrame
    klass = reportlab.platypus.doctemplate.FrameBreak
    attrMapping = {'name': 'ix'}


class ISetNextFrame(interfaces.IRMLDirectiveSignature):
    """Define the next frame to switch to."""
    name = attr.StringOrInt(
        title='Name',
        description=('The name or index of the next frame.'),
        required=True)


class SetNextFrame(Flowable):
    signature = INextFrame
    klass = reportlab.platypus.doctemplate.NextFrameFlowable
    attrMapping = {'name': 'ix'}


class INextPage(interfaces.IRMLDirectiveSignature):
    """Switch to the next page."""


class NextPage(Flowable):
    signature = INextPage
    klass = reportlab.platypus.PageBreak


class ISetNextTemplate(interfaces.IRMLDirectiveSignature):
    """Define the next page template to use."""
    name = attr.StringOrInt(
        title='Name',
        description='The name or index of the next page template.',
        required=True)


class SetNextTemplate(Flowable):
    signature = ISetNextTemplate
    klass = reportlab.platypus.doctemplate.NextPageTemplate
    attrMapping = {'name': 'pt'}


class IConditionalPageBreak(interfaces.IRMLDirectiveSignature):
    """Switch to the next page if not enough vertical space is available."""
    height = attr.Measurement(
        title='height',
        description='The minimal height that must be remaining on the page.',
        required=True)


class ConditionalPageBreak(Flowable):
    signature = IConditionalPageBreak
    klass = reportlab.platypus.CondPageBreak


class IKeepInFrame(interfaces.IRMLDirectiveSignature):
    """Ask a flowable to stay within the frame."""

    maxWidth = attr.Measurement(
        title='Maximum Width',
        description='The maximum width the flowables are allotted.',
        default=None,
        required=False)

    maxHeight = attr.Measurement(
        title='Maximum Height',
        description='The maximum height the flowables are allotted.',
        default=None,
        required=False)

    mergeSpace = attr.Boolean(
        title='Merge Space',
        description='A flag to set whether the space should be merged.',
        required=False)

    onOverflow = attr.Choice(
        title='On Overflow',
        description='Defines what has to be done, if an overflow is detected.',
        choices=('error', 'overflow', 'shrink', 'truncate'),
        required=False)

    id = attr.Text(
        title='Name/Id',
        description='The name/id of the flowable.',
        required=False)

    frame = attr.StringOrInt(
        title='Frame',
        description='The frame to which the flowable should be fitted.',
        required=False)


class KeepInFrame(Flowable):
    signature = IKeepInFrame
    klass = platypus.KeepInFrame
    attrMapping = {'onOverflow': 'mode', 'id': 'name'}

    def process(self):
        args = dict(self.getAttributeValues(attrMapping=self.attrMapping))
        # Circumvent broken-ness in zope.schema
        args['maxWidth'] = args.get('maxWidth', None)
        args['maxHeight'] = args.get('maxHeight', None)
        # If the frame was specifed, get us there
        frame = args.pop('frame', None)
        if frame:
            self.parent.flow.append(
                reportlab.platypus.doctemplate.FrameBreak(frame))
        # Create the content of the container
        flow = Flow(self.element, self.parent)
        flow.process()
        args['content'] = flow.flow
        # Create the keep in frame container
        frame = self.klass(**args)
        self.parent.flow.append(frame)


class IKeepTogether(interfaces.IRMLDirectiveSignature):
    """Keep the child flowables in the same frame. Add frame break when
    necessary."""

    maxHeight = attr.Measurement(
        title='Maximum Height',
        description='The maximum height the flowables are allotted.',
        default=None,
        required=False)


class KeepTogether(Flowable):
    signature = IKeepTogether
    klass = reportlab.platypus.flowables.KeepTogether

    def process(self):
        args = dict(self.getAttributeValues())

        # Create the content of the container
        flow = Flow(self.element, self.parent)
        flow.process()

        # Create the keep in frame container
        frame = self.klass(flow.flow, **args)
        self.parent.flow.append(frame)


class IImage(interfaces.IRMLDirectiveSignature):
    """An image."""

    src = attr.Image(
        title='Image Source',
        description='The file that is used to extract the image data.',
        onlyOpen=True,
        required=True)

    width = attr.Measurement(
        title='Image Width',
        description='The width of the image.',
        required=False)

    height = attr.Measurement(
        title='Image Height',
        description='The height the image.',
        required=False)

    preserveAspectRatio = attr.Boolean(
        title='Preserve Aspect Ratio',
        description=('If set, the aspect ratio of the image is kept. When '
                     'both, width and height, are specified, the image '
                     'will be fitted into that bounding box.'),
        default=False,
        required=False)

    mask = attr.Color(
        title='Mask',
        description='The color mask used to render the image, or "auto" to use'
                    ' the alpha channel if available.',
        default='auto',
        required=False,
        acceptAuto=True)

    align = attr.Choice(
        title='Alignment',
        description='The alignment of the image within the frame.',
        choices=interfaces.ALIGN_TEXT_CHOICES,
        required=False)

    vAlign = attr.Choice(
        title='Vertical Alignment',
        description='The vertical alignment of the image.',
        choices=interfaces.VALIGN_TEXT_CHOICES,
        required=False)


class Image(Flowable):
    signature = IImage
    klass = reportlab.platypus.flowables.Image
    attrMapping = {'src': 'filename', 'align': 'hAlign'}

    def process(self):
        args = dict(self.getAttributeValues(attrMapping=self.attrMapping))
        preserveAspectRatio = args.pop('preserveAspectRatio', False)
        if preserveAspectRatio:
            img = utils.ImageReader(args['filename'])
            args['filename'].seek(0)
            iw, ih = img.getSize()
            if 'width' in args and 'height' not in args:
                args['height'] = args['width'] * ih / iw
            elif 'width' not in args and 'height' in args:
                args['width'] = args['height'] * iw / ih
            elif 'width' in args and 'height' in args:
                # In this case, the width and height specify a bounding box
                # and the size of the image within that box is maximized.
                if args['width'] * ih / iw <= args['height']:
                    args['height'] = args['width'] * ih / iw
                elif args['height'] * iw / ih < args['width']:
                    args['width'] = args['height'] * iw / ih
                else:
                    # This should not happen.
                    raise ValueError('Cannot keep image in bounding box.')
            else:
                # No size was specified, so do nothing.
                pass

        vAlign = args.pop('vAlign', None)
        hAlign = args.pop('hAlign', None)
        img = self.klass(**args)
        if hAlign:
            img.hAlign = hAlign
        if vAlign:
            img.vAlign = vAlign
        self.parent.flow.append(img)


class IImageAndFlowables(interfaces.IRMLDirectiveSignature):
    """An image with flowables around it."""

    imageName = attr.Image(
        title='Image',
        description='The file that is used to extract the image data.',
        onlyOpen=True,
        required=True)

    imageWidth = attr.Measurement(
        title='Image Width',
        description='The width of the image.',
        required=False)

    imageHeight = attr.Measurement(
        title='Image Height',
        description='The height the image.',
        required=False)

    imageMask = attr.Color(
        title='Mask',
        description='The color mask used to render the image, or "auto" to use'
                    ' the alpha channel if available.',
        default='auto',
        required=False,
        acceptAuto=True)

    imageLeftPadding = attr.Measurement(
        title='Image Left Padding',
        description='The padding on the left side of the image.',
        required=False)

    imageRightPadding = attr.Measurement(
        title='Image Right Padding',
        description='The padding on the right side of the image.',
        required=False)

    imageTopPadding = attr.Measurement(
        title='Image Top Padding',
        description='The padding on the top of the image.',
        required=False)

    imageBottomPadding = attr.Measurement(
        title='Image Bottom Padding',
        description='The padding on the bottom of the image.',
        required=False)

    imageSide = attr.Choice(
        title='Image Side',
        description='The side at which the image will be placed.',
        choices=('left', 'right'),
        required=False)


class ImageAndFlowables(Flowable):
    signature = IImageAndFlowables
    klass = reportlab.platypus.flowables.ImageAndFlowables
    attrMapping = {'imageWidth': 'width', 'imageHeight': 'height',
                   'imageMask': 'mask', 'imageName': 'filename'}

    def process(self):
        flow = Flow(self.element, self.parent)
        flow.process()
        # Create the image
        args = dict(self.getAttributeValues(
            select=('imageName', 'imageWidth', 'imageHeight', 'imageMask'),
            attrMapping=self.attrMapping))
        img = reportlab.platypus.flowables.Image(**args)
        # Create the flowable and add it
        args = dict(self.getAttributeValues(
            ignore=('imageName', 'imageWidth', 'imageHeight', 'imageMask'),
            attrMapping=self.attrMapping))
        self.parent.flow.append(
            self.klass(img, flow.flow, **args))


class IIndent(interfaces.IRMLDirectiveSignature):
    """Indent the contained flowables."""

    left = attr.Measurement(
        title='Left',
        description='The indentation to the left.',
        required=False)

    right = attr.Measurement(
        title='Right',
        description='The indentation to the right.',
        required=False)


class Indent(Flowable):
    signature = IIndent

    def process(self):
        kw = dict(self.getAttributeValues())
        # Indent
        self.parent.flow.append(reportlab.platypus.doctemplate.Indenter(**kw))
        # Add Content
        flow = Flow(self.element, self.parent)
        flow.process()
        self.parent.flow += flow.flow
        # Dedent
        for name, value in kw.items():
            kw[name] = -value
        self.parent.flow.append(reportlab.platypus.doctemplate.Indenter(**kw))


class IFixedSize(interfaces.IRMLDirectiveSignature):
    """Create a container flowable of a fixed size."""

    width = attr.Measurement(
        title='Width',
        description='The width the flowables are allotted.',
        required=True)

    height = attr.Measurement(
        title='Height',
        description='The height the flowables are allotted.',
        required=True)


class FixedSize(Flowable):
    signature = IFixedSize
    klass = reportlab.platypus.flowables.KeepInFrame
    attrMapping = {'width': 'maxWidth', 'height': 'maxHeight'}

    def process(self):
        flow = Flow(self.element, self.parent)
        flow.process()
        args = dict(self.getAttributeValues(attrMapping=self.attrMapping))
        frame = self.klass(content=flow.flow, mode='shrink', **args)
        self.parent.flow.append(frame)


class IBookmarkPage(interfaces.IRMLDirectiveSignature):
    """
    This creates a bookmark to the current page which can be referred to with
    the given key elsewhere.

    PDF offers very fine grained control over how Acrobat reader is zoomed
    when people link to this. The default is to keep the user's current zoom
    settings. the last arguments may or may not be needed depending on the
    choice of 'fitType'.
    """

    name = attr.Text(
        title='Name',
        description='The name of the bookmark.',
        required=True)

    fit = attr.Choice(
        title='Fit',
        description='The Fit Type.',
        choices=('XYZ', 'Fit', 'FitH', 'FitV', 'FitR'),
        required=False)

    top = attr.Measurement(
        title='Top',
        description='The top position.',
        required=False)

    bottom = attr.Measurement(
        title='Bottom',
        description='The bottom position.',
        required=False)

    left = attr.Measurement(
        title='Left',
        description='The left position.',
        required=False)

    right = attr.Measurement(
        title='Right',
        description='The right position.',
        required=False)

    zoom = attr.Float(
        title='Zoom',
        description='The zoom level when clicking on the bookmark.',
        required=False)


class BookmarkPage(Flowable):
    signature = IBookmarkPage
    klass = platypus.BookmarkPage
    attrMapping = {'name': 'key', 'fitType': 'fit'}


class IBookmark(interfaces.IRMLDirectiveSignature):
    """
    This creates a bookmark to the current page which can be referred to with
    the given key elsewhere. (Used inside a story.)
    """

    name = attr.Text(
        title='Name',
        description='The name of the bookmark.',
        required=True)

    x = attr.Measurement(
        title='X Coordinate',
        description='The x-position of the bookmark.',
        default=0,
        required=False)

    y = attr.Measurement(
        title='Y Coordinate',
        description='The y-position of the bookmark.',
        default=0,
        required=False)


class Bookmark(Flowable):
    signature = IBookmark
    klass = platypus.Bookmark
    attrMapping = {'name': 'key', 'x': 'relativeX', 'y': 'relativeY'}


class ILink(interfaces.IRMLDirectiveSignature):
    """Place an internal link around a set of flowables."""

    destination = attr.Text(
        title='Destination',
        description='The name of the destination to link to.',
        required=False)

    url = attr.Text(
        title='URL',
        description='The URL to link to.',
        required=False)

    boxStrokeWidth = attr.Measurement(
        title='Box Stroke Width',
        description='The width of the box border line.',
        required=False)

    boxStrokeDashArray = attr.Sequence(
        title='Box Stroke Dash Array',
        description='The dash array of the box border line.',
        value_type=attr.Float(),
        required=False)

    boxStrokeColor = attr.Color(
        title='Box Stroke Color',
        description=('The color in which the box border is drawn.'),
        required=False)


class Link(Flowable):
    signature = ILink
    attrMapping = {'destination': 'destinationname',
                   'boxStrokeWidth': 'thickness',
                   'boxStrokeDashArray': 'dashArray',
                   'boxStrokeColor': 'color'}

    def process(self):
        flow = Flow(self.element, self.parent)
        flow.process()
        args = dict(self.getAttributeValues(attrMapping=self.attrMapping))
        self.parent.flow.append(platypus.Link(flow.flow, **args))


class IHorizontalRow(interfaces.IRMLDirectiveSignature):
    """Create a horizontal line on the page."""

    width = attr.Measurement(
        title='Width',
        description='The width of the line on the page.',
        allowPercentage=True,
        required=False)

    thickness = attr.Measurement(
        title='Thickness',
        description='Line Thickness',
        required=False)

    color = attr.Color(
        title='Color',
        description='The color of the line.',
        required=False)

    lineCap = attr.Choice(
        title='Cap',
        description='The cap at the end of the line.',
        choices=interfaces.CAP_CHOICES.keys(),
        required=False)

    spaceBefore = attr.Measurement(
        title='Space Before',
        description='The vertical space before the line.',
        required=False)

    spaceAfter = attr.Measurement(
        title='Space After',
        description='The vertical space after the line.',
        required=False)

    align = attr.Choice(
        title='Alignment',
        description='The alignment of the line within the frame.',
        choices=interfaces.ALIGN_TEXT_CHOICES,
        required=False)

    valign = attr.Choice(
        title='Vertical Alignment',
        description='The vertical alignment of the line.',
        choices=interfaces.VALIGN_TEXT_CHOICES,
        required=False)

    dash = attr.Sequence(
        title='Dash-Pattern',
        description='The dash-pattern of a line.',
        value_type=attr.Measurement(),
        default=None,
        required=False)


class HorizontalRow(Flowable):
    signature = IHorizontalRow
    klass = reportlab.platypus.flowables.HRFlowable
    attrMapping = {'align': 'hAlign'}


class IOutlineAdd(interfaces.IRMLDirectiveSignature):
    """Add a new entry to the outline of the PDF."""

    title = attr.TextNode(
        title='Title',
        description='The text displayed for this item.',
        required=True)

    key = attr.Text(
        title='Key',
        description='The unique key of the item.',
        required=False)

    level = attr.Integer(
        title='Level',
        description='The level in the outline tree.',
        required=False)

    closed = attr.Boolean(
        title='Closed',
        description=('A flag to determine whether the sub-tree is closed '
                     'by default.'),
        required=False)


class OutlineAdd(Flowable):
    signature = IOutlineAdd
    klass = platypus.OutlineAdd


class NamedStringFlowable(reportlab.platypus.flowables.Flowable,
                          special.TextFlowables):

    def __init__(self, manager, id, value):
        reportlab.platypus.flowables.Flowable.__init__(self)
        self.manager = manager
        self.id = id
        self._value = value
        self.value = ''

    def wrap(self, *args):
        return (0, 0)

    def draw(self):
        text = self._getText(self._value, self.manager.canvas,
                             include_final_tail=False)
        self.manager.names[self.id] = text


class INamedString(interfaces.IRMLDirectiveSignature):
    """Defines a name for a string."""

    id = attr.Text(
        title='Id',
        description='The id under which the value will be known.',
        required=True)

    value = attr.XMLContent(
        title='Value',
        description='The text that is displayed if the id is called.',
        required=True)


class NamedString(directive.RMLDirective):
    signature = INamedString

    def process(self):
        id, value = self.getAttributeValues(valuesOnly=True)
        manager = attr.getManager(self)
        # We have to delay assigning values, otherwise the last one wins.
        self.parent.flow.append(NamedStringFlowable(manager, id, self.element))


class IShowIndex(interfaces.IRMLDirectiveSignature):
    """Creates an index in the document."""

    name = attr.Text(
        title='Name',
        description='The name of the index.',
        default='index',
        required=False)

    dot = attr.Text(
        title='Dot',
        description='The character to use as a dot.',
        required=False)

    style = attr.Style(
        title='Style',
        description='The paragraph style that is applied to the index. ',
        required=False)

    tableStyle = attr.Style(
        title='Table Style',
        description='The table style that is applied to the index layout. ',
        required=False)


class ShowIndex(directive.RMLDirective):
    signature = IShowIndex

    def process(self):
        args = dict(self.getAttributeValues())
        manager = attr.getManager(self)
        index = manager.indexes[args['name']]
        args['format'] = index.formatFunc.__name__[8:]
        args['offset'] = index.offset
        index.setup(**args)
        self.parent.flow.append(index)


class IBaseLogCall(interfaces.IRMLDirectiveSignature):

    message = attr.RawXMLContent(
        title='Message',
        description='The message to be logged.',
        required=True)


class LogCallFlowable(reportlab.platypus.flowables.Flowable):

    def __init__(self, logger, level, message):
        self.logger = logger
        self.level = level
        self.message = message

    def wrap(self, *args):
        return (0, 0)

    def draw(self):
        self.logger.log(self.level, self.message)


class BaseLogCall(directive.RMLDirective):
    signature = IBaseLogCall
    level = None

    def process(self):
        message = self.getAttributeValues(
            select=('message',), valuesOnly=True)[0]
        manager = attr.getManager(self)
        self.parent.flow.append(
            LogCallFlowable(manager.logger, self.level, message))


class ILog(IBaseLogCall):
    """Log message at DEBUG level."""

    level = attr.Choice(
        title='Level',
        description='The default log level.',
        choices=interfaces.LOG_LEVELS,
        doLower=False,
        default=logging.INFO,
        required=True)


class Log(BaseLogCall):
    signature = ILog

    @property
    def level(self):
        return self.getAttributeValues(select=('level',), valuesOnly=True)[0]


class IDebug(IBaseLogCall):
    """Log message at DEBUG level."""


class Debug(BaseLogCall):
    signature = IDebug
    level = logging.DEBUG


class IInfo(IBaseLogCall):
    """Log message at INFO level."""


class Info(BaseLogCall):
    signature = IInfo
    level = logging.INFO


class IWarning(IBaseLogCall):
    """Log message at WARNING level."""


class Warning(BaseLogCall):
    signature = IWarning
    level = logging.WARNING


class IError(IBaseLogCall):
    """Log message at ERROR level."""


class Error(BaseLogCall):
    signature = IError
    level = logging.ERROR


class ICritical(IBaseLogCall):
    """Log message at CRITICAL level."""


class Critical(BaseLogCall):
    signature = ICritical
    level = logging.CRITICAL


class IFlow(interfaces.IRMLDirectiveSignature):
    """A list of flowables."""
    occurence.containing(
        occurence.ZeroOrMore('spacer', ISpacer),
        occurence.ZeroOrMore('illustration', IIllustration),
        occurence.ZeroOrMore('pre', IPreformatted),
        occurence.ZeroOrMore('xpre', IXPreformatted),
        occurence.ZeroOrMore('codesnippet', ICodeSnippet),
        occurence.ZeroOrMore('plugInFlowable', IPluginFlowable),
        occurence.ZeroOrMore('barCodeFlowable', IBarCodeFlowable),
        occurence.ZeroOrMore('outlineAdd', IOutlineAdd),
        occurence.ZeroOrMore('title', ITitle),
        occurence.ZeroOrMore('h1', IHeading1),
        occurence.ZeroOrMore('h2', IHeading2),
        occurence.ZeroOrMore('h3', IHeading3),
        occurence.ZeroOrMore('h4', IHeading4),
        occurence.ZeroOrMore('h5', IHeading5),
        occurence.ZeroOrMore('h6', IHeading6),
        occurence.ZeroOrMore('para', IParagraph),
        occurence.ZeroOrMore('blockTable', IBlockTable),
        occurence.ZeroOrMore('nextFrame', INextFrame),
        occurence.ZeroOrMore('setNextFrame', ISetNextFrame),
        occurence.ZeroOrMore('nextPage', INextPage),
        occurence.ZeroOrMore('setNextTemplate', ISetNextTemplate),
        occurence.ZeroOrMore('condPageBreak', IConditionalPageBreak),
        occurence.ZeroOrMore('keepInFrame', IKeepInFrame),
        occurence.ZeroOrMore('keepTogether', IKeepTogether),
        occurence.ZeroOrMore('img', IImage),
        occurence.ZeroOrMore('imageAndFlowables', IImageAndFlowables),
        occurence.ZeroOrMore('indent', IIndent),
        occurence.ZeroOrMore('fixedSize', IFixedSize),
        occurence.ZeroOrMore('bookmarkPage', IBookmarkPage),
        occurence.ZeroOrMore('bookmark', IBookmark),
        occurence.ZeroOrMore('link', ILink),
        occurence.ZeroOrMore('hr', IHorizontalRow),
        occurence.ZeroOrMore('showIndex', IShowIndex),
        occurence.ZeroOrMore('name', special.IName),
        occurence.ZeroOrMore('namedString', INamedString),
        occurence.ZeroOrMore('log', ILog),
        occurence.ZeroOrMore('debug', IDebug),
        occurence.ZeroOrMore('info', IInfo),
        occurence.ZeroOrMore('warning', IWarning),
        occurence.ZeroOrMore('error', IError),
        occurence.ZeroOrMore('critical', ICritical),
    )


class ITopPadder(interfaces.IRMLDirectiveSignature):
    """
    TopPadder
    """


class TopPadder(Flowable):
    signature = ITopPadder
    klass = reportlab.platypus.flowables.TopPadder
    attrMapping = {}

    def process(self):
        flow = Flow(self.element, self.parent)
        flow.process()
        frame = self.klass(flow.flow[0])
        self.parent.flow.append(frame)


class Flow(directive.RMLDirective):

    factories = {
        # Generic Flowables
        'spacer': Spacer,
        'illustration': Illustration,
        'pre': Preformatted,
        'xpre': XPreformatted,
        'codesnippet': CodeSnippet,
        'plugInFlowable': PluginFlowable,
        'barCodeFlowable': BarCodeFlowable,
        'outlineAdd': OutlineAdd,
        # Paragraph-Like Flowables
        'title': Title,
        'h1': Heading1,
        'h2': Heading2,
        'h3': Heading3,
        'h4': Heading4,
        'h5': Heading5,
        'h6': Heading6,
        'para': Paragraph,
        # Table Flowable
        'blockTable': BlockTable,
        # Page-level Flowables
        'nextFrame': NextFrame,
        'setNextFrame': SetNextFrame,
        'nextPage': NextPage,
        'setNextTemplate': SetNextTemplate,
        'condPageBreak': ConditionalPageBreak,
        'keepInFrame': KeepInFrame,
        'keepTogether': KeepTogether,
        'img': Image,
        'imageAndFlowables': ImageAndFlowables,
        'indent': Indent,
        'fixedSize': FixedSize,
        'bookmarkPage': BookmarkPage,
        'bookmark': Bookmark,
        'link': Link,
        'hr': HorizontalRow,
        'showIndex': ShowIndex,
        # Special Elements
        'name': special.Name,
        'namedString': NamedString,
        # Logging
        'log': Log,
        'debug': Debug,
        'info': Info,
        'warning': Warning,
        'error': Error,
        'critical': Critical,
        'topPadder': TopPadder,
    }

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.flow = []

    def process(self):
        self.processSubDirectives()
        return self.flow


class IPTOHeader(IFlow):
    """A container for flowables used at the beginning of a frame.
    """


class PTOHeader(Flow):

    def process(self):
        self.parent.header = super().process()


class IPTOTrailer(IFlow):
    """A container for flowables used at the end of a frame.
    """


class PTOTrailer(Flow):

    def process(self):
        self.parent.trailer = super().process()


class IPTO(IFlow):
    """A container for flowables decorated with trailer & header lists.

    If the split operation would be called then the trailer and header
    lists are injected before and after the split. This allows specialist
    "please turn over" and "continued from previous" like behaviours.
    """
    occurence.containing(
        occurence.ZeroOrOne('pto_header', IPTOHeader),
        occurence.ZeroOrOne('pto_trailer', IPTOTrailer),
    )


class PTO(Flow):
    signature = IPTO
    klass = reportlab.platypus.flowables.PTOContainer

    factories = dict(
        pto_header=PTOHeader,
        pto_trailer=PTOTrailer,
        **Flow.factories
    )

    header = None
    trailer = None

    def process(self):
        flow = super().process()
        self.parent.flow.append(
            self.klass(flow, self.trailer, self.header))
