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
"""Chart Element Processing

$Id$
"""
__docformat__ = "reStructuredText"
import reportlab.lib.formatters
from reportlab.graphics import shapes
from reportlab.graphics.charts import barcharts, lineplots, piecharts
from reportlab.graphics.charts import spider, doughnut
from z3c.rml import attr, element

try:
    import reportlab.graphics.barcode
except ImportError:
    # barcode package has not been installed
    import reportlab.graphics
    reportlab.graphics.barcode = types.ModuleType('barcode')
    reportlab.graphics.barcode.getCodeNames = lambda : ()

# Patches against Reportlab 2.0
lineplots.Formatter = reportlab.lib.formatters.Formatter


class PropertyItem(element.Element):
    attrs = None

    def process(self):
        attrs = element.extractAttributes(self.attrs, self.element, self)
        self.context.append(attrs)


class PropertyCollection(element.ContainerElement):
    propertyName = None
    attrs = None
    subElements = None

    def processAttributes(self):
        prop = getattr(self.context, self.propertyName)
        # Get global properties
        attrs = element.extractAttributes(self.attrs, self.element, self)
        for name, value in attrs.items():
            setattr(prop, name, value)

    def process(self):
        self.processAttributes()
        # Get item specific properties
        prop = getattr(self.context, self.propertyName)
        dataList = []
        self.processSubElements(dataList)
        for index, data in enumerate(dataList):
            for name, value in data.items():
                setattr(prop[index], name, value)


class Text(element.Element):
    attrs = (
        attr.Measurement('x'),
        attr.Measurement('y'),
        attr.Float('angle', 0),
        attr.TextNode(),
        attr.Measurement('fontSize'),
        attr.Color('fillColor'),
        attr.Text('fontName'),
        attr.Choice(
            'textAnchor',
            ('start','middle','end','boxauto')),
        )

    def process(self):
        attrs = element.extractAttributes(self.attrs, self.element, self)
        string = shapes.String(
            attrs.pop('x'), attrs.pop('y'), attrs.pop('TEXT'))
        angle = attrs.pop('angle')
        for name, value in attrs.items():
            setattr(string, name, value)
        group = shapes.Group(string)
        group.translate(0,0)
        group.rotate(angle)
        self.parent.parent.drawing.add(group)


class Texts(element.ContainerElement):
    subElements = {'text': Text}


class Series(element.Element):
    attrList = None

    def process(self):
        attrs = element.extractPositionalArguments(
            self.attrList, self.element, self)
        self.context.append(attrs[0])

class Data(element.ContainerElement):
    series = None

    def process(self):
        data = []
        self.subElements = {'series': self.series}
        self.processSubElements(data)
        self.context.data = data

class Series1D(Series):
    attrList = (attr.TextNodeSequence(attr.Float()),)

class Data1D(Data):
    series = Series1D

class SingleData1D(Data1D):

    def process(self):
        data = []
        self.subElements = {'series': self.series}
        self.processSubElements(data)
        self.context.data = data[0]

class Series2D(Series):
    attrList = (attr.TextNodeGrid(attr.Float(), 2),)

class Data2D(Data):
    series = Series2D


class Bar(PropertyItem):
    attrs = (
        attr.Color('strokeColor'),
        attr.Measurement('strokeWidth'),
        attr.Color('fillColor') )


class Bars(PropertyCollection):
    propertyName = 'bars'
    attrs = Bar.attrs
    subElements = {'bar': Bar}


class Label(PropertyItem):
    attrs = (
        attr.Measurement('x'),
        attr.Measurement('y'),
        attr.Measurement('dx'),
        attr.Measurement('dy'),
        attr.Float('angle'),
        attr.Choice(
            'boxAnchor',
            ('nw','n','ne','w','c','e','sw','s','se', 'autox', 'autoy')),
        attr.Color('boxStrokeColor'),
        attr.Measurement('boxStrokeWidth'),
        attr.Color('boxFillColor'),
        attr.Text('boxTarget'),
        attr.Color('fillColor'),
        attr.Color('strokeColor'),
        attr.Measurement('strokeWidth'),
        attr.Text('fontName'),
        attr.Measurement('fontSize'),
        attr.Measurement('leading'),
        attr.Measurement('width'),
        attr.Measurement('maxWidth'),
        attr.Measurement('height'),
        attr.Choice('textAnchor', ('start','middle','end','boxauto')),
        attr.Bool('visible'),
        attr.Measurement('topPadding'),
        attr.Measurement('leftPadding'),
        attr.Measurement('rightPadding'),
        attr.Measurement('bottomPadding'),
        attr.TextNode()
        )
    attrs[-1].name = 'text'


class Labels(PropertyCollection):
    propertyName = 'labels'
    attrs = Label.attrs[:-1]
    subElements = {'label': Label}


