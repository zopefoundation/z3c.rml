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
"""RML to PDF Converter Interfaces
"""
__docformat__ = "reStructuredText"
import logging
import reportlab.lib.enums
import zope.interface
import zope.schema

from z3c.rml.occurence import ZeroOrMore, ZeroOrOne, OneOrMore

JOIN_CHOICES = {'round': 1, 'mitered': 0, 'bevelled': 2}
CAP_CHOICES = {'default': 0, 'butt': 0, 'round': 1, 'square': 2}
ALIGN_CHOICES = {
    'left': reportlab.lib.enums.TA_LEFT,
    'right': reportlab.lib.enums.TA_RIGHT,
    'center': reportlab.lib.enums.TA_CENTER,
    'centre': reportlab.lib.enums.TA_CENTER,
    'justify': reportlab.lib.enums.TA_JUSTIFY}
ALIGN_TEXT_CHOICES = {
    'left': 'LEFT', 'right': 'RIGHT', 'center': 'CENTER', 'centre': 'CENTER',
    'decimal': 'DECIMAL'}
VALIGN_TEXT_CHOICES = {
    'top': 'TOP', 'middle': 'MIDDLE', 'bottom': 'BOTTOM'}
SPLIT_CHOICES = ('splitfirst', 'splitlast')
TEXT_TRANSFORM_CHOICES = ('uppercase', 'lowercase')
LIST_FORMATS = ('I', 'i', '123',  'ABC', 'abc')
ORDERED_LIST_TYPES = ('I', 'i', '1', 'A', 'a', 'l', 'L', 'O', 'o', 'R', 'r')
UNORDERED_BULLET_VALUES = (
    'bulletchar', 'bullet', 'circle', 'square', 'disc', 'diamond',
    'rarrowhead')
LOG_LEVELS = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARNING': logging.WARNING,
    'ERROR': logging.ERROR,
    'CRITICAL': logging.CRITICAL}

class IRML2PDF(zope.interface.Interface):
    """This is the main public API of z3c.rml"""

    def parseString(xml):
        """Parse an XML string and convert it to PDF.

        The output is a ``StringIO`` object.
        """

    def go(xmlInputName, outputFileName=None, outDir=None, dtdDir=None):
        """Convert RML 2 PDF.

        The generated file will be located in the ``outDir`` under the name
        ``outputFileName``.
        """

class IManager(zope.interface.Interface):
    """A manager of all document-global variables."""
    names = zope.interface.Attribute("Names dict")
    styles = zope.interface.Attribute("Styles dict")
    colors = zope.interface.Attribute("Colors dict")

class IPostProcessorManager(zope.interface.Interface):
    """Manages all post processors"""

    postProcessors = zope.interface.Attribute(
        "List of tuples of the form: (name, processor)")

class ICanvasManager(zope.interface.Interface):
    """A manager for the canvas."""
    canvas = zope.interface.Attribute("Canvas")

class IRMLDirectiveSignature(zope.interface.Interface):
    """The attribute and sub-directives signature of the current
    RML directive."""


class IRMLDirective(zope.interface.Interface):
    """A directive in RML extracted from an Element Tree element."""

    signature = zope.schema.Field(
        title=u'Signature',
        description=(u'The signature of the RML directive.'),
        required=True)

    parent = zope.schema.Field(
        title=u'Parent RML Element',
        description=u'The parent in the RML element hierarchy',
        required=True,)

    element = zope.schema.Field(
        title=u'Element',
        description=(u'The Element Tree element from which the data '
                     u'is retrieved.'),
        required=True)

    def getAttributeValues(ignore=None, select=None, includeMissing=False):
        """Return a list of name-value-tuples based on the signature.

        If ``ignore`` is specified, all attributes are returned except the
        ones listed in the argument. The values of the sequence are the
        attribute names.

        If ``select`` is specified, only attributes listed in the argument are
        returned. The values of the sequence are the attribute names.

        If ``includeMissing`` is set to true, then even missing attributes are
        included in the value list.
        """

    def processSubDirectives(self):
        """Process all sub-directives."""

    def process(self):
        """Process the directive.

        The main task for this method is to interpret the available data and
        to make the corresponding calls in the Reportlab document.

        This call should also process all sub-directives and process them.
        """


class IDeprecated(zope.interface.Interface):
    """Mark an attribute as being compatible."""

    deprecatedName = zope.schema.TextLine(
        title=u'Name',
        description=u'The name of the original attribute.',
        required=True)

    deprecatedReason = zope.schema.Text(
        title=u'Reason',
        description=u'The reason the attribute has been deprecated.',
        required=False)


class IDeprecatedDirective(zope.interface.interfaces.IInterface):
    """A directive that is deprecated."""
