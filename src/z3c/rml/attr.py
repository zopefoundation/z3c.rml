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
"""RML Attribute Implementation
"""
import collections
import io
import logging
import os
import re
import urllib
from importlib import import_module

import reportlab.graphics.widgets.markers
import reportlab.lib.colors
import reportlab.lib.pagesizes
import reportlab.lib.styles
import reportlab.lib.units
import reportlab.lib.utils
import zope.interface
import zope.schema
from lxml import etree

from z3c.rml import SampleStyleSheet
from z3c.rml import interfaces


MISSING = object()
logger = logging.getLogger("z3c.rml")


def getFileInfo(directive):
    root = directive
    while root.parent:
        root = root.parent
    # Elements added through API won't have a sourceline
    if directive.element.sourceline is None:
        return '(file %s)' % (root.filename)

    return '(file %s, line %i)' % (
        root.filename, directive.element.sourceline)


def getManager(context, interface=None):
    if interface is None:
        # Avoid circular imports
        from z3c.rml import interfaces
        interface = interfaces.IManager
    # Walk up the path until the manager is found
    # Using interface.providedBy is much slower because it does many more
    # checks
    while (
        context is not None and
        interface not in context.__class__.__dict__.get('__implemented__', {})
    ):
        context = context.parent
    # If no manager was found, raise an error
    if context is None:
        raise ValueError('The manager could not be found.')
    return context


def deprecated(oldName, attr, reason):
    zope.interface.directlyProvides(attr, interfaces.IDeprecated)
    attr.deprecatedName = oldName
    attr.deprecatedReason = reason
    return attr


class RMLAttribute(zope.schema.Field):
    """An attribute of the RML directive."""

    missing_value = MISSING
    default = MISSING

    def fromUnicode(self, ustr):
        """See zope.schema.interfaces.IField"""
        if self.context is None:
            raise ValueError('Attribute not bound to a context.')
        return super().fromUnicode(str(ustr))

    def get(self):
        """See zope.schema.interfaces.IField"""
        # If the attribute has a deprecated partner and the deprecated name
        # has been specified, use it.
        if (
            interfaces.IDeprecated.providedBy(self) and
            self.deprecatedName in self.context.element.attrib
        ):
            name = self.deprecatedName
            logger.warning(
                'Deprecated attribute "{}": {} {}'.format(
                    name, self.deprecatedReason, getFileInfo(self.context))
            )
        else:
            name = self.__name__
        # Extract the value.
        value = self.context.element.get(name, self.missing_value)
        # Get the correct default value.
        if value is self.missing_value:
            if self.default is not None:
                return self.default
            return self.missing_value
        return self.fromUnicode(value)


class BaseChoice(RMLAttribute):
    choices = {}
    doLower = True

    def fromUnicode(self, value):
        if self.doLower:
            value = value.lower()
        if value in self.choices:
            return self.choices[value]
        raise ValueError(
            '{!r} not a valid value for attribute "{}". {}'.format(
                value, self.__name__, getFileInfo(self.context))
        )


class Combination(RMLAttribute):
    """A combination of several other attribute types."""

    def __init__(self, value_types=(), *args, **kw):
        super().__init__(*args, **kw)
        self.value_types = value_types

    @property
    def element(self):
        return self.context.element

    @property
    def parent(self):
        return self.context.parent

    def fromUnicode(self, value):
        for value_type in self.value_types:
            bound = value_type.bind(self)
            try:
                return bound.fromUnicode(value)
            except ValueError:
                pass
        raise ValueError(
            f'"{value}" is not a valid value. {getFileInfo(self.context)}'
        )


class Text(RMLAttribute, zope.schema.Text):
    """A simple unicode string."""


class Integer(RMLAttribute, zope.schema.Int):
    """An integer. A minimum and maximum value can be specified."""
    # By making min and max simple attributes, we avoid some validation
    # problems.
    min = None
    max = None


class Float(RMLAttribute, zope.schema.Float):
    """An flaoting point. A minimum and maximum value can be specified."""
    # By making min and max simple attributes, we avoid some validation
    # problems.
    min = None
    max = None


