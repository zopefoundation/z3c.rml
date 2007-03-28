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


class IGetName(interfaces.IRMLDirectiveSignature):
    """Get the text for the id."""

    id = attr.String(
        title=u'Id',
        description=u'The id as which the value is known.',
        required=True)

class GetName(directive.RMLDirective):
    signature = IGetName

    def process(self):
        id = dict(self.getAttributeValues()).pop('id')
        manager = attr.getManager(self)
        text = manager.names[id] + (self.element.tail or u'')
        # Now replace the element with the text
        parent = self.element.getparent()
        if parent.text is None:
            parent.text = text
        else:
            parent.text += text
        parent.remove(self.element)


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
