##############################################################################
#
# Copyright (c) 2007-2012 Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTLAR PURPOSE.
#
##############################################################################
"""Testing all XML Locale functionality.
"""
import reportlab.platypus
import reportlab.lib.styles
import reportlab.graphics.widgets.markers
from reportlab.graphics import renderPDF, shapes
from reportlab.lib import colors
from z3c.rml import attr, interfaces, SampleStyleSheet

def myPreformatted(params):
    return reportlab.platypus.Preformatted('''
        Hey, this is a long text from a plugin. Hey, this is a long text from
        a plugin. Hey, this is a long text from a plugin. Hey, this is a long
        text from a plugin. Hey, this is a long text from a plugin. Hey, this
        is a long text from a plugin. Hey, this is a long text from a
        plugin. Hey, this is a long text from a plugin. Hey, this is a long
        text from a plugin. Hey, this is a long text from a plugin. Hey, this
        is a long text from a plugin. Hey, this is a long text from a
        plugin. Hey, this is a long text from a plugin. Hey, this is a long
        text from a plugin. Hey, this is a long text from a plugin. Hey, this
        is a long text from a plugin.''',
        SampleStyleSheet['Normal'])

class LinkURL(reportlab.platypus.flowables.Flowable):
    def __init__(self, link):
        self.link = link

    def wrap(self, *args):
        return (0, 0)

    def draw(self):
        self.canv.linkURL(self.link, None)


def linkURL(params):
    params = eval(params)
    return (
        reportlab.platypus.Paragraph(
            params[0], SampleStyleSheet['Normal']),
        LinkURL(*params))

class IMarker(interfaces.IRMLDirectiveSignature):
    x = attr.Measurement()
    y = attr.Measurement()
    dx = attr.Measurement()
    dy = attr.Measurement()
    size = attr.Measurement()
    fillColor = attr.Color(acceptNone=True, required=False)
    strokeColor = attr.Color(acceptNone=True, required=False)
    strokeWidth = attr.Measurement(required=False)
    arrowBarDx = attr.Measurement(required=False)
    arrowHeight = attr.Measurement(required=False)

def symbols(canvas, params):
    args = eval('dict(%s)' %params)
    name = args.pop('name')
    n = args.pop('n')
    for key, value in args.items():
        field = IMarker[key].bind(canvas.manager)
        args[key] = field.fromUnicode(value)
    m = reportlab.graphics.widgets.markers.makeMarker(name, **args)
    drawing = shapes.Drawing()
    drawing.add(m)
    for idx in range(n):
        drawing.drawOn(canvas, idx*args['dx'], idx*args['dy'])
