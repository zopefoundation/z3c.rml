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
"""Generate a DTD from the code

$Id$
"""
__docformat__ = "reStructuredText"
import zope.schema

from z3c.rml import attr, document, occurence

occurence2Symbol = {
    occurence.ZeroOrMore: '*',
    occurence.ZeroOrOne: '?',
    occurence.OneOrMore: '+',
    }


def generateElement(name, signature):
    if signature is None:
        return ''
    # Create the list of sub-elements.
    subElementList = []
    for occurence in signature.queryTaggedValue('directives', ()):
        subElementList.append(
            occurence.tag + occurence2Symbol.get(occurence.__class__, '')
            )
    fields = zope.schema.getFields(signature).keys()
    if len(fields) == 1 and isinstance(fields[0], attr.TextNode):
        subElementList.append('#PCDATA')
    subElementList = ','.join(subElementList)
    if subElementList:
        subElementList = ' (' + subElementList + ')'
    text = '\n<!ELEMENT %s%s>' %(name, subElementList)
    # Create a list of attributes for this element.
    for attrName, field in zope.schema.getFieldsInOrder(signature):
        # Create the type
        if isinstance(field, attr.Choice):
            type = '(' + '|'.join(field.choices.keys()) + ')'
        else:
            type = 'CDATA'
        # Create required flag
        if field.required:
            required = '#REQUIRED'
        else:
            required = '#IMPLIED'
        # Put it all together
        text += '\n<!ATTLIST %s %s %s %s>' %(name, attrName, type, required)
    text += '\n'
    # Walk through all sub-elements, creating th eDTD entries for them.
    for occurence in signature.queryTaggedValue('directives', ()):
        text += generateElement(occurence.tag, occurence.signature)
    return text


def generate(useWrapper=False):
    text = generateElement('document', document.Document.signature)
    if useWrapper:
        text = '<!DOCTYPE RML [\n%s]>\n' %text
    return text

def main():
    print generate()


if __name__ == '__main__':
    print main()
