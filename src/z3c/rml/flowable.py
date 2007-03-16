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
import reportlab.platypus
import reportlab.platypus.doctemplate
import reportlab.platypus.flowables
import reportlab.platypus.tables
from reportlab.lib import styles
from z3c.rml import attr, element, form, platypus, special

try:
    import reportlab.graphics.barcode
except ImportError:
    # barcode package has not been installed
    import reportlab.graphics
    reportlab.graphics.barcode = types.ModuleType('barcode')
    reportlab.graphics.barcode.getCodeNames = lambda : ()

class Flowable(element.FunctionElement):
    klass=None

    def process(self):
        args = self.getPositionalArguments()
        kw = self.getKeywordArguments()
        self.parent.flow.append(self.klass(*args, **kw))


class Spacer(Flowable):
    klass = reportlab.platypus.Spacer
    args = ( attr.Measurement('width', 100), attr.Measurement('length'), )


class Illustration(Flowable):
    klass = platypus.Illustration
    args = ( attr.Measurement('width'), attr.Measurement('height', 100))

    def process(self):
        args = self.getPositionalArguments()
        self.parent.flow.append(self.klass(self, *args))

class BarCodeFlowable(Flowable):
    klass = staticmethod(reportlab.graphics.barcode.createBarcodeDrawing)
    args = form.BarCode.args[:-1]
    kw = form.BarCode.kw[2:] + ( ('value', attr.Attribute('value')), )

class Preformatted(Flowable):
    klass = reportlab.platypus.Preformatted
    args = ( attr.RawXMLContent(u''), attr.Style('style', 'para', 'Normal') )

class XPreformatted(Flowable):
    klass = reportlab.platypus.XPreformatted
    args = ( attr.RawXMLContent(u''), attr.Style('style', 'para', 'Normal') )

class PluginFlowable(Flowable):
    args = ( attr.Text('module'), attr.Text('function'), attr.TextNode())

    def process(self):
        modulePath, functionName, text = self.getPositionalArguments()
        module = __import__(modulePath, {}, {}, [modulePath])
        function = getattr(module, functionName)
        self.parent.flow.append(function(text))

class Paragraph(Flowable):
    klass = reportlab.platypus.Paragraph
    args = ( attr.XMLContent(u''), attr.Style('style', 'para', 'Normal') )
    kw = ( ('bulletText', attr.Attribute('bulletText')), )

class Title(Paragraph):
    args = ( attr.XMLContent(u''), attr.Style('style', 'para', 'Title'), )

class Heading1(Paragraph):
    args = ( attr.XMLContent(u''), attr.Style('style', 'para', 'Heading1'), )

class Heading2(Paragraph):
    args = ( attr.XMLContent(u''), attr.Style('style', 'para', 'Heading2'), )

class Heading3(Paragraph):
    args = ( attr.XMLContent(u''), attr.Style('style', 'para', 'Heading3'), )

