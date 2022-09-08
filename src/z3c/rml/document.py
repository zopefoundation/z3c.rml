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
"""RML ``document`` element
"""
import io
import logging

import reportlab.pdfgen.canvas
import zope.interface
from reportlab.lib import colors
from reportlab.lib import fonts
from reportlab.pdfbase import cidfonts
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase import ttfonts
from reportlab.platypus import tableofcontents
from reportlab.platypus.doctemplate import IndexingFlowable

from z3c.rml import attr
from z3c.rml import canvas
from z3c.rml import directive
from z3c.rml import doclogic  # noqa: F401 imported but unused
from z3c.rml import interfaces
from z3c.rml import list  # noqa: F401 imported but unused
from z3c.rml import occurence
from z3c.rml import pdfinclude  # noqa: F401 imported but unused
from z3c.rml import special
from z3c.rml import storyplace  # noqa: F401 imported but unused
from z3c.rml import stylesheet
from z3c.rml import template


LOGGER_NAME = 'z3c.rml.render'


class IRegisterType1Face(interfaces.IRMLDirectiveSignature):
    """Register a new Type 1 font face."""

    afmFile = attr.File(
        title='AFM File',
        description='Path to AFM file used to register the Type 1 face.',
        doNotOpen=True,
        required=True)

    pfbFile = attr.File(
        title='PFB File',
        description='Path to PFB file used to register the Type 1 face.',
        doNotOpen=True,
        required=True)


class RegisterType1Face(directive.RMLDirective):
    signature = IRegisterType1Face

    def process(self):
        args = self.getAttributeValues(valuesOnly=True)
        face = pdfmetrics.EmbeddedType1Face(*args)
        pdfmetrics.registerTypeFace(face)


class IRegisterFont(interfaces.IRMLDirectiveSignature):
    """Register a new font based on a face and encoding."""

    name = attr.Text(
        title='Name',
        description=('The name under which the font can be used in style '
                     'declarations or other parameters that lookup a font.'),
        required=True)

    faceName = attr.Text(
        title='Face Name',
        description=('The name of the face the font uses. The face has to '
                     'be previously registered.'),
        required=True)

    encName = attr.Text(
        title='Encoding Name',
        description=('The name of the encdoing to be used.'),
        required=True)


class RegisterFont(directive.RMLDirective):
    signature = IRegisterFont

    def process(self):
        args = self.getAttributeValues(valuesOnly=True)
        font = pdfmetrics.Font(*args)
        pdfmetrics.registerFont(font)


class IAddMapping(interfaces.IRMLDirectiveSignature):
    """Map various styles(bold, italic) of a font name to the actual ps fonts
    used."""

    faceName = attr.Text(
        title='Name',
        description=('The name of the font to be mapped'),
        required=True)

    bold = attr.Integer(
        title='Bold',
        description=('Bold'),
        required=True)

    italic = attr.Integer(
        title='Italic',
        description=('Italic'),
        required=True)

    psName = attr.Text(
        title='psName',
        description=('Actual font name mapped'),
        required=True)


class AddMapping(directive.RMLDirective):
    signature = IAddMapping

    def process(self):
        args = self.getAttributeValues(valuesOnly=True)
        fonts.addMapping(*args)


class IRegisterTTFont(interfaces.IRMLDirectiveSignature):
    """Register a new TrueType font given the TT file and face name."""

    faceName = attr.Text(
        title='Face Name',
        description=('The name of the face the font uses. The face has to '
                     'be previously registered.'),
        required=True)

    fileName = attr.File(
        title='File Name',
        description='File path of the of the TrueType font.',
        doNotOpen=True,
        doNotModify=True,
        required=True)


class RegisterTTFont(directive.RMLDirective):
    signature = IRegisterTTFont

    def process(self):
        args = self.getAttributeValues(valuesOnly=True)
        font = ttfonts.TTFont(*args)
        pdfmetrics.registerFont(font)


class IRegisterCidFont(interfaces.IRMLDirectiveSignature):
    """Register a new CID font given the face name."""

    faceName = attr.Text(
        title='Face Name',
        description=('The name of the face the font uses. The face has to '
                     'be previously registered.'),
        required=True)

    encName = attr.Text(
        title='Encoding Name',
        description=('The name of the encoding to use for the font.'),
        required=False)


class RegisterCidFont(directive.RMLDirective):
    signature = IRegisterCidFont
    attrMapping = {'faceName': 'face', 'encName': 'encoding'}

    def process(self):
        args = dict(self.getAttributeValues(attrMapping=self.attrMapping))
        if 'encoding' in args:
            font = cidfonts.CIDFont(**args)
        else:
            font = cidfonts.UnicodeCIDFont(**args)
        pdfmetrics.registerFont(font)


