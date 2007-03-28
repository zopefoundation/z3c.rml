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

$Id$
"""
__docformat__ = "reStructuredText"
import zope.interface
from reportlab import platypus
from z3c.rml import attrng, directive, interfaces, occurence
from z3c.rml import canvas, flowable, stylesheet


class IStory(flowable.IFlow):
    """The story of the PDF file."""

    firstPageTemplate = attrng.Text(
        title=u'First Page Template',
        description=u'The first page template to be used.',
        default=None,
        required=False)

class Story(flowable.Flow):
    signature = IStory

    def process(self):
        self.parent.flowables = super(Story, self).process()
        self.parent.doc._firstPageTemplateIndex = self.getFirstPTIndex()

    def getFirstPTIndex(self):
        args = dict(self.getAttributeValues(select=('firstPageTemplate',)))
        fpt = args.pop('firstPageTemplate', None)
        if fpt is None:
            return 0
        for idx, pageTemplate in enumerate(self.parent.doc.pageTemplates):
            if pageTemplate.id == fpt:
                return idx
        raise ValueError('%r is not a correct page template id.' %fpt)


class IFrame(interfaces.IRMLDirectiveSignature):
    """A frame on a page."""

    x1 = attrng.Measurement(
        title=u'X-Position',
        description=u'The X-Position of the lower-left corner of the frame.',
        allowPercentage=True,
        required=True)

    y1 = attrng.Measurement(
        title=u'Y-Position',
        description=u'The Y-Position of the lower-left corner of the frame.',
        allowPercentage=True,
        required=True)

    width = attrng.Measurement(
        title=u'Width',
        description=u'The width of the frame.',
        allowPercentage=True,
        required=True)

    height = attrng.Measurement(
        title=u'Height',
        description=u'The height of the frame.',
        allowPercentage=True,
        required=True)

    id = attrng.Text(
        title=u'Id',
        description=u'The id of the frame.',
        required=False)

    leftPadding = attrng.Measurement(
        title=u'Left Padding',
        description=u'The left padding of the frame.',
        default=0,
        required=False)

    rightPadding = attrng.Measurement(
        title=u'Right Padding',
        description=u'The right padding of the frame.',
        default=0,
        required=False)

    topPadding = attrng.Measurement(
        title=u'Top Padding',
        description=u'The top padding of the frame.',
        default=0,
        required=False)

    bottomPadding = attrng.Measurement(
        title=u'Bottom Padding',
        description=u'The bottom padding of the frame.',
        default=0,
        required=False)

    showBoundary = attrng.Boolean(
        title=u'Show Boundary',
        description=u'A flag to show the boundary of the frame.',
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
            if isinstance(args[name], basestring) and args[name].endswith('%'):
                args[name] = float(args[name][:-1])/100*size[dir]
        frame = platypus.Frame(**args)
        self.parent.frames.append(frame)


class IPageGraphics(canvas.IDrawing):
    """Define the page graphics for the page template."""

class PageGraphics(directive.RMLDirective):
    zope.interface.implements(interfaces.ICanvasManager)
    signature = IPageGraphics

    def process(self):
        def drawOnCanvas(canv, doc):
            canv.saveState()
            self.canvas = canv
            drawing = canvas.Drawing(self.element, self)
            drawing.process()
            canv.restoreState()

        self.parent.pt.onPage = drawOnCanvas


class IPageTemplate(interfaces.IRMLDirectiveSignature):
    """Define a page template."""
    occurence.containing(
        occurence.OneOrMore('frame', IFrame),
        occurence.ZeroOrOne('pageGraphics', IPageGraphics),
        )

    id = attrng.Text(
        title=u'Id',
        description=u'The id of the template.',
        required=True)

    pagesize = attrng.PageSize(
        title=u'Page Size',
        description=u'The Page Size.',
        required=False)

    rotation = attrng.Integer(
        title=u'Rotation',
        description=u'The rotation of the page in multiples of 90 degrees.',
        required=False)



class PageTemplate(directive.RMLDirective):
    signature = IPageTemplate
    factories = {
        'frame': Frame,
        'pageGraphics': PageGraphics,
        }

    def process(self):
        args = dict(self.getAttributeValues())
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
        occurence.OneOrMore('pagetemplate', IPageTemplate),
        )

    pagesize = attrng.PageSize(
        title=u'Page Size',
        description=u'The Page Size.',
        required=False)

    rotation = attrng.Integer(
        title=u'Rotation',
        description=u'The rotation of the page in multiples of 90 degrees.',
        required=False)

    leftMargin = attrng.Measurement(
        title=u'Left Margin',
        description=u'The left margin of the template.',
        default=0,
        required=False)

    rightMargin = attrng.Measurement(
        title=u'Right Margin',
        description=u'The right margin of the template.',
        default=0,
        required=False)

    topMargin = attrng.Measurement(
        title=u'Top Margin',
        description=u'The top margin of the template.',
        default=0,
        required=False)

    bottomMargin = attrng.Measurement(
        title=u'Bottom Margin',
        description=u'The bottom margin of the template.',
        default=0,
        required=False)

    showBoundary = attrng.Boolean(
        title=u'Show Boundary',
        description=u'A flag to show the boundary of the template.',
        required=False)

    allowSplitting = attrng.Boolean(
        title=u'Allow Splitting',
        description=u'A flag to allow splitting over multiple templates.',
        required=False)

    title = attrng.Text(
        title=u'Title',
        description=u'The title of the PDF document.',
        required=False)

    author = attrng.Text(
        title=u'Author',
        description=u'The author of the PDF document.',
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

        self.parent.doc = platypus.BaseDocTemplate(
            self.parent.outputFile, **dict(args))
        self.processSubDirectives()
