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
import reportlab.platypus.flowables
import reportlab.rl_config
from reportlab.rl_config import overlapAttachedSpace
import zope.interface

from z3c.rml import interfaces

# Fix problem with reportlab 3.1.44
class KeepInFrame(reportlab.platypus.flowables.KeepInFrame):
    pass

    def __init__(self, maxWidth, maxHeight, content=[], mergeSpace=1,
                 mode='shrink', name='', hAlign='LEFT', vAlign='BOTTOM',
                 fakeWidth=None):

        self.name = name
        self.maxWidth = maxWidth
        self.maxHeight = maxHeight
        self.mode = mode
        assert mode in ('error','overflow','shrink','truncate'), \
               '%s invalid mode value %s' % (self.identity(),mode)
        # This is an unnecessary check, since wrap() handles None just fine!
        #assert maxHeight>=0,  \
        #       '%s invalid maxHeight value %s' % (self.identity(),maxHeight)
        if mergeSpace is None: mergeSpace = overlapAttachedSpace
        self.mergespace = mergeSpace
        self._content = content or []
        self.vAlign = vAlign
        self.hAlign = hAlign
        self.fakeWidth = fakeWidth


class BaseFlowable(reportlab.platypus.flowables.Flowable):
    def __init__(self, *args, **kw):
        reportlab.platypus.flowables.Flowable.__init__(self)
        self.args = args
        self.kw = kw

    def wrap(self, *args):
        return (0, 0)

    def draw(self):
        pass

class Illustration(reportlab.platypus.flowables.Flowable):
    def __init__(self, processor, width, height):
        self.processor = processor
        self.width = width
        self.height = height

    def wrap(self, *args):
        return (self.width, self.height)

    def draw(self):
        # Import here to avoid recursive imports
        from z3c.rml import canvas
        self.canv.saveState()
        drawing = canvas.Drawing(
            self.processor.element, self.processor)
        zope.interface.alsoProvides(drawing, interfaces.ICanvasManager)
        drawing.canvas = self.canv
        drawing.process()
        self.canv.restoreState()

class BookmarkPage(BaseFlowable):
    def draw(self):
        self.canv.bookmarkPage(*self.args, **self.kw)


class Bookmark(BaseFlowable):
    def draw(self):
        self.canv.bookmarkHorizontal(*self.args, **self.kw)


class OutlineAdd(BaseFlowable):
    def draw(self):
        if self.kw.get('key', None) is None:
            self.kw['key'] = str(hash(self))
        self.canv.bookmarkPage(self.kw['key'])
        self.canv.addOutlineEntry(**self.kw)


class Link(reportlab.platypus.flowables._Container,
           reportlab.platypus.flowables.Flowable):

    def __init__(self, content, **args):
        self._content = content
        self.args = args

    def wrap(self, availWidth, availHeight):
        self.width, self.height = reportlab.platypus.flowables._listWrapOn(
            self._content, availWidth, self.canv)
        return self.width, self.height

    def drawOn(self, canv, x, y, _sW=0, scale=1.0, content=None, aW=None):
        '''we simulate being added to a frame'''
        pS = 0
        if aW is None: aW = self.width
        aW = scale*(aW+_sW)
        if content is None:
            content = self._content
        y += self.height*scale

        startX = x
        startY = y
        totalWidth = 0
        totalHeight = 0

        for c in content:
            w, h = c.wrapOn(canv,aW,0xfffffff)
            if w < reportlab.rl_config._FUZZ or h < reportlab.rl_config._FUZZ:
                continue
            if c is not content[0]: h += max(c.getSpaceBefore()-pS,0)
            y -= h
            c.drawOn(canv,x,y,_sW=aW-w)
            if c is not content[-1]:
                pS = c.getSpaceAfter()
                y -= pS
            totalWidth += w
            totalHeight += h
        rectangle = [startX, startY-totalHeight,
                startX+totalWidth, startY]
        if 'url' in self.args:
            canv.linkURL(rect=rectangle, **self.args)
        else:
            canv.linkAbsolute('', Rect=rectangle, **self.args)
