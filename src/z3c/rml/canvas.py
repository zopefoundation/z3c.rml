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
"""
import zope.interface
import reportlab.pdfgen.canvas
from z3c.rml import attr, directive, interfaces, occurence, stylesheet
from z3c.rml import chart, flowable, form, page, special


class IShape(interfaces.IRMLDirectiveSignature):
    """A shape to be drawn on the canvas."""

    x = attr.Measurement(
        title=u'X-Coordinate',
        description=(u'The X-coordinate of the lower-left position of the '
                     u'shape.'),
        required=True)

    y = attr.Measurement(
        title=u'Y-Coordinate',
        description=(u'The Y-coordinate of the lower-left position of the '
                     u'shape.'),
        required=True)

    fill = attr.Boolean(
        title=u'Fill',
        description=u'A flag to specify whether the shape should be filled.',
        required=False)

    stroke = attr.Boolean(
        title=u'Stroke',
        description=(u"A flag to specify whether the shape's outline should "
                     u"be drawn."),
        required=False)


class CanvasRMLDirective(directive.RMLDirective):
    callable = None
    attrMapping = None

    def process(self):
        kwargs = dict(self.getAttributeValues(attrMapping=self.attrMapping))
        canvas = attr.getManager(self, interfaces.ICanvasManager).canvas
        getattr(canvas, self.callable)(**kwargs)


class ISaveState(interfaces.IRMLDirectiveSignature):
    """Saves the current canvas state."""

class SaveState(CanvasRMLDirective):
    signature = ISaveState
    callable = 'saveState'


class IRestoreState(interfaces.IRMLDirectiveSignature):
    """Saves the current canvas state."""

class RestoreState(CanvasRMLDirective):
    signature = IRestoreState
    callable = 'restoreState'


class IDrawString(interfaces.IRMLDirectiveSignature):
    """Draws a simple string (left aligned) onto the canvas at the specified
    location."""

    x = attr.Measurement(
        title=u'X-Coordinate',
        description=(u'The X-coordinate of the lower-left position of the '
                     u'string.'),
        required=True)

    y = attr.Measurement(
        title=u'Y-Coordinate',
        description=(u'The Y-coordinate of the lower-left position of the '
                     u'string.'),
        required=True)

    text = attr.RawXMLContent(
        title=u'Text',
        description=(u'The string/text that is put onto the canvas.'),
        required=True)

class DrawString(CanvasRMLDirective, special.TextFlowables):
    signature = IDrawString
    callable = 'drawString'

    def process(self):
        canvas = attr.getManager(self, interfaces.ICanvasManager).canvas
        kwargs = dict(self.getAttributeValues(attrMapping=self.attrMapping))
        kwargs['text'] = self._getText(self.element, canvas).strip()
        getattr(canvas, self.callable)(**kwargs)

class IDrawRightString(IDrawString):
    """Draws a simple string (right aligned) onto the canvas at the specified
    location."""

class DrawRightString(DrawString):
    signature = IDrawRightString
    callable = 'drawRightString'


class IDrawCenteredString(IDrawString):
    """Draws a simple string (centered aligned) onto the canvas at the specified
    location."""

class DrawCenteredString(DrawString):
    signature = IDrawCenteredString
    callable = 'drawCentredString'


class IDrawAlignedString(IDrawString):
    """Draws a simple string (aligned to the pivot character) onto the canvas
    at the specified location."""

    pivotChar = attr.Text(
        title=u'Text',
        description=(u'The string/text that is put onto the canvas.'),
        min_length=1,
        max_length=1,
        default=u'.',
        required=True)

class DrawAlignedString(DrawString):
    signature = IDrawAlignedString
    callable = 'drawAlignedString'


class IEllipse(IShape):
    """Draws an ellipse on the canvas."""

    width = attr.Measurement(
        title=u'Width',
        description=u'The width of the ellipse.',
        required=True)

    height = attr.Measurement(
        title=u'Height',
        description=u'The height of the ellipse.',
        required=True)

class Ellipse(CanvasRMLDirective):
    signature = IEllipse
    callable = 'ellipse'
    attrMapping = {'x': 'x1', 'y': 'y1'}

    def process(self):
        kwargs = dict(self.getAttributeValues(attrMapping=self.attrMapping))
        canvas = attr.getManager(self, interfaces.ICanvasManager).canvas
        # Convert width and height to end locations
        kwargs['x2'] = kwargs['x1'] + kwargs['width']
        del kwargs['width']
        kwargs['y2'] = kwargs['y1'] + kwargs['height']
        del kwargs['height']
        getattr(canvas, self.callable)(**kwargs)


class ICircle(IShape):
    """Draws a circle on the canvas."""

    radius = attr.Measurement(
        title=u'Radius',
        description=u'The radius of the circle.',
        required=True)

class Circle(CanvasRMLDirective):
    signature = ICircle
    callable = 'circle'
    attrMapping = {'x': 'x_cen', 'y': 'y_cen', 'radius': 'r'}


class IRectangle(IShape):
    """Draws an ellipse on the canvas."""

    width = attr.Measurement(
        title=u'Width',
        description=u'The width of the rectangle.',
        required=True)

    height = attr.Measurement(
        title=u'Height',
        description=u'The height of the rectangle.',
        required=True)

    round = attr.Measurement(
        title=u'Corner Radius',
        description=u'The radius of the rounded corners.',
        required=False)

    href = attr.Text(
        title=u'Link URL',
        description=u'When specified, the rectangle becomes a link to that URL.',
        required=False)

    destination = attr.Text(
        title=u'Link Destination',
        description=(u'When specified, the rectangle becomes a link to that '
                     u'destination.'),
        required=False)

class Rectangle(CanvasRMLDirective):
    signature = IRectangle
    callable = 'rect'
    attrMapping = {'round': 'radius'}

    def process(self):
        if 'round' in self.element.keys():
            self.callable = 'roundRect'
        kwargs = dict(self.getAttributeValues(attrMapping=self.attrMapping))
        canvas = attr.getManager(self, interfaces.ICanvasManager).canvas
        # Create a link
        url = kwargs.pop('href', None)
        if url:
            canvas.linkURL(
                url,
                (kwargs['x'], kwargs['y'],
                 kwargs['x']+kwargs['width'], kwargs['y']+kwargs['height']))
        dest = kwargs.pop('destination', None)
        if dest:
            canvas.linkRect(
                '', dest,
                (kwargs['x'], kwargs['y'],
                 kwargs['x']+kwargs['width'], kwargs['y']+kwargs['height']))

        # Render the rectangle
        getattr(canvas, self.callable)(**kwargs)

class IGrid(interfaces.IRMLDirectiveSignature):
    """A shape to be drawn on the canvas."""

    xs = attr.Sequence(
        title=u'X-Coordinates',
        description=(u'A sequence x-coordinates that represent the vertical '
                     u'line positions.'),
        value_type=attr.Measurement(),
        required=True)

    ys = attr.Sequence(
        title=u'Y-Coordinates',
        description=(u'A sequence y-coordinates that represent the horizontal '
                     u'line positions.'),
        value_type=attr.Measurement(),
        required=True)


class Grid(CanvasRMLDirective):
    signature = IGrid
    callable = 'grid'
    attrMapping = {'xs': 'xlist', 'ys': 'ylist'}


class ILines(interfaces.IRMLDirectiveSignature):
    """A path of connected lines drawn on the canvas."""

    linelist = attr.TextNodeGrid(
        title=u'Line List',
        description=(u'A list of lines coordinates to draw.'),
        value_type=attr.Measurement(),
        columns=4,
        required=True)

class Lines(CanvasRMLDirective):
    signature = ILines
    callable = 'lines'


class ICurves(interfaces.IRMLDirectiveSignature):
    """A path of connected bezier curves drawn on the canvas."""

    curvelist = attr.TextNodeGrid(
        title=u'Curve List',
        description=(u'A list of curve coordinates to draw.'),
        value_type=attr.Measurement(),
        columns=8,
        required=True)

class Curves(CanvasRMLDirective):
    signature = ICurves
    callable = 'bezier'

    def process(self):
        argset = self.getAttributeValues(valuesOnly=True)[0]
        canvas = attr.getManager(self, interfaces.ICanvasManager).canvas
        for args in argset:
            getattr(canvas, self.callable)(*args)


class IImage(interfaces.IRMLDirectiveSignature):
    """Draws an external image on the canvas."""

    file = attr.Image(
        title=u'File',
        description=(u'Reference to the external file of the iamge.'),
        required=True)

    x = attr.Measurement(
        title=u'X-Coordinate',
        description=(u'The X-coordinate of the lower-left position of the '
                     u'shape.'),
        required=True)

    y = attr.Measurement(
        title=u'Y-Coordinate',
        description=(u'The Y-coordinate of the lower-left position of the '
                     u'shape.'),
        required=True)

    width = attr.Measurement(
        title=u'Width',
        description=u'The width of the image.',
        required=False)

    height = attr.Measurement(
        title=u'Height',
        description=u'The height of the image.',
        required=False)

    showBoundary = attr.Boolean(
        title=u'Show Boundary',
        description=(u'A flag determining whether a border should be drawn '
                     u'around the image.'),
        default=False,
        required=False)

    preserveAspectRatio = attr.Boolean(
        title=u'Preserve Aspect Ratio',
        description=(u"A flag determining whether the image's aspect ration "
                     u"should be conserved under any circumstances."),
        default=False,
        required=False)

    mask = attr.Color(
        title=u'Mask',
        description=u'The color mask used to render the image, or "auto" to use the alpha channel if available.',
        default='auto',
        required=False,
        acceptAuto=True)

class Image(CanvasRMLDirective):
    signature = IImage
    callable = 'drawImage'
    attrMapping = {'file': 'image'}

    def process(self):
        kwargs = dict(self.getAttributeValues(attrMapping=self.attrMapping))
        preserve = kwargs.pop('preserveAspectRatio')
        show = kwargs.pop('showBoundary')

        if preserve:
            imgX, imgY = kwargs['image'].getSize()

            # Scale image correctly, if width and/or height were specified
            if 'width' in kwargs and 'height' not in kwargs:
                kwargs['height'] = imgY * kwargs['width'] / imgX
            elif 'height' in kwargs and 'width' not in kwargs:
                kwargs['width'] = imgX * kwargs['height'] / imgY
            elif 'width' in kwargs and 'height' in kwargs:
                if float(kwargs['width'])/kwargs['height'] > float(imgX)/imgY:
                    kwargs['width'] = imgX * kwargs['height'] / imgY
                else:
                    kwargs['height'] = imgY * kwargs['width'] / imgX

        canvas = attr.getManager(self, interfaces.ICanvasManager).canvas
        getattr(canvas, self.callable)(**kwargs)

        if show:
            width = kwargs.get('width', kwargs['image'].getSize()[0])
            height = kwargs.get('height', kwargs['image'].getSize()[1])
            canvas.rect(kwargs['x'], kwargs['y'], width, height)


class IPlace(interfaces.IRMLDirectiveSignature):
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

class Place(CanvasRMLDirective):
    signature = IPlace

    def process(self):
        x, y, width, height = self.getAttributeValues(
            select=('x', 'y', 'width', 'height'), valuesOnly=True)
        y += height

        flows = flowable.Flow(self.element, self.parent)
        flows.process()

        canvas = attr.getManager(self, interfaces.ICanvasManager).canvas
        for flow in flows.flow:
            flowWidth, flowHeight = flow.wrap(width, height)
            if flowWidth <= width and flowHeight <= height:
                y -= flowHeight
                flow.drawOn(canvas, x, y)
                height -= flowHeight
            else:
                raise ValueError("Not enough space")


class IParam(interfaces.IRMLDirectiveSignature):
    """Sets one paramter for the text annotation."""

    name = attr.String(
        title=u'Name',
        description=u'The name of the paramter.',
        required=True)

    value = attr.TextNode(
        title=u'Value',
        description=(u'The parameter value.'),
        required=True)

class Param(directive.RMLDirective):
    signature = IParam

    def process(self):
        args = dict(self.getAttributeValues())
        self.parent.params[args['name']] = args['value']


class ITextAnnotation(interfaces.IRMLDirectiveSignature):
    """Writes a low-level text annotation into the PDF."""
    occurence.containing(
        occurence.ZeroOrMore('param', IParam))

    contents = attr.FirstLevelTextNode(
        title=u'Contents',
        description=u'The PDF commands that are inserted as annotation.',
        required=True)

class TextAnnotation(CanvasRMLDirective):
    signature = ITextAnnotation
    factories = {'param': Param}

    paramTypes = {'escape': attr.Integer()}

    def process(self):
        contents = self.getAttributeValues(valuesOnly=True)[0]
        self.params = {}
        self.processSubDirectives()
        for name, type in self.paramTypes.items():
            if name in self.params:
                bound = type.bind(self)
                self.params[name] = bound.fromUnicode(self.params[name])
        canvas = attr.getManager(self, interfaces.ICanvasManager).canvas
        canvas.textAnnotation(contents, **self.params)


class IMoveTo(interfaces.IRMLDirectiveSignature):
    """Move the path cursor to the specified location."""

    position = attr.TextNodeSequence(
        title=u'Position',
        description=u'Position to which the path pointer is moved to.',
        value_type=attr.Measurement(),
        min_length=2,
        max_length=2,
        required=True)

class MoveTo(directive.RMLDirective):
    signature = IMoveTo

    def process(self):
        args = self.getAttributeValues(valuesOnly=True)
        self.parent.path.moveTo(*args[0])


class ICurveTo(interfaces.IRMLDirectiveSignature):
    """Create a bezier curve from the current location to the specified one."""

    curvelist = attr.TextNodeGrid(
        title=u'Curve Specification',
        description=u'Describes the end position and the curve properties.',
        value_type=attr.Measurement(),
        columns=6,
        required=True)

class CurveTo(directive.RMLDirective):
    signature = ICurveTo

    def process(self):
        argset = self.getAttributeValues(valuesOnly=True)[0]
        for args in argset:
            self.parent.path.curveTo(*args)

class ICurvesTo(ICurveTo):
    pass
directive.DeprecatedDirective(
    ICurvesTo,
    'Available for ReportLab RML compatibility. Please use the "curveto" '
    'directive instead.')


class IPath(IShape):
    """Create a line path."""
    occurence.containing(
        occurence.ZeroOrMore('moveto', IMoveTo),
        occurence.ZeroOrMore('curveto', ICurveTo),
        occurence.ZeroOrMore('curvesto', ICurvesTo),
        )

    points = attr.TextNodeGrid(
        title=u'Points',
        description=(u'A list of coordinate points that define th path.'),
        value_type=attr.Measurement(),
        columns=2,
        required=True)

    close = attr.Boolean(
        title=u'Close Path',
        description=(u"A flag specifying whether the path should be closed."),
        default=False,
        required=False)

    clip = attr.Boolean(
        title=u'Clip Path',
        description=(u"A flag specifying whether the path should clip "
                     u"overlapping elements."),
        default=False,
        required=False)

class Path(CanvasRMLDirective):
    signature = IPath
    factories = {
        'moveto': MoveTo,
        'curveto': CurveTo,
        'curvesto': CurveTo
        }

    def processPoints(self, text):
        if text.strip() == '':
            return
        bound = self.signature['points'].bind(self)
        for coords in bound.fromUnicode(text):
            self.path.lineTo(*coords)

    def process(self):
        kwargs = dict(self.getAttributeValues(ignore=('points',)))

        # Start the path and set the cursor to the start location.
        canvas = attr.getManager(self, interfaces.ICanvasManager).canvas
        self.path = canvas.beginPath()
        self.path.moveTo(kwargs.pop('x'), kwargs.pop('y'))

        # Process the text before the first sub-directive.
        if self.element.text is not None:
            self.processPoints(self.element.text)
        # Handle each sub-directive.
        for directive in self.element.getchildren():
            if directive.tag in self.factories:
                self.factories[directive.tag](directive, self).process()
            # If there is more text after sub-directive, process it.
            if directive.tail is not None:
                self.processPoints(directive.tail)

        if kwargs.pop('close', False):
            self.path.close()

        if kwargs.pop('clip', False):
            canvas.clipPath(self.path, **kwargs)
        else:
            canvas.drawPath(self.path, **kwargs)


class IFill(interfaces.IRMLDirectiveSignature):
    """Set the fill color."""

    color = attr.Color(
        title=u'Color',
        description=(u'The color value to be set.'),
        required=True)

class Fill(CanvasRMLDirective):
    signature = IFill
    callable = 'setFillColor'
    attrMapping = {'color': 'aColor'}


class IStroke(interfaces.IRMLDirectiveSignature):
    """Set the stroke/line color."""

    color = attr.Color(
        title=u'Color',
        description=(u'The color value to be set.'),
        required=True)

class Stroke(CanvasRMLDirective):
    signature = IStroke
    callable = 'setStrokeColor'
    attrMapping = {'color': 'aColor'}


class ISetFont(interfaces.IRMLDirectiveSignature):
    """Set the font name and/or size."""

    name = attr.String(
        title=u'Font Name',
        description=(u'The name of the font as it was registered.'),
        required=True)

    size = attr.Measurement(
        title=u'Size',
        description=(u'The font size.'),
        required=True)

    leading = attr.Measurement(
        title=u'Leading',
        description=(u'The font leading.'),
        required=False)

class SetFont(CanvasRMLDirective):
    signature = ISetFont
    callable = 'setFont'
    attrMapping = {'name': 'psfontname'}


class ISetFontSize(interfaces.IRMLDirectiveSignature):
    """Set the font size."""

    size = attr.Measurement(
        title=u'Size',
        description=(u'The font size.'),
        required=True)

    leading = attr.Measurement(
        title=u'Leading',
        description=(u'The font leading.'),
        required=False)

class SetFontSize(CanvasRMLDirective):
    signature = ISetFontSize
    callable = 'setFontSize'


class IScale(interfaces.IRMLDirectiveSignature):
    """Scale the drawing using x and y scaling factors."""

    sx = attr.Float(
        title=u'X-Scaling-Factor',
        description=(u'The scaling factor applied on x-coordinates.'),
        default=1,
        required=False)

    sy = attr.Float(
        title=u'Y-Scaling-Factor',
        description=(u'The scaling factor applied on y-coordinates.'),
        default=1,
        required=False)

class Scale(CanvasRMLDirective):
    signature = IScale
    callable = 'scale'
    attrMapping = {'sx': 'x', 'sy': 'y'}


class ITranslate(interfaces.IRMLDirectiveSignature):
    """Translate the drawing coordinates by the specified x and y offset."""

    dx = attr.Measurement(
        title=u'X-Offset',
        description=(u'The amount to move the drawing to the right.'),
        required=True)

    dy = attr.Measurement(
        title=u'Y-Offset',
        description=(u'The amount to move the drawing upward.'),
        required=True)

class Translate(CanvasRMLDirective):
    signature = ITranslate
    callable = 'translate'


class IRotate(interfaces.IRMLDirectiveSignature):
    """Rotate the drawing counterclockwise."""

    degrees = attr.Measurement(
        title=u'Angle',
        description=(u'The angle in degrees.'),
        required=True)

class Rotate(CanvasRMLDirective):
    signature = IRotate
    callable = 'rotate'
    attrMapping = {'degrees': 'theta'}


class ISkew(interfaces.IRMLDirectiveSignature):
    """Skew the drawing."""

    alpha = attr.Measurement(
        title=u'Alpha',
        description=(u'The amount to skew the drawing in the horizontal.'),
        required=True)

    beta = attr.Measurement(
        title=u'Beta',
        description=(u'The amount to skew the drawing in the vertical.'),
        required=True)

class Skew(CanvasRMLDirective):
    signature = ISkew
    callable = 'skew'


class ITransform(interfaces.IRMLDirectiveSignature):
    """A full 2-D matrix transformation"""

    matrix = attr.TextNodeSequence(
        title=u'Matrix',
        description=u'The transformation matrix.',
        value_type=attr.Float(),
        min_length=6,
        max_length=6,
        required=True)

class Transform(CanvasRMLDirective):
    signature = ITransform

    def process(self):
        args = self.getAttributeValues(valuesOnly=True)
        canvas = attr.getManager(self, interfaces.ICanvasManager).canvas
        canvas.transform(*args[0])


class ILineMode(interfaces.IRMLDirectiveSignature):
    """Set the line mode for the following graphics elements."""

    width = attr.Measurement(
        title=u'Width',
        description=(u'The line width.'),
        required=False)

    dash = attr.Sequence(
        title=u'Dash-Pattern',
        description=(u'The dash-pattern of a line.'),
        value_type=attr.Measurement(),
        required=False)

    miterLimit = attr.Measurement(
        title=u'Miter Limit',
        description=(u'The ???.'),
        required=False)

    join = attr.Choice(
        title=u'Join',
        description=u'The way lines are joined together.',
        choices=interfaces.JOIN_CHOICES,
        required=False)

    cap = attr.Choice(
        title=u'Cap',
        description=u'The cap is the desciption of how the line-endings look.',
        choices=interfaces.CAP_CHOICES,
        required=False)

class LineMode(CanvasRMLDirective):
    signature = ILineMode

    def process(self):
        kw = dict(self.getAttributeValues())
        canvas = attr.getManager(self, interfaces.ICanvasManager).canvas
        if 'width' in kw:
            canvas.setLineWidth(kw['width'])
        if 'join' in kw:
            canvas.setLineJoin(kw['join'])
        if 'cap' in kw:
            canvas.setLineCap(kw['cap'])
        if 'miterLimit' in kw:
            canvas.setMiterLimit(kw['miterLimit'])
        if 'dash' in kw:
            canvas.setDash(kw['dash'])


class IBookmark(interfaces.IRMLDirectiveSignature):
    """
    This creates a bookmark to the current page which can be referred to with
    the given key elsewhere. (Used inside a page drawing.)
    """

    name = attr.Text(
        title=u'Name',
        description=u'The name of the bookmark.',
        required=True)

    fit = attr.Choice(
        title=u'Fit',
        description=u'The Fit Type.',
        choices=('XYZ', 'Fit', 'FitH', 'FitV', 'FitR'),
        required=False)

    zoom = attr.Float(
        title=u'Zoom',
        description=u'The zoom level when clicking on the bookmark.',
        required=False)

    x = attr.Measurement(
        title=u'X-Position',
        description=u'The x-position.',
        required=False)

    y = attr.Measurement(
        title=u'Y-Position',
        description=u'The y-position.',
        required=False)

class Bookmark(CanvasRMLDirective):
    signature = IBookmark

    def process(self):
        args = dict(self.getAttributeValues())
        canvas = attr.getManager(self, interfaces.ICanvasManager).canvas
        args['left'], args['top'] = canvas.absolutePosition(args['x'], args['y'])
        canvas.bookmarkPage(**args)


class IPlugInGraphic(interfaces.IRMLDirectiveSignature):
    """Inserts a custom graphic developed in Python."""

    module = attr.String(
        title=u'Module',
        description=u'The Python module in which the flowable is located.',
        required=True)

    function = attr.String(
        title=u'Function',
        description=(u'The name of the factory function within the module '
                     u'that returns the custom flowable.'),
        required=True)

    params = attr.TextNode(
        title=u'Parameters',
        description=(u'A list of parameters encoded as a long string.'),
        required=False)

class PlugInGraphic(CanvasRMLDirective):
    signature = IPlugInGraphic

    def process(self):
        modulePath, functionName, params = self.getAttributeValues(
            valuesOnly=True)
        module = __import__(modulePath, {}, {}, [modulePath])
        function = getattr(module, functionName)
        canvas = attr.getManager(self, interfaces.ICanvasManager).canvas
        function(canvas, params)


class IDrawing(interfaces.IRMLDirectiveSignature):
    """A container directive for all directives that draw directly on the
    cnavas."""
    occurence.containing(
        # State Manipulation
        occurence.ZeroOrMore('saveState', ISaveState),
        occurence.ZeroOrMore('restoreState', IRestoreState),
        # String Drawing
        occurence.ZeroOrMore('drawString', IDrawString),
        occurence.ZeroOrMore('drawRightString', IDrawRightString),
        occurence.ZeroOrMore('drawCenteredString', IDrawCenteredString),
        occurence.ZeroOrMore('drawCentredString', IDrawCenteredString),
        occurence.ZeroOrMore('drawAlignedString', IDrawAlignedString),
        # Drawing Operations
        occurence.ZeroOrMore('ellipse', IEllipse),
        occurence.ZeroOrMore('circle', ICircle),
        occurence.ZeroOrMore('rect', IRectangle),
        occurence.ZeroOrMore('grid', IGrid),
        occurence.ZeroOrMore('lines', ILines),
        occurence.ZeroOrMore('curves', ICurves),
        occurence.ZeroOrMore('image', IImage),
        occurence.ZeroOrMore('place', IPlace),
        occurence.ZeroOrMore('textAnnotation', ITextAnnotation),
        occurence.ZeroOrMore('path', IPath),
        # State Change Operations
        occurence.ZeroOrMore('fill', IFill),
        occurence.ZeroOrMore('stroke', IStroke),
        occurence.ZeroOrMore('setFont', ISetFont),
        occurence.ZeroOrMore('setFontSize', ISetFontSize),
        occurence.ZeroOrMore('scale', IScale),
        occurence.ZeroOrMore('translate', ITranslate),
        occurence.ZeroOrMore('rotate', IRotate),
        occurence.ZeroOrMore('skew', ISkew),
        occurence.ZeroOrMore('transform', ITransform),
        occurence.ZeroOrMore('lineMode', ILineMode),
        # Form Field Elements
        occurence.ZeroOrMore('barCode', form.IBarCode),
        occurence.ZeroOrMore('textField', form.ITextField),
        occurence.ZeroOrMore('buttonField', form.IButtonField),
        occurence.ZeroOrMore('selectField', form.ISelectField),
        # Charts
        occurence.ZeroOrMore('barChart', chart.IBarChart),
        occurence.ZeroOrMore('barChart3D', chart.IBarChart3D),
        occurence.ZeroOrMore('linePlot', chart.ILinePlot),
        occurence.ZeroOrMore('linePlot3D', chart.ILinePlot3D),
        occurence.ZeroOrMore('pieChart', chart.IPieChart),
        occurence.ZeroOrMore('pieChart3D', chart.IPieChart3D),
        occurence.ZeroOrMore('spiderChart', chart.ISpiderChart),
        # Misc
        occurence.ZeroOrMore('bookmark', IBookmark),
        occurence.ZeroOrMore('plugInGraphic', IPlugInGraphic),
        )

class Drawing(directive.RMLDirective):
    signature = IDrawing

    factories = {
        # State Management
        'saveState': SaveState,
        'restoreState': RestoreState,
        # Drawing Strings
        'drawString': DrawString,
        'drawRightString': DrawRightString,
        'drawCenteredString': DrawCenteredString,
        'drawCentredString': DrawCenteredString,
        'drawAlignedString': DrawAlignedString,
        # Drawing Operations
        'ellipse': Ellipse,
        'circle': Circle,
        'rect': Rectangle,
        'grid': Grid,
        'lines': Lines,
        'curves': Curves,
        'image': Image,
        'place': Place,
        'textAnnotation': TextAnnotation,
        'path': Path,
        # Form Field Elements
        'barCode': form.BarCode,
        'textField': form.TextField,
        'buttonField': form.ButtonField,
        'selectField': form.SelectField,
        # State Change Operations
        'fill': Fill,
        'stroke': Stroke,
        'setFont': SetFont,
        'setFontSize': SetFontSize,
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
        'linePlot3D': chart.LinePlot3D,
        'pieChart': chart.PieChart,
        'pieChart3D': chart.PieChart3D,
        'spiderChart': chart.SpiderChart,
        # Misc
        'bookmark': Bookmark,
        'plugInGraphic': PlugInGraphic,
        }


class IPageDrawing(IDrawing):
    """Draws directly on the content of one page's canvas. Every call of this
    directive creates a new page."""

    occurence.containing(
        #'mergePage': IMergePage,
        *IDrawing.getTaggedValue('directives'))

class PageDrawing(Drawing):
    signature = IDrawing

    factories = Drawing.factories.copy()
    factories.update({
        'mergePage': page.MergePage
        })

    def process(self):
        super(Drawing, self).process()
        canvas = attr.getManager(self, interfaces.ICanvasManager).canvas
        canvas.showPage()


class IPageInfo(interfaces.IRMLDirectiveSignature):
    """Set's up page-global settings."""

    pageSize = attr.PageSize(
        title=u'Page Size',
        description=(u'The page size of all pages within this document.'),
        required=True)

class PageInfo(CanvasRMLDirective):
    signature=IPageInfo
    callable = 'setPageSize'
    attrMapping = {'pageSize': 'size'}
