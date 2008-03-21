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

$Id$
"""
__docformat__ = "reStructuredText"
import copy
import re
import reportlab.lib.styles
import reportlab.platypus
import reportlab.platypus.doctemplate
import reportlab.platypus.flowables
import reportlab.platypus.tables
import zope.schema
from reportlab.lib import styles
from z3c.rml import attr, directive, interfaces, occurence
from z3c.rml import form, platypus, special, stylesheet

try:
    import reportlab.graphics.barcode
except ImportError:
    # barcode package has not been installed
    import types
    import reportlab.graphics
    reportlab.graphics.barcode = types.ModuleType('barcode')
    reportlab.graphics.barcode.createBarcodeDrawing = None

class Flowable(directive.RMLDirective):
    klass=None
    attrMapping = None

    def process(self):
        args = dict(self.getAttributeValues(attrMapping=self.attrMapping))
        self.parent.flow.append(self.klass(**args))

class ISpacer(interfaces.IRMLDirectiveSignature):
    """Creates a vertical space in the flow."""

    width = attr.Measurement(
        title=u'Width',
        description=u'The width of the spacer. Currently not implemented.',
        default=100,
        required=False)

    length = attr.Measurement(
        title=u'Length',
        description=u'The height of the spacer.',
        required=True)

class Spacer(Flowable):
    signature = ISpacer
    klass = reportlab.platypus.Spacer
    attrMapping = {'length': 'height'}


class IIllustration(interfaces.IRMLDirectiveSignature):
    """Inserts an illustration with graphics elements."""

    width = attr.Measurement(
        title=u'Width',
        description=u'The width of the illustration.',
        required=True)

    height = attr.Measurement(
        title=u'Height',
        description=u'The height of the illustration.',
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

    value = attr.String(
        title=u'Value',
        description=u'The value represented by the code.',
        required=True)

class BarCodeFlowable(Flowable):
    signature = IBarCodeFlowable
    klass = staticmethod(reportlab.graphics.barcode.createBarcodeDrawing)
    attrMapping = {'code': 'codeName'}

class IPluginFlowable(interfaces.IRMLDirectiveSignature):
    """Inserts a custom flowable developed in Python."""

    module = attr.String(
        title=u'Module',
        description=u'The Python module in which the flowable is located.',
        required=True)

    function = attr.String(
        title=u'Function',
        description=(u'The name of the factory function within the module '
                     u'that returns the custom flowable.'),
        required=True)

    params = attr.TextNode(
        title=u'Parameters',
        description=(u'A list of parameters encoded as a long string.'),
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
        title=u'Style',
        description=(u'The paragraph style that is applied to the paragraph. '
                     u'See the ``paraStyle`` tag for creating a paragraph '
                     u'style.'),
        default=reportlab.lib.styles.getSampleStyleSheet()['Normal'],
        required=True)

    bulletText = attr.String(
        title=u'Bullet Character',
        description=(u'The bullet character is the ASCII representation of '
                     u'the symbol making up the bullet in a listing.'),
        required=False)

    dedent = attr.Integer(
        title=u'Dedent',
        description=(u'Number of characters to be removed in front of every '
                     u'line of the text.'),
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

    text = attr.RawXMLContent(
        title=u'Text',
        description=(u'The text that will be layed out.'),
        required=True)

class Preformatted(Flowable):
    signature = IPreformatted
    klass = reportlab.platypus.Preformatted


class IXPreformatted(IParagraphBase):
    """A preformatted text that allows paragraph markup."""

    text = attr.RawXMLContent(
        title=u'Text',
        description=(u'The text that will be layed out.'),
        required=True)

class XPreformatted(Flowable):
    signature = IXPreformatted
    klass = reportlab.platypus.XPreformatted


class IParagraph(IParagraphBase, stylesheet.IBaseParagraphStyle):
    """Lays out an entire paragraph."""

    text = attr.XMLContent(
        title=u'Text',
        description=(u'The text that will be layed out.'),
        required=True)

class Paragraph(Flowable):
    signature = IParagraph
    klass = reportlab.platypus.Paragraph

    styleAttributes = zope.schema.getFieldNames(stylesheet.IBaseParagraphStyle)

    def processStyle(self, style):
        attrs = self.getAttributeValues(select=self.styleAttributes)
        if attrs:
            style = copy.deepcopy(style)
            for name, value in attrs:
                setattr(style, name, value)
        return style

    def process(self):
        args = dict(self.getAttributeValues(ignore=self.styleAttributes))
        args['style'] = self.processStyle(args['style'])
        self.parent.flow.append(self.klass(**args))


class ITitle(IParagraph):
    """The title is a simple paragraph with a special title style."""

    style = attr.Style(
        title=u'Style',
        description=(u'The paragraph style that is applied to the paragraph. '
                     u'See the ``paraStyle`` tag for creating a paragraph '
                     u'style.'),
        default=reportlab.lib.styles.getSampleStyleSheet()['Title'],
        required=True)

class Title(Paragraph):
    signature = ITitle


class IHeading1(IParagraph):
    """Heading 1 is a simple paragraph with a special heading 1 style."""

    style = attr.Style(
        title=u'Style',
        description=(u'The paragraph style that is applied to the paragraph. '
                     u'See the ``paraStyle`` tag for creating a paragraph '
                     u'style.'),
        default=reportlab.lib.styles.getSampleStyleSheet()['Heading1'],
        required=True)

class Heading1(Paragraph):
    signature = IHeading1


class IHeading2(IParagraph):
    """Heading 2 is a simple paragraph with a special heading 2 style."""

    style = attr.Style(
        title=u'Style',
        description=(u'The paragraph style that is applied to the paragraph. '
                     u'See the ``paraStyle`` tag for creating a paragraph '
                     u'style.'),
        default=reportlab.lib.styles.getSampleStyleSheet()['Heading2'],
        required=True)

class Heading2(Paragraph):
    signature = IHeading2


class IHeading3(IParagraph):
    """Heading 3 is a simple paragraph with a special heading 3 style."""

    style = attr.Style(
        title=u'Style',
        description=(u'The paragraph style that is applied to the paragraph. '
                     u'See the ``paraStyle`` tag for creating a paragraph '
                     u'style.'),
        default=reportlab.lib.styles.getSampleStyleSheet()['Heading3'],
        required=True)

class Heading3(Paragraph):
    signature = IHeading3


class ITableCell(interfaces.IRMLDirectiveSignature):
    """A table cell within a table."""

    content = attr.RawXMLContent(
        title=u'Content',
        description=(u'The content of the cell; can be text or any flowable.'),
        required=True)

    fontName = attr.String(
        title=u'Font Name',
        description=u'The name of the font for the cell.',
        required=False)

    fontSize = attr.Measurement(
        title=u'Font Size',
        description=u'The font size for the text of the cell.',
        required=False)

    leading = attr.Measurement(
        title=u'Leading',
        description=(u'The height of a single text line. It includes '
                     u'character height.'),
        required=False)

    fontColor = attr.Color(
        title=u'Font Color',
        description=u'The color in which the text will appear.',
        required=False)

    leftPadding = attr.Measurement(
        title=u'Left Padding',
        description=u'The size of the padding on the left side.',
        required=False)

    rightPadding = attr.Measurement(
        title=u'Right Padding',
        description=u'The size of the padding on the right side.',
        required=False)

    topPadding = attr.Measurement(
        title=u'Top Padding',
        description=u'The size of the padding on the top.',
        required=False)

    bottomPadding = attr.Measurement(
        title=u'Bottom Padding',
        description=u'The size of the padding on the bottom.',
        required=False)

    background = attr.Color(
        title=u'Background Color',
        description=u'The color to use as the background for the cell.',
        required=False)

    align = attr.Choice(
        title=u'Text Alignment',
        description=u'The text alignment within the cell.',
        choices=interfaces.ALIGN_TEXT_CHOICES,
        required=False)

    vAlign = attr.Choice(
        title=u'Vertical Alignment',
        description=u'The vertical alignment of the text within the cell.',
        choices=interfaces.VALIGN_TEXT_CHOICES,
        required=False)

    lineBelowThickness = attr.Measurement(
        title=u'Line Below Thickness',
        description=u'The thickness of the line below the cell.',
        required=False)

    lineBelowColor = attr.Color(
        title=u'Line Below Color',
        description=u'The color of the line below the cell.',
        required=False)

    lineBelowCap = attr.Choice(
        title=u'Line Below Cap',
        description=u'The cap at the end of the line below the cell.',
        choices=interfaces.CAP_CHOICES,
        required=False)

    lineBelowCount = attr.Integer(
        title=u'Line Below Count',
        description=(u'Describes whether the line below is a single (1) or '
                     u'double (2) line.'),
        required=False)

    lineBelowSpace = attr.Measurement(
        title=u'Line Below Space',
        description=u'The space of the line below the cell.',
        required=False)

    lineAboveThickness = attr.Measurement(
        title=u'Line Above Thickness',
        description=u'The thickness of the line above the cell.',
        required=False)

    lineAboveColor = attr.Color(
        title=u'Line Above Color',
        description=u'The color of the line above the cell.',
        required=False)

    lineAboveCap = attr.Choice(
        title=u'Line Above Cap',
        description=u'The cap at the end of the line above the cell.',
        choices=interfaces.CAP_CHOICES,
        required=False)

    lineAboveCount = attr.Integer(
        title=u'Line Above Count',
        description=(u'Describes whether the line above is a single (1) or '
                     u'double (2) line.'),
        required=False)

    lineAboveSpace = attr.Measurement(
        title=u'Line Above Space',
        description=u'The space of the line above the cell.',
        required=False)

    lineLeftThickness = attr.Measurement(
        title=u'Left Line Thickness',
        description=u'The thickness of the line left of the cell.',
        required=False)

    lineLeftColor = attr.Color(
        title=u'Left Line Color',
        description=u'The color of the line left of the cell.',
        required=False)

    lineLeftCap = attr.Choice(
        title=u'Line Left Cap',
        description=u'The cap at the end of the line left of the cell.',
        choices=interfaces.CAP_CHOICES,
        required=False)

    lineLeftCount = attr.Integer(
        title=u'Line Left Count',
        description=(u'Describes whether the left line is a single (1) or '
                     u'double (2) line.'),
        required=False)

    lineLeftSpace = attr.Measurement(
        title=u'Line Left Space',
        description=u'The space of the line left of the cell.',
        required=False)

    lineRightThickness = attr.Measurement(
        title=u'Right Line Thickness',
        description=u'The thickness of the line right of the cell.',
        required=False)

    lineRightColor = attr.Color(
        title=u'Right Line Color',
        description=u'The color of the line right of the cell.',
        required=False)

    lineRightCap = attr.Choice(
        title=u'Line Right Cap',
        description=u'The cap at the end of the line right of the cell.',
        choices=interfaces.CAP_CHOICES,
        required=False)

    lineRightCount = attr.Integer(
        title=u'Line Right Count',
        description=(u'Describes whether the right line is a single (1) or '
                     u'double (2) line.'),
        required=False)

    lineRightSpace = attr.Measurement(
        title=u'Line Right Space',
        description=u'The space of the line right of the cell.',
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
                       'lineBelowCap', 'lineBelowCount', 'lineBelowSpace')),
        ('LINEABOVE', ('lineAboveThickness', 'lineAboveColor',
                       'lineAboveCap', 'lineAboveCount', 'lineAboveSpace')),
        ('LINEBEFORE', ('lineLeftThickness', 'lineLeftColor',
                        'lineLeftCap', 'lineLeftCount', 'lineLeftSpace')),
        ('LINEAFTER', ('lineRightThickness', 'lineRightColor',
                       'lineRightCap', 'lineRightCount', 'lineRightSpace')),
        )

    def processStyle(self):
        row = len(self.parent.parent.rows)
        col = len(self.parent.cols)
        for styleAction, attrNames in self.styleAttributesMapping:
            args = self.getAttributeValues(select=attrNames, valuesOnly=True)
            if args or len(attrNames) == 0:
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
        title=u'Content',
        description=u'The bulk data.',
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
        title=u'Style',
        description=(u'The table style that is applied to the table. '),
        required=False)

    rowHeights = attr.Sequence(
        title=u'Row Heights',
        description=u'A list of row heights in the table.',
        value_type=attr.Measurement(),
        required=False)

    colWidths = attr.Sequence(
        title=u'Column Widths',
        description=u'A list of column widths in the table.',
        value_type=attr.Measurement(allowPercentage=True, allowStar=True),
        required=False)

    repeatRows = attr.Integer(
        title=u'Repeat Rows',
        description=u'A flag to repeat rows upon table splits.',
        required=False)

    alignment = attr.Choice(
        title=u'Alignment',
        description=u'The alignment of whole table.',
        choices=interfaces.ALIGN_TEXT_CHOICES,
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
        self.style = attrs.pop('style', None)
        if self.style is None:
            self.style = reportlab.platypus.tables.TableStyle()
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
        title=u'Name',
        description=(u'The name or index of the next frame.'),
        required=False)

class NextFrame(Flowable):
    signature = INextFrame
    klass = reportlab.platypus.doctemplate.FrameBreak
    attrMapping = {'name': 'ix'}


class ISetNextFrame(interfaces.IRMLDirectiveSignature):
    """Define the next frame to switch to."""
    name = attr.StringOrInt(
        title=u'Name',
        description=(u'The name or index of the next frame.'),
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
        title=u'Name',
        description=u'The name or index of the next page template.',
        required=True)

class SetNextTemplate(Flowable):
    signature = ISetNextTemplate
    klass = reportlab.platypus.doctemplate.NextPageTemplate
    attrMapping = {'name': 'pt'}


class IConditionalPageBreak(interfaces.IRMLDirectiveSignature):
    """Switch to the next page if not enough vertical space is available."""
    height = attr.Measurement(
        title=u'height',
        description=u'The minimal height that must be remaining on the page.',
        required=True)

class ConditionalPageBreak(Flowable):
    signature = IConditionalPageBreak
    klass = reportlab.platypus.CondPageBreak


class IKeepInFrame(interfaces.IRMLDirectiveSignature):
    """Ask a flowable to stay within the frame."""

    maxWidth = attr.Measurement(
        title=u'Maximum Width',
        description=u'The maximum width the flowables are allotted.',
        default=None,
        required=False)

    maxHeight = attr.Measurement(
        title=u'Maximum Height',
        description=u'The maximum height the flowables are allotted.',
        default=None,
        required=False)

    mergeSpace = attr.Boolean(
        title=u'Merge Space',
        description=u'A flag to set whether the space should be merged.',
        required=False)

    onOverflow = attr.Choice(
        title=u'On Overflow',
        description=u'Defines what has to be done, if an overflow is detected.',
        choices=('error', 'overflow', 'shrink', 'truncate'),
        required=False)

    id = attr.Text(
        title=u'Name/Id',
        description=u'The name/id of the flowable.',
        required=False)

    frame = attr.StringOrInt(
        title=u'Frame',
        description=u'The frame to which the flowable should be fitted.',
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
        title=u'Maximum Height',
        description=u'The maximum height the flowables are allotted.',
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

class IImageAndFlowables(interfaces.IRMLDirectiveSignature):
    """An image with flowables around it."""

    imageName = attr.Image(
        title=u'Image',
        description=u'The file that is used to extract the image data.',
        onlyOpen=True,
        required=True)

    imageWidth = attr.Measurement(
        title=u'Image Width',
        description=u'The width of the image.',
        required=False)

    imageHeight = attr.Measurement(
        title=u'Image Height',
        description=u'The height the image.',
        required=False)

    imageMask = attr.Color(
        title=u'Mask',
        description=u'The height the image.',
        required=False)

    imageLeftPadding = attr.Measurement(
        title=u'Image Left Padding',
        description=u'The padding on the left side of the image.',
        required=False)

    imageRightPadding = attr.Measurement(
        title=u'Image Right Padding',
        description=u'The padding on the right side of the image.',
        required=False)

    imageTopPadding = attr.Measurement(
        title=u'Image Top Padding',
        description=u'The padding on the top of the image.',
        required=False)

    imageBottomPadding = attr.Measurement(
        title=u'Image Bottom Padding',
        description=u'The padding on the bottom of the image.',
        required=False)

    imageSide = attr.Choice(
        title=u'Image Side',
        description=u'The side at which the image will be placed.',
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


class IPTO(interfaces.IRMLDirectiveSignature):
    '''A container for flowables decorated with trailer & header lists.
    If the split operation would be called then the trailer and header
    lists are injected before and after the split. This allows specialist
    "please turn over" and "continued from previous" like behaviours.'''

class PTO(Flowable):
    signature = IPTO
    klass = reportlab.platypus.flowables.PTOContainer

    def process(self):
        # Get Content
        flow = Flow(self.element, self.parent)
        flow.process()
        # Get the header
        ptoHeader = self.element.find('pto_header')
        header = None
        if ptoHeader is not None:
            header = Flow(ptoHeader, self.parent)
            header.process()
            header = header.flow
        # Get the trailer
        ptoTrailer = self.element.find('pto_trailer')
        trailer = None
        if ptoTrailer is not None:
            trailer = Flow(ptoTrailer, self.parent)
            trailer.process()
            trailer = trailer.flow
        # Create and add the PTO Container
        self.parent.flow.append(self.klass(flow.flow, trailer, header))


class IIndent(interfaces.IRMLDirectiveSignature):
    """Indent the contained flowables."""

    left = attr.Measurement(
        title=u'Left',
        description=u'The indentation to the left.',
        required=False)

    right = attr.Measurement(
        title=u'Right',
        description=u'The indentation to the right.',
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
        title=u'Width',
        description=u'The width the flowables are allotted.',
        required=True)

    height = attr.Measurement(
        title=u'Height',
        description=u'The height the flowables are allotted.',
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


class IBookmark(interfaces.IRMLDirectiveSignature):
    """
    This creates a bookmark to the current page which can be referred to with
    the given key elsewhere.

    PDF offers very fine grained control over how Acrobat reader is zoomed
    when people link to this. The default is to keep the user's current zoom
    settings. the last arguments may or may not be needed depending on the
    choice of 'fitType'.
    """

    name = attr.Text(
        title=u'Name',
        description=u'The name of the bookmark.',
        required=True)

    fitType = attr.Choice(
        title=u'Fit Type',
        description=u'The Fit Type.',
        choices=('Fit', 'FitH', 'FitV', 'FitR'),
        required=False)

    left = attr.Measurement(
        title=u'Left',
        description=u'The left position.',
        required=False)

    right = attr.Measurement(
        title=u'Right',
        description=u'The right position.',
        required=False)

    top = attr.Measurement(
        title=u'Top',
        description=u'The top position.',
        required=False)

    right = attr.Measurement(
        title=u'Right',
        description=u'The right position.',
        required=False)

    zoom = attr.Float(
        title=u'Zoom',
        description=u'The zoom level when clicking on the bookmark.',
        required=False)

class Bookmark(Flowable):
    signature = IBookmark
    klass = platypus.BookmarkPage
    attrMapping = {'name': 'key', 'fitType': 'fit'}


class ILink(interfaces.IRMLDirectiveSignature):
    """Place an internal link around a set of flowables."""

    destination = attr.Text(
        title=u'Destination',
        description=u'The name of the destination to link to.',
        required=False)

    url = attr.Text(
        title=u'URL',
        description=u'The URL to link to.',
        required=False)

    boxStrokeWidth = attr.Measurement(
        title=u'Box Stroke Width',
        description=u'The width of the box border line.',
        required=False)

    boxStrokeDashArray = attr.Sequence(
        title=u'Box Stroke Dash Array',
        description=u'The dash array of the box border line.',
        value_type=attr.Float(),
        required=False)

    boxStrokeColor = attr.Color(
        title=u'Box Stroke Color',
        description=(u'The color in which the box border is drawn.'),
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
        title=u'Width',
        description=u'The width of the line on the page.',
        allowPercentage=True,
        required=False)

    thickness = attr.Measurement(
        title=u'Thickness',
        description=u'Line Thickness',
        required=False)

    color = attr.Color(
        title=u'Color',
        description=u'The color of the line.',
        required=False)

    lineCap = attr.Choice(
        title=u'Cap',
        description=u'The cap at the end of the line.',
        choices=interfaces.CAP_CHOICES.keys(),
        required=False)

    spaceBefore = attr.Measurement(
        title=u'Space Before',
        description=u'The vertical space before the line.',
        required=False)

    spaceAfter = attr.Measurement(
        title=u'Space After',
        description=u'The vertical space after the line.',
        required=False)

    align = attr.Choice(
        title=u'Alignment',
        description=u'The alignment of the line within the frame.',
        choices=interfaces.ALIGN_TEXT_CHOICES,
        required=False)

    valign = attr.Choice(
        title=u'Vertical Alignment',
        description=u'The vertical alignment of the line.',
        choices=interfaces.VALIGN_TEXT_CHOICES,
        required=False)

    dash = attr.Sequence(
        title=u'Dash-Pattern',
        description=u'The dash-pattern of a line.',
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
        title=u'Title',
        description=u'The text displayed for this item.',
        required=True)

    key = attr.String(
        title=u'Key',
        description=u'The unique key of the item.',
        required=False)

    level = attr.Integer(
        title=u'Level',
        description=u'The level in the outline tree.',
        required=False)

    closed = attr.Boolean(
        title=u'Closed',
        description=(u'A flag to determine whether the sub-tree is closed '
                     u'by default.'),
        required=False)


class OutlineAdd(Flowable):
    signature = IOutlineAdd
    klass = platypus.OutlineAdd


class IFlow(interfaces.IRMLDirectiveSignature):
    """A list of flowables."""
    occurence.containing(
        occurence.ZeroOrMore('spacer', ISpacer),
        occurence.ZeroOrMore('illustration', IIllustration),
        occurence.ZeroOrMore('pre', IPreformatted),
        occurence.ZeroOrMore('xpre', IXPreformatted),
        occurence.ZeroOrMore('plugInFlowable', IPluginFlowable),
        occurence.ZeroOrMore('barCodeFlowable', IBarCodeFlowable),
        occurence.ZeroOrMore('outlineAdd', IOutlineAdd),
        occurence.ZeroOrMore('title', ITitle),
        occurence.ZeroOrMore('h1', IHeading1),
        occurence.ZeroOrMore('h2', IHeading2),
        occurence.ZeroOrMore('h3', IHeading3),
        occurence.ZeroOrMore('para', IParagraph),
        occurence.ZeroOrMore('blockTable', IBlockTable),
        occurence.ZeroOrMore('nextFrame', INextFrame),
        occurence.ZeroOrMore('setNextFrame', ISetNextFrame),
        occurence.ZeroOrMore('nextPage', INextPage),
        occurence.ZeroOrMore('setNextTemplate', ISetNextTemplate),
        occurence.ZeroOrMore('condPageBreak', IConditionalPageBreak),
        occurence.ZeroOrMore('keepInFrame', IKeepInFrame),
        occurence.ZeroOrMore('keepTogether', IKeepTogether),
        occurence.ZeroOrMore('imageAndFlowables', IImageAndFlowables),
        occurence.ZeroOrMore('pto', IPTO),
        occurence.ZeroOrMore('indent', IIndent),
        occurence.ZeroOrMore('fixedSize', IFixedSize),
        occurence.ZeroOrMore('bookmark', IBookmark),
        occurence.ZeroOrMore('link', ILink),
        occurence.ZeroOrMore('hr', IHorizontalRow),
        occurence.ZeroOrMore('name', special.IName),
        )

class Flow(directive.RMLDirective):

    factories = {
        # Generic Flowables
        'spacer': Spacer,
        'illustration': Illustration,
        'pre': Preformatted,
        'xpre': XPreformatted,
        'plugInFlowable': PluginFlowable,
        'barCodeFlowable': BarCodeFlowable,
        'outlineAdd': OutlineAdd,
        # Paragraph-Like Flowables
        'title': Title,
        'h1': Heading1,
        'h2': Heading2,
        'h3': Heading3,
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
        'imageAndFlowables': ImageAndFlowables,
        'pto': PTO,
        'indent': Indent,
        'fixedSize': FixedSize,
        'bookmark': Bookmark,
        'link': Link,
        'hr': HorizontalRow,
        # Special Elements
        'name': special.Name,
        }

    def __init__(self, *args, **kw):
        super(Flow, self).__init__(*args, **kw)
        self.flow = []

    def process(self):
        self.processSubDirectives()
        return self.flow
