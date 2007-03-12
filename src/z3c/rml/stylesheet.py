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

$Id$
"""
__docformat__ = "reStructuredText"
import copy
import reportlab.lib.styles
import reportlab.lib.enums
import reportlab.platypus
from z3c.rml import attr, element, error, special


class Initialize(element.ContainerElement):

    subElements = {
        'name': special.Name,
        'alias': special.Alias,
        }

class ParagraphStyle(element.Element):
    attrs = (
        attr.Text('name'),
        attr.Text('alias'),
        attr.Text('parent'),
        attr.Text('fontName'),
        attr.Measurement('fontSize'),
        attr.Measurement('leading'),
        attr.Measurement('leftIndent'),
        attr.Measurement('rightIndent'),
        attr.Measurement('firstLineIndent'),
        attr.Measurement('spaceBefore'),
        attr.Measurement('spaceAfter'),
        attr.Choice('alignment',
            {'left':reportlab.lib.enums.TA_LEFT,
             'right':reportlab.lib.enums.TA_RIGHT,
             'center':reportlab.lib.enums.TA_CENTER,
             'justify':reportlab.lib.enums.TA_JUSTIFY}),
        attr.Text('bulletFontname'),
        attr.Measurement('bulletFontsize'),
        attr.Measurement('bulletIndent'),
        attr.Color('textColor'),
        attr.Color('backColor')
        )

    def baseStyle(self, name=None):
        name = name or 'Normal'
        styles = reportlab.lib.styles.getSampleStyleSheet()
        return copy.deepcopy(styles[name])

    def process(self):
        attrs = element.extractKeywordArguments(
            [(attr.name, attr) for attr in self.attrs], self.element)

        style = self.baseStyle(attrs.get('parent'))
        if 'parent' in attrs:
            del attrs['parent']

        for name, value in attrs.items():
            setattr(style, name, value)

        self.parent.parent.styles.setdefault('para', {})[style.name] = style


class TableStyleCommand(element.Element):
    name = None
    attrs = (
        attr.Sequence('start', attr.Int(), [0, 0], length=2),
        attr.Sequence('stop', attr.Int(), [-1, -1], length=2) )

    def process(self):
        args = [self.name]
        for attribute in self.attrs:
            value = attribute.get(self.element)
            if value is not attr.DEFAULT:
                args.append(value)
        self.context.add(*args)

class BlockFont(TableStyleCommand):
    name = 'FONT'
    attrs = TableStyleCommand.attrs + (
        attr.Text('name'),
        attr.Measurement('size'),
        attr.Measurement('leading') )

class BlockLeading(TableStyleCommand):
    name = 'LEADING'
    attrs = TableStyleCommand.attrs + (attr.Measurement('length'), )

class BlockTextColor(TableStyleCommand):
    name = 'TEXTCOLOR'
    attrs = TableStyleCommand.attrs + (attr.Color('colorName'), )

class BlockAlignment(TableStyleCommand):
    name = 'ALIGNMENT'
    attrs = TableStyleCommand.attrs + (
        attr.Choice('value',
                    {'left': 'LEFT', 'right': 'RIGHT',
                     'center': 'CENTER', 'decimal': 'DECIMAL'}), )

class BlockLeftPadding(TableStyleCommand):
    name = 'LEFTPADDING'
    attrs = TableStyleCommand.attrs + (attr.Measurement('length'), )

class BlockRightPadding(TableStyleCommand):
    name = 'RIGHTPADDING'
    attrs = TableStyleCommand.attrs + (attr.Measurement('length'), )

class BlockBottomPadding(TableStyleCommand):
    name = 'BOTTOMPADDING'
    attrs = TableStyleCommand.attrs + (attr.Measurement('length'), )

class BlockTopPadding(TableStyleCommand):
    name = 'TOPPADDING'
    attrs = TableStyleCommand.attrs + (attr.Measurement('length'), )

class BlockBackground(TableStyleCommand):
    name = 'BACKGROUND'
    attrs = TableStyleCommand.attrs + (attr.Color('colorName'), )

class BlockRowBackground(TableStyleCommand):
    name = 'ROWBACKGROUNDS'
    attrs = TableStyleCommand.attrs + (
        attr.Sequence('colorNames', attr.Color()), )

class BlockColBackground(TableStyleCommand):
    name = 'COLBACKGROUNDS'
    attrs = TableStyleCommand.attrs + (
        attr.Sequence('colorNames', attr.Color()), )

class BlockValign(TableStyleCommand):
    name = 'VALIGN'
    attrs = TableStyleCommand.attrs + (
        attr.Choice('value',
                    {'top': 'TOP', 'middle': 'MIDDLE', 'bottom': 'BOTTOM'}), )

class BlockSpan(TableStyleCommand):
    name = 'SPAN'

class LineStyle(TableStyleCommand):
    attrs = TableStyleCommand.attrs + (
        attr.Measurement('thickness', 1),
        attr.Color('colorName'), )

    @property
    def name(self):
        cmds = ['GRID', 'BOX', 'OUTLINE', 'INNERGRID',
                'LINEBELOW', 'LINEABOVE', 'LINEBEFORE', 'LINEAFTER']
        return attr.Choice(
            'kind', dict([(cmd.lower(), cmd) for cmd in cmds])
            ).get(self.element)

class BlockTableStyle(element.ContainerElement):

    subElements = {
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
        id = attr.Text('id').get(self.element)
        style = reportlab.platypus.tables.TableStyle()
        self.processSubElements(style)
        self.parent.parent.styles.setdefault('table', {})[id] = style


class Stylesheet(element.ContainerElement):

    subElements = {
        'initialize': Initialize,
        'paraStyle': ParagraphStyle,
        'blockTableStyle': BlockTableStyle,
        # TODO: 'boxStyle': BoxStyle,
        }
    order = ('paraStyle', 'blockTableStyle', 'initialize')