class TableCell(element.Element):

    styleAttrs = (
        ('FONTNAME', (attr.Text('fontName'),)),
        ('FONTSIZE', (attr.Measurement('fontSize'),)),
        ('LEADING', (attr.Measurement('leading'),)),
        ('LEFTPADDING', (attr.Measurement('leftPadding'),)),
        ('RIGHTPADDING', (attr.Measurement('rightPadding'),)),
        ('TOPPADDING', (attr.Measurement('topPadding'),)),
        ('BOTTOMPADDING', (attr.Measurement('bottomPadding'),)),
        ('BACKGROUND', (attr.Color('background'),)),
        ('ALIGNMENT', (attr.Choice('align',
                           {'left': 'LEFT', 'right': 'RIGHT',
                            'center': 'CENTER', 'decimal': 'DECIMAL'}),)),
        ('VALIGN', (attr.Choice('vAlign',
                        {'top': 'TOP', 'middle': 'MIDDLE',
                         'bottom': 'BOTTOM'}), )),
        ('LINEBELOW', (attr.Measurement('lineBelowThickness'),
                       attr.Color('lineBelowColor'),
                       attr.Choice('lineBelowCap',
                                   {'butt': 0, 'round': 1, 'square': 2}),
                       attr.Int('lineBelowCount'),
                       attr.Measurement('lineBelowSpace'))),
        ('LINEABOVE', (attr.Measurement('lineAboveThickness'),
                       attr.Color('lineAboveColor'),
                       attr.Choice('lineAboveCap',
                                   {'butt': 0, 'round': 1, 'square': 2}),
                       attr.Int('lineAboveCount'),
                       attr.Measurement('lineAboveSpace'))),
        ('LINEBEFORE', (attr.Measurement('lineLeftThickness'),
                        attr.Color('lineLeftColor'),
                        attr.Choice('lineLeftCap',
                                    {'butt': 0, 'round': 1, 'square': 2}),
                        attr.Int('lineLeftCount'),
                        attr.Measurement('lineLeftSpace'))),
        ('LINEAFTER', (attr.Measurement('lineRightThickness'),
                       attr.Color('lineRightColor'),
                       attr.Choice('lineRightCap',
                                   {'butt': 0, 'round': 1, 'square': 2}),
                       attr.Int('lineRightCount'),
                       attr.Measurement('lineRightSpace'))),
        )

    def processStyle(self):
        row = len(self.parent.parent.rows)
        col = len(self.parent.cols)
        for styleName, attrs in self.styleAttrs:
            args = []
            for attribute in attrs:
                value = attribute.get(self.element)
                if value is not attr.DEFAULT:
                    args.append(value)
            if args or len(attrs) == 0:
                self.parent.parent.style.add(
                    styleName, [col, row], [col, row], *args)
    def process(self):
        # Produce style
        self.processStyle()
        # Produce cell data
        flow = Flow(self.element, self.parent, self.context)
        flow.process()
        content = flow.flow
        if len(content) == 0:
            content = attr.TextNode().get(self.element)
        self.parent.cols.append(content)

class TableRow(element.ContainerElement):

    subElements = {'td': TableCell}

    def process(self):
        self.cols = []
        self.processSubElements(None)
        self.parent.rows.append(self.cols)

class BlockTable(element.ContainerElement, Flowable):
    klass = reportlab.platypus.Table
    kw = (
        ('rowHeights', attr.Sequence('rowHeights', attr.Measurement())),
        ('colWidths', attr.Sequence('colWidths', attr.Measurement())),
        )

    subElements = {'tr': TableRow}

    def process(self):
        # Get the table style; create a new one, if none is found
        self.style = attr.Style('style', 'table').get(self.element, None, self)
        if self.style is None:
            self.style = reportlab.platypus.tables.TableStyle()
        # Extract all table rows and cells
        self.rows = []
        self.processSubElements(None)
        # Create the table
        kw = self.getKeywordArguments()
        table = self.klass(self.rows, style=self.style, **kw)

        self.parent.flow.append(table)


class NextFrame(Flowable):
    klass = reportlab.platypus.doctemplate.FrameBreak
    kw = (
        ('ix', attr.StringOrInt('name')), )

class SetNextFrame(Flowable):
    klass = reportlab.platypus.doctemplate.NextFrameFlowable
    kw = (
        ('ix', attr.StringOrInt('name')), )

class NextPage(Flowable):
    klass = reportlab.platypus.PageBreak

class SetNextTemplate(Flowable):
    klass = reportlab.platypus.doctemplate.NextPageTemplate
    args = ( attr.StringOrInt('name'), )

class ConditionalPageBreak(Flowable):
    klass = reportlab.platypus.CondPageBreak
    args = ( attr.Measurement('height'), )


class KeepInFrame(Flowable):
    klass = reportlab.platypus.flowables.KeepInFrame
    args = (
        attr.Measurement('maxWidth'),
        attr.Measurement('maxHeight'), )
    kw = (
        ('mergeSpace', attr.Bool('mergeSpace')),
        ('mode', attr.Choice('onOverflow',
                             ('error', 'overflow', 'shrink', 'truncate'))),
        ('name', attr.Text('id')) )

    def process(self):
        flow = Flow(self.element, self.parent, self.context)
        flow.process()
        args = self.getPositionalArguments()
        kw = self.getKeywordArguments()
        kw['content'] = flow.flow
        frame = self.klass(*args, **kw)
        self.parent.flow.append(frame)


