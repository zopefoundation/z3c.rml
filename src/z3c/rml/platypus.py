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
import reportlab.platypus.flowables
import zope.interface

from z3c.rml import interfaces


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


class OutlineAdd(BaseFlowable):
    def draw(self):
        if self.kw.get('key', None) is None:
            self.kw['key'] = str(hash(self))
        self.canv.bookmarkPage(self.kw['key'])
        self.canv.addOutlineEntry(**self.kw)
