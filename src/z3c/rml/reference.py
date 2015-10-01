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
"""
import copy
import re
import os
import pygments.token
import zope.schema
import zope.schema.interfaces
from lxml import etree
from xml.sax import saxutils
from pygments.lexers import XmlLexer
from z3c.rml import attr, document, interfaces, pagetemplate, __version__


INPUT_URL = ('https://github.com/zopefoundation/z3c.rml/blob/master/src/z3c/'
             'rml/tests/input/%s')
EXPECTED_URL = ('https://github.com/zopefoundation/z3c.rml/blob/master/src/z3c/'
                'rml/tests/expected/%s?raw=true')

EXAMPLES_DIRECTORY = os.path.join(os.path.dirname(__file__), 'tests', 'input')
IGNORE_ATTRIBUTES = ('RMLAttribute', 'BaseChoice')
CONTENT_FIELD_TYPES = (
    attr.TextNode, attr.TextNodeSequence, attr.TextNodeGrid,
    attr.RawXMLContent, attr.XMLContent)
STYLES_FORMATTING = {
     pygments.token.Name.Tag : ('<font textColor="red">', '</font>'),
     pygments.token.Literal.String : ('<font textColor="blue">', '</font>'),
    }
EXAMPLE_NS = 'http://namespaces.zope.org/rml/doc'
EXAMPLE_ATTR_NAME = '{%s}example' %EXAMPLE_NS


def dedent(rml):
    spaces = re.findall('\n( *)<', rml)
    if not spaces:
        return rml
    least = min([len(s) for s in spaces if s != ''])
    return rml.replace('\n'+' '*least, '\n')


def enforceColumns(rml, columns=80):
    result = []
    for line in rml.split('\n'):
        if len(line) <= columns:
            result.append(line)
            continue
        # Determine the indentation for all other lines
        lineStart = re.findall('^( *<[a-zA-Z0-9]+ )', line)
        lineIndent = 0
        if lineStart:
            lineIndent = len(lineStart[0])
        # Create lines having at most the specified number of columns
        while len(line) > columns:
            end = line[:columns].rfind(' ')
            result.append(line[:end])
            line = ' '*lineIndent + line[end+1:]
        result.append(line)

    return '\n'.join(result)

def highlightRML(rml):
    lexer = XmlLexer()
    styledRml = ''
    for ttype, token in lexer.get_tokens(rml):
        start, end = STYLES_FORMATTING.get(ttype, ('', ''))
        styledRml += start + saxutils.escape(token) + end
    return styledRml


def removeDocAttributes(elem):
    for name in elem.attrib.keys():
        if name.startswith('{'+EXAMPLE_NS+'}'):
            del elem.attrib[name]
    for child in elem.getchildren():
        removeDocAttributes(child)


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

def formatCombination(field):
    vts = [typeFormatters.get(vt.__class__, formatField)(vt)
           for vt in field.value_types]
    return '%s of %s' %(field.__class__.__name__, ', '.join(vts))

typeFormatters = {
    attr.Choice: formatChoice,
    attr.Sequence: formatSequence,
    attr.Combination: formatCombination,
    attr.TextNodeSequence: formatSequence,
    attr.TextNodeGrid: formatGrid}

def processSignature(name, signature, examples, directives=None):
    if directives is None:
        directives = {}
    # Process this directive
    if signature not in directives:
        info = {'name': name, 'description': signature.getDoc(),
                'id': str(hash(signature)), 'deprecated': False}
        # If directive is deprecated, then add some info
        if interfaces.IDeprecatedDirective.providedBy(signature):
            info['deprecated'] = True
            info['reason'] = signature.getTaggedValue('deprecatedReason')
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
                'deprecated': False,
                }
            if field.__class__ in CONTENT_FIELD_TYPES:
                content = fieldInfo
            else:
                attrs.append(fieldInfo)

            # Add a separate entry for the deprecated field
            if interfaces.IDeprecated.providedBy(field):
                deprFieldInfo = fieldInfo.copy()
                deprFieldInfo['deprecated'] = True
                deprFieldInfo['name'] = field.deprecatedName
                deprFieldInfo['reason'] = field.deprecatedReason
                attrs.append(deprFieldInfo)

        info['attributes'] = attrs
        info['content'] = content
        # Examples can be either gotten by interface path or tag name
        ifacePath = signature.__module__ + '.' + signature.__name__
        if ifacePath in examples:
            info['examples'] = examples[ifacePath]
        else:
            info['examples'] = examples.get(name, None)

        subs = []
        for occurence in signature.queryTaggedValue('directives', ()):
            subs.append({
                'name': occurence.tag,
                'occurence': occurence.__class__.__name__,
                'deprecated': interfaces.IDeprecatedDirective.providedBy(
                                 occurence.signature),
                'id': str(hash(occurence.signature))
                })
        info['sub-directives'] = subs
        directives[signature] = info
    # Process Children
    for occurence in signature.queryTaggedValue('directives', ()):
        processSignature(occurence.tag, occurence.signature,
                         examples, directives)


def extractExamples(directory):
    examples = {}
    for filename in os.listdir(directory):
        if not filename.endswith('.rml'):
            continue
        rmlFile = open(os.path.join(directory, filename), 'rb')
        root = etree.parse(rmlFile).getroot()
        elements = root.xpath('//@doc:example/parent::*',
                              namespaces={'doc': EXAMPLE_NS})
        # Phase 1: Collect all elements
        for elem in elements:
            demoTag = elem.get(EXAMPLE_ATTR_NAME) or elem.tag
            elemExamples = examples.setdefault(demoTag, [])
            elemExamples.append({
                'filename': filename,
                'line': elem.sourceline,
                'element': elem,
                'rmlurl': INPUT_URL %filename,
                'pdfurl': EXPECTED_URL %(filename[:-4]+'.pdf')
                })
        # Phase 2: Render all elements
        removeDocAttributes(root)
        for dirExamples in examples.values():
            for example in dirExamples:
                xml = etree.tounicode(example['element']).strip()
                xml = re.sub(
                    ' ?xmlns:doc="http://namespaces.zope.org/rml/doc"', '', xml)
                xml = dedent(xml)
                xml = enforceColumns(xml, 80)
                xml = highlightRML(xml)
                example['code'] = xml

        rmlFile.close()

    return examples


def main(outPath=None):
    examples = extractExamples(EXAMPLES_DIRECTORY)

    template = pagetemplate.RMLPageTemplateFile('reference.pt')

    directives = {}
    processSignature('document', document.IDocument, examples, directives)
    directives = sorted(directives.values(), key=lambda d: d['name'])

    pdf = template(
        version=__version__,
        types=getAttributeTypes(),
        directives=directives)
    file_ = open(outPath or 'rml-reference.pdf', 'wb')
    file_.write(pdf)
    file_.close()
