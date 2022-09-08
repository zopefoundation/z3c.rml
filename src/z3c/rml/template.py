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
"""Style Related Element Processing
"""

import zope.interface
from reportlab import platypus

from z3c.rml import attr
from z3c.rml import canvas
from z3c.rml import directive
from z3c.rml import flowable
from z3c.rml import interfaces
from z3c.rml import occurence
from z3c.rml import page
from z3c.rml import stylesheet  # noqa: F401 imported but unused


class IStory(flowable.IFlow):
    """The story of the PDF file."""
    occurence.containing(
        occurence.ZeroOrMore('pto', flowable.IPTO),
        *flowable.IFlow.getTaggedValue('directives'))

    firstPageTemplate = attr.Text(
        title='First Page Template',
        description='The first page template to be used.',
        default=None,
        required=False)


class Story(flowable.Flow):
    signature = IStory

    factories = dict(
        pto=flowable.PTO,
        **flowable.Flow.factories
    )

    def process(self):
        self.parent.flowables = super().process()
        self.parent.doc._firstPageTemplateIndex = self.getFirstPTIndex()

    def getFirstPTIndex(self):
        args = dict(self.getAttributeValues(select=('firstPageTemplate',)))
        fpt = args.pop('firstPageTemplate', None)
        if fpt is None:
            return 0
        for idx, pageTemplate in enumerate(self.parent.doc.pageTemplates):
            if pageTemplate.id == fpt:
                return idx
        raise ValueError('%r is not a correct page template id.' % fpt)


class IFrame(interfaces.IRMLDirectiveSignature):
    """A frame on a page."""

    x1 = attr.Measurement(
        title='X-Position',
        description='The X-Position of the lower-left corner of the frame.',
        allowPercentage=True,
        required=True)

    y1 = attr.Measurement(
        title='Y-Position',
        description='The Y-Position of the lower-left corner of the frame.',
        allowPercentage=True,
        required=True)

    width = attr.Measurement(
        title='Width',
        description='The width of the frame.',
        allowPercentage=True,
        required=True)

    height = attr.Measurement(
        title='Height',
        description='The height of the frame.',
        allowPercentage=True,
        required=True)

    id = attr.Text(
        title='Id',
        description='The id of the frame.',
        required=False)

    leftPadding = attr.Measurement(
        title='Left Padding',
        description='The left padding of the frame.',
        default=0,
        required=False)

    rightPadding = attr.Measurement(
        title='Right Padding',
        description='The right padding of the frame.',
        default=0,
        required=False)

    topPadding = attr.Measurement(
        title='Top Padding',
        description='The top padding of the frame.',
        default=0,
        required=False)

    bottomPadding = attr.Measurement(
        title='Bottom Padding',
        description='The bottom padding of the frame.',
        default=0,
        required=False)

    showBoundary = attr.Boolean(
        title='Show Boundary',
        description='A flag to show the boundary of the frame.',
        required=False)


class Frame(directive.RMLDirective):
    signature = IFrame

    def process(self):
        # get the page size
        size = self.parent.pt.pagesize
        if size is None:
            size = self.parent.parent.parent.doc.pagesize
        # Get the arguments
        args = dict(self.getAttributeValues())
        # Deal with percentages
        for name, dir in (('x1', 0), ('y1', 1), ('width', 0), ('height', 1)):
            if (isinstance(args[name], str) and
                    args[name].endswith('%')):
                args[name] = float(args[name][:-1]) / 100 * size[dir]
        frame = platypus.Frame(**args)
        self.parent.frames.append(frame)


class IPageGraphics(canvas.IDrawing):
    """Define the page graphics for the page template."""


@zope.interface.implementer(interfaces.ICanvasManager)
class PageGraphics(directive.RMLDirective):
    signature = IPageGraphics

    def process(self):
        onPage = self.parent.pt.onPage

        def drawOnCanvas(canv, doc):
            onPage(canv, doc)
            canv.saveState()
            self.canvas = canv
            drawing = canvas.Drawing(self.element, self)
            drawing.process()
            canv.restoreState()

        self.parent.pt.onPage = drawOnCanvas


