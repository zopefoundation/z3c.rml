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
from z3c.rml import attrng, directive, interfaces, occurence

# Patches against Reportlab 2.0
lineplots.Formatter = reportlab.lib.formatters.Formatter


class PropertyItem(directive.RMLDirective):

    def process(self):
        attrs = dict(self.getAttributeValues())
        self.parent.dataList.append(attrs)


class PropertyCollection(directive.RMLDirective):
    propertyName = None

    def processAttributes(self):
        prop = getattr(self.parent.context, self.propertyName)
        # Get global properties
        for name, value in self.getAttributeValues():
            setattr(prop, name, value)

    def process(self):
        self.processAttributes()
        # Get item specific properties
        prop = getattr(self.parent.context, self.propertyName)
        self.dataList = []
        self.processSubDirectives()
        for index, data in enumerate(self.dataList):
            for name, value in data.items():
                setattr(prop[index], name, value)


class IText(interfaces.IRMLDirectiveSignature):
    """Draw a text on the chart."""

    x = attrng.Measurement(
        title=u'X-Coordinate',
        description=(u'The X-coordinate of the lower-left position of the '
                     u'text.'),
        required=True)

    y = attrng.Measurement(
        title=u'Y-Coordinate',
        description=(u'The Y-coordinate of the lower-left position of the '
                     u'text.'),
        required=True)

    angle = attrng.Float(
        title=u'Rotation Angle',
        description=(u'The angle about which the text will be rotated.'),
        required=False)

    text = attrng.TextNode(
        title=u'Text',
        description=u'The text to be printed.',
        required=True)

    fontName = attrng.String(
        title=u'Font Name',
        description=u'The name of the font.',
        required=False)

    fontSize = attrng.Measurement(
        title=u'Font Size',
        description=u'The font size for the text.',
        required=False)

    fillColor = attrng.Color(
        title=u'Fill Color',
        description=u'The color in which the text will appear.',
        required=False)

    textAnchor = attrng.Choice(
        title=u'Text Anchor',
        description=u'The position in the text to which the coordinates refer.',
        choices=('start', 'middle', 'end', 'boxauto'),
        required=False)


class Text(directive.RMLDirective):
    signature = IText

    def process(self):
        attrs = dict(self.getAttributeValues())
        string = shapes.String(
            attrs.pop('x'), attrs.pop('y'), attrs.pop('text'))
        angle = attrs.pop('angle', 0)
        for name, value in attrs.items():
            setattr(string, name, value)
        group = shapes.Group(string)
        group.translate(0,0)
        group.rotate(angle)
        self.parent.parent.drawing.add(group)


class ITexts(interfaces.IRMLDirectiveSignature):
    """A set of texts drawn on the chart."""
    occurence.containing(
        occurence.ZeroOrMore('text', IText)
        )

class Texts(directive.RMLDirective):
    signature = ITexts
    factories = {'text': Text}


class Series(directive.RMLDirective):

    def process(self):
        attrs = self.getAttributeValues(valuesOnly=True)
        self.parent.data.append(attrs[0])


class Data(directive.RMLDirective):
    series = None

    def process(self):
        self.data = []
        self.factories = {'series': self.series}
        self.processSubDirectives()
        self.parent.context.data = self.data


class ISeries1D(interfaces.IRMLDirectiveSignature):
    """A one-dimensional series."""

    values = attrng.TextNodeSequence(
        title=u'Values',
        description=u"Numerical values representing the series' data.",
        value_type=attrng.Float(),
        required=True)

class Series1D(Series):
    signature = ISeries1D

class Data1D(Data):
    series = Series1D

class SingleData1D(Data1D):

    def process(self):
        self.data = []
        self.factories = {'series': self.series}
        self.processSubDirectives()
        self.parent.context.data = self.data[0]


class ISeries2D(interfaces.IRMLDirectiveSignature):
    """A two-dimensional series."""

    values = attrng.TextNodeGrid(
        title=u'Values',
        description=u"Numerical values representing the series' data.",
        value_type=attrng.Float(),
        columns=2,
        required=True)

class Series2D(Series):
    signature = ISeries2D

class Data2D(Data):
    series = Series2D


