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
"""RML Reference Generator

$Id$
"""
__docformat__ = "reStructuredText"
import os
import zope.schema
import zope.schema.interfaces
from lxml import etree
from z3c.rml import attr, document, pagetemplate

EXAMPLES_DIRECTORY = os.path.join(os.path.dirname(__file__), 'tests', 'input')
IGNORE_ATTRIBUTES = ('RMLAttribute', 'BaseChoice')
CONTENT_FIELD_TYPES = (
    attr.TextNode, attr.TextNodeSequence, attr.TextNodeGrid,
    attr.RawXMLContent, attr.XMLContent)

def getAttributeTypes():
    types = []
    candidates = sorted(attr.__dict__.items(), key=lambda e: e[0])
    for name, candidate in candidates:
        if not (isinstance(candidate, type) and
                zope.schema.interfaces.IField.implementedBy(candidate) and
                name not in IGNORE_ATTRIBUTES):
            continue
        types.append({
            'name': name,
            'description': candidate.__doc__
            })
    return types


def formatField(field):
    return field.__class__.__name__

def formatChoice(field):
    choices = ', '.join([repr(choice) for choice in field.choices.keys()])
    return '%s of (%s)' %(field.__class__.__name__, choices)

def formatSequence(field):
    vtFormatter = typeFormatters.get(field.value_type.__class__, formatField)
    return '%s of %s' %(field.__class__.__name__, vtFormatter(field.value_type))

def formatGrid(field):
    vtFormatter = typeFormatters.get(field.value_type.__class__, formatField)
    return '%s with %i cols of %s' %(
        field.__class__.__name__, field.columns, vtFormatter(field.value_type))

typeFormatters = {
    attr.Choice: formatChoice,
    attr.Sequence: formatSequence,
    attr.TextNodeSequence: formatSequence,
    attr.TextNodeGrid: formatGrid}

def processSignature(name, signature, examples, directives=None):
    if directives is None:
        directives = {}
    # Process this directive
    if signature not in directives:
        info = {'name': name, 'description': signature.getDoc()}
        attrs = []
        content = None
        for fname, field in zope.schema.getFieldsInOrder(signature):
            # Handle the case, where the field describes the content
            typeFormatter = typeFormatters.get(field.__class__, formatField)
            fieldInfo = {
                'name': fname,
                'type': typeFormatter(field),
                'title': field.title,
                'description': field.description,
                'required': field.required,
                }
            if field.__class__ in CONTENT_FIELD_TYPES:
                content = fieldInfo
            else:
                attrs.append(fieldInfo)
        info['attributes'] = attrs
        info['content'] = content
        info['examples'] = examples.get(name, None)

        subs = []
        for occurence in signature.queryTaggedValue('directives', ()):
            subs.append({
                'name': occurence.tag,
                'occurence': occurence.__class__.__name__,
                })
        info['sub-directives'] = subs
        directives[signature] = info
    # Process Children
    for occurence in signature.queryTaggedValue('directives', ()):
        processSignature(occurence.tag, occurence.signature,
                         examples, directives)


def extractExamples(directory):
    EXAMPLE_NS = 'http://namespaces.zope.org/rml/doc'
    EXAMPLE_ATTR_NAME = '{%s}elementExample' %EXAMPLE_NS
    examples = {}
    for fileName in os.listdir(directory):
        if not fileName.endswith('.rml'):
            continue
        rmlFile = open(os.path.join(directory, fileName), 'r')
        root = etree.parse(rmlFile).getroot()
        elements = root.xpath('//@doc:elementExample/parent::*',
                              {'doc': EXAMPLE_NS})
        for elem in elements:
            demoTag = elem.get(EXAMPLE_ATTR_NAME)
            del elem.attrib[EXAMPLE_ATTR_NAME]
            xml = etree.tounicode(elem, pretty_print=True).strip()
            elemExamples = examples.setdefault(demoTag, [])
            elemExamples.append(xml)

    return examples


if __name__ == '__main__':
    examples = extractExamples(EXAMPLES_DIRECTORY)

    template = pagetemplate.RMLPageTemplateFile('rml-reference.pt')

    directives = {}
    processSignature('document', document.IDocument, examples, directives)
    directives = sorted(directives.values(), key=lambda d: d['name'])

    pdf = template(types=getAttributeTypes(), directives=directives)
    open('rml-reference.pdf', 'wb').write(pdf)