class Header(PageGraphics):

    def process(self):
        onPage = self.parent.pt.onPage

        def drawOnCanvas(canv, doc):
            onPage(canv, doc)
            canv.saveState()
            self.canvas = canv
            place = canvas.Place(self.element, self)
            place.process()
            canv.restoreState()

        self.parent.pt.onPage = drawOnCanvas


class Footer(Header):
    pass


class IPageTemplate(interfaces.IRMLDirectiveSignature):
    """Define a page template."""
    occurence.containing(
        occurence.OneOrMore('frame', IFrame),
        occurence.ZeroOrOne('pageGraphics', IPageGraphics),
        occurence.ZeroOrOne('mergePage', page.IMergePage),
    )

    id = attr.Text(
        title='Id',
        description='The id of the template.',
        required=True)

    pagesize = attr.PageSize(
        title='Page Size',
        description='The Page Size.',
        required=False)

    autoNextTemplate = attr.Text(
        title='Auto Next Page Template',
        description='The page template to use automatically for the next'
                    ' page.',
        required=False)


class PageTemplate(directive.RMLDirective):
    signature = IPageTemplate
    attrMapping = {'autoNextTemplate': 'autoNextPageTemplate'}
    factories = {
        'frame': Frame,
        'pageGraphics': PageGraphics,
        'mergePage': page.MergePageInPageTemplate,
        'header': Header,
        'footer': Footer,
    }

    def process(self):
        args = dict(self.getAttributeValues(attrMapping=self.attrMapping))
        pagesize = args.pop('pagesize', None)

        self.frames = []
        self.pt = platypus.PageTemplate(**args)

        self.processSubDirectives()
        self.pt.frames = self.frames

        if pagesize:
            self.pt.pagesize = pagesize

        self.parent.parent.doc.addPageTemplates(self.pt)


class ITemplate(interfaces.IRMLDirectiveSignature):
    """Define a page template."""
    occurence.containing(
        occurence.OneOrMore('pageTemplate', IPageTemplate),
    )

    pagesize = attr.PageSize(
        title='Page Size',
        description='The Page Size.',
        required=False)

    rotation = attr.Integer(
        title='Rotation',
        description='The rotation of the page in multiples of 90 degrees.',
        required=False)

    leftMargin = attr.Measurement(
        title='Left Margin',
        description='The left margin of the template.',
        default=0,
        required=False)

    rightMargin = attr.Measurement(
        title='Right Margin',
        description='The right margin of the template.',
        default=0,
        required=False)

    topMargin = attr.Measurement(
        title='Top Margin',
        description='The top margin of the template.',
        default=0,
        required=False)

    bottomMargin = attr.Measurement(
        title='Bottom Margin',
        description='The bottom margin of the template.',
        default=0,
        required=False)

    showBoundary = attr.Boolean(
        title='Show Boundary',
        description='A flag to show the boundary of the template.',
        required=False)

    allowSplitting = attr.Boolean(
        title='Allow Splitting',
        description='A flag to allow splitting over multiple templates.',
        required=False)

    title = attr.Text(
        title='Title',
        description='The title of the PDF document.',
        required=False)

    author = attr.Text(
        title='Author',
        description='The author of the PDF document.',
        required=False)


class Template(directive.RMLDirective):
    signature = ITemplate
    factories = {
        'pageTemplate': PageTemplate,
    }

    def process(self):
        args = self.getAttributeValues()
        args += self.parent.getAttributeValues(
            select=('debug', 'compression', 'invariant'),
            attrMapping={'debug': '_debug', 'compression': 'pageCompression'})
        args += (('cropMarks', self.parent.cropMarks),)

        self.parent.doc = platypus.BaseDocTemplate(
            self.parent.outputFile, **dict(args))
        self.processSubDirectives()
