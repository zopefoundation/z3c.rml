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
        id, value = self.getPositionalArguments()
        manager = attr.getManager(self, interfaces.INamesManager)
        manager.names[id] = value


class GetName(element.Element):

    def process(self):
        id = attr.Text('id').get(self.element)
        manager = attr.getManager(self, interfaces.INamesManager)
        text = manager.names[id] + (self.element.tail or u'')
        # Now replace the element with the text
        parent = self.element.getparent()
        if parent.text is None:
            parent.text = text
        else:
            parent.text += text
        parent.remove(self.element)


class Alias(element.FunctionElement):
    args = (
        attr.Text('id'),
        attr.Style('value'), )

    def process(self):
        id, value = self.getPositionalArguments()
        manager = attr.getManager(self, interfaces.IStylesManager)
        manager.styles[id] = value
