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
"""Page Drawing Related Element Processing

$Id$
"""
__docformat__ = "reStructuredText"
import zope.interface
import reportlab.pdfgen.canvas
from z3c.rml import attr, element, flowable, interfaces, stylesheet
from z3c.rml import chart, form


class DrawString(element.FunctionElement):
    functionName = 'drawString'
    args = (
        attr.Measurement('x'),
        attr.Measurement('y'),
        attr.TextNode())


class DrawRightString(DrawString):
    functionName = 'drawRightString'


class DrawCenteredString(DrawString):
    functionName = 'drawCentredString'


class Shape(element.FunctionElement):
    args = (
        attr.Measurement('x'),
        attr.Measurement('y') )
    kw = (
        ('fill', attr.Bool('fill')),
        ('stroke', attr.Bool('stroke')) )


class Ellipse(Shape):
    functionName = 'ellipse'
    args = Shape.args + (
        attr.Measurement('width'),
        attr.Measurement('height') )

    def process(self):
        args = self.getPositionalArguments()
        kw = self.getKeywordArguments()
        # Convert width and height to end locations
        args[2] += args[0]
        args[3] += args[1]
        getattr(self.context, self.functionName)(*args, **kw)

class Circle(Shape):
    functionName = 'circle'
    args = Shape.args + (
        attr.Measurement('radius'), )


class Rectangle(Shape):
    functionName = 'rect'
    args = Shape.args + (
        attr.Measurement('width'),
        attr.Measurement('height') )
    kw = Shape.kw + (
        ('radius', attr.Measurement('round')),
        )

    def process(self):
        if 'round' in self.element.keys():
            self.functionName = 'roundRect'
        super(Rectangle, self).process()


class Grid(element.FunctionElement):
    functionName = 'grid'
    args = (
        attr.Sequence('xs', attr.Measurement()),
        attr.Sequence('ys', attr.Measurement()) )


class Lines(element.FunctionElement):
    functionName = 'lines'
    args = (
        attr.TextNodeGrid(attr.Measurement(), 4),
        )


class Curves(element.FunctionElement):
    functionName = 'bezier'
    args = (
        attr.TextNodeGrid(attr.Measurement(), 8),
        )

    def process(self):
        argset = self.getPositionalArguments()
        for args in argset[0]:
            getattr(self.context, self.functionName)(*args)


class Image(element.FunctionElement):
    functionName = 'drawImage'
    args = (
        attr.Image('file'),
        attr.Measurement('x'),
        attr.Measurement('y') )
    kw = (
        ('width', attr.Measurement('width')),
        ('height', attr.Measurement('height')) )

    def process(self):
        args = self.getPositionalArguments()
        kw = self.getKeywordArguments()

        preserve = attr.Bool('preserveAspectRatio').get(self.element, False)

        if preserve:
            imgX, imgY = args[0].getSize()

            # Scale image correctly, if width and/or height were specified
            if 'width' in kw and 'height' not in kw:
                kw['height'] = imgY * kw['width'] / imgX
            elif 'height' in kw and 'width' not in kw:
                kw['width'] = imgX * kw['height'] / imgY
            elif 'width' in kw and 'height' in kw:
                if float(kw['width']) / kw['height'] > float(imgX) / imgY:
                    kw['width'] = imgX * kw['height'] / imgY
                else:
                    kw['height'] = imgY * kw['width'] / imgX

        getattr(self.context, self.functionName)(*args, **kw)

        show = attr.Bool('showBoundary').get(self.element, False)
        if show:
            width = kw.get('width', args[0].getSize()[0])
            height = kw.get('height', args[0].getSize()[1])
            self.context.rect(args[1], args[2], width, height)


class Place(element.FunctionElement):
    args = (
        attr.Measurement('x'), attr.Measurement('y'),
        attr.Measurement('width'), attr.Measurement('height') )

    def process(self):
        x, y, width, height = self.getPositionalArguments()
        y += height

        flows = flowable.Flow(self.element, self.parent, self.context)
        flows.process()
        for flow in flows.flow:
            flowWidth, flowHeight = flow.wrap(width, height)
            if flowWidth <= width and flowHeight <= height:
                y -= flowHeight
                flow.drawOn(self.context, x, y)
                height -= flowHeight
            else:
                raise ValueError("Not enough space")


class MoveTo(element.FunctionElement):
    args = (
        attr.TextNodeSequence(attr.Measurement(), length=2),
        )

    def process(self):
        args = self.getPositionalArguments()
        self.context.moveTo(*args[0])

class CurvesTo(Curves):
    functionName = 'curveTo'
    args = (
        attr.TextNodeGrid(attr.Measurement(), 6),
        )

