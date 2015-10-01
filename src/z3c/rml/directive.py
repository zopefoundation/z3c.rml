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
"""RML Directive Implementation
"""
import logging
import zope.interface
import zope.schema

from lxml import etree
from z3c.rml import interfaces
from z3c.rml.attr import getManager

logging.raiseExceptions = False
logger = logging.getLogger("z3c.rml")

ABORT_ON_INVALID_DIRECTIVE = False

def DeprecatedDirective(iface, reason):
    zope.interface.directlyProvides(iface, interfaces.IDeprecatedDirective)
    iface.setTaggedValue('deprecatedReason', reason)
    return iface

def getFileInfo(directive, element=None):
    root = directive
    while root.parent:
        root = root.parent
    if element is None:
        element = directive.element
    return '(file %s, line %i)' %(root.filename, element.sourceline)

@zope.interface.implementer(interfaces.IRMLDirective)
class RMLDirective(object):
    signature = None
    factories = {}

    def __init__(self, element, parent):
        self.element = element
        self.parent = parent

    def getAttributeValues(self, ignore=None, select=None, attrMapping=None,
                           includeMissing=False, valuesOnly=False):
        """See interfaces.IRMLDirective"""
        manager = getManager(self)
        cache = '%s.%s' % (self.signature.__module__, self.signature.__name__)
        if cache in manager.attributesCache:
            fields = manager.attributesCache[cache]
        else:
            fields = []
            for name, attr in zope.schema.getFieldsInOrder(self.signature):
                fields.append((name, attr))
            manager.attributesCache[cache] = fields

        items = []
        for name, attr in fields:
            # Only add the attribute to the list, if it is supposed there
            if ((ignore is None or name not in ignore) and
                (select is None or name in select)):
                # Get the value.
                value = attr.bind(self).get()
                # If no value was found for a required field, raise a value
                # error
                if attr.required and value is attr.missing_value:
                    raise ValueError(
                        'No value for required attribute "%s" '
                        'in directive "%s" %s.' % (
                        name, self.element.tag, getFileInfo(self)))
                # Only add the entry if the value is not the missing value or
                # missing values are requested to be included.
                if value is not attr.missing_value or includeMissing:
                    items.append((name, value))

        # Sort the items based on the section
        if select is not None:
            select = list(select)
            items = sorted(items, key=lambda n: select.index(n[0]))

        # If the attribute name does not match the internal API
        # name, then convert the name to the internal one
        if attrMapping:
            items = [(attrMapping.get(name, name), value)
                     for name, value in items]

        # Sometimes we only want the values without the names
        if valuesOnly:
            return [value for name, value in items]

        return items

    def processSubDirectives(self, select=None, ignore=None):
        # Go through all children of the directive and try to process them.
        for element in self.element.getchildren():
            # Ignore all comments
            if isinstance(element, etree._Comment):
                continue
            # Raise an error/log any unknown directive.
            if element.tag not in self.factories:
                msg = "Directive %r could not be processed and was " \
                      "ignored. %s" %(element.tag, getFileInfo(self, element))
                # Record any tags/elements that could not be processed.
                logger.warning(msg)
                if ABORT_ON_INVALID_DIRECTIVE:
                    raise ValueError(msg)
                continue
            if select is not None and element.tag not in select:
                continue
            if ignore is not None and element.tag in ignore:
                continue
            directive = self.factories[element.tag](element, self)
            directive.process()

    def process(self):
        self.processSubDirectives()