class StringOrInt(RMLAttribute):
    """A (bytes) string or an integer."""

    def fromUnicode(self, value):
        try:
            return int(value)
        except ValueError:
            return str(value)


class Sequence(RMLAttribute, zope.schema._field.AbstractCollection):
    """A list of values of a specified type."""

    splitre = re.compile('[ \t\n,;]+')

    def __init__(self, splitre=None, *args, **kw):
        super().__init__(*args, **kw)
        if splitre is not None:
            self.splitre = splitre

    def fromUnicode(self, ustr):
        if ustr.startswith('(') and ustr.endswith(')'):
            ustr = ustr[1:-1]
        ustr = ustr.strip()
        raw_values = self.splitre.split(ustr)
        result = [self.value_type.bind(self.context).fromUnicode(raw.strip())
                  for raw in raw_values]
        if (
            (self.min_length is not None and len(result) < self.min_length) or
            (self.max_length is not None and len(result) > self.max_length)
        ):
            raise ValueError(
                f'Length of sequence must be at least {self.min_length} '
                f'and at most {self.max_length}. {getFileInfo(self.context)}'
            )
        return result


class IntegerSequence(Sequence):
    """A sequence of integers."""

    def __init__(
            self,
            numberingStartsAt=0,
            lowerBoundInclusive=True,
            upperBoundInclusive=True,
            *args, **kw):
        super(Sequence, self).__init__(*args, **kw)
        self.numberingStartsAt = numberingStartsAt
        self.lowerBoundInclusive = lowerBoundInclusive
        self.upperBoundInclusive = upperBoundInclusive

    def fromUnicode(self, ustr):
        ustr = ustr.strip()
        pieces = self.splitre.split(ustr)
        numbers = []
        for piece in pieces:
            # Ignore empty pieces.
            if not piece:
                continue
            # The piece is a range.
            if '-' in piece:
                start, end = map(int, piece.split('-'))
                # Make sure internally numbering starts as 0
                start -= self.numberingStartsAt
                end -= self.numberingStartsAt
                # Apply lower-bound exclusive.
                if not self.lowerBoundInclusive:
                    start += 1
                # Apply upper-bound inclusive.
                if self.upperBoundInclusive:
                    end += 1
                # Make range lower and upper bound inclusive.
                numbers.append((start, end))
                continue
            # The piece is just a number
            value = int(piece)
            value -= self.numberingStartsAt
            numbers.append((value, value + 1))
        return numbers


class Choice(BaseChoice):
    """A choice of several values. The values are always case-insensitive."""

    def __init__(self, choices=None, doLower=True, *args, **kw):
        super().__init__(*args, **kw)
        if not isinstance(choices, dict):
            choices = collections.OrderedDict(
                [(val.lower() if doLower else val, val) for val in choices])
        else:
            choices = collections.OrderedDict(
                [(key.lower() if doLower else key, val)
                 for key, val in choices.items()])
        self.choices = choices
        self.doLower = doLower


class Boolean(BaseChoice):
    '''A boolean value.

    For true the values "true", "yes", and "1" are allowed. For false, the
    values "false", "no", "1" are allowed.
    '''
    choices = {'true': True, 'false': False,
               'yes': True, 'no': False,
               '1': True, '0': False,
               }


class TextBoolean(BaseChoice):
    '''A boolean value as text.

    ReportLab sometimes exposes low-level APIs, so we have to provide values
    that are directly inserted into the PDF.

    For "true" the values "true", "yes", and "1" are allowed. For "false", the
    values "false", "no", "1" are allowed.
    '''
    choices = {'true': 'true', 'false': 'false',
               'yes': 'true', 'no': 'false',
               '1': 'true', '0': 'false',
               }


class BooleanWithDefault(Boolean):
    '''This is a boolean field that can also receive the value "default".'''
    choices = Boolean.choices.copy()
    choices.update({'default': None})