class IRegisterFontFamily(interfaces.IRMLDirectiveSignature):
    """Register a new font family."""

    name = attr.Text(
        title='Name',
        description=('The name of the font family.'),
        required=True)

    normal = attr.Text(
        title='Normal Font Name',
        description=('The name of the normal font variant.'),
        required=False)

    bold = attr.Text(
        title='Bold Font Name',
        description=('The name of the bold font variant.'),
        required=False)

    italic = attr.Text(
        title='Italic Font Name',
        description=('The name of the italic font variant.'),
        required=False)

    boldItalic = attr.Text(
        title='Bold/Italic Font Name',
        description=('The name of the bold/italic font variant.'),
        required=True)


class RegisterFontFamily(directive.RMLDirective):
    signature = IRegisterFontFamily
    attrMapping = {'name': 'family'}

    def process(self):
        args = dict(self.getAttributeValues(attrMapping=self.attrMapping))
        pdfmetrics.registerFontFamily(**args)


class IColorDefinition(interfaces.IRMLDirectiveSignature):
    """Define a new color and give it a name to be known under."""

    id = attr.Text(
        title='Id',
        description=('The id/name the color will be available under.'),
        required=True)

    RGB = attr.Color(
        title='RGB Color',
        description=('The color value that is represented.'),
        required=False)

    CMYK = attr.Color(
        title='CMYK Color',
        description=('The color value that is represented.'),
        required=False)

    value = attr.Color(
        title='Color',
        description=('The color value that is represented.'),
        required=False)

    spotName = attr.Text(
        title='Spot Name',
        description=('The Spot Name of the CMYK color.'),
        required=False)

    density = attr.Float(
        title='Density',
        description=('The color density of the CMYK color.'),
        min=0.0,
        max=1.0,
        required=False)

    knockout = attr.Text(
        title='Knockout',
        description=('The knockout of the CMYK color.'),
        required=False)

    alpha = attr.Float(
        title='Alpha',
        description=('The alpha channel of the color.'),
        min=0.0,
        max=1.0,
        required=False)


class ColorDefinition(directive.RMLDirective):
    signature = IColorDefinition

    def process(self):
        kwargs = dict(self.getAttributeValues())
        id = kwargs.pop('id')
        for attrName in ('RGB', 'CMYK', 'value'):
            color = kwargs.pop(attrName, None)
            if color is not None:
                # CMYK has additional attributes.
                for name, value in kwargs.items():
                    setattr(color, name, value)
                manager = attr.getManager(self)
                manager.colors[id] = color
                return
        raise ValueError('At least one color definition must be specified.')


# Initialize also supports the <color> tag.
stylesheet.Initialize.factories['color'] = ColorDefinition
stylesheet.IInitialize.setTaggedValue(
    'directives',
    stylesheet.IInitialize.getTaggedValue('directives') +
    (occurence.ZeroOrMore('color', IColorDefinition),)
)


class IStartIndex(interfaces.IRMLDirectiveSignature):
    """Start a new index."""

    name = attr.Text(
        title='Name',
        description='The name of the index.',
        default='index',
        required=True)

    offset = attr.Integer(
        title='Offset',
        description='The counting offset.',
        min=0,
        required=False)

    format = attr.Choice(
        title='Format',
        description=('The format the index is going to use.'),
        choices=interfaces.LIST_FORMATS,
        required=False)


class StartIndex(directive.RMLDirective):
    signature = IStartIndex

    def process(self):
        kwargs = dict(self.getAttributeValues())
        name = kwargs['name']
        manager = attr.getManager(self)
        manager.indexes[name] = tableofcontents.SimpleIndex(**kwargs)


class ICropMarks(interfaces.IRMLDirectiveSignature):
    """Crop Marks specification"""

    name = attr.Text(
        title='Name',
        description='The name of the index.',
        default='index',
        required=True)

    borderWidth = attr.Measurement(
        title='Border Width',
        description='The width of the crop mark border.',
        required=False)

    markColor = attr.Color(
        title='Mark Color',
        description='The color of the crop marks.',
        required=False)

    markWidth = attr.Measurement(
        title='Mark Width',
        description='The line width of the actual crop marks.',
        required=False)

    markLength = attr.Measurement(
        title='Mark Length',
        description='The length of the actual crop marks.',
        required=False)

    markLast = attr.Boolean(
        title='Mark Last',
        description='If set, marks are drawn after the content is rendered.',
        required=False)

    bleedWidth = attr.Measurement(
        title='Bleed Width',
        description=('The width of the page bleed.'),
        required=False)