class Axis(element.ContainerElement):
    name = ''
    attrs = (
        attr.Bool('visible'),
        attr.Bool('visibleAxis'),
        attr.Bool('visibleTicks'),
        attr.Bool('visibleLabels'),
        attr.Bool('visibleGrid'),
        attr.Measurement('strokeWidth'),
        attr.Color('strokeColor'),
        attr.Sequence('strokeDashArray', attr.Float()),
        attr.Measurement('gridStrokeWidth'),
        attr.Color('gridStrokeColor'),
        attr.Sequence('gridStrokeDashArray', attr.Float()),
        attr.Measurement('gridStart'),
        attr.Measurement('gridEnd'),
        attr.Choice('style', ('parallel', 'stacked', 'parallel_3d')),
        )

    subElements = {'labels': Labels}

    def process(self):
        attrs = element.extractAttributes(self.attrs, self.element, self)
        axis = getattr(self.context, self.__name__)
        for name, value in attrs.items():
            setattr(axis, name, value)
        self.processSubElements(axis)


class Name(element.Element):
    attrs = (attr.TextNode(),)

    def process(self):
        attrs = element.extractAttributes(self.attrs, self.element, self)
        self.context.append(attrs['TEXT'])


class CategoryNames(element.ContainerElement):
    subElements = {'name': Name}

    def process(self):
        self.context.categoryNames = []
        self.processSubElements(self.context.categoryNames)

class CategoryAxis(Axis):
    name = 'categoryAxis'
    attrs = Axis.attrs + (
        attr.Sequence('categoryNames', attr.Text()),
        attr.Bool('joinAxis'),
        attr.Measurement('joinAxisPos'),
        attr.Bool('reverseDirection'),
        attr.Choice('labelAxisMode', ('high', 'low', 'axis')),
        attr.Bool('tickShift'),
        )
    subElements = Axis.subElements.copy()
    subElements.update({
        'categoryNames': CategoryNames,
        })

class XCategoryAxis(CategoryAxis):
    attrs = CategoryAxis.attrs + (
        attr.Measurement('tickUp'),
        attr.Measurement('tickDown'),
        attr.Choice('joinAxisMode',
                    ('bottom', 'top', 'value', 'points', 'None')) )


class YCategoryAxis(CategoryAxis):
    attrs = CategoryAxis.attrs + (
        attr.Measurement('tickLeft'),
        attr.Measurement('tickRight'),
        attr.Choice('joinAxisMode',
                    ('bottom', 'top', 'value', 'points', 'None')) )


class ValueAxis(Axis):
    name = 'valueAxis'
    attrs = Axis.attrs + (
        attr.Bool('forceZero'), # TODO: Support 'near'
        attr.Measurement('minimumTickSpacing'),
        attr.Int('maximumTicks'),
        attr.Attribute('labelTextFormat'),
        attr.Text('labelTextPostFormat'),
        attr.Float('labelTextScale'),
        attr.Float('valueMin'),
        attr.Float('valueMax'),
        attr.Float('valueStep'),
        attr.Measurement('valueSteps'),
        attr.Text('rangeRound'),
        attr.Float('zrangePref'),
        )


class XValueAxis(ValueAxis):
    attrs = ValueAxis.attrs + (
        attr.Measurement('tickUp'),
        attr.Measurement('tickDown'),
        attr.Bool('joinAxis'),
        attr.Choice('joinAxisMode',
                    ('bottom', 'top', 'value', 'points', 'None')),
        attr.Float('joinAxisPos'),
        )

class YValueAxis(ValueAxis):
    attrs = ValueAxis.attrs + (
        attr.Measurement('tickLeft'),
        attr.Measurement('tickRight'),
        attr.Bool('joinAxis'),
        attr.Choice('joinAxisMode',
                    ('bottom', 'top', 'value', 'points', 'None')),
        attr.Float('joinAxisPos'),
        )


class Line(PropertyItem):
    attrs = (
        attr.Measurement('strokeWidth'),
        attr.Color('strokeColor'),
        attr.Sequence('strokeDashArray', attr.Float()),
        attr.Symbol('symbol'),
        attr.Text('name'),
        )


class Lines(PropertyCollection):
    propertyName = 'lines'
    attrs = Line.attrs[:-1]
    subElements = {'line': Line}


class SliceLabel(Label):
    attrs = Label.attrs[2:]

    def process(self):
        attrs = element.extractAttributes(self.attrs, self.element, self)
        for name, value in attrs.items():
            self.context['label_'+name] = value
        # Now we do not have simple labels anymore
        self.parent.parent.context.simpleLabels = False