class Path(element.FunctionElement):
    args = (
        attr.Measurement('x'),
        attr.Measurement('y') )
    kw = (
        ('close', attr.Bool('close')),
        ('fill', attr.Bool('fill')),
        ('stroke', attr.Bool('stroke')) )

    points = attr.TextNodeGrid(attr.Measurement(), 2)

    subElements = {
        'moveto': MoveTo,
        'curvesto': CurvesTo
        }

    def processPoints(self, text):
        if text.strip() == '':
            return
        for coords in self.points.convert(text):
            self.path.lineTo(*coords)

    def process(self):
        args = self.getPositionalArguments()
        kw = self.getKeywordArguments()

        self.path = self.context.beginPath()
        self.path.moveTo(*args)

        if self.element.text is not None:
            self.processPoints(self.element.text)
        for subElement in self.element.getchildren():
            if subElement.tag in self.subElements:
                self.subElements[subElement.tag](
                    subElement, self, self.path).process()
            if subElement.tail is not None:
                self.processPoints(subElement.tail)

        if kw.get('close', False):
            self.path.close()
            del kw['close']

        self.context.drawPath(self.path, **kw)


class Fill(element.FunctionElement):
    functionName = 'setFillColor'
    args = (
        attr.Color('color'), )


class Stroke(element.FunctionElement):
    functionName = 'setStrokeColor'
    args = (
        attr.Color('color'), )


class SetFont(element.FunctionElement):
    functionName = 'setFont'
    args = (
        attr.Text('name'),
        attr.Measurement('size'), )


class Scale(element.FunctionElement):
    functionName = 'scale'
    args = (attr.Float('sx'), attr.Float('sy'), )


class Translate(element.FunctionElement):
    functionName = 'translate'
    args = (attr.Measurement('dx', 0), attr.Measurement('dy', 0), )


class Rotate(element.FunctionElement):
    functionName = 'rotate'
    args = (attr.Float('degrees'), )


class Skew(element.FunctionElement):
    functionName = 'skew'
    args = (attr.Measurement('alpha'), attr.Measurement('beta'), )


class Transform(element.FunctionElement):
    functionName = 'transform'
    args = (attr.TextNodeSequence(attr.Float()), )

    def process(self):
        args = self.getPositionalArguments()
        getattr(self.context, self.functionName)(*args[0])


class LineMode(element.FunctionElement):
    kw = (
        ('width', attr.Measurement('width')),
        ('dash', attr.Sequence('dash', attr.Measurement())),
        ('miterLimit', attr.Measurement('miterLimit')),
        ('join', attr.Choice(
             'join', {'round': 1, 'mitered': 0, 'bevelled': 2})),
        ('cap', attr.Choice(
             'cap', {'default': 0, 'round': 1, 'square': 2})),
        )

    def process(self):
        kw = self.getKeywordArguments()
        if 'width' in kw:
            self.context.setLineWidth(kw['width'])
        if 'join' in kw:
            self.context.setLineJoin(kw['join'])
        if 'cap' in kw:
            self.context.setLineCap(kw['cap'])
        if 'miterLimit' in kw:
            self.context.setMiterLimit(kw['miterLimit'])
        if 'dash' in kw:
            self.context.setDash(kw['dash'])


class Drawing(element.ContainerElement):

    subElements = {
        'drawString': DrawString,
        'drawRightString': DrawRightString,
        'drawCenteredString': DrawCenteredString,
        'drawCentredString': DrawCenteredString,
        # Drawing Operations
        'ellipse': Ellipse,
        'circle': Circle,
        'rect': Rectangle,
        'grid': Grid,
        'lines': Lines,
        'curves': Curves,
        'image': Image,
        'place': Place,
        'path': Path,
        # Form Field Elements
        'barCode': form.BarCode,
        # State Change Operations
        'fill': Fill,
        'stroke': Stroke,
        'setFont': SetFont,
        'scale': Scale,
        'translate': Translate,
        'rotate': Rotate,
        'skew': Skew,
        'transform': Transform,
        'lineMode': LineMode,
        # Charts
        'barChart': chart.BarChart,
        'barChart3D': chart.BarChart3D,
        'linePlot': chart.LinePlot,
        'pieChart': chart.PieChart,
        'pieChart3D': chart.PieChart3D,
        'spiderChart': chart.SpiderChart
        }


class PageDrawing(Drawing):

    subElements = Drawing.subElements.copy()

    def process(self):
        super(Drawing, self).process()
        self.context.showPage()


class PageInfo(element.Element):

    def process(self):
        pageSize = attr.Sequence(
            'pageSize', attr.Measurement(), length=2).get(self.element)
        self.context.setPageSize(pageSize)


class Canvas(element.ContainerElement):
    zope.interface.implements(interfaces.IStylesManager)

    subElements = {
        'stylesheet': stylesheet.Stylesheet,
        'pageDrawing': PageDrawing,
        'pageInfo': PageInfo,
        }

    def __init__(self, element):
        self.element = element
        self.styles = {}

    def process(self, outputFile):
        verbosity = attr.Bool('verbosity').get(self.element, 0)
        compression = attr.DefaultBool('compression').get(self.element, 0)

        canvas = reportlab.pdfgen.canvas.Canvas(
            outputFile,
            pageCompression=compression,
            verbosity=verbosity)
        self.processSubElements(canvas)

        canvas.save()