class CropMarksProperties:
    borderWidth = 36
    markWidth = 0.5
    markColor = colors.toColor('green')
    markLength = 18
    markLast = True
    bleedWidth = 0


class CropMarks(directive.RMLDirective):
    signature = ICropMarks

    def process(self):
        cmp = CropMarksProperties()
        for name, value in self.getAttributeValues():
            setattr(cmp, name, value)
        self.parent.parent.cropMarks = cmp


class ILogConfig(interfaces.IRMLDirectiveSignature):
    """Configure the render logger."""

    level = attr.Choice(
        title='Level',
        description='The default log level.',
        choices=interfaces.LOG_LEVELS,
        doLower=False,
        required=False)

    format = attr.Text(
        title='Format',
        description='The format of the log messages.',
        required=False)

    filename = attr.File(
        title='File Name',
        description='The path to the file that is being logged.',
        doNotOpen=True,
        required=True)

    filemode = attr.Choice(
        title='File Mode',
        description='The mode to open the file in.',
        choices={'WRITE': 'w', 'APPEND': 'a'},
        default='a',
        required=False)

    datefmt = attr.Text(
        title='Date Format',
        description='The format of the log message date.',
        required=False)


class LogConfig(directive.RMLDirective):
    signature = ILogConfig

    def process(self):
        args = dict(self.getAttributeValues())
        logger = logging.getLogger(LOGGER_NAME)
        handler = logging.FileHandler(args['filename'][8:], args['filemode'])
        formatter = logging.Formatter(
            args.get('format'), args.get('datefmt'))
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        if 'level' in args:
            logger.setLevel(args['level'])
        self.parent.parent.logger = logger


class IDocInit(interfaces.IRMLDirectiveSignature):
    occurence.containing(
        occurence.ZeroOrMore('color', IColorDefinition),
        occurence.ZeroOrMore('name', special.IName),
        occurence.ZeroOrMore('registerType1Face', IRegisterType1Face),
        occurence.ZeroOrMore('registerFont', IRegisterFont),
        occurence.ZeroOrMore('registerCidFont', IRegisterCidFont),
        occurence.ZeroOrMore('registerTTFont', IRegisterTTFont),
        occurence.ZeroOrMore('registerFontFamily', IRegisterFontFamily),
        occurence.ZeroOrMore('addMapping', IAddMapping),
        occurence.ZeroOrMore('logConfig', ILogConfig),
        occurence.ZeroOrMore('cropMarks', ICropMarks),
        occurence.ZeroOrMore('startIndex', IStartIndex),
    )

    pageMode = attr.Choice(
        title='Page Mode',
        description=('The page mode in which the document is opened in '
                     'the viewer.'),
        choices=('UseNone', 'UseOutlines', 'UseThumbs', 'FullScreen'),
        required=False)

    pageLayout = attr.Choice(
        title='Page Layout',
        description=('The layout in which the pages are displayed in '
                     'the viewer.'),
        choices=('SinglePage', 'OneColumn', 'TwoColumnLeft', 'TwoColumnRight'),
        required=False)

    useCropMarks = attr.Boolean(
        title='Use Crop Marks',
        description='A flag when set shows crop marks on the page.',
        required=False)

    hideToolbar = attr.TextBoolean(
        title='Hide Toolbar',
        description=('A flag indicating that the toolbar is hidden in '
                     'the viewer.'),
        required=False)

    hideMenubar = attr.TextBoolean(
        title='Hide Menubar',
        description=('A flag indicating that the menubar is hidden in '
                     'the viewer.'),
        required=False)

    hideWindowUI = attr.TextBoolean(
        title='Hide Window UI',
        description=('A flag indicating that the window UI is hidden in '
                     'the viewer.'),
        required=False)

    fitWindow = attr.TextBoolean(
        title='Fit Window',
        description='A flag indicating that the page fits in the viewer.',
        required=False)

    centerWindow = attr.TextBoolean(
        title='Center Window',
        description=('A flag indicating that the page fits is centered '
                     'in the viewer.'),
        required=False)

    displayDocTitle = attr.TextBoolean(
        title='Display Doc Title',
        description=('A flag indicating that the document title is displayed '
                     'in the viewer.'),
        required=False)

    nonFullScreenPageMode = attr.Choice(
        title='Non-Full-Screen Page Mode',
        description=('Non-Full-Screen page mode in the viewer.'),
        choices=('UseNone', 'UseOutlines', 'UseThumbs', 'UseOC'),
        required=False)

    direction = attr.Choice(
        title='Text Direction',
        description=('The text direction of the PDF.'),
        choices=('L2R', 'R2L'),
        required=False)

    viewArea = attr.Choice(
        title='View Area',
        description=('View Area setting used in the viewer.'),
        choices=('MediaBox', 'CropBox', 'BleedBox', 'TrimBox', 'ArtBox'),
        required=False)

    viewClip = attr.Choice(
        title='View Clip',
        description=('View Clip setting used in the viewer.'),
        choices=('MediaBox', 'CropBox', 'BleedBox', 'TrimBox', 'ArtBox'),
        required=False)

    printArea = attr.Choice(
        title='Print Area',
        description=('Print Area setting used in the viewer.'),
        choices=('MediaBox', 'CropBox', 'BleedBox', 'TrimBox', 'ArtBox'),
        required=False)

    printClip = attr.Choice(
        title='Print Clip',
        description=('Print Clip setting used in the viewer.'),
        choices=('MediaBox', 'CropBox', 'BleedBox', 'TrimBox', 'ArtBox'),
        required=False)

    printScaling = attr.Choice(
        title='Print Scaling',
        description=('The print scaling mode in which the document is opened '
                     'in the viewer.'),
        choices=('None', 'AppDefault'),
        required=False)


