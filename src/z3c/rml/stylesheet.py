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
"""
import copy

import reportlab.lib.enums
import reportlab.lib.styles
import reportlab.platypus

from z3c.rml import SampleStyleSheet
from z3c.rml import attr
from z3c.rml import directive
from z3c.rml import interfaces
from z3c.rml import occurence
from z3c.rml import paraparser
from z3c.rml import special


class IInitialize(interfaces.IRMLDirectiveSignature):
    """Do some RML processing initialization."""
    occurence.containing(
        occurence.ZeroOrMore('name', special.IName),
        occurence.ZeroOrMore('alias', special.IAlias),
    )


class Initialize(directive.RMLDirective):
    signature = IInitialize
    factories = {
        'name': special.Name,
        'alias': special.Alias,
    }


class ISpanStyle(interfaces.IRMLDirectiveSignature):
    """Defines a span style and gives it a name."""

    name = attr.Text(
        title='Name',
        description='The name of the style.',
        required=True)

    alias = attr.Text(
        title='Alias',
        description='An alias under which the style will also be known as.',
        required=False)

    parent = attr.Style(
        title='Parent',
        description=('The apragraph style that will be used as a base for '
                     'this one.'),
        required=False)

    fontName = attr.Text(
        title='Font Name',
        description='The name of the font for the span.',
        required=False)

    fontSize = attr.Measurement(
        title='Font Size',
        description='The font size for the text of the span.',
        required=False)

    textTransform = attr.Choice(
        title='Text Transform',
        description='Text transformation.',
        choices=interfaces.TEXT_TRANSFORM_CHOICES,
        required=False)

    underline = attr.Boolean(
        title='Underline Text',
        description='A flag, when set, causes text to be underlined.',
        required=False)

    underlineColor = attr.Color(
        title='Underline Color',
        description='The color in which the underline will appear.',
        required=False)

    underlineWidth = attr.FontSizeRelativeMeasurement(
        title='Underline Width',
        description=('The width/thickness of the underline.'),
        required=False)

    underlineOffset = attr.FontSizeRelativeMeasurement(
        title='Underline Offset',
        description=(
            'The offset of the underline with respect to the baseline.'),
        required=False)

    underlineGap = attr.FontSizeRelativeMeasurement(
        title='Underline Gap',
        description='The gap between lines for double and triple underlines.',
        required=False)

    underlineKind = attr.Choice(
        title='Underline Kind',
        description=('The kind of the underline to use.'),
        choices=interfaces.UNDERLINE_KIND_CHOICES,
        default='single',
        required=False)

    strike = attr.Boolean(
        title='Strike-through Text',
        description='A flag, when set, causes text to be struck out.',
        required=False)

    strikeColor = attr.Color(
        title='Strike Color',
        description='The color in which the strike line will appear.',
        required=False)

    strikeWidth = attr.FontSizeRelativeMeasurement(
        title='Strike Width',
        description=('The width of the strike line.'),
        required=False)

    strikeOffset = attr.FontSizeRelativeMeasurement(
        title='Strike Offset',
        description=(
            'The offset of the strike line with respect to the baseline.'),
        required=False)

    strikeGap = attr.FontSizeRelativeMeasurement(
        title='Strike Gap',
        description=(
            'The gap between lines for double and triple strike lines.'),
        required=False)

    strikeKind = attr.Choice(
        title='Strike Kind',
        description=('The kind of the strike to use.'),
        choices=interfaces.STRIKE_KIND_CHOICES,
        default='single',
        required=False)

    textColor = attr.Color(
        title='Text Color',
        description='The color in which the text will appear.',
        required=False)

    backColor = attr.Color(
        title='Background Color',
        description='The background color of the span.',
        required=False)

    linkUnderline = attr.Boolean(
        title='Underline Links',
        description=(
            'A flag, when set indicating that all links should be '
            'underlined.'),
        default=False,
        required=False)


class SpanStyle(directive.RMLDirective):
    signature = ISpanStyle

    def process(self):
        kwargs = dict(self.getAttributeValues())
        parent = kwargs.pop('parent', paraparser.SpanStyle('DefaultSpan'))
        name = kwargs.pop('name')
        style = copy.deepcopy(parent)
        style.name = name[6:] if name.startswith('style.') else name

        for name, value in kwargs.items():
            setattr(style, name, value)

        manager = attr.getManager(self)
        manager.styles[style.name] = style


class IBaseParagraphStyle(ISpanStyle):

    leading = attr.Measurement(
        title='Leading',
        description=('The height of a single paragraph line. It includes '
                     'character height.'),
        required=False)

    leftIndent = attr.Measurement(
        title='Left Indentation',
        description='General indentation on the left side.',
        required=False)

    rightIndent = attr.Measurement(
        title='Right Indentation',
        description='General indentation on the right side.',
        required=False)

    firstLineIndent = attr.Measurement(
        title='First Line Indentation',
        description='The indentation of the first line in the paragraph.',
        required=False)

    alignment = attr.Choice(
        title='Alignment',
        description='The text alignment.',
        choices=interfaces.ALIGN_CHOICES,
        required=False)

    spaceBefore = attr.Measurement(
        title='Space Before',
        description='The vertical space before the paragraph.',
        required=False)

    spaceAfter = attr.Measurement(
        title='Space After',
        description='The vertical space after the paragraph.',
        required=False)

    bulletFontName = attr.Text(
        title='Bullet Font Name',
        description='The font in which the bullet character will be rendered.',
        required=False)

    bulletFontSize = attr.Measurement(
        title='Bullet Font Size',
        description='The font size of the bullet character.',
        required=False)

    bulletIndent = attr.Measurement(
        title='Bullet Indentation',
        description='The indentation that is kept for a bullet point.',
        required=False)

    bulletColor = attr.Color(
        title='Bullet Color',
        description='The color in which the bullet will appear.',
        required=False)

    wordWrap = attr.Choice(
        title='Word Wrap Method',
        description=(
            'When set to "CJK", invoke CJK word wrapping. LTR RTL use '
            'left to right / right to left with support from pyfribi2 if '
            'available'),
        choices=interfaces.WORD_WRAP_CHOICES,
        required=False)

    borderWidth = attr.Measurement(
        title='Paragraph Border Width',
        description='The width of the paragraph border.',
        required=False)

    borderPadding = attr.Padding(
        title='Paragraph Border Padding',
        description='Padding of the paragraph.',
        required=False)

    borderColor = attr.Color(
        title='Border Color',
        description='The color in which the paragraph border will appear.',
        required=False)

    borderRadius = attr.Measurement(
        title='Paragraph Border Radius',
        description='The radius of the paragraph border.',
        required=False)

    allowWidows = attr.Boolean(
        title='Allow Widows',
        description=('Allow widows.'),
        required=False)

    allowOrphans = attr.Boolean(
        title='Allow Orphans',
        description=('Allow orphans.'),
        required=False)

    endDots = attr.Text(
        title='End Dots',
        description='Characters/Dots at the end of a paragraph.',
        required=False)

    splitLongWords = attr.Boolean(
        title='Split Long Words',
        description=('Try to split long words at the end of a line.'),
        default=True,
        required=False)

    justifyLastLine = attr.Integer(
        title='Justify Last Line',
        description=(
            'Justify last line if there are more then this number of words. '
            'Otherwise, don\'t bother.'),
        default=0,
        required=False)

    justifyBreaks = attr.Boolean(
        title='Justify Breaks',
        description=(
            'A flag, when set indicates that a line with a break should be '
            'justified as well.'),
        default=False,
        required=False)

    spaceShrinkage = attr.Float(
        title='Allowed Whitespace Shrinkage Fraction',
        description=(
            'The fraction of the original whitespace by which the '
            'whitespace is allowed to shrink to fit content on the same '
            'line.'),
        required=False)

    bulletAnchor = attr.Choice(
        title='Bullet Anchor',
        description='The place at which the bullet is anchored.',
        choices=interfaces.BULLET_ANCHOR_CHOICES,
        default='start',
        required=False)

    # Attributes not part of the official style attributes, but are accessed
    # by the paragraph renderer.

    keepWithNext = attr.Boolean(
        title='Keep with Next',
        description=('When set, this paragraph will always be in the same '
                     'frame as the following flowable.'),
        required=False)

    pageBreakBefore = attr.Boolean(
        title='Page Break Before',
        description=('Specifies whether a page break should be inserted '
                     'before the directive.'),
        required=False)

    frameBreakBefore = attr.Boolean(
        title='Frame Break Before',
        description=('Specifies whether a frame break should be inserted '
                     'before the directive.'),
        required=False)


class IParagraphStyle(IBaseParagraphStyle):
    """Defines a paragraph style and gives it a name."""

    name = attr.Text(
        title='Name',
        description='The name of the style.',
        required=True)

    alias = attr.Text(
        title='Alias',
        description='An alias under which the style will also be known as.',
        required=False)

    parent = attr.Style(
        title='Parent',
        description=('The apragraph style that will be used as a base for '
                     'this one.'),
        required=False)


class ParagraphStyle(directive.RMLDirective):
    signature = IParagraphStyle

    def process(self):
        kwargs = dict(self.getAttributeValues())
        parent = kwargs.pop(
            'parent', SampleStyleSheet['Normal'])
        name = kwargs.pop('name')
        style = copy.deepcopy(parent)
        style.name = name[6:] if name.startswith('style.') else name

        for name, value in kwargs.items():
            setattr(style, name, value)

        manager = attr.getManager(self)
        manager.styles[style.name] = style


class ITableStyleCommand(interfaces.IRMLDirectiveSignature):

    start = attr.Sequence(
        title='Start Coordinates',
        description='The start table coordinates for the style instruction',
        value_type=attr.Combination(
            value_types=(attr.Integer(),
                         attr.Choice(choices=interfaces.SPLIT_CHOICES))
        ),
        default=[0, 0],
        min_length=2,
        max_length=2,
        required=True)

    stop = attr.Sequence(
        title='End Coordinates',
        description='The end table coordinates for the style instruction',
        value_type=attr.Combination(
            value_types=(attr.Integer(),
                         attr.Choice(choices=interfaces.SPLIT_CHOICES))
        ),
        default=[-1, -1],
        min_length=2,
        max_length=2,
        required=True)


class TableStyleCommand(directive.RMLDirective):
    name = None

    def process(self):
        args = [self.name]
        args += self.getAttributeValues(valuesOnly=True)
        self.parent.style.add(*args)


class IBlockFont(ITableStyleCommand):
    """Set the font properties for the texts."""

    name = attr.Text(
        title='Font Name',
        description='The name of the font for the cell.',
        required=False)

    size = attr.Measurement(
        title='Font Size',
        description='The font size for the text of the cell.',
        required=False)

    leading = attr.Measurement(
        title='Leading',
        description=('The height of a single text line. It includes '
                     'character height.'),
        required=False)


class BlockFont(TableStyleCommand):
    signature = IBlockFont
    name = 'FONT'


class IBlockLeading(ITableStyleCommand):
    """Set the text leading."""

    length = attr.Measurement(
        title='Length',
        description=('The height of a single text line. It includes '
                     'character height.'),
        required=True)


class BlockLeading(TableStyleCommand):
    signature = IBlockLeading
    name = 'LEADING'


class IBlockTextColor(ITableStyleCommand):
    """Set the text color."""

    colorName = attr.Color(
        title='Color Name',
        description='The color in which the text will appear.',
        required=True)


class BlockTextColor(TableStyleCommand):
    signature = IBlockTextColor
    name = 'TEXTCOLOR'


class IBlockAlignment(ITableStyleCommand):
    """Set the text alignment."""

    value = attr.Choice(
        title='Text Alignment',
        description='The text alignment within the cell.',
        choices=interfaces.ALIGN_TEXT_CHOICES,
        required=True)


class BlockAlignment(TableStyleCommand):
    signature = IBlockAlignment
    name = 'ALIGNMENT'


class IBlockLeftPadding(ITableStyleCommand):
    """Set the left padding of the cells."""

    length = attr.Measurement(
        title='Length',
        description='The size of the padding.',
        required=True)


class BlockLeftPadding(TableStyleCommand):
    signature = IBlockLeftPadding
    name = 'LEFTPADDING'


class IBlockRightPadding(ITableStyleCommand):
    """Set the right padding of the cells."""

    length = attr.Measurement(
        title='Length',
        description='The size of the padding.',
        required=True)


class BlockRightPadding(TableStyleCommand):
    signature = IBlockRightPadding
    name = 'RIGHTPADDING'


class IBlockBottomPadding(ITableStyleCommand):
    """Set the bottom padding of the cells."""

    length = attr.Measurement(
        title='Length',
        description='The size of the padding.',
        required=True)


class BlockBottomPadding(TableStyleCommand):
    signature = IBlockBottomPadding
    name = 'BOTTOMPADDING'


class IBlockTopPadding(ITableStyleCommand):
    """Set the top padding of the cells."""

    length = attr.Measurement(
        title='Length',
        description='The size of the padding.',
        required=True)


class BlockTopPadding(TableStyleCommand):
    signature = IBlockTopPadding
    name = 'TOPPADDING'


class IBlockBackground(ITableStyleCommand):
    """Define the background color of the cells.

    It also supports alternating colors.
    """

    colorName = attr.Color(
        title='Color Name',
        description='The color to use as the background for every cell.',
        required=False)

    colorsByRow = attr.Sequence(
        title='Colors By Row',
        description='A list of colors to be used circularly for rows.',
        value_type=attr.Color(acceptNone=True),
        required=False)

    colorsByCol = attr.Sequence(
        title='Colors By Column',
        description='A list of colors to be used circularly for columns.',
        value_type=attr.Color(acceptNone=True),
        required=False)


class BlockBackground(TableStyleCommand):
    signature = IBlockBackground
    name = 'BACKGROUND'

    def process(self):
        args = [self.name]
        if 'colorsByRow' in self.element.keys():
            args = [BlockRowBackground.name]
        elif 'colorsByCol' in self.element.keys():
            args = [BlockColBackground.name]

        args += self.getAttributeValues(valuesOnly=True)
        self.parent.style.add(*args)


class IBlockRowBackground(ITableStyleCommand):
    """Define the background colors for rows."""

    colorNames = attr.Sequence(
        title='Colors By Row',
        description='A list of colors to be used circularly for rows.',
        value_type=attr.Color(),
        required=True)


class BlockRowBackground(TableStyleCommand):
    signature = IBlockRowBackground
    name = 'ROWBACKGROUNDS'


class IBlockColBackground(ITableStyleCommand):
    """Define the background colors for columns."""

    colorNames = attr.Sequence(
        title='Colors By Row',
        description='A list of colors to be used circularly for rows.',
        value_type=attr.Color(),
        required=True)


class BlockColBackground(TableStyleCommand):
    signature = IBlockColBackground
    name = 'COLBACKGROUNDS'


class IBlockValign(ITableStyleCommand):
    """Define the vertical alignment of the cells."""

    value = attr.Choice(
        title='Vertical Alignment',
        description='The vertical alignment of the text with the cells.',
        choices=interfaces.VALIGN_TEXT_CHOICES,
        required=True)


class BlockValign(TableStyleCommand):
    signature = IBlockValign
    name = 'VALIGN'


class IBlockSpan(ITableStyleCommand):
    """Define a span over multiple cells (rows and columns)."""


class BlockSpan(TableStyleCommand):
    signature = IBlockSpan
    name = 'SPAN'


class IBlockNosplit(ITableStyleCommand):
    """Define a nosplit over multiple cells (rows and columns)."""


class BlockNosplit(TableStyleCommand):
    signature = IBlockNosplit
    name = 'NOSPLIT'


class ILineStyle(ITableStyleCommand):
    """Define the border line style of each cell."""

    kind = attr.Choice(
        title='Kind',
        description='The kind of line actions to be taken.',
        choices=('GRID', 'BOX', 'OUTLINE', 'INNERGRID',
                 'LINEBELOW', 'LINEABOVE', 'LINEBEFORE', 'LINEAFTER'),
        required=True)

    thickness = attr.Measurement(
        title='Thickness',
        description='Line Thickness',
        default=1,
        required=True)

    colorName = attr.Color(
        title='Color',
        description='The color of the border line.',
        default=None,
        required=True)

    cap = attr.Choice(
        title='Cap',
        description='The cap at the end of a border line.',
        choices=interfaces.CAP_CHOICES,
        default=1,
        required=True)

    dash = attr.Sequence(
        title='Dash-Pattern',
        description='The dash-pattern of a line.',
        value_type=attr.Measurement(),
        default=None,
        required=False)

    join = attr.Choice(
        title='Join',
        description='The way lines are joined together.',
        choices=interfaces.JOIN_CHOICES,
        default=1,
        required=False)

    count = attr.Integer(
        title='Count',
        description=('Describes whether the line is a single (1) or '
                     'double (2) line.'),
        default=1,
        required=False)


class LineStyle(TableStyleCommand):
    signature = ILineStyle

    def process(self):
        name = self.getAttributeValues(select=('kind',), valuesOnly=True)[0]
        args = [name]
        args += self.getAttributeValues(ignore=('kind',), valuesOnly=True,
                                        includeMissing=True)
        args = [val if val is not attr.MISSING else None for val in args]
        self.parent.style.add(*args)


class IBlockTableStyle(interfaces.IRMLDirectiveSignature):
    """A style defining the look of a table."""
    occurence.containing(
        occurence.ZeroOrMore('blockFont', IBlockFont),
        occurence.ZeroOrMore('blockLeading', IBlockLeading),
        occurence.ZeroOrMore('blockTextColor', IBlockTextColor),
        occurence.ZeroOrMore('blockAlignment', IBlockAlignment),
        occurence.ZeroOrMore('blockLeftPadding', IBlockLeftPadding),
        occurence.ZeroOrMore('blockRightPadding', IBlockRightPadding),
        occurence.ZeroOrMore('blockBottomPadding', IBlockBottomPadding),
        occurence.ZeroOrMore('blockTopPadding', IBlockTopPadding),
        occurence.ZeroOrMore('blockBackground', IBlockBackground),
        occurence.ZeroOrMore('blockRowBackground', IBlockRowBackground),
        occurence.ZeroOrMore('blockColBackground', IBlockColBackground),
        occurence.ZeroOrMore('blockValign', IBlockValign),
        occurence.ZeroOrMore('blockSpan', IBlockSpan),
        occurence.ZeroOrMore('blockNosplit', IBlockNosplit),
        occurence.ZeroOrMore('lineStyle', ILineStyle)
    )

    id = attr.Text(
        title='Id',
        description='The name/id of the style.',
        required=True)

    keepWithNext = attr.Boolean(
        title='Keep with Next',
        description=('When set, this paragraph will always be in the same '
                     'frame as the following flowable.'),
        required=False)


class BlockTableStyle(directive.RMLDirective):
    signature = IBlockTableStyle

    factories = {
        'blockFont': BlockFont,
        'blockLeading': BlockLeading,
        'blockTextColor': BlockTextColor,
        'blockAlignment': BlockAlignment,
        'blockLeftPadding': BlockLeftPadding,
        'blockRightPadding': BlockRightPadding,
        'blockBottomPadding': BlockBottomPadding,
        'blockTopPadding': BlockTopPadding,
        'blockBackground': BlockBackground,
        'blockRowBackground': BlockRowBackground,
        'blockColBackground': BlockColBackground,
        'blockValign': BlockValign,
        'blockSpan': BlockSpan,
        'blockNosplit': BlockNosplit,
        'lineStyle': LineStyle,
    }

    def process(self):
        kw = dict(self.getAttributeValues())
        id = kw.pop('id')
        # Create Style
        self.style = reportlab.platypus.tables.TableStyle()
        for name, value in kw.items():
            setattr(self.style, name, value)
        # Fill style
        self.processSubDirectives()
        # Add style to the manager
        manager = attr.getManager(self)
        manager.styles[id] = self.style


class IMinimalListStyle(interfaces.IRMLDirectiveSignature):

    leftIndent = attr.Measurement(
        title='Left Indentation',
        description='General indentation on the left side.',
        required=False)

    rightIndent = attr.Measurement(
        title='Right Indentation',
        description='General indentation on the right side.',
        required=False)

    bulletColor = attr.Color(
        title='Bullet Color',
        description='The color in which the bullet will appear.',
        required=False)

    bulletFontName = attr.Text(
        title='Bullet Font Name',
        description='The font in which the bullet character will be rendered.',
        required=False)

    bulletFontSize = attr.Measurement(
        title='Bullet Font Size',
        description='The font size of the bullet character.',
        required=False)

    bulletOffsetY = attr.Measurement(
        title='Bullet Y-Offset',
        description='The vertical offset of the bullet.',
        required=False)

    bulletDedent = attr.StringOrInt(
        title='Bullet Dedent',
        description='Either pixels of dedent or auto (default).',
        required=False)

    bulletDir = attr.Choice(
        title='Bullet Layout Direction',
        description='The layout direction of the bullet.',
        choices=('ltr', 'rtl'),
        required=False)

    bulletFormat = attr.Text(
        title='Bullet Format',
        description='A formatting expression for the bullet text.',
        required=False)

    bulletType = attr.Choice(
        title='Bullet Type',
        description='The type of number to display.',
        choices=interfaces.ORDERED_LIST_TYPES +
        interfaces.UNORDERED_BULLET_VALUES,
        doLower=False,
        required=False)


class IBaseListStyle(IMinimalListStyle):

    start = attr.Combination(
        title='Start Value',
        description='The counter start value.',
        value_types=(
            # Numeric start value.
            attr.Integer(),
            # Bullet types.
            attr.Choice(choices=interfaces.UNORDERED_BULLET_VALUES),
            # Arbitrary text.
            attr.Text(),
        ),
        required=False)


class IListStyle(IBaseListStyle):
    """Defines a list style and gives it a name."""

    name = attr.Text(
        title='Name',
        description='The name of the style.',
        required=True)

    parent = attr.Style(
        title='Parent',
        description=('The list style that will be used as a base for '
                     'this one.'),
        required=False)


class ListStyle(directive.RMLDirective):
    signature = IListStyle

    def process(self):
        kwargs = dict(self.getAttributeValues())
        parent = kwargs.pop(
            'parent', reportlab.lib.styles.ListStyle(name='List'))
        name = kwargs.pop('name')
        style = copy.deepcopy(parent)
        style.name = name[6:] if name.startswith('style.') else name

        for name, value in kwargs.items():
            setattr(style, name, value)

        manager = attr.getManager(self)
        manager.styles[style.name] = style


class IStylesheet(interfaces.IRMLDirectiveSignature):
    """A styleheet defines the styles that can be used in the document."""
    occurence.containing(
        occurence.ZeroOrOne('initialize', IInitialize),
        occurence.ZeroOrMore('spanStyle', ISpanStyle),
        occurence.ZeroOrMore('paraStyle', IParagraphStyle),
        occurence.ZeroOrMore('blockTableStyle', IBlockTableStyle),
        occurence.ZeroOrMore('listStyle', IListStyle),
        # TODO:
        # occurence.ZeroOrMore('boxStyle', IBoxStyle),
    )


class Stylesheet(directive.RMLDirective):
    signature = IStylesheet

    factories = {
        'initialize': Initialize,
        'spanStyle': SpanStyle,
        'paraStyle': ParagraphStyle,
        'blockTableStyle': BlockTableStyle,
        'listStyle': ListStyle,
    }
