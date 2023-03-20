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
"""
import reportlab.lib.formatters
from reportlab.graphics import shapes
from reportlab.graphics.charts import barcharts
from reportlab.graphics.charts import doughnut  # noqa: F401 unused
from reportlab.graphics.charts import lineplots
from reportlab.graphics.charts import piecharts
from reportlab.graphics.charts import spider

from z3c.rml import attr
from z3c.rml import directive
from z3c.rml import interfaces
from z3c.rml import occurence


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
        title='X-Coordinate',
        description=('The X-coordinate of the lower-left position of the '
                     'text.'),
        required=True)

    y = attr.Measurement(
        title='Y-Coordinate',
        description=('The Y-coordinate of the lower-left position of the '
                     'text.'),
        required=True)

    angle = attr.Float(
        title='Rotation Angle',
        description=('The angle about which the text will be rotated.'),
        required=False)

    text = attr.TextNode(
        title='Text',
        description='The text to be printed.',
        required=True)

    fontName = attr.Text(
        title='Font Name',
        description='The name of the font.',
        required=False)

    fontSize = attr.Measurement(
        title='Font Size',
        description='The font size for the text.',
        required=False)

    fillColor = attr.Color(
        title='Fill Color',
        description='The color in which the text will appear.',
        required=False)

    textAnchor = attr.Choice(
        title='Text Anchor',
        description='The position in the text to which the coordinates refer.',
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
        group.translate(0, 0)
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
        title='Values',
        description="Numerical values representing the series' data.",
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
        title='Values',
        description="Numerical values representing the series' data.",
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
        title='Stroke Color',
        description='The color in which the bar border is drawn.',
        required=False)

    strokeWidth = attr.Measurement(
        title='Stroke Width',
        description='The width of the bar border line.',
        required=False)

    fillColor = attr.Color(
        title='Fill Color',
        description='The color with which the bar is filled.',
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
        title='Horizontal Extension',
        description=('The width of the label.'),
        required=False)

    dy = attr.Measurement(
        title='Vertical Extension',
        description=('The height of the label.'),
        required=False)

    angle = attr.Float(
        title='Angle',
        description=('The angle to rotate the label.'),
        required=False)

    boxAnchor = attr.Choice(
        title='Box Anchor',
        description=('The position relative to the label.'),
        choices=(
            'nw',
            'n',
            'ne',
            'w',
            'c',
            'e',
            'sw',
            's',
            'se',
            'autox',
            'autoy'),
        required=False)

    boxStrokeColor = attr.Color(
        title='Box Stroke Color',
        description=('The color of the box border line.'),
        acceptNone=True,
        required=False)

    boxStrokeWidth = attr.Measurement(
        title='Box Stroke Width',
        description='The width of the box border line.',
        required=False)

    boxFillColor = attr.Color(
        title='Box Fill Color',
        description=('The color in which the box is filled.'),
        acceptNone=True,
        required=False)

    boxTarget = attr.Text(
        title='Box Target',
        description='The box target.',
        required=False)

    fillColor = attr.Color(
        title='Fill Color',
        description=('The color in which the label is filled.'),
        required=False)

    strokeColor = attr.Color(
        title='Stroke Color',
        description=('The color of the label.'),
        required=False)

    strokeWidth = attr.Measurement(
        title='Stroke Width',
        description='The width of the label line.',
        required=False)

    fontName = attr.Text(
        title='Font Name',
        description='The font used to print the value.',
        required=False)

    fontSize = attr.Measurement(
        title='Font Size',
        description='The size of the value text.',
        required=False)

    leading = attr.Measurement(
        title='Leading',
        description=('The height of a single text line. It includes '
                     'character height.'),
        required=False)

    width = attr.Measurement(
        title='Width',
        description='The width the label.',
        required=False)

    maxWidth = attr.Measurement(
        title='Maximum Width',
        description='The maximum width the label.',
        required=False)

    height = attr.Measurement(
        title='Height',
        description='The height the label.',
        required=False)

    textAnchor = attr.Choice(
        title='Text Anchor',
        description='The position in the text to which the coordinates refer.',
        choices=('start', 'middle', 'end', 'boxauto'),
        required=False)

    visible = attr.Boolean(
        title='Visible',
        description='A flag making the label text visible.',
        required=False)

    leftPadding = attr.Measurement(
        title='Left Padding',
        description='The size of the padding on the left side.',
        required=False)

    rightPadding = attr.Measurement(
        title='Right Padding',
        description='The size of the padding on the right side.',
        required=False)

    topPadding = attr.Measurement(
        title='Top Padding',
        description='The size of the padding on the top.',
        required=False)

    bottomPadding = attr.Measurement(
        title='Bottom Padding',
        description='The size of the padding on the bottom.',
        required=False)


class IPositionLabelBase(ILabelBase):

    x = attr.Measurement(
        title='X-Coordinate',
        description=('The X-coordinate of the lower-left position of the '
                     'label.'),
        required=False)

    y = attr.Measurement(
        title='Y-Coordinate',
        description=('The Y-coordinate of the lower-left position of the '
                     'label.'),
        required=False)


class ILabel(IPositionLabelBase):
    """A label for the chart on an axis."""

    text = attr.TextNode(
        title='Text',
        description='The label text to be displayed.',
        required=True)


class Label(PropertyItem):
    signature = ILabel


class IBarLabels(ILabelBase):
    """A set of labels for a bar chart"""
    occurence.containing(
        occurence.ZeroOrMore('label', ILabel)
    )


class BarLabels(PropertyCollection):
    signature = IBarLabels
    propertyName = 'barLabels'
    factories = {'label': Label}
    name = 'barLabels'


class ILabels(IPositionLabelBase):
    """A set of labels of an axis."""
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
        title='Visible',
        description='When true, draw the entire axis with all details.',
        required=False)

    visibleAxis = attr.Boolean(
        title='Visible Axis',
        description='When true, draw the axis line.',
        required=False)

    visibleTicks = attr.Boolean(
        title='Visible Ticks',
        description='When true, draw the axis ticks on the line.',
        required=False)

    visibleLabels = attr.Boolean(
        title='Visible Labels',
        description='When true, draw the axis labels.',
        required=False)

    visibleGrid = attr.Boolean(
        title='Visible Grid',
        description='When true, draw the grid lines for the axis.',
        required=False)

    strokeWidth = attr.Measurement(
        title='Stroke Width',
        description='The width of axis line and ticks.',
        required=False)

    strokeColor = attr.Color(
        title='Stroke Color',
        description='The color in which the axis line and ticks are drawn.',
        required=False)

    strokeDashArray = attr.Sequence(
        title='Stroke Dash Array',
        description='The dash array that is used for the axis line and ticks.',
        value_type=attr.Float(),
        required=False)

    gridStrokeWidth = attr.Measurement(
        title='Grid Stroke Width',
        description='The width of the grid lines.',
        required=False)

    gridStrokeColor = attr.Color(
        title='Grid Stroke Color',
        description='The color in which the grid lines are drawn.',
        required=False)

    gridStrokeDashArray = attr.Sequence(
        title='Grid Stroke Dash Array',
        description='The dash array that is used for the grid lines.',
        value_type=attr.Float(),
        required=False)

    gridStart = attr.Measurement(
        title='Grid Start',
        description=('The start of the grid lines with respect to the '
                     'axis origin.'),
        required=False)

    gridEnd = attr.Measurement(
        title='Grid End',
        description=('The end of the grid lines with respect to the '
                     'axis origin.'),
        required=False)

    style = attr.Choice(
        title='Style',
        description='The plot style of the common categories.',
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
    """A category name"""
    text = attr.TextNode(
        title='Text',
        description='The text value that is the name.',
        required=True)


class Name(directive.RMLDirective):
    signature = IName

    def process(self):
        text = self.getAttributeValues(valuesOnly=True)[0]
        self.parent.names.append(text)


class ICategoryNames(interfaces.IRMLDirectiveSignature):
    """A list of category names."""
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
    """An axis displaying categories (instead of numerical values)."""
    occurence.containing(
        occurence.ZeroOrOne('categoryNames', ICategoryNames),
        *IAxis.queryTaggedValue('directives', ())
    )

    categoryNames = attr.Sequence(
        title='Category Names',
        description='A simple list of category names.',
        value_type=attr.Text(),
        required=False)

    joinAxis = attr.Boolean(
        title='Join Axis',
        description='When true, both axes join together.',
        required=False)

    joinAxisPos = attr.Measurement(
        title='Join Axis Position',
        description='The position at which the axes should join together.',
        required=False)

    reverseDirection = attr.Boolean(
        title='Reverse Direction',
        description='A flag to reverse the direction of category names.',
        required=False)

    labelAxisMode = attr.Choice(
        title='Label Axis Mode',
        description='Defines the relative position of the axis labels.',
        choices=('high', 'low', 'axis'),
        required=False)

    tickShift = attr.Boolean(
        title='Tick Shift',
        description=('When true, place the ticks in the center of a '
                     'category instead the beginning and end.'),
        required=False)


class CategoryAxis(Axis):
    signature = ICategoryAxis
    name = 'categoryAxis'
    factories = Axis.factories.copy()
    factories.update({
        'categoryNames': CategoryNames,
    })


class IXCategoryAxis(ICategoryAxis):
    """X-Category Axis"""

    tickUp = attr.Measurement(
        title='Tick Up',
        description='Length of tick above the axis line.',
        required=False)

    tickDown = attr.Measurement(
        title='Tick Down',
        description='Length of tick below the axis line.',
        required=False)

    joinAxisMode = attr.Choice(
        title='Join Axis Mode',
        description='Mode for connecting axes.',
        choices=('bottom', 'top', 'value', 'points', 'None'),
        required=False)


class XCategoryAxis(CategoryAxis):
    signature = IXCategoryAxis


class IYCategoryAxis(ICategoryAxis):
    """Y-Category Axis"""

    tickLeft = attr.Measurement(
        title='Tick Left',
        description='Length of tick left to the axis line.',
        required=False)

    tickRight = attr.Measurement(
        title='Tick Right',
        description='Length of tick right to the axis line.',
        required=False)

    joinAxisMode = attr.Choice(
        title='Join Axis Mode',
        description='Mode for connecting axes.',
        choices=('bottom', 'top', 'value', 'points', 'None'),
        required=False)


class YCategoryAxis(CategoryAxis):
    signature = IYCategoryAxis


class IValueAxis(IAxis):

    forceZero = attr.Boolean(
        title='Force Zero',
        description='When set, the range will contain the origin.',
        required=False)

    minimumTickSpacing = attr.Measurement(
        title='Minimum Tick Spacing',
        description='The minimum distance between ticks.',
        required=False)

    maximumTicks = attr.Integer(
        title='Maximum Ticks',
        description='The maximum number of ticks to be shown.',
        required=False)

    labelTextFormat = attr.Combination(
        title='Label Text Format',
        description=(
            'Formatting string or Python path to formatting function for '
            'axis labels.'),
        value_types=(
            # Python path to function.
            attr.ObjectRef(),
            # Formatting String.
            attr.Text(),
        ),
        required=False)

    labelTextPostFormat = attr.Text(
        title='Label Text Post Format',
        description='An additional formatting string.',
        required=False)

    labelTextScale = attr.Float(
        title='Label Text Scale',
        description='The sclaing factor for the label tick values.',
        required=False)

    valueMin = attr.Float(
        title='Minimum Value',
        description='The smallest value on the axis.',
        required=False)

    valueMax = attr.Float(
        title='Maximum Value',
        description='The largest value on the axis.',
        required=False)

    valueStep = attr.Float(
        title='Value Step',
        description='The step size between ticks',
        required=False)

    valueSteps = attr.Sequence(
        title='Step Sizes',
        description='List of step sizes between ticks.',
        value_type=attr.Float(),
        required=False)

    rangeRound = attr.Choice(
        title='Range Round',
        description='Method to be used to round the range values.',
        choices=('none', 'both', 'ceiling', 'floor'),
        required=False)

    zrangePref = attr.Float(
        title='Zero Range Preference',
        description='Zero range axis limit preference.',
        required=False)


class ValueAxis(Axis):
    signature = IValueAxis
    name = 'valueAxis'


class IXValueAxis(IValueAxis):
    """X-Value Axis"""

    tickUp = attr.Measurement(
        title='Tick Up',
        description='Length of tick above the axis line.',
        required=False)

    tickDown = attr.Measurement(
        title='Tick Down',
        description='Length of tick below the axis line.',
        required=False)

    joinAxis = attr.Boolean(
        title='Join Axis',
        description='Whether to join the axes.',
        required=False)

    joinAxisMode = attr.Choice(
        title='Join Axis Mode',
        description='Mode for connecting axes.',
        choices=('bottom', 'top', 'value', 'points', 'None'),
        required=False)

    joinAxisPos = attr.Measurement(
        title='Join Axis Position',
        description='The position in the plot at which to join the axes.',
        required=False)


class XValueAxis(ValueAxis):
    signature = IXValueAxis


class LineXValueAxis(XValueAxis):
    name = 'xValueAxis'


class IYValueAxis(IValueAxis):
    """Y-Value Axis"""

    tickLeft = attr.Measurement(
        title='Tick Left',
        description='Length of tick left to the axis line.',
        required=False)

    tickRight = attr.Measurement(
        title='Tick Right',
        description='Length of tick right to the axis line.',
        required=False)

    joinAxis = attr.Boolean(
        title='Join Axis',
        description='Whether to join the axes.',
        required=False)

    joinAxisMode = attr.Choice(
        title='Join Axis Mode',
        description='Mode for connecting axes.',
        choices=('bottom', 'top', 'value', 'points', 'None'),
        required=False)

    joinAxisPos = attr.Measurement(
        title='Join Axis Position',
        description='The position in the plot at which to join the axes.',
        required=False)


class YValueAxis(ValueAxis):
    signature = IYValueAxis


class LineYValueAxis(YValueAxis):
    name = 'yValueAxis'


class ILineLabels(IPositionLabelBase):
    """A set of labels of an axis."""
    occurence.containing(
        occurence.ZeroOrMore('label', ILabel)
    )


class LineLabels(PropertyCollection):
    signature = ILineLabels
    propertyName = 'lineLabels'
    factories = {'label': Label}


class ILineBase(interfaces.IRMLDirectiveSignature):

    strokeWidth = attr.Measurement(
        title='Stroke Width',
        description='The width of the plot line.',
        required=False)

    strokeColor = attr.Color(
        title='Stroke Color',
        description='The color of the plot line.',
        required=False)

    strokeDashArray = attr.Sequence(
        title='Stroke Dash Array',
        description='The dash array of the plot line.',
        value_type=attr.Float(),
        required=False)

    symbol = attr.Symbol(
        title='Symbol',
        description='The symbol to be used for every data point in the plot.',
        required=False)


class ILine(ILineBase):
    """A line description of a series of a line plot."""

    name = attr.Text(
        title='Name',
        description='The name of the line.',
        required=False)


class Line(PropertyItem):
    signature = ILine


class ILines(ILineBase):
    """The set of all line descriptions in the line plot."""
    occurence.containing(
        occurence.OneOrMore('line', ILine),
    )


class Lines(PropertyCollection):
    signature = ILines
    propertyName = 'lines'
    factories = {'line': Line}


class ISliceLabel(ILabelBase):
    """The label of a slice within a bar chart."""

    text = attr.TextNode(
        title='Text',
        description='The label text to be displayed.',
        required=True)


class SliceLabel(Label):
    signature = ISliceLabel

    def process(self):
        for name, value in self.getAttributeValues():
            self.parent.context['label_' + name] = value
        # Now we do not have simple labels anymore
        self.parent.parent.parent.context.simpleLabels = False


class ISlicePointer(interfaces.IRMLDirectiveSignature):
    """A pointer to a slice in a pie chart."""

    strokeColor = attr.Color(
        title='Stroke Color',
        description='The color of the pointer line.',
        required=False)

    strokeWidth = attr.Measurement(
        title='Stroke Width',
        description='The wodth of the pointer line.',
        required=False)

    elbowLength = attr.Measurement(
        title='Elbow Length',
        description='The length of the final segment of the pointer.',
        required=False)

    edgePad = attr.Measurement(
        title='Edge Padding',
        description='The padding between between the pointer label and box.',
        required=False)

    piePad = attr.Measurement(
        title='Pie Padding',
        description='The padding between between the pointer label and chart.',
        required=False)


class SlicePointer(directive.RMLDirective):
    signature = ISlicePointer

    def process(self):
        for name, value in self.getAttributeValues():
            self.parent.context['label_pointer_' + name] = value


class ISliceBase(interfaces.IRMLDirectiveSignature):

    strokeWidth = attr.Measurement(
        title='Stroke Width',
        description='The wodth of the slice line.',
        required=False)

    fillColor = attr.Color(
        title='Fill Color',
        description='The fill color of the slice.',
        required=False)

    strokeColor = attr.Color(
        title='Stroke Color',
        description='The color of the pointer line.',
        required=False)

    strokeDashArray = attr.Sequence(
        title='Stroke Dash Array',
        description='Teh dash array of the slice borderline.',
        value_type=attr.Float(),
        required=False)

    popout = attr.Measurement(
        title='Popout',
        description='The distance of how much the slice should be popped out.',
        required=False)

    fontName = attr.Text(
        title='Font Name',
        description='The font name of the label.',
        required=False)

    fontSize = attr.Measurement(
        title='Font Size',
        description='The font size of the label.',
        required=False)

    labelRadius = attr.Measurement(
        title='Label Radius',
        description=('The radius at which the label should be placed around '
                     'the pie.'),
        required=False)


class ISlice(ISliceBase):
    """A slice in a pie chart."""
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
    """A 3-D slice of a 3-D pie chart."""

    fillColorShaded = attr.Color(
        title='Fill Color Shade',
        description='The shade used for the fill color.',
        required=False)


class Slice3D(Slice):
    signature = ISlice3D
    factories = {}
    # Sigh, the 3-D Pie does not support advanced slice labels. :-(
    #     'label': SliceLabel}


class ISlices(ISliceBase):
    """The collection of all 2-D slice descriptions."""
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
    """The collection of all 3-D slice descriptions."""
    occurence.containing(
        occurence.OneOrMore('slice', ISlice3D),
    )

    fillColorShaded = attr.Color(
        required=False)


class Slices3D(Slices):
    signature = ISlices3D
    factories = {'slice': Slice3D}


class ISimpleLabel(IName):
    """A simple label"""


class SimpleLabel(Name):
    signature = ISimpleLabel


class ISimpleLabels(interfaces.IRMLDirectiveSignature):
    """A set of simple labels for a chart."""
    occurence.containing(
        occurence.OneOrMore('label', ISimpleLabel),
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
        title='Stroke Width',
        description='The line width of the strand.',
        required=False)

    fillColor = attr.Color(
        title='Fill Color',
        description='The fill color of the strand area.',
        required=False)

    strokeColor = attr.Color(
        title='Stroke Color',
        description='The color of the strand line.',
        required=False)

    strokeDashArray = attr.Sequence(
        title='Stroke Dash Array',
        description='The dash array of the strand line.',
        value_type=attr.Float(),
        required=False)

    symbol = attr.Symbol(
        title='Symbol',
        description='The symbol to use to mark the strand.',
        required=False)

    symbolSize = attr.Measurement(
        title='Symbol Size',
        description='The size of the strand symbol.',
        required=False)


class IStrand(IStrandBase):
    """A strand in the spider diagram"""

    name = attr.Text(
        title='Name',
        description='The name of the strand.',
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

    row = attr.Integer(
        title='Row',
        description='The row of the strand label',
        required=False)

    col = attr.Integer(
        title='Column',
        description='The column of the strand label.',
        required=False)

    format = attr.Text(
        title='Format',
        description='The format string for the label.',
        required=False)


class IStrandLabel(IStrandLabelBase):
    """A label for a strand."""

    _text = attr.TextNode(
        title='Text',
        description='The label text of the strand.',
        required=False)

    dR = attr.Float(
        title='Radial Shift',
        description='The radial shift of the label.',
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
    """A spoke in the spider diagram."""

    strokeWidth = attr.Measurement(
        title='Stroke Width',
        description="The width of the spoke's line.",
        required=False)

    fillColor = attr.Color(
        title='Fill Color',
        description="The fill color of the spoke's area.",
        required=False)

    strokeColor = attr.Color(
        title='Stroke Color',
        description='The color of the spoke line.',
        required=False)

    strokeDashArray = attr.Sequence(
        title='Stroke Dash Array',
        description='The dash array of the spoke line.',
        value_type=attr.Float(),
        required=False)

    labelRadius = attr.Measurement(
        title='Label Radius',
        description='The radius of the label arouns the spoke.',
        required=False)

    visible = attr.Boolean(
        title='Visible',
        description='When true, the spoke line is drawn.',
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
    """A label for a spoke."""
    _text = attr.TextNode(
        title='Text',
        description='The text of the spoke (label).',
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
        title='Drawing X-Position',
        description='The x-position of the entire drawing on the canvas.',
        required=False)

    dy = attr.Measurement(
        title='Drawing Y-Position',
        description='The y-position of the entire drawing on the canvas.',
        required=False)

    dwidth = attr.Measurement(
        title='Drawing Width',
        description='The width of the entire drawing',
        required=False)

    dheight = attr.Measurement(
        title='Drawing Height',
        description='The height of the entire drawing',
        required=False)

    angle = attr.Float(
        title='Angle',
        description='The orientation of the drawing as an angle in degrees.',
        required=False)

    # Plot Area Options

    x = attr.Measurement(
        title='Chart X-Position',
        description='The x-position of the chart within the drawing.',
        required=False)

    y = attr.Measurement(
        title='Chart Y-Position',
        description='The y-position of the chart within the drawing.',
        required=False)

    width = attr.Measurement(
        title='Chart Width',
        description='The width of the chart.',
        required=False)

    height = attr.Measurement(
        title='Chart Height',
        description='The height of the chart.',
        required=False)

    strokeColor = attr.Color(
        title='Stroke Color',
        description='Color of the chart border.',
        required=False)

    strokeWidth = attr.Measurement(
        title='Stroke Width',
        description='Width of the chart border.',
        required=False)

    fillColor = attr.Color(
        title='Fill Color',
        description='Color of the chart interior.',
        required=False)

    debug = attr.Boolean(
        title='Debugging',
        description='A flag that when set to True turns on debug messages.',
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
        self.drawing = shapes.Drawing(
            attrs.pop('dwidth'), attrs.pop('dheight'))
        self.context = chart = self.createChart(attrs)
        self.processSubDirectives()
        group = shapes.Group(chart)
        group.translate(0, 0)
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
        occurence.ZeroOrOne('barLabels', IBarLabels),
        *IChart.queryTaggedValue('directives', ())
    )

    direction = attr.Choice(
        title='Direction',
        description='The direction of the bars within the chart.',
        choices=('horizontal', 'vertical'),
        default='horizontal',
        required=False)

    useAbsolute = attr.Boolean(
        title='Use Absolute Spacing',
        description='Flag to use absolute spacing values.',
        default=False,
        required=False)

    barWidth = attr.Measurement(
        title='Bar Width',
        description='The width of an individual bar.',
        default=10,
        required=False)

    groupSpacing = attr.Measurement(
        title='Group Spacing',
        description='Width between groups of bars.',
        default=5,
        required=False)

    barSpacing = attr.Measurement(
        title='Bar Spacing',
        description='Width between individual bars.',
        default=0,
        required=False)

    barLabelFormat = attr.Text(
        title='Bar Label Text Format',
        description='Formatting string for bar labels.',
        required=False)


class BarChart(Chart):
    signature = IBarChart
    nameBase = 'BarChart'
    factories = Chart.factories.copy()
    factories.update({
        'data': Data1D,
        'bars': Bars,
        'barLabels': BarLabels,
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
            barcharts, direction.capitalize() + self.nameBase)()
        for name, value in attrs.items():
            setattr(chart, name, value)
        return chart


class IBarChart3D(IBarChart):
    """Creates a three-dimensional bar chart."""
    occurence.containing(
        *IBarChart.queryTaggedValue('directives', ())
    )

    thetaX = attr.Float(
        title='Theta-X',
        description='Fraction of dx/dz.',
        required=False)

    thetaY = attr.Float(
        title='Theta-Y',
        description='Fraction of dy/dz.',
        required=False)

    zDepth = attr.Measurement(
        title='Z-Depth',
        description='Depth of an individual series/bar.',
        required=False)

    zSpace = attr.Measurement(
        title='Z-Space',
        description='Z-Gap around a series/bar.',
        required=False)


class BarChart3D(BarChart):
    signature = IBarChart3D
    nameBase = 'BarChart3D'
    attrMapping = {'thetaX': 'theta_x', 'thetaY': 'theta_y'}


class ILinePlot(IChart):
    """A line plot."""
    occurence.containing(
        occurence.One('data', IData2D),
        occurence.ZeroOrOne('lines', ILines),
        occurence.ZeroOrOne('xValueAxis', IXValueAxis),
        occurence.ZeroOrOne('yValueAxis', IYValueAxis),
        occurence.ZeroOrOne('lineLabels', ILineLabels),
        *IChart.queryTaggedValue('directives', ())
    )

    reversePlotOrder = attr.Boolean(
        title='Reverse Plot Order',
        description='When true, the coordinate system is reversed.',
        required=False)

    lineLabelNudge = attr.Measurement(
        title='Line Label Nudge',
        description='The distance between the data point and its label.',
        required=False)

    lineLabelFormat = attr.Text(
        title='Line Label Format',
        description='Formatting string for data point labels.',
        required=False)

    joinedLines = attr.Boolean(
        title='Joined Lines',
        description='When true, connect all data points with lines.',
        required=False)

    inFill = attr.Boolean(
        title='Name',
        description=(
            'Flag indicating whether the line plot should be filled, '
            'in other words converted to an area chart.'),
        required=False)


class LinePlot(Chart):
    signature = ILinePlot
    attrMapping = {'inFill': '_inFill'}

    factories = Chart.factories.copy()
    factories.update({
        'data': Data2D,
        'lines': Lines,
        'xValueAxis': LineXValueAxis,
        'yValueAxis': LineYValueAxis,
        'lineLabels': LineLabels,
    })

    def createChart(self, attrs):
        # Generate the chart
        chart = lineplots.LinePlot()
        for name, value in attrs.items():
            setattr(chart, name, value)
        return chart


class ILinePlot3D(ILinePlot):
    """Creates a three-dimensional line plot."""
    occurence.containing(
        *ILinePlot.queryTaggedValue('directives', ())
    )

    thetaX = attr.Float(
        title='Theta-X',
        description='Fraction of dx/dz.',
        required=False)

    thetaY = attr.Float(
        title='Theta-Y',
        description='Fraction of dy/dz.',
        required=False)

    zDepth = attr.Measurement(
        title='Z-Depth',
        description='Depth of an individual series/bar.',
        required=False)

    zSpace = attr.Measurement(
        title='Z-Space',
        description='Z-Gap around a series/bar.',
        required=False)


class LinePlot3D(LinePlot):
    signature = ILinePlot3D
    nameBase = 'LinePlot3D'
    attrMapping = {'thetaX': 'theta_x', 'thetaY': 'theta_y'}

    def createChart(self, attrs):
        # Generate the chart
        chart = lineplots.LinePlot3D()
        for name, value in attrs.items():
            setattr(chart, name, value)
        return chart


class IPieChart(IChart):
    """A pie chart."""
    occurence.containing(
        occurence.One('data', ISingleData1D),
        occurence.ZeroOrOne('slices', ISlices),
        occurence.ZeroOrOne('labels', ISimpleLabels),
        *IChart.queryTaggedValue('directives', ())
    )

    startAngle = attr.Integer(
        title='Start Angle',
        description='The start angle in the chart of the first slice '
                    'in degrees.',
        required=False)

    direction = attr.Choice(
        title='Direction',
        description='The direction in which the pie chart will be built.',
        choices=('clockwise', 'anticlockwise'),
        required=False)

    checkLabelOverlap = attr.Boolean(
        title='Check Label Overlap',
        description=('When true, check and attempt to fix standard '
                     'label overlaps'),
        required=False)

    pointerLabelMode = attr.Choice(
        title='Pointer Label Mode',
        description=('The location relative to the slace the label should '
                     'be placed.'),
        choices={'none': None,
                 'leftright': 'LeftRight',
                 'leftandright': 'LeftAndRight'},
        required=False)

    sameRadii = attr.Boolean(
        title='Same Radii',
        description='When true, make x/y radii the same.',
        required=False)

    orderMode = attr.Choice(
        title='Order Mode',
        description='',
        choices=('fixed', 'alternate'),
        required=False)

    xradius = attr.Measurement(
        title='X-Radius',
        description='The radius of the X-directions',
        required=False)

    yradius = attr.Measurement(
        title='Y-Radius',
        description='The radius of the Y-directions',
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
    """A 3-D pie chart."""
    occurence.containing(
        occurence.One('slices', ISlices3D),
        *IChart.queryTaggedValue('directives', ())
    )

    perspective = attr.Float(
        title='Perspsective',
        description='The flattening parameter.',
        required=False)

    depth_3d = attr.Measurement(
        title='3-D Depth',
        description='The depth of the pie.',
        required=False)

    angle_3d = attr.Float(
        title='3-D Angle',
        description='The view angle in the Z-coordinate.',
        required=False)


class PieChart3D(PieChart):
    signature = IPieChart3D
    chartClass = piecharts.Pie3d

    factories = PieChart.factories.copy()
    factories.update({
        'slices': Slices3D,
    })


class ISpiderChart(IChart):
    """A spider chart."""
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
        title='Start Angle',
        description='The start angle in the chart of the first strand '
                    'in degrees.',
        required=False)

    direction = attr.Choice(
        title='Direction',
        description='The direction in which the spider chart will be built.',
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
