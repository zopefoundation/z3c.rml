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
import os
import re
import reportlab
import reportlab.lib.colors
import reportlab.lib.styles
import reportlab.lib.units
import reportlab.lib.utils
import reportlab.lib.pagesizes
import reportlab.graphics.widgets.markers
import urllib
from lxml import etree
from xml.sax import saxutils

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
    choices = Bool.choices.copy()
    choices.update({'default': None})


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
        raise ValueError('The value %r is not a valid measurement.' %value)

class Image(Text):

    open = staticmethod(urllib.urlopen)
    packageExtract = re.compile('^\[([0-9A-z_.]*)\]/(.*)$')

    def __init__(self, name=None, default=DEFAULT, onlyOpen=False):
        super(Image, self).__init__(name, default)
        self.onlyOpen = onlyOpen

    def convert(self, value, context=None):
        # Check whether the value is of the form:
        #    [<module.path>]/rel/path/image.gif"
        if value.startswith('['):
            result = self.packageExtract.match(value)
            if result is None:
                raise ValueError(
                    'The package-path-pair you specified was incorrect')
            modulepath, path = result.groups()
            module = __import__(modulepath, {}, {}, (modulepath))
            value = os.path.join(os.path.dirname(module.__file__), path)
        # Open/Download the file
        fileObj = self.open(value)
        if self.onlyOpen:
            return fileObj
        # ImageReader wants to be able to seek, but URL info objects can only
        # be read, so we make a string IO object out of it
        sio = cStringIO.StringIO()
        sio.write(fileObj.read())
        fileObj.close()
        sio.seek(0)
        return reportlab.lib.utils.ImageReader(sio)


class Color(Text):

    def convert(self, value, context=None):
        # Color name
        if value in ALL_COLORS:
            return ALL_COLORS[value]
        # Decimal triplet
        rgb = Sequence(valueType=Float(), length=3).convert(value)
        if len(rgb) == 3:
            return [float(num) for num in rgb]
        # Hexdecimal triplet
        if value.startswith('#'):
            return [float(int(value[i:i+1], 16)) for i in range(1, 7, 2)]
        raise ValueError('%r not a valid color.' %value)


class Style(Text):

    def __init__(self, name=None, type='para', default='Normal'):
        super(Style, self).__init__(name, default)
        self.type = type

    def convert(self, value, context=None):
        # First, get the custom styles
        proc = context
        while (not interfaces.IStylesManager.providedBy(proc) and
               proc is not None):
            proc = proc.parent
        for styles in (proc.styles.get(self.type, {}),
                       reportlab.lib.styles.getSampleStyleSheet().byName):
            if value in styles:
                return styles[value]
            elif 'style.' + value in styles:
                return styles['style.' + value]
            elif value.startswith('style.') and value[6:] in styles:
                return styles[value[6:]]
        raise ValueError('Style %r could not be found.' %value)

    def get(self, element, default=DEFAULT, context=None):
        value = element.get(self.name, DEFAULT)
        if value is DEFAULT:
            if default is DEFAULT:
                return self.convert(self.default, context)
            elif default is None:
                return None
            return self.convert(default, context)
        return self.convert(value, context)


class Symbol(Text):

    def convert(self, value, context=None):
        return reportlab.graphics.widgets.markers.makeMarker(value)

class PageSize(Attribute):

    sizePair = Sequence(valueType=Measurement())
    words = Sequence(valueType=Attribute())

    def convert(self, value, context=None):
        # First try to get a pair
        try:
            return self.sizePair.convert(value, context)
        except ValueError:
            pass
        # Now we try to lookup a name. The following type of combinations must
        # work: "Letter" "LETTER" "A4 landscape" "letter portrait"
        words = self.words.convert(value, context)
        words = [word.lower() for word in words]
        # First look for the orientation
        orienter = None
        for orientation in ('landscape', 'portrait'):
            if orientation in words:
                orienter = getattr(reportlab.lib.pagesizes, orientation)
                words.remove(orientation)
        # We must have exactely one value left that matches a paper size
        pagesize = getattr(reportlab.lib.pagesizes, words[0].upper())
        # Now do the final touches
        if orienter:
            pagesize = orienter(pagesize)
        return pagesize


class TextNode(Attribute):
    """Text ndoes are not really attributes, but behave mostly like it."""

    def __init__(self):
        super(TextNode, self).__init__('TEXT')

    def get(self, element, default=DEFAULT, context=None):
        if element.text is None:
            return u''
        return unicode(element.text).strip()

class FirstLevelTextNode(TextNode):
    """Text ndoes are not really attributes, but behave mostly like it."""

    def __init__(self):
        super(TextNode, self).__init__('TEXT')

    def get(self, element, default=DEFAULT, context=None):
        text = element.text or u''
        for child in element.getchildren():
            text += child.tail or u''
        return text


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
        text = saxutils.escape(element.text or u'')
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