class Measurement(RMLAttribute):
    '''This field represents a length value.

    The units "in" (inch), "cm", "mm", and "pt" are allowed. If no units are
    specified, the value is given in points/pixels.
    '''

    def __init__(self, allowPercentage=False, allowStar=False, *args, **kw):
        super().__init__(*args, **kw)
        self.allowPercentage = allowPercentage
        self.allowStar = allowStar

    units = [
        (re.compile(r'^(-?[0-9\.]+)\s*in$'), reportlab.lib.units.inch),
        (re.compile(r'^(-?[0-9\.]+)\s*cm$'), reportlab.lib.units.cm),
        (re.compile(r'^(-?[0-9\.]+)\s*mm$'), reportlab.lib.units.mm),
        (re.compile(r'^(-?[0-9\.]+)\s*pt$'), 1),
        (re.compile(r'^(-?[0-9\.]+)\s*$'), 1)
    ]

    allowPercentage = False
    allowStar = False

    def fromUnicode(self, value):
        if value == 'None':
            return None
        if value == '*' and self.allowStar:
            return value
        if value.endswith('%') and self.allowPercentage:
            return value
        for unit in self.units:
            res = unit[0].search(value, 0)
            if res:
                return unit[1] * float(res.group(1))
        raise ValueError(
            'The value {!r} is not a valid measurement. {}'.format(
                value, getFileInfo(self.context)
            )
        )


class FontSizeRelativeMeasurement(RMLAttribute):
    """This field is a measurement always relative to the current font size.

    The units "F", "f" and "L" refer to a multiple of the current font size,
    while "P" refers to the fractional font size. If no units are specified,
    the value is given in points/pixels.
    """

    _format = re.compile(r'^\s*(\+?-?[0-9\.]*)\s*(P|L|f|F)?\s*$')

    def fromUnicode(self, value):
        if value == 'None':
            return None
        # Normalize
        match = self._format.match(value)
        if match is None:
            raise ValueError(
                'The value {!r} is not a valid text line measurement.'
                ' {}'.format(value, getFileInfo(self.context)))
        number, unit = match.groups()
        normalized = number
        if unit is not None:
            normalized += '*' + unit
        return normalized


class ObjectRef(Text):
    """This field will return a Python object.

    The value is a Python path to the object which is being resolved. The
    sysntax is expected to be ``<path.to.module>.<name>``.
    """
    pythonPath = re.compile(r'^([A-z_][0-9A-z_.]*)\.([A-z_][0-9A-z_]*)$')

    def __init__(self, doNotResolve=False, *args, **kw):
        super().__init__(*args, **kw)
        self.doNotResolve = doNotResolve

    def fromUnicode(self, value):
        result = self.pythonPath.match(value)
        if result is None:
            raise ValueError(
                'The Python path you specified is incorrect. %s' % (
                    getFileInfo(self.context)
                )
            )
        if self.doNotResolve:
            return value
        modulePath, objectName = result.groups()
        try:
            module = import_module(modulePath)
        except ImportError:
            raise ValueError(
                'The module you specified was not found: %s' % modulePath)
        try:
            object = getattr(module, objectName)
        except AttributeError:
            raise ValueError(
                'The object you specified was not found: %s' % objectName)
        return object


class File(Text):
    """This field will return a file object.

    The value itself can either be a relative or absolute path. Additionally
    the following syntax is supported: [path.to.python.mpackage]/path/to/file
    """
    packageExtract = re.compile(r'^\[([0-9A-z_.]*)\]/(.*)$')

    doNotOpen = False
    doNotModify = False

    def __init__(self, doNotOpen=False, doNotModify=False, *args, **kw):
        super().__init__(*args, **kw)
        self.doNotOpen = doNotOpen
        self.doNotModify = doNotModify

    def fromUnicode(self, value):
        # Check whether the value is of the form:
        #    [<module.path>]/rel/path/image.gif"
        if value.startswith('['):
            result = self.packageExtract.match(value)
            if result is None:
                raise ValueError(
                    'The package-path-pair you specified was incorrect. %s' %
                    (getFileInfo(self.context))
                )
            modulepath, path = result.groups()
            module = import_module(modulepath)
            # PEP 420 namespace support means that a module can have
            # multiple paths
            for module_path in module.__path__:
                value = os.path.join(module_path, path)
                if os.path.exists(value):
                    break
        # In some cases ReportLab has its own mechanisms for finding a
        # file. In those cases, the filename should not be modified beyond
        # module resolution.
        if self.doNotModify:
            return value
        # Under Python 3 all platforms need a protocol for local files
        if not urllib.parse.urlparse(value).scheme:
            value = 'file:///' + os.path.abspath(value)
        # If the file is not to be opened, simply return the path.
        if self.doNotOpen:
            return value
        # Open/Download the file
        fileObj = reportlab.lib.utils.open_for_read(value)
        sio = io.BytesIO(fileObj.read())
        fileObj.close()
        sio.seek(0)
        return sio


