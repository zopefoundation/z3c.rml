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
"""Special Element Processing

$Id$
"""
__docformat__ = "reStructuredText"
from z3c.rml import attr, directive, interfaces


class IName(interfaces.IRMLDirectiveSignature):
    """Defines a name for a string."""

    id = attr.String(
        title=u'Id',
        description=u'The id under which the value will be known.',
        required=True)

    value = attr.Text(
        title=u'Value',
        description=u'The text that is displayed if the id is called.',
        required=True)

class Name(directive.RMLDirective):
    signature = IName

    def process(self):
        id, value = self.getAttributeValues(valuesOnly=True)
        manager = attr.getManager(self)
        manager.names[id] = value


class IAlias(interfaces.IRMLDirectiveSignature):
    """Defines an alias for a given style."""

    id = attr.String(
        title=u'Id',
        description=u'The id as which the style will be known.',
        required=True)

    value = attr.Style(
        title=u'Value',
        description=u'The style that is represented.',
        required=True)

class Alias(directive.RMLDirective):
    signature = IAlias

    def process(self):
        id, value = self.getAttributeValues(valuesOnly=True)
        manager = attr.getManager(self)
        manager.styles[id] = value