class IBar(interfaces.IRMLDirectiveSignature):
    """Define the look of a bar."""

    strokeColor = attrng.Color(
        title=u'Stroke Color',
        description=u'The color in which the bar border is drawn.',
        required=False)

    strokeWidth = attrng.Measurement(
        title=u'Stroke Width',
        description=u'The width of the bar border line.',
        required=False)

    fillColor = attrng.Color(
        title=u'Fill Color',
        description=u'The color with which the bar is filled.',
        required=False)

class Bar(PropertyItem):
    signature = IBar

class IBars(IBar):
    """Collection of bar subscriptions."""
    occurence.containing(
        occurence.ZeroOrMore('bar', IBar)
        )

class Bars(PropertyCollection):
    signature = IBars
    propertyName = 'bars'
    factories = {'bar': Bar}


class ILabelBase(interfaces.IRMLDirectiveSignature):

    dx = attrng.Measurement(
        title=u'Horizontal Extension',
        description=(u'The width of the label.'),
        required=False)

    dy = attrng.Measurement(
        title=u'Vertical Extension',
        description=(u'The height of the label.'),
        required=False)

    angle = attrng.Float(
        title=u'Angle',
        description=(u'The angle to rotate the label.'),
        required=False)

    boxAnchor = attrng.Choice(
        title=u'Box Anchor',
        description=(u'The position relative to the label.'),
        choices=('nw','n','ne','w','c','e','sw','s','se', 'autox', 'autoy'),
        required=False)

    boxStrokeColor = attrng.Color(
        title=u'Box Stroke Color',
        description=(u'The color of the box border line.'),
        required=False)

    boxStrokeWidth = attrng.Measurement(
        title=u'Box Stroke Width',
        description=u'The width of the box border line.',
        required=False)

    boxFillColor = attrng.Color(
        title=u'Box Fill Color',
        description=(u'The color in which the box is filled.'),
        required=False)

    boxTarget = attrng.Text(
        title=u'Box Target',
        description=u'The box target.',
        required=False)

    fillColor = attrng.Color(
        title=u'Fill Color',
        description=(u'The color in which the label is filled.'),
        required=False)

    strokeColor = attrng.Color(
        title=u'Stroke Color',
        description=(u'The color of the label.'),
        required=False)

    strokeWidth = attrng.Measurement(
        title=u'Stroke Width',
        description=u'The width of the label line.',
        required=False)

    frontName = attrng.String(
        title=u'Font Name',
        description=u'The font used to print the value.',
        required=False)

    frontSize = attrng.Measurement(
        title=u'Font Size',
        description=u'The size of the value text.',
        required=False)

    leading = attrng.Measurement(
        title=u'Leading',
        description=(u'The height of a single text line. It includes '
                     u'character height.'),
        required=False)

    width = attrng.Measurement(
        title=u'Width',
        description=u'The width the label.',
        required=False)

    maxWidth = attrng.Measurement(
        title=u'Maximum Width',
        description=u'The maximum width the label.',
        required=False)

    height = attrng.Measurement(
        title=u'Height',
        description=u'The height the label.',
        required=False)

    textAnchor = attrng.Choice(
        title=u'Text Anchor',
        description=u'The position in the text to which the coordinates refer.',
        choices=('start', 'middle', 'end', 'boxauto'),
        required=False)

    visible = attrng.Boolean(
        title=u'Visible',
        description=u'A flag making the label text visible.',
        required=False)

    leftPadding = attrng.Measurement(
        title=u'Left Padding',
        description=u'The size of the padding on the left side.',
        required=False)

    rightPadding = attrng.Measurement(
        title=u'Right Padding',
        description=u'The size of the padding on the right side.',
        required=False)

    topPadding = attrng.Measurement(
        title=u'Top Padding',
        description=u'The size of the padding on the top.',
        required=False)

    bottomPadding = attrng.Measurement(
        title=u'Bottom Padding',
        description=u'The size of the padding on the bottom.',
        required=False)


class IPositionLabelBase(ILabelBase):

    x = attrng.Measurement(
        title=u'X-Coordinate',
        description=(u'The X-coordinate of the lower-left position of the '
                     u'label.'),
        required=False)

    y = attrng.Measurement(
        title=u'Y-Coordinate',
        description=(u'The Y-coordinate of the lower-left position of the '
                     u'label.'),
        required=False)


class ILabel(IPositionLabelBase):
    """A label for the chart."""

    text = attrng.TextNode(
        title=u'Text',
        description=u'The label text to be displayed.',
        required=True)