class Image(File):
    """Similar to the file File attribute, except that an image is internally
    expected."""

    def __init__(self, onlyOpen=False, *args, **kw):
        super().__init__(*args, **kw)
        self.onlyOpen = onlyOpen

    def fromUnicode(self, value):
        if value.lower().endswith('.svg') or value.lower().endswith('.svgz'):
            return self._load_svg(value)
        fileObj = super().fromUnicode(value)
        if self.onlyOpen:
            return fileObj
        return reportlab.lib.utils.ImageReader(fileObj)

    def _load_svg(self, value):
        manager = getManager(self.context)

        width = self.context.element.get('width')
        if width is not None:
            width = Measurement().fromUnicode(width)
        height = self.context.element.get('height')
        if height is not None:
            height = Measurement().fromUnicode(height)
        preserve = self.context.element.get('preserveAspectRatio')
        if preserve is not None:
            preserve = Boolean().fromUnicode(preserve)

        cache_key = f'{value}-{width}x{height}-{preserve}'
        if cache_key in manager.svgs:
            return manager.svgs[cache_key]

        from gzip import GzipFile
        from xml.etree import cElementTree

        from reportlab.graphics import renderPM
        from svglib.svglib import SvgRenderer

        fileObj = super().fromUnicode(value)
        svg = fileObj.getvalue()
        if svg[:2] == b'\037\213':
            fileObj = GzipFile(fileobj=fileObj)
        parser = etree.XMLParser(
            remove_comments=True,
            recover=True,
            resolve_entities=False)
        svg = cElementTree.parse(fileObj, parser=parser).getroot()

        renderer = SvgRenderer(value)
        svg = renderer.render(svg)

        if preserve:
            if width is not None or height is not None:
                if width is not None and height is None:
                    height = svg.height * width / svg.width
                elif height is not None and width is None:
                    width = svg.width * height / svg.height
                elif float(width) / height > float(svg.width) / svg.height:
                    width = svg.width * height / svg.height
                else:
                    height = svg.height * width / svg.width
        else:
            if width is None:
                width = svg.width
            if height is None:
                height = svg.height

        svg.scale(width / svg.width, height / svg.height)
        svg.width = width
        svg.height = height

        svg = renderPM.drawToPIL(svg, dpi=300)
        svg = reportlab.lib.utils.ImageReader(svg)
        # A hack to getImageReader through as an open Image when used with
        # imageAndFlowables
        svg.read = True
        manager.svgs[cache_key] = svg
        return svg


class Color(RMLAttribute):
    """Requires the input of a color. There are several supported formats.

    Three values in a row are interpreted as RGB value ranging from 0-255.
    A string is interpreted as a name to a pre-defined color.
    The 'CMYK()' wrapper around four values represents a CMYK color
    specification.
    """

    def __init__(self, acceptNone=False, acceptAuto=False, *args, **kw):
        super().__init__(*args, **kw)
        self.acceptNone = acceptNone
        self.acceptAuto = acceptAuto

    def fromUnicode(self, value):
        if self.acceptNone and value.lower() == 'none':
            return None
        if self.acceptAuto and value.lower() == 'auto':
            return 'auto'
        manager = getManager(self.context)

        if value.startswith('rml:'):
            value = manager.get_name(value[4:], '#000000')

        if value in manager.colors:
            return manager.colors[value]
        try:
            return reportlab.lib.colors.toColor(value)
        except ValueError:
            raise ValueError(
                'The color specification "{}" is not valid. {}'.format(
                    value, getFileInfo(self.context)
                )
            )