class SlicePointer(element.Element):
    attrs = (
        attr.Color('strokeColor'),
        attr.Measurement('strokeWidth'),
        attr.Measurement('elbowLength'),
        attr.Measurement('edgePad'),
        attr.Measurement('piePad'),
        )

    def process(self):
        attrs = element.extractAttributes(self.attrs, self.element, self)
        for name, value in attrs.items():
            self.context['label_pointer_'+name] = value

class Slice(element.ContainerElement):
    attrs = (
        attr.Measurement('strokeWidth'),
        attr.Color('fillColor'),
        attr.Color('strokeColor'),
        attr.Sequence('strokeDashArray', attr.Float()),
        attr.Measurement('popout'),
        attr.Text('fontName'),
        attr.Measurement('fontSize'),
        attr.Measurement('labelRadius'),
        attr.Symbol('swatchMarker'),
        )

    subElements = {
        'label': SliceLabel,
        'pointer': SlicePointer}

    def process(self):
        attrs = element.extractAttributes(self.attrs, self.element, self)
        self.processSubElements(attrs)
        self.context.append(attrs)

class Slice3D(Slice):
    attrs = Slice.attrs + (
        attr.Color('fillColorShaded'),
        )

    subElements = {}
    # Sigh, the 3-D Pie does not support advanced slice labels. :-(
    #     'label': SliceLabel}

class Slices(element.ContainerElement):
    attrs = Slice.attrs[:-1]
    subElements = {'slice': Slice}

    def process(self):
        # Get global slice properties
        attrs = element.extractAttributes(self.attrs, self.element, self)
        for name, value in attrs.items():
            setattr(self.context.slices, name, value)
        # Get slice specific properties
        slicesData = []
        self.processSubElements(slicesData)
        for index, sliceData in enumerate(slicesData):
            for name, value in sliceData.items():
                setattr(self.context.slices[index], name, value)

class Slices3D(Slices):
    attrs = Slice3D.attrs[:-1]
    subElements = {'slice': Slice3D}


class SimpleLabels(element.ContainerElement):
    subElements = {'label': Name}

    def process(self):
        self.context.labels = []
        self.processSubElements(self.context.labels)


class Strand(PropertyItem):
    attrs = (
        attr.Measurement('strokeWidth'),
        attr.Color('fillColor'),
        attr.Color('strokeColor'),
        attr.Sequence('strokeDashArray', attr.Float()),
        attr.Symbol('symbol'),
        attr.Measurement('symbolSize'),
        attr.Text('name'),
        )


class Strands(PropertyCollection):
    propertyName = 'strands'
    attrs = Strand.attrs[:-1]
    subElements = {'strand': Strand}


class StrandLabel(Label):
    attrs = Label.attrs[2:-1] + (attr.TextNode(),)
    attrs[-1].name = '_text'
    attrs += (
        attr.Int('row'),
        attr.Int('col'),
        attr.Attribute('format'),
        attr.Float('dR')
        )

class StrandLabels(PropertyCollection):
    propertyName = 'strandLabels'
    attrs = StrandLabel.attrs[:-1]
    subElements = {'label': StrandLabel}

    def process(self):
        self.processAttributes()
        # Get item specific properties
        prop = getattr(self.context, self.propertyName)
        dataList = []
        self.processSubElements(dataList)
        for data in dataList:
            row = data.pop('row')
            col = data.pop('col')
            for name, value in data.items():
                setattr(prop[row, col], name, value)


class Spoke(PropertyItem):
    attrs = (
        attr.Measurement('strokeWidth'),
        attr.Color('fillColor'),
        attr.Color('strokeColor'),
        attr.Sequence('strokeDashArray', attr.Float()),
        attr.Measurement('labelRadius'),
        attr.Bool('visible'),
        )


class Spokes(PropertyCollection):
    propertyName = 'spokes'
    attrs = Spoke.attrs[:-1]
    subElements = {'spoke': Spoke}


class SpokeLabel(Label):
    attrs = Label.attrs[2:-1] + (attr.TextNode(),)
    attrs[-1].name = '_text'

class SpokeLabels(PropertyCollection):
    propertyName = 'spokeLabels'
    attrs = SpokeLabel.attrs[:-1]
    subElements = {'label': SpokeLabel}


