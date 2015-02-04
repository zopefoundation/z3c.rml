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
import reportlab.lib.styles
import reportlab.lib.enums
import reportlab.platypus
from z3c.rml import attr, directive, interfaces, occurence, SampleStyleSheet, \
    special


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


class IBaseParagraphStyle(interfaces.IRMLDirectiveSignature):

    fontName = attr.String(
        title=u'Font Name',
        description=u'The name of the font for the paragraph.',
        required=False)

    fontSize = attr.Measurement(
        title=u'Font Size',
        description=u'The font size for the text of the paragraph.',
        required=False)

    leading = attr.Measurement(
        title=u'Leading',
        description=(u'The height of a single paragraph line. It includes '
                     u'character height.'),
        required=False)

    leftIndent = attr.Measurement(
        title=u'Left Indentation',
        description=u'General indentation on the left side.',
        required=False)

    rightIndent = attr.Measurement(
        title=u'Right Indentation',
        description=u'General indentation on the right side.',
        required=False)

    firstLineIndent = attr.Measurement(
        title=u'First Line Indentation',
        description=u'The indentation of the first line in the paragraph.',
        required=False)

    alignment = attr.Choice(
        title=u'Alignment',
        description=u'The text alignment.',
        choices=interfaces.ALIGN_CHOICES,
        required=False)

    spaceBefore = attr.Measurement(
        title=u'Space Before',
        description=u'The vertical space before the paragraph.',
        required=False)

    spaceAfter = attr.Measurement(
        title=u'Space After',
        description=u'The vertical space after the paragraph.',
        required=False)

    bulletFontName = attr.String(
        title=u'Bullet Font Name',
        description=u'The font in which the bullet character will be rendered.',
        required=False)

    bulletFontSize = attr.Measurement(
        title=u'Bullet Font Size',
        description=u'The font size of the bullet character.',
        required=False)

    bulletIndent = attr.Measurement(
        title=u'Bullet Indentation',
        description=u'The indentation that is kept for a bullet point.',
        required=False)

    textColor = attr.Color(
        title=u'Text Color',
        description=u'The color in which the text will appear.',
        required=False)

    backColor = attr.Color(
        title=u'Background Color',
        description=u'The background color of the paragraph.',
        required=False)

    wordWrap = attr.String(
        title=u'Word Wrap Method',
        description=(u'When set to "CJK", invoke CJK word wrapping'),
        required=False)

    borderWidth = attr.Measurement(
        title=u'Paragraph Border Width',
        description=u'The width of the paragraph border.',
        required=False)

    borderPadding = attr.Padding(
        title=u'Paragraph Border Padding',
        description=u'Padding of the paragraph.',
        required=False)

    borderColor = attr.Color(
        title=u'Border Color',
        description=u'The color in which the paragraph border will appear.',
        required=False)

    borderRadius = attr.Measurement(
        title=u'Paragraph Border Radius',
        description=u'The radius of the paragraph border.',
        required=False)

    allowWidows = attr.Boolean(
        title=u'Allow Widows',
        description=(u'Allow widows.'),
        required=False)

    allowOrphans = attr.Boolean(
        title=u'Allow Orphans',
        description=(u'Allow orphans.'),
        required=False)

    textTransforms = attr.Choice(
        title=u'Text Transforms',
        description=u'Text transformations.',
        choices=interfaces.TEXT_TRANSFORM_CHOICES,
        required=False)

    endDots = attr.String(
        title=u'End Dots',
        description=u'Characters/Dots at the end of a paragraph.',
        required=False)

    # Attributes not part of the official style attributes, but are accessed
    # by the paragraph renderer.

    keepWithNext = attr.Boolean(
        title=u'Keep with Next',
        description=(u'When set, this paragraph will always be in the same '
                     u'frame as the following flowable.'),
        required=False)

    pageBreakBefore = attr.Boolean(
        title=u'Page Break Before',
        description=(u'Specifies whether a page break should be inserted '
                     u'before the directive.'),
        required=False)

    frameBreakBefore = attr.Boolean(
        title=u'Frame Break Before',
        description=(u'Specifies whether a frame break should be inserted '
                     u'before the directive.'),
        required=False)