class Label(PropertyItem):
    signature = ILabel


class ILabels(IPositionLabelBase):
    """A set of labels."""
    occurence.containing(
        occurence.ZeroOrMore('label', ILabel)
        )

class Labels(PropertyCollection):
    signature = ILabels
    propertyName = 'labels'
    factories = {'label': Label}


class IAxis(interfaces.IRMLDirectiveSignature):
    occurence.containing(
        occurence.ZeroOrMore('labels', ILabels)
        )

    visible = attrng.Boolean(
        required=False)

    visibleAxis = attrng.Boolean(
        required=False)

    visibleTicks = attrng.Boolean(
        required=False)

    visibleLabels = attrng.Boolean(
        required=False)

    visibleGrid = attrng.Boolean(
        required=False)

    strokeWidth = attrng.Measurement(
        required=False)

    strokeColor = attrng.Color(
        required=False)

    strokeDashArray = attrng.Sequence(
        value_type=attrng.Float(),
        required=False)

    gridStrokeWidth = attrng.Measurement(
        required=False)

    gridStrokeColor = attrng.Color(
        required=False)

    gridStrokeDashArray = attrng.Sequence(
        value_type=attrng.Float(),
        required=False)

    gridStart = attrng.Measurement(
        required=False)

    gridEnd = attrng.Measurement(
        required=False)

    style = attrng.Choice(
        choices=('parallel', 'stacked', 'parallel_3d'),
        required=False)


class Axis(directive.RMLDirective):
    signature = IAxis
    name = ''
    factories = {'labels': Labels}

    def process(self):
        self.context = axis = getattr(self.parent.context, self.name)
        for name, value in self.getAttributeValues():
            setattr(axis, name, value)
        self.processSubDirectives()


class IName(interfaces.IRMLDirectiveSignature):

    text = attrng.TextNode(
        title=u'Text',
        required=True)

class Name(directive.RMLDirective):
    signature = IName

    def process(self):
        text = self.getAttributeValues(valuesOnly=True)[0]
        self.parent.names.append(text)


class CategoryNames(directive.RMLDirective):
    factories = {'name': Name}

    def process(self):
        self.names = []
        self.processSubDirectives()
        self.parent.context.categoryNames = self.names


class ICategoryAxis(IAxis):

    categoryNames = attrng.Sequence(
        value_type=attrng.Text(),
        required=False)

    joinAxis = attrng.Boolean(
        required=False)

    joinAxisPos = attrng.Measurement(
        required=False)

    reverseDirection = attrng.Boolean(
        required=False)

    labelAxisMode = attrng.Choice(
        choices=('high', 'low', 'axis'),
        required=False)

    tickShift = attrng.Boolean(
        required=False)

class CategoryAxis(Axis):
    signature = ICategoryAxis
    name = 'categoryAxis'
    factories = Axis.factories.copy()
    factories.update({
        'categoryNames': CategoryNames,
        })


class IXCategoryAxis(ICategoryAxis):

    tickUp = attrng.Measurement(
        required=False)

    tickDown = attrng.Measurement(
        required=False)

    joinAxisMode = attrng.Choice(
        choices=('bottom', 'top', 'value', 'points', 'None'),
        required=False)

class XCategoryAxis(CategoryAxis):
    signature = IXCategoryAxis


class IYCategoryAxis(ICategoryAxis):

    tickLeft = attrng.Measurement(
        required=False)

    tickRight = attrng.Measurement(
        required=False)

    joinAxisMode = attrng.Choice(
        choices=('bottom', 'top', 'value', 'points', 'None'),
        required=False)

class YCategoryAxis(CategoryAxis):
    signature = IYCategoryAxis


class IValueAxis(IAxis):

    forceZero = attrng.Boolean(
        required=False)

    minimumTickSpacing = attrng.Measurement(
        required=False)

    maximumTicks = attrng.Integer(
        required=False)

    labelTextFormat = attrng.String(
        required=False)

    labelTextPostFormat = attrng.Text(
        required=False)

    labelTextScale = attrng.Float(
        required=False)

    valueMin = attrng.Float(
        required=False)

    valueMax = attrng.Float(
        required=False)

    valueStep = attrng.Float(
        required=False)

    valueSteps = attrng.Measurement(
        required=False)

    rangeRound = attrng.Text(
        required=False)

    zrangePref = attrng.Float(
        required=False)