class Chart(element.ContainerElement):
    attrs = (
        # Drawing Options
        attr.Measurement('dx'),
        attr.Measurement('dy'),
        attr.Measurement('dwidth'),
        attr.Measurement('dheight'),
        attr.Float('angle'),
        # Plot Area Options
        attr.Measurement('x'),
        attr.Measurement('y'),
        attr.Measurement('width'),
        attr.Measurement('height'),
        attr.Color('strokeColor'),
        attr.Measurement('strokeWidth'),
        attr.Color('fillColor'),
        attr.Bool('debug'),
        )

    subElements = {
        'texts': Texts
        }

    def getAttributes(self):
        attrs = [(attr.name, attr) for attr in self.attrs]
        return element.extractKeywordArguments(attrs, self.element, self)

    def createChart(self, attributes):
        raise NotImplementedError

    def process(self):
        attrs = self.getAttributes()
        angle = attrs.pop('angle', 0)
        x, y = attrs.pop('dx'), attrs.pop('dy')
        self.drawing = shapes.Drawing(attrs.pop('dwidth'), attrs.pop('dheight'))
        chart = self.createChart(attrs)
        self.processSubElements(chart)
        group = shapes.Group(chart)
        group.translate(0,0)
        group.rotate(angle)
        self.drawing.add(group)
        self.drawing.drawOn(self.context, x, y)


class BarChart(Chart):
    nameBase = 'BarChart'
    attrs = Chart.attrs + (
        attr.Choice('direction', ('horizontal', 'vertical'), 'horizontal'),
        attr.Bool('useAbsolute', False),
        attr.Measurement('barWidth', 10),
        attr.Measurement('groupSpacing', 5),
        attr.Measurement('barSpacing', 0),
        )

    subElements = Chart.subElements.copy()
    subElements.update({
        'data': Data1D,
        'bars': Bars,
        })

    def createChart(self, attrs):
        direction = attrs.pop('direction')
        # Setup sub-elements based on direction
        if direction == 'horizontal':
            self.subElements['categoryAxis'] = YCategoryAxis
            self.subElements['valueAxis'] = XValueAxis
        else:
            self.subElements['categoryAxis'] = XCategoryAxis
            self.subElements['valueAxis'] = YValueAxis
        # Generate the chart
        chart = getattr(
            barcharts, direction.capitalize()+self.nameBase)()
        for name, value in attrs.items():
            setattr(chart, name, value)
        return chart


class BarChart3D(BarChart):
    nameBase = 'BarChart3D'
    attrs = BarChart.attrs + (
        attr.Float('theta_x'),
        attr.Float('theta_y'),
        attr.Measurement('zDepth'),
        attr.Measurement('zSpace')
        )


class LinePlot(Chart):
    attrs = Chart.attrs + (
        attr.Bool('reversePlotOrder'),
        attr.Measurement('lineLabelNudge'),
        attr.Attribute('lineLabelFormat'),
        attr.Bool('joinedLines'),
        )

    subElements = Chart.subElements.copy()
    subElements.update({
        'data': Data2D,
        'lines': Lines,
        'xValueAxis': XValueAxis,
        'yValueAxis': YValueAxis,
        'lineLabels': Labels,
        })

    def createChart(self, attrs):
        # Generate the chart
        chart = lineplots.LinePlot()
        for name, value in attrs.items():
            setattr(chart, name, value)
        return chart

class PieChart(Chart):
    chartClass = piecharts.Pie
    attrs = Chart.attrs + (
        attr.Int('startAngle'),
        attr.Choice('direction', ('clockwise', 'anticlockwise')),
        attr.Bool('checkLabelOverlap'),
        attr.Choice('pointerLabelMode',
                    {'none': None,
                     'leftright': 'LeftRight',
                     'leftandright': 'LeftAndRight'}),
        attr.Bool('sameRadii'),
        attr.Choice('orderMode', ('fixed', 'alternate')),
        attr.Measurement('xradius'),
        attr.Measurement('yradius'),
        )

    subElements = Chart.subElements.copy()
    subElements.update({
        'data': SingleData1D,
        'slices': Slices,
        'labels': SimpleLabels,
        })

    def createChart(self, attrs):
        # Generate the chart
        chart = self.chartClass()
        for name, value in attrs.items():
            setattr(chart, name, value)
        return chart

class PieChart3D(PieChart):
    chartClass = piecharts.Pie3d
    attrs = PieChart.attrs + (
        attr.Float('perspective'),
        attr.Measurement('depth_3d'),
        attr.Float('angle_3d'),
        )

    subElements = PieChart.subElements.copy()
    subElements.update({
        'slices': Slices3D,
        })

class SpiderChart(Chart):
    attrs = Chart.attrs + (
        attr.Int('startAngle'),
        attr.Choice('direction', ('clockwise', 'anticlockwise')),
        attr.Float('startAngle'),
        )

    subElements = Chart.subElements.copy()
    subElements.update({
        'data': Data1D,
        'strands': Strands,
        'strandLabels': StrandLabels,
        'spokes': Spokes,
        'spokeLabels': SpokeLabels,
        'labels': SimpleLabels,
        })

    def createChart(self, attrs):
        # Generate the chart
        chart = spider.SpiderChart()
        for name, value in attrs.items():
            setattr(chart, name, value)
        return chart