class IParagraphStyle(IBaseParagraphStyle):
    """Defines a paragraph style and gives it a name."""

    name = attr.String(
        title=u'Name',
        description=u'The name of the style.',
        required=True)

    alias = attr.String(
        title=u'Alias',
        description=u'An alias under which the style will also be known as.',
        required=False)

    parent = attr.Style(
        title=u'Parent',
        description=(u'The apragraph style that will be used as a base for '
                     u'this one.'),
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
        title=u'Start Coordinates',
        description=u'The start table coordinates for the style instruction',
        value_type=attr.Combination(
            value_types=(attr.Integer(),
                         attr.Choice(choices=interfaces.SPLIT_CHOICES))
            ),
        default=[0, 0],
        min_length=2,
        max_length=2,
        required=True)

    stop = attr.Sequence(
        title=u'End Coordinates',
        description=u'The end table coordinates for the style instruction',
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

    name = attr.String(
        title=u'Font Name',
        description=u'The name of the font for the cell.',
        required=False)

    size = attr.Measurement(
        title=u'Font Size',
        description=u'The font size for the text of the cell.',
        required=False)

    leading = attr.Measurement(
        title=u'Leading',
        description=(u'The height of a single text line. It includes '
                     u'character height.'),
        required=False)

class BlockFont(TableStyleCommand):
    signature = IBlockFont
    name = 'FONT'

class IBlockLeading(ITableStyleCommand):
    """Set the text leading."""

    length = attr.Measurement(
        title=u'Length',
        description=(u'The height of a single text line. It includes '
                     u'character height.'),
        required=True)

class BlockLeading(TableStyleCommand):
    signature = IBlockLeading
    name = 'LEADING'

class IBlockTextColor(ITableStyleCommand):
    """Set the text color."""

    colorName = attr.Color(
        title=u'Color Name',
        description=u'The color in which the text will appear.',
        required=True)

class BlockTextColor(TableStyleCommand):
    signature = IBlockTextColor
    name = 'TEXTCOLOR'

class IBlockAlignment(ITableStyleCommand):
    """Set the text alignment."""

    value = attr.Choice(
        title=u'Text Alignment',
        description=u'The text alignment within the cell.',
        choices=interfaces.ALIGN_TEXT_CHOICES,
        required=True)

class BlockAlignment(TableStyleCommand):
    signature = IBlockAlignment
    name = 'ALIGNMENT'

class IBlockLeftPadding(ITableStyleCommand):
    """Set the left padding of the cells."""

    length = attr.Measurement(
        title=u'Length',
        description=u'The size of the padding.',
        required=True)

class BlockLeftPadding(TableStyleCommand):
    signature = IBlockLeftPadding
    name = 'LEFTPADDING'

class IBlockRightPadding(ITableStyleCommand):
    """Set the right padding of the cells."""

    length = attr.Measurement(
        title=u'Length',
        description=u'The size of the padding.',
        required=True)

class BlockRightPadding(TableStyleCommand):
    signature = IBlockRightPadding
    name = 'RIGHTPADDING'

class IBlockBottomPadding(ITableStyleCommand):
    """Set the bottom padding of the cells."""

    length = attr.Measurement(
        title=u'Length',
        description=u'The size of the padding.',
        required=True)

class BlockBottomPadding(TableStyleCommand):
    signature = IBlockBottomPadding
    name = 'BOTTOMPADDING'

class IBlockTopPadding(ITableStyleCommand):
    """Set the top padding of the cells."""

    length = attr.Measurement(
        title=u'Length',
        description=u'The size of the padding.',
        required=True)

class BlockTopPadding(TableStyleCommand):
    signature = IBlockTopPadding
    name = 'TOPPADDING'

class IBlockBackground(ITableStyleCommand):
    """Define the background color of the cells.

    It also supports alternating colors.
    """

    colorName = attr.Color(
        title=u'Color Name',
        description=u'The color to use as the background for every cell.',
        required=False)

    colorsByRow = attr.Sequence(
        title=u'Colors By Row',
        description=u'A list of colors to be used circularly for rows.',
        value_type=attr.Color(acceptNone=True),
        required=False)

    colorsByCol = attr.Sequence(
        title=u'Colors By Column',
        description=u'A list of colors to be used circularly for columns.',
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
        title=u'Colors By Row',
        description=u'A list of colors to be used circularly for rows.',
        value_type=attr.Color(),
        required=True)

class BlockRowBackground(TableStyleCommand):
    signature = IBlockRowBackground
    name = 'ROWBACKGROUNDS'

class IBlockColBackground(ITableStyleCommand):
    """Define the background colors for columns."""

    colorNames = attr.Sequence(
        title=u'Colors By Row',
        description=u'A list of colors to be used circularly for rows.',
        value_type=attr.Color(),
        required=True)

class BlockColBackground(TableStyleCommand):
    signature = IBlockColBackground
    name = 'COLBACKGROUNDS'

class IBlockValign(ITableStyleCommand):
    """Define the vertical alignment of the cells."""

    value = attr.Choice(
        title=u'Vertical Alignment',
        description=u'The vertical alignment of the text with the cells.',
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

class ILineStyle(ITableStyleCommand):
    """Define the border line style of each cell."""

    kind = attr.Choice(
        title=u'Kind',
        description=u'The kind of line actions to be taken.',
        choices=('GRID', 'BOX', 'OUTLINE', 'INNERGRID',
                 'LINEBELOW', 'LINEABOVE', 'LINEBEFORE', 'LINEAFTER'),
        required=True)

    thickness = attr.Measurement(
        title=u'Thickness',
        description=u'Line Thickness',
        default=1,
        required=True)

    colorName = attr.Color(
        title=u'Color',
        description=u'The color of the border line.',
        default=None,
        required=True)

    cap = attr.Choice(
        title=u'Cap',
        description=u'The cap at the end of a border line.',
        choices=interfaces.CAP_CHOICES,
        default=1,
        required=True)

    dash = attr.Sequence(
        title=u'Dash-Pattern',
        description=u'The dash-pattern of a line.',
        value_type=attr.Measurement(),
        default=None,
        required=False)

    join = attr.Choice(
        title=u'Join',
        description=u'The way lines are joined together.',
        choices=interfaces.JOIN_CHOICES,
        default=1,
        required=False)

    count = attr.Integer(
        title=u'Count',
        description=(u'Describes whether the line is a single (1) or '
                     u'double (2) line.'),
        default=1,
        required=False)

class LineStyle(TableStyleCommand):
    signature = ILineStyle

    def process(self):
        name = self.getAttributeValues(select=('kind',), valuesOnly=True)[0]
        args = [name]
        args += self.getAttributeValues(ignore=('kind',), valuesOnly=True,
                                        includeMissing=True)
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
        occurence.ZeroOrMore('lineStyle', ILineStyle)
        )

    id = attr.String(
        title=u'Id',
        description=u'The name/id of the style.',
        required=True)

    keepWithNext = attr.Boolean(
        title=u'Keep with Next',
        description=(u'When set, this paragraph will always be in the same '
                     u'frame as the following flowable.'),
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
        'lineStyle': LineStyle,
        }

    def process(self):
        kw = dict(self.getAttributeValues())
        id  = kw.pop('id')
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
        title=u'Left Indentation',
        description=u'General indentation on the left side.',
        required=False)

    rightIndent = attr.Measurement(
        title=u'Right Indentation',
        description=u'General indentation on the right side.',
        required=False)

    bulletColor = attr.Color(
        title=u'Bullet Color',
        description=u'The color in which the bullet will appear.',
        required=False)

    bulletFontName = attr.String(
        title=u'Bullet Font Name',
        description=u'The font in which the bullet character will be rendered.',
        required=False)

    bulletFontSize = attr.Measurement(
        title=u'Bullet Font Size',
        description=u'The font size of the bullet character.',
        required=False)

    bulletOffsetY = attr.Measurement(
        title=u'Bullet Y-Offset',
        description=u'The vertical offset of the bullet.',
        required=False)

    bulletDedent = attr.StringOrInt(
        title=u'Bullet Dedent',
        description=u'Either pixels of dedent or auto (default).',
        required=False)

    bulletDir = attr.Choice(
        title=u'Bullet Layout Direction',
        description=u'The layout direction of the bullet.',
        choices=('ltr', 'rtl'),
        required=False)

    bulletFormat = attr.String(
        title=u'Bullet Format',
        description=u'A formatting expression for the bullet text.',
        required=False)

    bulletType = attr.Choice(
        title=u'Bullet Type',
        description=u'The type of number to display.',
        choices=interfaces.ORDERED_LIST_TYPES + \
                interfaces.UNORDERED_BULLET_VALUES,
        doLower=False,
        required=False)

class IBaseListStyle(IMinimalListStyle):

    start = attr.Combination(
        title=u'Start Value',
        description=u'The counter start value.',
        value_types=(
            # Numeric start value.
            attr.Integer(),
            # Bullet types.
            attr.Choice(choices=interfaces.UNORDERED_BULLET_VALUES),
            # Arbitrary text.
            attr.String(),
            ),
        required=False)


class IListStyle(IBaseListStyle):
    """Defines a list style and gives it a name."""

    name = attr.String(
        title=u'Name',
        description=u'The name of the style.',
        required=True)

    parent = attr.Style(
        title=u'Parent',
        description=(u'The list style that will be used as a base for '
                     u'this one.'),
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
        occurence.ZeroOrMore('paraStyle', IParagraphStyle),
        occurence.ZeroOrMore('blockTableStyle', IBlockTableStyle),
        occurence.ZeroOrMore('listStyle', IListStyle),
        # TODO:
        #occurence.ZeroOrMore('boxStyle', IBoxStyle),
        )

class Stylesheet(directive.RMLDirective):
    signature = IStylesheet

    factories = {
        'initialize': Initialize,
        'paraStyle': ParagraphStyle,
        'blockTableStyle': BlockTableStyle,
        'listStyle': ListStyle,
        }
