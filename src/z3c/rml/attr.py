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
"""RML-specific XML tools

$Id$
"""
__docformat__ = "reStructuredText"
import cStringIO
import re
import reportlab
import reportlab.lib.colors
import reportlab.lib.styles
import reportlab.lib.units
import reportlab.lib.utils
import reportlab.graphics.widgets.markers
import urllib
from lxml import etree

from z3c.rml import interfaces

ALL_COLORS = reportlab.lib.colors.getAllNamedColors()

DEFAULT = object()


class Attribute(object):

    def __init__(self, name=None, default=DEFAULT):
        self.name = name
        self.default = default

    def convert(self, value, context=None):
        return value

    def get(self, element, default=DEFAULT, context=None):
        value = element.get(self.name, DEFAULT)
        if value is DEFAULT or value is default:
            if default is DEFAULT:
                return self.default
            return default
        return self.convert(value, context)


class Text(Attribute):

    def convert(self, value, context=None):
        return unicode(value)


class Int(Attribute):

    def convert(self, value, context=None):
        return int(value)


class Float(Attribute):

    def convert(self, value, context=None):
        return float(value)


class StringOrInt(Attribute):

    def convert(self, value, context=None):
        try:
            return int(value)
        except ValueError:
            return str(value)


class Sequence(Attribute):

    splitre = re.compile('[ \t\n,]*')
    minLength = None
    maxLength = None

    def __init__(self, name=None, valueType=None, default=DEFAULT,
                 splitre=None, minLength=None, maxLength=None, length=None):
        super(Sequence, self).__init__(name, default)
        self.valueType = valueType
        if minLength is not None:
            self.minLength = minLength
        if maxLength is not None:
            self.maxLength = maxLength
        if length is not None:
            self.minLength = self.maxLength = length
        if splitre is not None:
            self.splitre = splitre

    def convert(self, value, context=None):
        if value.startswith('(') and value.endswith(')'):
            value = value[1:-1]
        value = value.strip()
        values = self.splitre.split(value)
        result = [self.valueType.convert(value.strip(), context)
                  for value in values]
        if ((self.minLength is not None and len(result) < self.minLength) and
            (self.maxLength is not None and len(result) > self.maxLength)):
            raise ValueError(
                'Length of sequence must be at least %s and at most %i' % (
                self.minLength, self.maxLength))
        return result


class BaseChoice(Attribute):
    choices = {}

    def convert(self, value, context=None):
        value = value.lower()
        if value in self.choices:
            return self.choices[value]
        raise ValueError(
            '%r not a valid value for attribute "%s"' % (value, self.name))


class Choice(BaseChoice):

    def __init__(self, name=None, choices=None, default=DEFAULT):
        super(Choice, self).__init__(name, default)
        if isinstance(choices, (tuple, list)):
            choices = dict([(val.lower(), val) for val in choices])
        self.choices = choices


class Bool(BaseChoice):
    choices = {'true': True, 'false': False,
               'yes': True, 'no': False,
               '1': True, '0': False,
               }


class DefaultBool(Bool):
    choices = Bool.choices.copy().update({'default': None})


class Measurement(Attribute):

    units = [
	(re.compile('^(-?[0-9\.]+)\s*in$'), reportlab.lib.units.inch),
	(re.compile('^(-?[0-9\.]+)\s*cm$'), reportlab.lib.units.cm),
	(re.compile('^(-?[0-9\.]+)\s*mm$'), reportlab.lib.units.mm),
	(re.compile('^(-?[0-9\.]+)\s*$'), 1)
        ]

    def convert(self, value, context=None):
	for unit in self.units:
            res = unit[0].search(value, 0)
            if res:
                return unit[1]*float(res.group(1))


class Image(Text):

    open = urllib.urlopen

    def __init__(self, name=None, default=DEFAULT, onlyOpen=False):
        super(Image, self).__init__(name, default)
        self.onlyOpen = onlyOpen

    def convert(self, value, context=None):
        fileObj = self.open(value)
        if self.onlyOpen:
            return fileObj
        return reportlab.lib.utils.ImageReader(fileObj)


class Color(Text):

    def convert(self, value, context=None):
        # Color name
        if value in ALL_COLORS:
            return ALL_COLORS[value]
        # Decimal triplet
        rgb = value.split(',')
        if len(rgb) == 3:
            return (float(num) for num in rgb)
        # Hexdecimal triplet
        if value.startswith('#'):
            return (float(int(value[i:i+1], 16)) for i in range(1, 7, 2))
        raise ValueError('%r not a valid color.' %value)


class Style(Text):

    def __init__(self, name=None, type='para', default='Normal'):
        super(Style, self).__init__(name, default)
        self.type = type

    def convert(self, value, context=None, isDefault=False):
        # First, get the custom styles
        proc = context
        while (not interfaces.IStylesManager.providedBy(proc) and
               proc is not None):
            proc = proc.parent
        styles = proc.styles.get(self.type, {})
        # Now look up default values
        if isDefault:
            if 'style.' + value in styles:
                return styles['style.' + value]
            return reportlab.lib.styles.getSampleStyleSheet()[value]
        return styles[value]

    def get(self, element, default=DEFAULT, context=None):
        value = element.get(self.name, DEFAULT)
        if value is DEFAULT:
            if default is DEFAULT:
                return self.convert(self.default, context, True)
            elif default is None:
                return None
            return self.convert(default, context, True)
        return self.convert(value, context)


class Symbol(Text):

    def convert(self, value, context=None):
        return reportlab.graphics.widgets.markers.makeMarker(value)


class TextNode(Attribute):
    """Text ndoes are not really attributes, but behave mostly like it."""

    def __init__(self):
        super(TextNode, self).__init__('TEXT')

    def get(self, element, default=DEFAULT, context=None):
        return unicode(element.text).strip()


class TextNodeSequence(Sequence):

    def __init__(self, *args, **kw):
        super(TextNodeSequence, self).__init__('TEXT', *args, **kw)

    def get(self, element, default=DEFAULT, context=None):
        return self.convert(element.text, context)


class TextNodeGrid(TextNodeSequence):

    def __init__(self, valueType=None, cols=None, default=DEFAULT):
        super(TextNodeSequence, self).__init__(
            'TEXT', valueType, default, length=cols)
        self.cols = cols

    def convert(self, value, context=None):
        result = super(TextNodeGrid, self).convert(value, context)
        if len(result) % self.cols != 0:
            import pdb; pdb.set_trace()
            raise ValueError(
                'Number of elements must be divisible by %i.' %self.cols)
        return [result[i*self.cols:(i+1)*self.cols]
                for i in range(len(result)/self.cols)]


class RawXMLContent(Attribute):

    def __init__(self, default=DEFAULT):
        super(RawXMLContent, self).__init__('XML', default)
        # Do it in here, since we hace a recursive problem otherwise
        from z3c.rml import special
        self.handleElements = {'getName': special.GetName}

    def get(self, element, default=DEFAULT, context=None):
        # Replace what we can replace
        for subElement in element.iterdescendants():
            if subElement.tag in self.handleElements:
                substitute = self.handleElements[subElement.tag](
                    subElement, context, None)
                substitute.process()
        # Now create the text
        text = element.text or u''
        for child in element.getchildren():
            text += etree.tounicode(child)
        if text is None:
            if default is DEFAULT:
                return self.default
            return default
        return text


class XMLContent(RawXMLContent):

    def get(self, element, default=DEFAULT, context=None):
        result = super(XMLContent, self).get(element, default, context)
        return result.strip()
