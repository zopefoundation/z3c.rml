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
from reportlab import platypus
from z3c.rml import attr, canvas, element, flowable, interfaces, stylesheet


class Story(flowable.Flow):

    def getFirstPageTemplateIndex(self, doc):
        fpt = attr.Text('firstPageTemplate').get(self.element, None)
        if fpt is None:
            return 0
        for idx, pageTemplate in enumerate(doc.pageTemplates):
            if pageTemplate.id == fpt:
                return idx
        raise ValueError('%r is not a correct page template id.' %fpt)

class Frame(element.FunctionElement):
    args = (
        attr.Measurement('x1', allowPercentage=True),
        attr.Measurement('y1', allowPercentage=True),
        attr.Measurement('width', allowPercentage=True),
        attr.Measurement('height', allowPercentage=True),
        )
    kw = (
        ('id', attr.Text('id')),
        # Non-RML compliant extensions
        ('leftPadding', attr.Measurement('leftPadding', 0)),
        ('rightPadding', attr.Measurement('rightPadding', 0)),
        ('topPadding', attr.Measurement('topPadding', 0)),
        ('bottomPadding', attr.Measurement('bottomPadding', 0)),
        ('showBoundary', attr.Bool('showBoundary')),
        )

    def process(self):
        # get the page size
        size = self.context.pagesize
        if size is None:
            size = self.parent.context.pagesize
        # Get the arguments
        args = self.getPositionalArguments()
        kw = self.getKeywordArguments()
        # Deal with percentages
        if isinstance(args[0], basestring) and args[0].endswith('%'):
            args[0] = float(args[0][:-1])/100*size[0]
        if isinstance(args[1], basestring) and args[1].endswith('%'):
            args[1] = float(args[1][:-1])/100*size[1]
        if isinstance(args[2], basestring) and args[2].endswith('%'):
            args[2] = float(args[2][:-1])/100*size[0]
        if isinstance(args[3], basestring) and args[3].endswith('%'):
            args[3] = float(args[3][:-1])/100*size[1]
        frame = platypus.Frame(*args, **kw)
        self.parent.frames.append(frame)


class PageGraphics(element.Element):

    def process(self):
        def drawOnCanvas(canv, doc):
            canv.saveState()
            drawing = canvas.Drawing(self.element, self, canv)
            drawing.process()
            canv.restoreState()

        self.context.onPage = drawOnCanvas


class PageTemplate(element.FunctionElement, element.ContainerElement):
    args = (attr.Text('id'),)
    kw = (
        ('pagesize', attr.PageSize('pageSize',)),
        ('rotation', attr.Int('rotation')) )

    subElements = {
        'frame': Frame,
        'pageGraphics': PageGraphics,
        }

    def process(self):
        args = self.getPositionalArguments()
        self.frames = []
        pt = platypus.PageTemplate(*args)
        self.processSubElements(pt)
        pt.frames = self.frames

        kw = self.getKeywordArguments()
        if 'pagesize' in kw:
            pt.pagesize = kw['pagesize']

        self.context.addPageTemplates(pt)


class Template(element.ContainerElement):

    templateArgs = (
        ('pagesize', attr.PageSize('pageSize',)),
        ('rotation', attr.Int('rotation')),
        ('leftMargin', attr.Measurement('leftMargin')),
        ('rightMargin', attr.Measurement('rightMargin')),
        ('topMargin', attr.Measurement('topMargin')),
        ('bottomMargin', attr.Measurement('bottomMargin')),
        ('showBoundary', attr.Bool('showBoundary')),
        ('allowSplitting', attr.Bool('allowSplitting')),
        ('title', attr.Text('title')),
        ('author', attr.Text('author')) )

    documentArgs = (
        ('_debug', attr.Bool('debug')),
        ('pageCompression', attr.DefaultBool('compression')),
        ('invariant', attr.DefaultBool('invariant')) )

    subElements = {
        'pageTemplate': PageTemplate,
        'stylesheet': stylesheet.Stylesheet,
        }

    def process(self, outputFile):
        docElement = self.element
        self.processSubElements(None)

        self.element = self.element.find('template')

        kw = element.extractKeywordArguments(
            self.documentArgs, docElement, self)
        kw.update(element.extractKeywordArguments(
            self.templateArgs, self.element, self))
        doc = platypus.BaseDocTemplate(outputFile, **kw)

        self.processSubElements(doc)

        story = Story(docElement.find('story'), self, doc)
        flowables = story.process()

        doc._firstPageTemplateIndex = story.getFirstPageTemplateIndex(doc)
        doc.multiBuild(flowables)