class DocInit(directive.RMLDirective):
    signature = IDocInit
    factories = {
        'name': special.Name,
        'color': ColorDefinition,
        'registerType1Face': RegisterType1Face,
        'registerFont': RegisterFont,
        'registerTTFont': RegisterTTFont,
        'registerCidFont': RegisterCidFont,
        'registerFontFamily': RegisterFontFamily,
        'addMapping': AddMapping,
        'logConfig': LogConfig,
        'cropMarks': CropMarks,
        'startIndex': StartIndex,
    }

    viewerOptions = {
        option[0].lower() + option[1:]: option
        for option in ['HideToolbar', 'HideMenubar', 'HideWindowUI',
                       'FitWindow', 'CenterWindow', 'DisplayDocTitle',
                       'NonFullScreenPageMode', 'Direction', 'ViewArea',
                       'ViewClip', 'PrintArea', 'PrintClip', 'PrintScaling']}

    def process(self):
        kwargs = dict(self.getAttributeValues())
        self.parent.cropMarks = kwargs.get('useCropMarks', False)
        self.parent.pageMode = kwargs.get('pageMode')
        self.parent.pageLayout = kwargs.get('pageLayout')
        for name in self.viewerOptions:
            setattr(self.parent, name, kwargs.get(name))
        super().process()


class IDocument(interfaces.IRMLDirectiveSignature):
    occurence.containing(
        occurence.ZeroOrOne('docinit', IDocInit),
        occurence.ZeroOrOne('stylesheet', stylesheet.IStylesheet),
        occurence.ZeroOrOne('template', template.ITemplate),
        occurence.ZeroOrOne('story', template.IStory),
        occurence.ZeroOrOne('pageInfo', canvas.IPageInfo),
        occurence.ZeroOrMore('pageDrawing', canvas.IPageDrawing),
    )

    filename = attr.Text(
        title='File Name',
        description=('The default name of the output file, if no output '
                     'file was provided.'),
        required=True)

    title = attr.Text(
        title='Title',
        description=('The "Title" annotation for the PDF document.'),
        required=False)

    subject = attr.Text(
        title='Subject',
        description=('The "Subject" annotation for the PDF document.'),
        required=False)

    author = attr.Text(
        title='Author',
        description=('The "Author" annotation for the PDF document.'),
        required=False)

    creator = attr.Text(
        title='Creator',
        description=('The "Creator" annotation for the PDF document.'),
        required=False)

    debug = attr.Boolean(
        title='Debug',
        description='A flag to activate the debug output.',
        default=False,
        required=False)

    compression = attr.BooleanWithDefault(
        title='Compression',
        description=('A flag determining whether page compression should '
                     'be used.'),
        required=False)

    invariant = attr.BooleanWithDefault(
        title='Invariant',
        description=('A flag that determines whether the produced PDF '
                     'should be invariant with respect to the date and '
                     'the exact contents.'),
        required=False)


@zope.interface.implementer(interfaces.IManager,
                            interfaces.IPostProcessorManager,
                            interfaces.ICanvasManager)
