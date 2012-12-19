##############################################################################
#
# Copyright (c) 2012 Zope Foundation and Contributors.
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
"""``pdfInclude`` Directive.
"""
__docformat__ = "reStructuredText"
from reportlab.platypus import flowables

from z3c.rml import attr, flowable, interfaces, occurence


class StoryPlaceFlowable(flowables.Flowable):

    def __init__(self, x, y, width, height, origin, flows):
        flowables.Flowable.__init__(self)
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.origin = origin
        self.flows = flows

    def wrap(self, *args):
        return (0, 0)

    def draw(self):
        saveState = False
        x, y = self.x, self.y
        self.canv.restoreState()
        if self.origin == 'frame':
            x += self._frame._x1
            y += self._frame._y1
        elif self.origin == 'local':
            x += self._frame._x
            y += self._frame._y
        else:
            # origin == 'page'
            pass
        width, height  = self.width, self.height
        y += height
        for flow in self.flows.flow:
            flowWidth, flowHeight = flow.wrap(width, height)
            if flowWidth <= width and flowHeight <= height:
                y -= flowHeight
                flow.drawOn(self.canv, x, y)
                height -= flowHeight
            else:
                raise ValueError("Not enough space")
        self.canv.saveState()


class IStoryPlace(interfaces.IRMLDirectiveSignature):
    """Draws a set of flowables on the canvas within a given region."""

    x = attr.Measurement(
        title=u'X-Coordinate',
        description=(u'The X-coordinate of the lower-left position of the '
                     u'place.'),
        required=True)

    y = attr.Measurement(
        title=u'Y-Coordinate',
        description=(u'The Y-coordinate of the lower-left position of the '
                     u'place.'),
        required=True)

    width = attr.Measurement(
        title=u'Width',
        description=u'The width of the place.',
        required=False)

    height = attr.Measurement(
        title=u'Height',
        description=u'The height of the place.',
        required=False)

    origin = attr.Choice(
        title=u'Origin',
        description=u'The origin of the coordinate system for the story.',
        choices=('page', 'frame', 'local'),
        default = 'page',
        required=False)

class StoryPlace(flowable.Flowable):
    signature = IStoryPlace

    def process(self):
        x, y, width, height, origin = self.getAttributeValues(
            select=('x', 'y', 'width', 'height', 'origin'), valuesOnly=True)

        flows = flowable.Flow(self.element, self.parent)
        flows.process()
        self.parent.flow.append(
            StoryPlaceFlowable(x, y, width, height, origin, flows))


flowable.Flow.factories['storyPlace'] = StoryPlace
flowable.IFlow.setTaggedValue(
    'directives',
    flowable.IFlow.getTaggedValue('directives') +
    (occurence.ZeroOrMore('storyPlace', IStoryPlace),)
    )
