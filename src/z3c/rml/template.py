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
import six
import zope.interface
from reportlab import platypus
from z3c.rml import attr, directive, interfaces, occurence
from z3c.rml import canvas, flowable, page, stylesheet


class IStory(flowable.IFlow):
    """The story of the PDF file."""
    occurence.containing(
        *flowable.IFlow.getTaggedValue('directives'))

    firstPageTemplate = attr.Text(
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

    x1 = attr.Measurement(
        title=u'X-Position',
        description=u'The X-Position of the lower-left corner of the frame.',
        allowPercentage=True,
        required=True)

    y1 = attr.Measurement(
        title=u'Y-Position',
        description=u'The Y-Position of the lower-left corner of the frame.',
        allowPercentage=True,
        required=True)

    width = attr.Measurement(
        title=u'Width',
        description=u'The width of the frame.',
        allowPercentage=True,
        required=True)

    height = attr.Measurement(
        title=u'Height',
        description=u'The height of the frame.',
        allowPercentage=True,
        required=True)

    id = attr.Text(
        title=u'Id',
        description=u'The id of the frame.',
        required=False)

    leftPadding = attr.Measurement(
        title=u'Left Padding',
        description=u'The left padding of the frame.',
        default=0,
        required=False)

    rightPadding = attr.Measurement(
        title=u'Right Padding',
        description=u'The right padding of the frame.',
        default=0,
        required=False)

    topPadding = attr.Measurement(
        title=u'Top Padding',
        description=u'The top padding of the frame.',
        default=0,
        required=False)

    bottomPadding = attr.Measurement(
        title=u'Bottom Padding',
        description=u'The bottom padding of the frame.',
        default=0,
        required=False)

    showBoundary = attr.Boolean(
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
            if isinstance(args[name], six.string_types) and args[name].endswith('%'):
                args[name] = float(args[name][:-1])/100*size[dir]
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


class IPageTemplate(interfaces.IRMLDirectiveSignature):
    """Define a page template."""
    occurence.containing(
        occurence.OneOrMore('frame', IFrame),
        occurence.ZeroOrOne('pageGraphics', IPageGraphics),
        occurence.ZeroOrOne('mergePage', page.IMergePage),
        )

    id = attr.Text(
        title=u'Id',
        description=u'The id of the template.',
        required=True)

    pagesize = attr.PageSize(
        title=u'Page Size',
        description=u'The Page Size.',
        required=False)

    autoNextTemplate = attr.String(
        title=u'Auto Next Page Template',
        description=u'The page template to use automatically for the next page.',
        required=False)



class PageTemplate(directive.RMLDirective):
    signature = IPageTemplate
    attrMapping = {'autoNextTemplate': 'autoNextPageTemplate'}
    factories = {
        'frame': Frame,
        'pageGraphics': PageGraphics,
        'mergePage': page.MergePageInPageTemplate,
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
        title=u'Page Size',
        description=u'The Page Size.',
        required=False)

    rotation = attr.Integer(
        title=u'Rotation',
        description=u'The rotation of the page in multiples of 90 degrees.',
        required=False)

    leftMargin = attr.Measurement(
        title=u'Left Margin',
        description=u'The left margin of the template.',
        default=0,
        required=False)

    rightMargin = attr.Measurement(
        title=u'Right Margin',
        description=u'The right margin of the template.',
        default=0,
        required=False)

    topMargin = attr.Measurement(
        title=u'Top Margin',
        description=u'The top margin of the template.',
        default=0,
        required=False)

    bottomMargin = attr.Measurement(
        title=u'Bottom Margin',
        description=u'The bottom margin of the template.',
        default=0,
        required=False)

    showBoundary = attr.Boolean(
        title=u'Show Boundary',
        description=u'A flag to show the boundary of the template.',
        required=False)

    allowSplitting = attr.Boolean(
        title=u'Allow Splitting',
        description=u'A flag to allow splitting over multiple templates.',
        required=False)

    title = attr.Text(
        title=u'Title',
        description=u'The title of the PDF document.',
        required=False)

    author = attr.Text(
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
        args += (('cropMarks',  self.parent.cropMarks),)

        self.parent.doc = platypus.BaseDocTemplate(
            self.parent.outputFile, **dict(args))
        self.processSubDirectives()
