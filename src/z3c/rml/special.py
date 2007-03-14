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
from z3c.rml import attr, element, interfaces


class Name(element.FunctionElement):
    args = (
        attr.Text('id'),
        attr.Text('value'), )

    def process(self):
        args = self.getPositionalArguments()
        elem = self
        while not hasattr(elem, 'names') and elem is not None:
            elem = elem.parent
        elem.names[args[0]] = args[1]


class GetName(element.Element):

    def process(self):
        id = attr.Text('id').get(self.element)
        elem = self
        while not hasattr(elem, 'names') and elem is not None:
            elem = elem.parent
        text = elem.names[id] + (self.element.tail or u'')
        # Now replace the element with the text
        parent = self.element.getparent()
        if parent.text is None:
            parent.text = text
        else:
            parent.text += text
        parent.remove(self.element)


class Alias(element.FunctionElement):
    args = (
        attr.Style('id'),
        attr.Text('value'), )

    def process(self):
        id, value = self.getPositionalArguments()
        elem = self
        while (not interfaces.IStylesManager.providedBy(elem) and
               elem is not None):
            elem = elem.parent
        elem.styles[value] = id