def _getStyle(context, value):
    manager = getManager(context)
    for styles in (manager.styles, SampleStyleSheet.byName):
        if value in styles:
            return styles[value]
        elif 'style.' + value in styles:
            return styles['style.' + value]
        elif value.startswith('style.') and value[6:] in styles:
            return styles[value[6:]]
    raise ValueError('Style {!r} could not be found. {}'.format(
        value, getFileInfo(context)))


class Style(Text):
    """Requires a valid style to be entered.

    Whether the style is a paragraph, table or box style is irrelevant, except
    that it has to fit the tag.
    """
    default = SampleStyleSheet.byName['Normal']

    def fromUnicode(self, value):
        return _getStyle(self.context, value)


class Padding(Sequence):
    """This attribute is specific for padding and will produce the proper
    length of the padding sequence."""

    def __init__(self, *args, **kw):
        kw.update(dict(value_type=Integer(), min_length=1, max_length=4))
        super().__init__(*args, **kw)

    def fromUnicode(self, value):
        seq = super().fromUnicode(value)
        # pdfgen does not like a single paddign value.
        if len(seq) == 1:
            seq.append(seq[0])
        return seq


class Symbol(Text):
    """This attribute should contain the text representation of a symbol to be
    used."""

    def fromUnicode(self, value):
        return reportlab.graphics.widgets.markers.makeMarker(value)


class PageSize(RMLAttribute):
    """A simple measurement pair that specifies the page size. Optionally you
    can also specify a the name of a page size, such as A4, letter, or legal.
    """

    sizePair = Sequence(value_type=Measurement())
    words = Sequence(value_type=Text())

    def fromUnicode(self, value):
        # First try to get a pair
        try:
            return self.sizePair.bind(self.context).fromUnicode(value)
        except ValueError:
            pass
        # Now we try to lookup a name. The following type of combinations must
        # work: "Letter" "LETTER" "A4 landscape" "letter portrait"
        words = self.words.bind(self.context).fromUnicode(value)
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


class TextNode(RMLAttribute):
    """Return the text content of an element."""

    def get(self):
        if self.context.element.text is None:
            return ''
        return str(self.context.element.text).strip()


class FirstLevelTextNode(TextNode):
    """Gets all the text content of an element without traversing into any
    child-elements."""

    def get(self):
        text = self.context.element.text or ''
        for child in self.context.element.getchildren():
            text += child.tail or ''
        return text.strip()


class TextNodeSequence(Sequence, TextNode):
    """A sequence of values retrieved from the element's content."""

    def get(self):
        return self.fromUnicode(self.context.element.text)


class TextNodeGrid(TextNodeSequence):
    """A grid/matrix of values retrieved from the element's content.

    The number of columns is specified for every case, but the number of rows
    is dynamic.
    """

    def __init__(self, columns=None, *args, **kw):
        super().__init__(*args, **kw)
        self.columns = columns

    def fromUnicode(self, ustr):
        result = super().fromUnicode(ustr)
        if len(result) % self.columns != 0:
            raise ValueError(
                'Number of elements must be divisible by %i. %s' % (
                    self.columns, getFileInfo(self.context)
                )
            )
        return [result[i * self.columns:(i + 1) * self.columns]
                for i in range(len(result) // self.columns)]


class RawXMLContent(RMLAttribute):
    """Retrieve the raw content of an element.

    Only some special element substitution will be made.
    """

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)

    def get(self):
        # ReportLab's paragraph parser does not like attributes from other
        # namespaces; sigh. So we have to improvize.
        text = etree.tounicode(self.context.element, pretty_print=False)
        text = text[text.find('>') + 1:text.rfind('<')]
        return text


class XMLContent(RawXMLContent):
    """Same as 'RawXMLContent', except that the whitespace is normalized."""

    def get(self):
        text = super().get()
        return text.strip().replace('\t', ' ')