class Document(directive.RMLDirective):
    signature = IDocument

    factories = {
        'docinit': DocInit,
        'stylesheet': stylesheet.Stylesheet,
        'template': template.Template,
        'story': template.Story,
        'pageInfo': canvas.PageInfo,
        'pageDrawing': canvas.PageDrawing,
    }

    def __init__(self, element, canvasClass=None):
        super().__init__(element, None)
        self.names = {}
        self.styles = {}
        self.colors = {}
        self.indexes = {}
        self.postProcessors = []
        self.filename = '<unknown>'
        self.cropMarks = False
        self.pageLayout = None
        self.pageMode = None
        self.logger = None
        self.svgs = {}
        self.attributesCache = {}
        for name in DocInit.viewerOptions:
            setattr(self, name, None)
        if not canvasClass:
            canvasClass = reportlab.pdfgen.canvas.Canvas
        self.canvasClass = canvasClass

    def _indexAdd(self, canvas, name, label):
        self.indexes[name](canvas, name, label)

    def _beforeDocument(self):
        self._initCanvas(self.doc.canv)
        self.canvas = self.doc.canv

    def _initCanvas(self, canvas):
        canvas._indexAdd = self._indexAdd
        canvas.manager = self
        if self.pageLayout:
            canvas._doc._catalog.setPageLayout(self.pageLayout)
        if self.pageMode:
            canvas._doc._catalog.setPageMode(self.pageMode)
        for name, option in DocInit.viewerOptions.items():
            if getattr(self, name) is not None:
                canvas.setViewerPreference(option, getattr(self, name))
        # Setting annotations.
        data = dict(self.getAttributeValues(
            select=('title', 'subject', 'author', 'creator')))
        canvas.setTitle(data.get('title'))
        canvas.setSubject(data.get('subject'))
        canvas.setAuthor(data.get('author'))
        canvas.setCreator(data.get('creator'))

    def process(self, outputFile=None, maxPasses=2):
        """Process document"""
        # Reset all reportlab global variables. This is very important for
        # ReportLab not to fail.
        reportlab.rl_config._reset()

        debug = self.getAttributeValues(select=('debug',), valuesOnly=True)[0]
        if not debug:
            reportlab.rl_config.shapeChecking = 0

        # Add our colors mapping to the default ones.
        colors.toColor.setExtraColorsNameSpace(self.colors)

        if outputFile is None:
            # TODO: This is relative to the input file *not* the CWD!!!
            outputFile = open(self.element.get('filename'), 'wb')

        # Create a temporary output file, so that post-processors can
        # massage the output
        self.outputFile = tempOutput = io.BytesIO()

        # Process common sub-directives
        self.processSubDirectives(select=('docinit', 'stylesheet'))

        # Handle Page Drawing Documents
        if self.element.find('pageDrawing') is not None:
            kwargs = dict(self.getAttributeValues(
                select=('compression', 'debug'),
                attrMapping={'compression': 'pageCompression',
                             'debug': 'verbosity'}
            ))
            kwargs['cropMarks'] = self.cropMarks

            self.canvas = self.canvasClass(tempOutput, **kwargs)
            self._initCanvas(self.canvas)
            self.processSubDirectives(select=('pageInfo', 'pageDrawing'))

            if hasattr(self.canvas, 'AcroForm'):
                # Makes default values appear in ReportLab >= 3.1.44
                self.canvas.AcroForm.needAppearances = 'true'

            self.canvas.save()

        # Handle Flowable-based documents.
        elif self.element.find('template') is not None:
            self.processSubDirectives(select=('template', 'story'))
            self.doc.beforeDocument = self._beforeDocument

            def callback(event, value):
                if event == 'PASS':
                    self.doc.current_pass = value

            self.doc.setProgressCallBack(callback)
            self.doc.multiBuild(
                self.flowables, maxPasses=maxPasses,
                **{'canvasmaker': self.canvasClass})

        # Process all post processors
        for name, processor in self.postProcessors:
            tempOutput.seek(0)
            tempOutput = processor.process(tempOutput)

        # Save the result into our real output file
        tempOutput.seek(0)
        outputFile.write(tempOutput.getvalue())

        # Cleanup.
        colors.toColor.setExtraColorsNameSpace({})
        reportlab.rl_config.shapeChecking = 1

    def get_name(self, name, default=None):
        if default is None:
            default = ''

        if name not in self.names:
            if self.doc._indexingFlowables and isinstance(
                self.doc._indexingFlowables[-1],
                DummyIndexingFlowable
            ):
                return default
            self.doc._indexingFlowables.append(DummyIndexingFlowable())

        return self.names.get(name, default)


class DummyIndexingFlowable(IndexingFlowable):
    """A dummy flowable to trick multiBuild into performing +1 pass."""

    def __init__(self):
        self.i = -1

    def isSatisfied(self):
        self.i += 1
        return self.i
