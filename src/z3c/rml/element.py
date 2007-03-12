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
"""Generic RML element

$Id$
"""
__docformat__ = "reStructuredText"
from z3c.rml import attr, error

class Element(object):

    def __init__(self, element, parent, context):
        self.element = element
        self.parent = parent
        self.context = context

class ContainerElement(Element):

    subElements = {}
    order = None

    def processSubElements(self, context):
        if self.order is not None:
            for tag in self.order:
                for element in self.element.findall(tag):
                    self.subElements[tag](element, self, context).process()
        else:
            for subElement in self.element.getchildren():
                if subElement.tag in self.subElements:
                    self.subElements[subElement.tag](
                        subElement, self, context).process()

    def process(self):
        self.processSubElements(self.context)


def extractPositionalArguments(argsList, element, context=None):
    args = []
    for Attr in argsList:
        value = Attr.get(element, context=context)
        if value is attr.DEFAULT:
            raise error.RequiredAttributeMissing(element, Attr.name)
        args.append(value)
    return args

def extractKeywordArguments(kwList, element, context=None):
        kw = {}
        for apiName, Attr in kwList:
            value = Attr.get(element, context=context)
            if value is not attr.DEFAULT:
                kw[apiName] = value
        return kw


class FunctionElement(Element):

    functionName = None
    args = ()
    kw = ()

    def getPositionalArguments(self):
        return extractPositionalArguments(self.args, self.element, self)

    def getKeywordArguments(self):
        return extractKeywordArguments(self.kw, self.element, self)

    def process(self):
        args = self.getPositionalArguments()
        kw = self.getKeywordArguments()
        getattr(self.context, self.functionName)(*args, **kw)
