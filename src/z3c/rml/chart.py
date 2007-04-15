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
from z3c.rml import attr, directive, interfaces, occurence

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

    x = attr.Measurement(
        title=u'X-Coordinate',
        description=(u'The X-coordinate of the lower-left position of the '
                     u'text.'),
        required=True)

    y = attr.Measurement(
        title=u'Y-Coordinate',
        description=(u'The Y-coordinate of the lower-left position of the '
                     u'text.'),
        required=True)

    angle = attr.Float(
        title=u'Rotation Angle',
        description=(u'The angle about which the text will be rotated.'),
        required=False)

    text = attr.TextNode(
        title=u'Text',
        description=u'The text to be printed.',
        required=True)

    fontName = attr.String(
        title=u'Font Name',
        description=u'The name of the font.',
        required=False)

    fontSize = attr.Measurement(
        title=u'Font Size',
        description=u'The font size for the text.',
        required=False)

    fillColor = attr.Color(
        title=u'Fill Color',
        description=u'The color in which the text will appear.',
        required=False)

    textAnchor = attr.Choice(
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

    values = attr.TextNodeSequence(
        title=u'Values',
        description=u"Numerical values representing the series' data.",
        value_type=attr.Float(),
        required=True)

class Series1D(Series):
    signature = ISeries1D


class IData1D(interfaces.IRMLDirectiveSignature):
    """A 1-D data set."""
    occurence.containing(
        occurence.OneOrMore('series', ISeries1D)
        )

class Data1D(Data):
    signature = IData1D
    series = Series1D


class ISingleData1D(interfaces.IRMLDirectiveSignature):
    """A 1-D data set."""
    occurence.containing(
        occurence.One('series', ISeries1D)
        )

class SingleData1D(Data1D):
    signature = ISingleData1D

    def process(self):
        self.data = []
        self.factories = {'series': self.series}
        self.processSubDirectives()
        self.parent.context.data = self.data[0]


class ISeries2D(interfaces.IRMLDirectiveSignature):
    """A two-dimensional series."""

    values = attr.TextNodeGrid(
        title=u'Values',
        description=u"Numerical values representing the series' data.",
        value_type=attr.Float(),
        columns=2,
        required=True)

class Series2D(Series):
    signature = ISeries2D


class IData2D(interfaces.IRMLDirectiveSignature):
    """A 2-D data set."""
    occurence.containing(
        occurence.OneOrMore('series', ISeries2D)
        )

class Data2D(Data):
    signature = IData2D
    series = Series2D


class IBar(interfaces.IRMLDirectiveSignature):
    """Define the look of a bar."""

    strokeColor = attr.Color(
        title=u'Stroke Color',
        description=u'The color in which the bar border is drawn.',
        required=False)

    strokeWidth = attr.Measurement(
        title=u'Stroke Width',
        description=u'The width of the bar border line.',
        required=False)

    fillColor = attr.Color(
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

    dx = attr.Measurement(
        title=u'Horizontal Extension',
        description=(u'The width of the label.'),
        required=False)

    dy = attr.Measurement(
        title=u'Vertical Extension',
        description=(u'The height of the label.'),
        required=False)

    angle = attr.Float(
        title=u'Angle',
        description=(u'The angle to rotate the label.'),
        required=False)

    boxAnchor = attr.Choice(
        title=u'Box Anchor',
        description=(u'The position relative to the label.'),
        choices=('nw','n','ne','w','c','e','sw','s','se', 'autox', 'autoy'),
        required=False)

    boxStrokeColor = attr.Color(
        title=u'Box Stroke Color',
        description=(u'The color of the box border line.'),
        required=False)

    boxStrokeWidth = attr.Measurement(
        title=u'Box Stroke Width',
        description=u'The width of the box border line.',
        required=False)

    boxFillColor = attr.Color(
        title=u'Box Fill Color',
        description=(u'The color in which the box is filled.'),
        required=False)

    boxTarget = attr.Text(
        title=u'Box Target',
        description=u'The box target.',
        required=False)

    fillColor = attr.Color(
        title=u'Fill Color',
        description=(u'The color in which the label is filled.'),
        required=False)

    strokeColor = attr.Color(
        title=u'Stroke Color',
        description=(u'The color of the label.'),
        required=False)

    strokeWidth = attr.Measurement(
        title=u'Stroke Width',
        description=u'The width of the label line.',
        required=False)

    frontName = attr.String(
        title=u'Font Name',
        description=u'The font used to print the value.',
        required=False)

    frontSize = attr.Measurement(
        title=u'Font Size',
        description=u'The size of the value text.',
        required=False)

    leading = attr.Measurement(
        title=u'Leading',
        description=(u'The height of a single text line. It includes '
                     u'character height.'),
        required=False)

    width = attr.Measurement(
        title=u'Width',
        description=u'The width the label.',
        required=False)

    maxWidth = attr.Measurement(
        title=u'Maximum Width',
        description=u'The maximum width the label.',
        required=False)

    height = attr.Measurement(
        title=u'Height',
        description=u'The height the label.',
        required=False)

    textAnchor = attr.Choice(
        title=u'Text Anchor',
        description=u'The position in the text to which the coordinates refer.',
        choices=('start', 'middle', 'end', 'boxauto'),
        required=False)

    visible = attr.Boolean(
        title=u'Visible',
        description=u'A flag making the label text visible.',
        required=False)

    leftPadding = attr.Measurement(
        title=u'Left Padding',
        description=u'The size of the padding on the left side.',
        required=False)

    rightPadding = attr.Measurement(
        title=u'Right Padding',
        description=u'The size of the padding on the right side.',
        required=False)

    topPadding = attr.Measurement(
        title=u'Top Padding',
        description=u'The size of the padding on the top.',
        required=False)

    bottomPadding = attr.Measurement(
        title=u'Bottom Padding',
        description=u'The size of the padding on the bottom.',
        required=False)


class IPositionLabelBase(ILabelBase):

    x = attr.Measurement(
        title=u'X-Coordinate',
        description=(u'The X-coordinate of the lower-left position of the '
                     u'label.'),
        required=False)

    y = attr.Measurement(
        title=u'Y-Coordinate',
        description=(u'The Y-coordinate of the lower-left position of the '
                     u'label.'),
        required=False)


class ILabel(IPositionLabelBase):
    """A label for the chart."""

    text = attr.TextNode(
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

    visible = attr.Boolean(
        required=False)

    visibleAxis = attr.Boolean(
        required=False)

    visibleTicks = attr.Boolean(
        required=False)

    visibleLabels = attr.Boolean(
        required=False)

    visibleGrid = attr.Boolean(
        required=False)

    strokeWidth = attr.Measurement(
        required=False)

    strokeColor = attr.Color(
        required=False)

    strokeDashArray = attr.Sequence(
        value_type=attr.Float(),
        required=False)

    gridStrokeWidth = attr.Measurement(
        required=False)

    gridStrokeColor = attr.Color(
        required=False)

    gridStrokeDashArray = attr.Sequence(
        value_type=attr.Float(),
        required=False)

    gridStart = attr.Measurement(
        required=False)

    gridEnd = attr.Measurement(
        required=False)

    style = attr.Choice(
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

    text = attr.TextNode(
        title=u'Text',
        required=True)

class Name(directive.RMLDirective):
    signature = IName

    def process(self):
        text = self.getAttributeValues(valuesOnly=True)[0]
        self.parent.names.append(text)


class ICategoryNames(IAxis):
    occurence.containing(
        occurence.OneOrMore('name', IName),
        )

class CategoryNames(directive.RMLDirective):
    signature = ICategoryNames
    factories = {'name': Name}

    def process(self):
        self.names = []
        self.processSubDirectives()
        self.parent.context.categoryNames = self.names


class ICategoryAxis(IAxis):
    occurence.containing(
        occurence.ZeroOrOne('categoryNames', ICategoryNames),
        *IAxis.queryTaggedValue('directives', ())
        )

    categoryNames = attr.Sequence(
        value_type=attr.Text(),
        required=False)

    joinAxis = attr.Boolean(
        required=False)

    joinAxisPos = attr.Measurement(
        required=False)

    reverseDirection = attr.Boolean(
        required=False)

    labelAxisMode = attr.Choice(
        choices=('high', 'low', 'axis'),
        required=False)

    tickShift = attr.Boolean(
        required=False)

class CategoryAxis(Axis):
    signature = ICategoryAxis
    name = 'categoryAxis'
    factories = Axis.factories.copy()
    factories.update({
        'categoryNames': CategoryNames,
        })


class IXCategoryAxis(ICategoryAxis):

    tickUp = attr.Measurement(
        required=False)

    tickDown = attr.Measurement(
        required=False)

    joinAxisMode = attr.Choice(
        choices=('bottom', 'top', 'value', 'points', 'None'),
        required=False)

class XCategoryAxis(CategoryAxis):
    signature = IXCategoryAxis


class IYCategoryAxis(ICategoryAxis):

    tickLeft = attr.Measurement(
        required=False)

    tickRight = attr.Measurement(
        required=False)

    joinAxisMode = attr.Choice(
        choices=('bottom', 'top', 'value', 'points', 'None'),
        required=False)

class YCategoryAxis(CategoryAxis):
    signature = IYCategoryAxis


class IValueAxis(IAxis):

    forceZero = attr.Boolean(
        required=False)

    minimumTickSpacing = attr.Measurement(
        required=False)

    maximumTicks = attr.Integer(
        required=False)

    labelTextFormat = attr.String(
        required=False)

    labelTextPostFormat = attr.Text(
        required=False)

    labelTextScale = attr.Float(
        required=False)

    valueMin = attr.Float(
        required=False)

    valueMax = attr.Float(
        required=False)

    valueStep = attr.Float(
        required=False)

    valueSteps = attr.Measurement(
        required=False)

    rangeRound = attr.Text(
        required=False)

    zrangePref = attr.Float(
        required=False)

class ValueAxis(Axis):
    signature = IValueAxis
    name = 'valueAxis'


class IXValueAxis(IValueAxis):

    tickUp = attr.Measurement(
        required=False)

    tickDown = attr.Measurement(
        required=False)

    joinAxis = attr.Boolean(
        required=False)

    joinAxisMode = attr.Choice(
        choices=('bottom', 'top', 'value', 'points', 'None'),
        required=False)

    joinAxisPos = attr.Measurement(
        required=False)

class XValueAxis(ValueAxis):
    signature = IXValueAxis

class LineXValueAxis(XValueAxis):
    name = 'xValueAxis'

class IYValueAxis(IValueAxis):

    tickLeft = attr.Measurement(
        required=False)

    tickRight = attr.Measurement(
        required=False)

    joinAxis = attr.Boolean(
        required=False)

    joinAxisMode = attr.Choice(
        choices=('bottom', 'top', 'value', 'points', 'None'),
        required=False)

    joinAxisPos = attr.Measurement(
        required=False)

class YValueAxis(ValueAxis):
    signature = IYValueAxis

class LineYValueAxis(YValueAxis):
    name = 'yValueAxis'


class ILineBase(interfaces.IRMLDirectiveSignature):

    strokeWidth = attr.Measurement(
        required=False)

    strokeColor = attr.Color(
        required=False)

    strokeDashArray = attr.Sequence(
        value_type = attr.Float(),
        required=False)

    symbol = attr.Symbol(
        required=False)

class ILine(ILineBase):

    name = attr.Text(
        required=False)

class Line(PropertyItem):
    signature = ILine

class ILines(ILineBase):
    occurence.containing(
        occurence.OneOrMore('line', ILine),
        )

class Lines(PropertyCollection):
    signature = ILines
    propertyName = 'lines'
    factories = {'line': Line}


class ISliceLabel(ILabelBase):

    text = attr.TextNode(
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

    strokeColor = attr.Color(
        required=False)

    strokeWidth = attr.Measurement(
        required=False)

    elbowLength = attr.Measurement(
        required=False)

    edgePad = attr.Measurement(
        required=False)

    piePad = attr.Measurement(
        required=False)

class SlicePointer(directive.RMLDirective):
    signature = ISlicePointer

    def process(self):
        for name, value in self.getAttributeValues():
            self.parent.context['label_pointer_'+name] = value


class ISliceBase(interfaces.IRMLDirectiveSignature):

    strokeWidth = attr.Measurement(
        required=False)

    fillColor = attr.Color(
        required=False)

    strokeColor = attr.Color(
        required=False)

    strokeDashArray = attr.Sequence(
        value_type=attr.Float(),
        required=False)

    popout = attr.Measurement(
        required=False)

    fontName = attr.String(
        required=False)

    fontSize = attr.Measurement(
        required=False)

    labelRadius = attr.Measurement(
        required=False)


class ISlice(ISliceBase):
    occurence.containing(
        occurence.ZeroOrOne('label', ISliceLabel),
        occurence.ZeroOrOne('pointer', ISlicePointer),
        )

    swatchMarker = attr.Symbol(
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

    fillColorShaded = attr.Color(
        required=False)

class Slice3D(Slice):
    signature = ISlice3D
    factories = {}
    # Sigh, the 3-D Pie does not support advanced slice labels. :-(
    #     'label': SliceLabel}


class ISlices(ISliceBase):
    occurence.containing(
        occurence.OneOrMore('slice', ISlice),
        )

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
    occurence.containing(
        occurence.OneOrMore('slice', ISlice3D),
        )

    fillColorShaded = attr.Color(
        required=False)

class Slices3D(Slices):
    signature = ISlices3D
    factories = {'slice': Slice3D}


class ISimpleLabels(interfaces.IRMLDirectiveSignature):
    occurence.containing(
        occurence.OneOrMore('label', IName),
        )

class SimpleLabels(directive.RMLDirective):
    signature = ISimpleLabels
    factories = {'label': Name}

    def process(self):
        self.names = []
        self.processSubDirectives()
        self.parent.context.labels = self.names


class IStrandBase(interfaces.IRMLDirectiveSignature):

    strokeWidth = attr.Measurement(
        required=False)

    fillColor = attr.Color(
        required=False)

    strokeColor= attr.Color(
        required=False)

    strokeDashArray = attr.Sequence(
        value_type=attr.Float(),
        required=False)

    symbol = attr.Symbol(
        required=False)

    symbolSize = attr.Measurement(
        required=False)

class IStrand(IStrandBase):

     name = attr.Text(
        required=False)

class Strand(PropertyItem):
    signature = IStrand


class IStrands(IStrand):
    """A collection of strands."""
    occurence.containing(
        occurence.OneOrMore('strand', IStrand)
        )

class Strands(PropertyCollection):
    signature = IStrands
    propertyName = 'strands'
    attrs = IStrandBase
    factories = {'strand': Strand}


class IStrandLabelBase(ILabelBase):

    _text = attr.TextNode(
        required=False)

    row = attr.Integer(
        required=False)

    col = attr.Integer(
        required=False)

    format = attr.String(
        required=False)

class IStrandLabel(IStrandLabelBase):

    dR = attr.Float(
        required=False)

class StrandLabel(Label):
    signature = IStrandLabel


class IStrandLabels(IStrandLabelBase):
    """A set of strand labels."""
    occurence.containing(
        occurence.OneOrMore('label', IStrandLabel)
        )

class StrandLabels(PropertyCollection):
    signature = IStrandLabels
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

    strokeWidth = attr.Measurement(
        required=False)

    fillColor = attr.Color(
        required=False)

    strokeColor= attr.Color(
        required=False)

    strokeDashArray = attr.Sequence(
        value_type=attr.Float(),
        required=False)

    labelRadius = attr.Measurement(
        required=False)

    visible = attr.Measurement(
        required=False)

class Spoke(PropertyItem):
    signature = ISpoke


class ISpokes(ISpoke):
    """A collection of spokes."""
    occurence.containing(
        occurence.OneOrMore('spoke', ISpoke)
        )

class Spokes(PropertyCollection):
    signature = ISpokes
    propertyName = 'spokes'
    factories = {'spoke': Spoke}


class ISpokeLabelBase(ILabelBase):
    pass

class ISpokeLabel(ISpokeLabelBase):

    _text = attr.TextNode(
        required=False)

class SpokeLabel(Label):
    signature = ISpokeLabel


class ISpokeLabels(ISpokeLabelBase):
    """A set of spoke labels."""
    occurence.containing(
        occurence.OneOrMore('label', ISpokeLabel)
        )

class SpokeLabels(PropertyCollection):
    signature = ISpokeLabels
    propertyName = 'spokeLabels'
    factories = {'label': SpokeLabel}


class IChart(interfaces.IRMLDirectiveSignature):
    occurence.containing(
        occurence.ZeroOrOne('texts', ITexts),
        )

    # Drawing Options

    dx = attr.Measurement(
        title=u'Drawing X-Position',
        description=u'The x-position of the entire drawing on the canvas.',
        required=False)

    dy = attr.Measurement(
        title=u'Drawing Y-Position',
        description=u'The y-position of the entire drawing on the canvas.',
        required=False)

    dwidth = attr.Measurement(
        title=u'Drawing Width',
        description=u'The width of the entire drawing',
        required=False)

    dheight = attr.Measurement(
        title=u'Drawing Height',
        description=u'The height of the entire drawing',
        required=False)

    angle = attr.Float(
        title=u'Angle',
        description=u'The orientation of the drawing as an angle in degrees.',
        required=False)

    # Plot Area Options

    x = attr.Measurement(
        title=u'Chart X-Position',
        description=u'The x-position of the chart within the drawing.',
        required=False)

    y = attr.Measurement(
        title=u'Chart Y-Position',
        description=u'The y-position of the chart within the drawing.',
        required=False)

    width = attr.Measurement(
        title=u'Chart Width',
        description=u'The width of the chart.',
        required=False)

    height = attr.Measurement(
        title=u'Chart Height',
        description=u'The height of the chart.',
        required=False)

    strokeColor = attr.Color(
        title=u'Stroke Color',
        description=u'Color of the chart border.',
        required=False)

    strokeWidth = attr.Measurement(
        title=u'Stroke Width',
        description=u'Width of the chart border.',
        required=False)

    fillColor = attr.Color(
        title=u'Fill Color',
        description=u'Color of the chart interior.',
        required=False)

    debug = attr.Boolean(
        title=u'Debugging',
        description=u'A flag that when set to True turns on debug messages.',
        required=False)

class Chart(directive.RMLDirective):
    signature = IChart
    factories = {
        'texts': Texts
        }
    attrMapping = {}

    def createChart(self, attributes):
        raise NotImplementedError

    def process(self):
        attrs = dict(self.getAttributeValues(attrMapping=self.attrMapping))
        angle = attrs.pop('angle', 0)
        x, y = attrs.pop('dx'), attrs.pop('dy')
        self.drawing = shapes.Drawing(attrs.pop('dwidth'), attrs.pop('dheight'))
        self.context = chart = self.createChart(attrs)
        self.processSubDirectives()
        group = shapes.Group(chart)
        group.translate(0,0)
        group.rotate(angle)
        self.drawing.add(group)
        manager = attr.getManager(self, interfaces.ICanvasManager)
        self.drawing.drawOn(manager.canvas, x, y)


class IBarChart(IChart):
    """Creates a two-dimensional bar chart."""
    occurence.containing(
        occurence.One('data', IData1D),
        occurence.ZeroOrOne('bars', IBars),
        occurence.ZeroOrOne('categoryAxis', ICategoryAxis),
        occurence.ZeroOrOne('valueAxis', IValueAxis),
        *IChart.queryTaggedValue('directives', ())
        )

    direction = attr.Choice(
        title=u'Direction',
        description=u'The direction of the bars within the chart.',
        choices=('horizontal', 'vertical'),
        default='horizontal',
        required=False)

    useAbsolute = attr.Boolean(
        title=u'Use Absolute Spacing',
        description=u'Flag to use absolute spacing values.',
        default=False,
        required=False)

    barWidth = attr.Measurement(
        title=u'Bar Width',
        description=u'The width of an individual bar.',
        default=10,
        required=False)

    groupSpacing = attr.Measurement(
        title=u'Group Spacing',
        description=u'Width between groups of bars.',
        default=5,
        required=False)

    barSpacing = attr.Measurement(
        title=u'Bar Spacing',
        description=u'Width between individual bars.',
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
    """Creates a three-dimensional bar chart."""
    occurence.containing(
        *IBarChart.queryTaggedValue('directives', ())
        )

    thetaX = attr.Float(
        title=u'Theta-X',
        description=u'Fraction of dx/dz.',
        required=False)

    thetaY = attr.Float(
        title=u'Theta-Y',
        description=u'Fraction of dy/dz.',
        required=False)

    zDepth = attr.Measurement(
        title=u'Z-Depth',
        description=u'Depth of an individual series/bar.',
        required=False)

    zSpace = attr.Measurement(
        title=u'Z-Space',
        description=u'Z-Gap around a series/bar.',
        required=False)

class BarChart3D(BarChart):
    signature = IBarChart3D
    nameBase = 'BarChart3D'
    attrMapping = {'thetaX': 'theta_x', 'thetaY': 'theta_y'}


class ILinePlot(IChart):
    occurence.containing(
        occurence.One('data', IData2D),
        occurence.ZeroOrOne('lines', ILines),
        occurence.ZeroOrOne('xValueAxis', IXValueAxis),
        occurence.ZeroOrOne('yValueAxis', IYValueAxis),
        occurence.ZeroOrOne('lineLabels', ILabels),
        *IChart.queryTaggedValue('directives', ())
        )

    reversePlotOrder = attr.Boolean(
        required=False)

    lineLabelNudge = attr.Measurement(
        required=False)

    lineLabelFormat = attr.String(
        required=False)

    joinedLines = attr.Boolean(
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
    occurence.containing(
        occurence.One('data', ISingleData1D),
        occurence.ZeroOrOne('slices', ISlices),
        occurence.ZeroOrOne('labels', ISimpleLabels),
        *IChart.queryTaggedValue('directives', ())
        )

    startAngle = attr.Integer(
        title=u'Start Angle',
        description=u'The start angle in the chart of the first slice '
                    u'in degrees.',
        required=False)

    direction = attr.Choice(
        choices=('clockwise', 'anticlockwise'),
        required=False)

    checkLabelOverlap = attr.Boolean(
        required=False)

    pointerLabelMode = attr.Choice(
        choices={'none': None,
                 'leftright': 'LeftRight',
                 'leftandright': 'LeftAndRight'},
        required=False)

    sameRadii = attr.Boolean(
        required=False)

    orderMode = attr.Choice(
        choices=('fixed', 'alternate'),
        required=False)

    xradius = attr.Measurement(
        required=False)

    yradius = attr.Measurement(
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
    occurence.containing(
        occurence.One('slices', ISlices3D),
        *IChart.queryTaggedValue('directives', ())
        )

    perspective = attr.Float(
        required=False)

    depth_3d = attr.Measurement(
        required=False)

    angle_3d = attr.Float(
        required=False)

class PieChart3D(PieChart):
    signature = IPieChart3D
    chartClass = piecharts.Pie3d

    factories = PieChart.factories.copy()
    factories.update({
        'slices': Slices3D,
        })


class ISpiderChart(IChart):
    occurence.containing(
        occurence.One('data', IData1D),
        occurence.ZeroOrOne('strands', IStrands),
        occurence.ZeroOrOne('strandLabels', IStrandLabels),
        occurence.ZeroOrOne('spokes', ISpokes),
        occurence.ZeroOrOne('spokeLabels', ISpokeLabels),
        occurence.ZeroOrOne('labels', ISimpleLabels),
        *IChart.queryTaggedValue('directives', ())
        )

    startAngle = attr.Integer(
        required=False)

    direction = attr.Choice(
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
