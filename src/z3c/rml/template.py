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
from z3c.rml import attr, canvas, element, flowable, interfaces, stylesheet



class Story(flowable.Flow):
    pass

class Frame(element.FunctionElement):
    args = (
        attr.Measurement('x1'), attr.Measurement('y1'),
        attr.Measurement('width'), attr.Measurement('height'),
        )
    kw = (
        ('id', attr.Text('id')),
        # Non-RML compliant extensions
        ('leftPadding', attr.Measurement('leftPadding')),
        ('rightPadding', attr.Measurement('rightPadding')),
        ('topPadding', attr.Measurement('topPadding')),
        ('bottomPadding', attr.Measurement('bottomPadding')),
        ('showBoundary', attr.Bool('showBoundary')),
        )

    def process(self):
        args = self.getPositionalArguments()
        kw = self.getKeywordArguments()
        frame = platypus.Frame(*args, **kw)
        self.context.frames.append(frame)


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
        ('pagesize', attr.Sequence('pageSize', attr.Measurement(), length=2)),
        ('rotation', attr.Int('rotation')) )

    subElements = {
        'frame': Frame,
        'pageGraphics': PageGraphics,
        }

    def process(self):
        args = self.getPositionalArguments()
        pt = platypus.PageTemplate(*args)

        kw = self.getKeywordArguments()
        if 'pagesize' in kw:
            pt.pagesize = kw['pagesize']

        self.processSubElements(pt)
        self.context.addPageTemplates(pt)


class Template(element.ContainerElement):
    zope.interface.implements(interfaces.IStylesManager)

    templateArgs = (
        ('pagesize', attr.Sequence('PageSize', attr.Measurement(), length=2)),
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

    def __init__(self, element):
        self.element = element
        self.names = {}
        self.styles = {}

    def process(self, outputFile):
        docElement = self.element
        self.processSubElements(None)

        self.element = self.element.find('template')

        kw = element.extractKeywordArguments(self.documentArgs, docElement)
        kw.update(element.extractKeywordArguments(
            self.templateArgs, self.element))
        doc = platypus.BaseDocTemplate(outputFile, **kw)

        self.processSubElements(doc)

        story = Story(docElement.find('story'), self, doc).process()
        doc.build(story)