class ImageAndFlowables(Flowable):
    klass = reportlab.platypus.flowables.ImageAndFlowables
    args = ( attr.Image('imageName', onlyOpen=True), )
    kw = (
        ('width', attr.Measurement('imageWidth')),
        ('height', attr.Measurement('imageHeight')),
        ('mask', attr.Color('imageMask')),
        ('imageLeftPadding', attr.Measurement('imageLeftPadding')),
        ('imageRightPadding', attr.Measurement('imageRightPadding')),
        ('imageTopPadding', attr.Measurement('imageTopPadding')),
        ('imageBottomPadding', attr.Measurement('imageBottomPadding')),
        ('imageSide', attr.Choice('imageSide', ('left', 'right'))) )

    def process(self):
        flow = Flow(self.element, self.parent, self.context)
        flow.process()
        args = self.getPositionalArguments()
        kw = self.getKeywordArguments()
        # Create the image
        img = reportlab.platypus.flowables.Image(
            width=kw.get('width'), height=kw.get('height'),
            mask=kw.get('mask', 'auto'), *args)
        for option in ('width', 'height', 'mask'):
            if option in kw:
                del kw[option]
        # Create the flowable and add it
        self.parent.flow.append(
            self.klass(img, flow.flow, **kw))


class PTO(Flowable):
    klass = reportlab.platypus.flowables.PTOContainer

    def process(self):
        # Get Content
        flow = Flow(self.element, self.parent, self.context)
        flow.process()
        # Get the header
        ptoHeader = self.element.find('pto_header')
        header = None
        if ptoHeader:
            header = Flow(ptoHeader, self.parent, self.context)
            header.process()
            header = header.flow
        # Get the trailer
        ptoTrailer = self.element.find('pto_trailer')
        trailer = None
        if ptoTrailer:
            trailer = Flow(ptoTrailer, self.parent, self.context)
            trailer.process()
            trailer = trailer.flow
        # Create and add the PTO Container
        self.parent.flow.append(self.klass(flow.flow, trailer, header))


class Indent(Flowable):
    kw = (
        ('left', attr.Measurement('left')),
        ('right', attr.Measurement('right')) )

    def process(self):
        kw = self.getKeywordArguments()
        # Indent
        self.parent.flow.append(reportlab.platypus.doctemplate.Indenter(**kw))
        # Add Content
        flow = Flow(self.element, self.parent, self.context)
        flow.process()
        self.parent.flow += flow.flow
        # Dedent
        for name, value in kw.items():
            kw[name] = -value
        self.parent.flow.append(reportlab.platypus.doctemplate.Indenter(**kw))


class FixedSize(Flowable):
    klass = reportlab.platypus.flowables.KeepInFrame
    args = (
        attr.Measurement('width'),
        attr.Measurement('height'), )

    def process(self):
        flow = Flow(self.element, self.parent, self.context)
        flow.process()
        args = self.getPositionalArguments()
        frame = self.klass(content=flow.flow, mode='shrink', *args)
        self.parent.flow.append(frame)


class Flow(element.ContainerElement):

    subElements = {
        # Generic Flowables
        'spacer': Spacer,
        'illustration': Illustration,
        'pre': Preformatted,
        'xpre': XPreformatted,
        'pluginFlowable': PluginFlowable,
        'barCodeFlowable': BarCodeFlowable,
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
        'imageAndFlowables': ImageAndFlowables,
        'pto': PTO,
        'indent': Indent,
        'fixedSize': FixedSize,
        # Special Elements
        'name': special.Name,
        }

    def __init__(self, *args, **kw):
        super(Flow, self).__init__(*args, **kw)
        self.flow = []

    def process(self):
        self.processSubElements(None)
        return self.flow