class ValueAxis(Axis):
    signature = IValueAxis
    name = 'valueAxis'


class IXValueAxis(IValueAxis):

    tickUp = attrng.Measurement(
        required=False)

    tickDown = attrng.Measurement(
        required=False)

    joinAxis = attrng.Boolean(
        required=False)

    joinAxisMode = attrng.Choice(
        choices=('bottom', 'top', 'value', 'points', 'None'),
        required=False)

    joinAxisPos = attrng.Measurement(
        required=False)

class XValueAxis(ValueAxis):
    signature = IXValueAxis

class LineXValueAxis(XValueAxis):
    name = 'xValueAxis'

class IYValueAxis(IValueAxis):

    tickLeft = attrng.Measurement(
        required=False)

    tickRight = attrng.Measurement(
        required=False)

    joinAxis = attrng.Boolean(
        required=False)

    joinAxisMode = attrng.Choice(
        choices=('bottom', 'top', 'value', 'points', 'None'),
        required=False)

    joinAxisPos = attrng.Measurement(
        required=False)

class YValueAxis(ValueAxis):
    signature = IYValueAxis

class LineYValueAxis(YValueAxis):
    name = 'yValueAxis'


class ILineBase(interfaces.IRMLDirectiveSignature):

    strokeWidth = attrng.Measurement(
        required=False)

    strokeColor = attrng.Color(
        required=False)

    strokeDashArray = attrng.Sequence(
        value_type = attrng.Float(),
        required=False)

    symbol = attrng.Symbol(
        required=False)

class ILine(ILineBase):

    name = attrng.Text(
        required=False)

class Line(PropertyItem):
    signature = ILine

class ILines(ILineBase):
    pass

class Lines(PropertyCollection):
    signature = ILines
    propertyName = 'lines'
    factories = {'line': Line}


class ISliceLabel(ILabelBase):

    text = attrng.TextNode(
        title=u'Text',
        description=u'The label text to be displayed.',
        required=True)

class SliceLabel(Label):
    signature = ISliceLabel

    def process(self):
        for name, value in self.getAttributeValues():
            self.parent.context['label_'+name] = value
        # Now we do not have simple labels anymore
        self.parent.parent.parent.context.simpleLabels = False


class ISlicePointer(interfaces.IRMLDirectiveSignature):

    strokeColor = attrng.Color(
        required=False)

    strokeWidth = attrng.Measurement(
        required=False)

    elbowLength = attrng.Measurement(
        required=False)

    edgePad = attrng.Measurement(
        required=False)

    piePad = attrng.Measurement(
        required=False)

class SlicePointer(directive.RMLDirective):
    signature = ISlicePointer

    def process(self):
        for name, value in self.getAttributeValues():
            self.parent.context['label_pointer_'+name] = value


class ISliceBase(interfaces.IRMLDirectiveSignature):

    strokeWidth = attrng.Measurement(
        required=False)

    fillColor = attrng.Color(
        required=False)

    strokeColor = attrng.Color(
        required=False)

    strokeDashArray = attrng.Sequence(
        value_type=attrng.Float(),
        required=False)

    popout = attrng.Measurement(
        required=False)

    fontName = attrng.String(
        required=False)

    fontSize = attrng.Measurement(
        required=False)

    labelRadius = attrng.Measurement(
        required=False)

class ISlice(ISliceBase):

    swatchMarker = attrng.Symbol(
        required=False)


class Slice(directive.RMLDirective):
    signature = ISlice
    factories = {
        'label': SliceLabel,
        'pointer': SlicePointer}

    def process(self):
        self.context = attrs = dict(self.getAttributeValues())
        self.processSubDirectives()
        self.parent.context.append(attrs)


class ISlice3D(ISlice):

    fillColorShaded = attrng.Color(
        required=False)

class Slice3D(Slice):
    signature = ISlice3D
    subElements = {}
    # Sigh, the 3-D Pie does not support advanced slice labels. :-(
    #     'label': SliceLabel}


class ISlices(ISliceBase):
    pass

class Slices(directive.RMLDirective):
    signature = ISlices
    factories = {'slice': Slice}

    def process(self):
        # Get global slice properties
        for name, value in self.getAttributeValues():
            setattr(self.parent.context.slices, name, value)
        # Get slice specific properties
        self.context = slicesData = []
        self.processSubDirectives()
        for index, sliceData in enumerate(slicesData):
            for name, value in sliceData.items():
                setattr(self.parent.context.slices[index], name, value)


