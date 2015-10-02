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
"""
import six
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


class TextFlowables(object):
    def _getManager(self):
        if hasattr(self, 'manager'):
            return self.manager
        else:
            return  attr.getManager(self)

    def getPageNumber(self, elem, canvas):
        return six.text_type(
            canvas.getPageNumber() + int(elem.get('countingFrom', 1)) - 1
        )

    def getName(self, elem, canvas):
        return self._getManager().get_name(
            elem.get('id'),
            elem.get('default')
        )

    def evalString(self, elem, canvas):
        return do_eval(self._getText(elem, canvas, False))

    def namedString(self, elem, canvas):
        self._getManager().names[elem.get('id')] = self._getText(
            elem, canvas, include_final_tail=False
        )
        return u''

    def name(self, elem, canvas):
        self._getManager().names[elem.get('id')] = elem.get('value')
        return u''

    handleElements = {'pageNumber': getPageNumber,
                      'getName': getName,
                      'evalString': evalString,
                      'namedString': namedString,
                      'name': name}

    def _getText(self, node, canvas, include_final_tail=True):
        text = node.text or u''
        for sub in node.getchildren():
            if sub.tag in self.handleElements:
                text += self.handleElements[sub.tag](self, sub, canvas)
            else:
                self._getText(sub, canvas)
            text += sub.tail or u''
        if include_final_tail:
            text += node.tail or u''
        return text

def do_eval(value):
    # Maybe still not safe
    value = value.strip()
    if value:
        return six.text_type(eval(value.strip(), {'__builtins__': None}, {}))
    return u''