class ISlices3D(ISliceBase):

    fillColorShaded = attrng.Color(
        required=False)

class Slices3D(Slices):
    signature = ISlices3D
    factories = {'slice': Slice3D}


class SimpleLabels(directive.RMLDirective):
    factories = {'label': Name}

    def process(self):
        self.names = []
        self.processSubDirectives()
        self.parent.context.labels = self.names


class IStrandBase(interfaces.IRMLDirectiveSignature):

    strokeWidth = attrng.Measurement(
        required=False)

    fillColor = attrng.Color(
        required=False)

    strokeColor= attrng.Color(
        required=False)

    strokeDashArray = attrng.Sequence(
        value_type=attrng.Float(),
        required=False)

    symbol = attrng.Symbol(
        required=False)

    symbolSize = attrng.Measurement(
        required=False)

class IStrand(IStrandBase):

     name = attrng.Text(
        required=False)

class Strand(PropertyItem):
    signature = IStrand

class Strands(PropertyCollection):
    signature = IStrandBase
    propertyName = 'strands'
    attrs = IStrandBase
    factories = {'strand': Strand}


class IStrandLabelBase(ILabelBase):

    _text = attrng.TextNode(
        required=False)

    row = attrng.Integer(
        required=False)

    col = attrng.Integer(
        required=False)

    format = attrng.String(
        required=False)

class IStrandLabel(IStrandLabelBase):

    dR = attrng.Float(
        required=False)

class StrandLabel(Label):
    signature = IStrandLabel

class StrandLabels(PropertyCollection):
    signature = IStrandLabelBase
    propertyName = 'strandLabels'
    factories = {'label': StrandLabel}

    def process(self):
        self.processAttributes()
        # Get item specific properties
        prop = getattr(self.parent.context, self.propertyName)
        self.dataList = []
        self.processSubDirectives()
        for data in self.dataList:
            row = data.pop('row')
            col = data.pop('col')
            for name, value in data.items():
                setattr(prop[row, col], name, value)


class ISpoke(interfaces.IRMLDirectiveSignature):

    strokeWidth = attrng.Measurement(
        required=False)

    fillColor = attrng.Color(
        required=False)

    strokeColor= attrng.Color(
        required=False)

    strokeDashArray = attrng.Sequence(
        value_type=attrng.Float(),
        required=False)

    labelRadius = attrng.Measurement(
        required=False)

    visible = attrng.Measurement(
        required=False)

class Spoke(PropertyItem):
    signature = ISpoke

class Spokes(PropertyCollection):
    signature = ISpoke
    propertyName = 'spokes'
    factories = {'spoke': Spoke}


class ISpokeLabelBase(ILabelBase):
    pass

class ISpokeLabel(ISpokeLabelBase):

    _text = attrng.TextNode(
        required=False)

class SpokeLabel(Label):
    signature = ISpokeLabel

class SpokeLabels(PropertyCollection):
    signature = ISpokeLabelBase
    propertyName = 'spokeLabels'
    factories = {'label': SpokeLabel}


class IChart(interfaces.IRMLDirectiveSignature):

    # Drawing Options

    dx = attrng.Measurement(
        required=False)

    dy = attrng.Measurement(
        required=False)

    dwidth = attrng.Measurement(
        required=False)

    dheight = attrng.Measurement(
        required=False)

    angle = attrng.Float(
        required=False)

    # Plot Area Options

    x = attrng.Measurement(
        required=False)

    y = attrng.Measurement(
        required=False)

    width = attrng.Measurement(
        required=False)

    height = attrng.Measurement(
        required=False)

    strokeColor = attrng.Color(
        required=False)

    strokeWidth = attrng.Measurement(
        required=False)

    fillColor = attrng.Color(
        required=False)

    debug = attrng.Boolean(
        required=False)

class Chart(directive.RMLDirective):
    signature = IChart
    factories = {
        'texts': Texts
        }

    def createChart(self, attributes):
        raise NotImplementedError

    def process(self):
        attrs = dict(self.getAttributeValues())
        angle = attrs.pop('angle', 0)
        x, y = attrs.pop('dx'), attrs.pop('dy')
        self.drawing = shapes.Drawing(attrs.pop('dwidth'), attrs.pop('dheight'))
        self.context = chart = self.createChart(attrs)
        self.processSubDirectives()
        group = shapes.Group(chart)
        group.translate(0,0)
        group.rotate(angle)
        self.drawing.add(group)
        manager = attrng.getManager(self, interfaces.ICanvasManager)
        self.drawing.drawOn(manager.canvas, x, y)


class IBarChart(IChart):

    direction = attrng.Choice(
        choices=('horizontal', 'vertical'),
        default='horizontal',
        required=False)

    useAbsolute = attrng.Boolean(
        default=False,
        required=False)

    barWidth = attrng.Measurement(
        default=10,
        required=False)

    groupSpacing = attrng.Measurement(
        default=5,
        required=False)

    barSpacing = attrng.Measurement(
        default=0,
        required=False)

class BarChart(Chart):
    signature = IBarChart
    nameBase = 'BarChart'
    factories = Chart.factories.copy()
    factories.update({
        'data': Data1D,
        'bars': Bars,
        })

    def createChart(self, attrs):
        direction = attrs.pop('direction')
        # Setup sub-elements based on direction
        if direction == 'horizontal':
            self.factories['categoryAxis'] = YCategoryAxis
            self.factories['valueAxis'] = XValueAxis
        else:
            self.factories['categoryAxis'] = XCategoryAxis
            self.factories['valueAxis'] = YValueAxis
        # Generate the chart
        chart = getattr(
            barcharts, direction.capitalize()+self.nameBase)()
        for name, value in attrs.items():
            setattr(chart, name, value)
        return chart


class IBarChart3D(IBarChart):

    theta_x = attrng.Float(
        required=False)

    theta_y = attrng.Float(
        required=False)

    zDepth = attrng.Measurement(
        required=False)

    zSpace = attrng.Measurement(
        required=False)

class BarChart3D(BarChart):
    signature = IBarChart3D
    nameBase = 'BarChart3D'


class ILinePlot(IChart):

    reversePlotOrder = attrng.Boolean(
        required=False)

    lineLabelNudge = attrng.Measurement(
        required=False)

    lineLabelFormat = attrng.String(
        required=False)

    joinedLines = attrng.Boolean(
        required=False)

class LinePlot(Chart):
    signature = ILinePlot

    factories = Chart.factories.copy()
    factories.update({
        'data': Data2D,
        'lines': Lines,
        'xValueAxis': LineXValueAxis,
        'yValueAxis': LineYValueAxis,
        'lineLabels': Labels,
        })

    def createChart(self, attrs):
        # Generate the chart
        chart = lineplots.LinePlot()
        for name, value in attrs.items():
            setattr(chart, name, value)
        return chart


class IPieChart(IChart):

    startAngle = attrng.Integer(
        required=False)

    direction = attrng.Choice(
        choices=('clockwise', 'anticlockwise'),
        required=False)

    checkLabelOverlap = attrng.Boolean(
        required=False)

    pointerLabelMode = attrng.Choice(
        choices={'none': None,
                 'leftright': 'LeftRight',
                 'leftandright': 'LeftAndRight'},
        required=False)

    sameRadii = attrng.Boolean(
        required=False)

    orderMode = attrng.Choice(
        choices=('fixed', 'alternate'),
        required=False)

    xradius = attrng.Measurement(
        required=False)

    yradius = attrng.Measurement(
        required=False)


class PieChart(Chart):
    signature = IPieChart
    chartClass = piecharts.Pie

    factories = Chart.factories.copy()
    factories.update({
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


class IPieChart3D(IPieChart):

    perspective = attrng.Float(
        required=False)

    depth_3d = attrng.Measurement(
        required=False)

    angle_3d = attrng.Float(
        required=False)

class PieChart3D(PieChart):
    signature = IPieChart3D
    chartClass = piecharts.Pie3d

    factories = PieChart.factories.copy()
    factories.update({
        'slices': Slices3D,
        })


class ISpiderChart(IChart):

    startAngle = attrng.Integer(
        required=False)

    direction = attrng.Choice(
        choices=('clockwise', 'anticlockwise'),
        required=False)

class SpiderChart(Chart):
    signature = ISpiderChart
    factories = Chart.factories.copy()
    factories.update({
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
