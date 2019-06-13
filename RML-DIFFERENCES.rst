==============================================
RML2PDF and z3c.rml Implementation Differences
==============================================

This document outlines the differences between ReportLab Inc.'s RML2PDF
library and z3c.rml.

Incompatibilies
---------------

- ``<template>``

  * `pageSize`: This is called `pagesize` in this implementation to match the
    API.

- ``<pageTemplate>``

  * `pageSize`: This is called `pagesize` in this implementation to match the
    API.

- ``<addMapping>``: This is a useful API function that was supported in
  earlier versions of RML2PDF. It is now gone, but this library still supports
  it.

- ``<barCode>``

  * Most barcode attributes available via the API and the flowable are not
    supported in the drawing version in RML2PDF. I have no idea why!

  * `isoScale`: This attributes forces the bar code to keep the original
    aspect ratio. This is straight from the API.

- ``<barCodeFlowable>``

  * `widthSize`: This is called `width` in this implementation to match the
    API.

  * `heightSize`: This is called `height` in this implementation to match the
    API.

  * `tracking`: This is only used for USPS4S and the API actually uses the
    `value` argument for this. Thus this attribute is omitted.

- ``<catchForms>``: This feature requires PageCatcher, which is a ReportLab
  commercial product and there is no Open Source alternative.

- ``<docinit>``:

  * ``outlineAdd`` directive really does not make much sense here. The API
    docs claim its availability but the hand-written docs state it must be
    within a story.

  * ``alias`` directive is completely undocumented in this context.

- ``<drawing>``: There is no documentation for this tag and I do not know what
  it is supposed to do. Thus z3c.rml does not implement it.

- ``<img>``: Support for `preserveAspectRatio` attribute, which is not
  available in RML or ReportLab.

- ``<join>``: This directive is not implemented due to lack of documentation.

- ``<keepTogether>``: This directive is not implemented in RML2PDF, but there
  exists an API flowable for it and it seems obviously useful.

- ``<length>``: This directive is not implemented due to lack of documentation.

- ``<template>``: The `firstPageTemplate` attribute is not implemented, since
  it belongs to the ``<story>`` directive. Several RML2PDF examples use it
  that way too, so why is it documented differently?

- ``<widget>``: There is no documentation for this tag and I do not know what
  it is supposed to do. Thus z3c.rml does not implement it.

- ``<paraStyle>``:

  * ``underline``: A boolean field indicating whether the entire paragraph is
    underlined. The following related attributes have also been added to the
    style: ``underlineColor``, ``underlineOffset``, ``underlineWidth``,
    ``underlineGap``, and ``underlineKind``

  * ``strike``: A boolean field indicating whether the entire paragraph is
    stricken. The following related attributes have also been added to the
    style: ``strikeColor``, ``strikeOffset``, ``strikeWidth``,
    ``strikeGap``, and ``strikeKind``

  * ``justifyLastLine``: Added attribute that is available in the API.

  * ``justifyBreaks``: Added attribute that is available in the API.

  * ``spaceShrinkage``: Added attribute that is available in the API.

  * ``linkUnderline``: Added attribute that is available in the API.


Extensions
----------

z3c.rml implements ``<header>`` and ``<footer>`` directives. These go inside
``<pageTemplate>`` directives, and are equivalent to having
``<pageGraphics><place>`` and take the same arguments as ``<pageGraphics>``.

The purpose of these directives is to be able to handle headers and footers
differently then from other graphical elements when dealing with other
formats than PDF.

If you want one left aligned header or footer, and one right aligned, you
simply add multiple headers or footers.

See src/z3c/rml/tests/input/rml-examples-050-header-footer.rml for an example.


To be Done
----------

Each major bullet represents a missing element. Names after the elements are
missing attributes. A "-" (minus) sign in front of an element or attribute
denotes a feature not in RML2PDF. The "->" arrow designates a difference in
naming.


- pre/xpre: -bulletText, -dedent

- blockTable: -repeatRows, -alignment

- evalString

- image: -showBoundary, -preserveAspectRatio

- doForm

- figure

- imageFigure

- checkBox

- letterBoxes

- textBox

- boxStyle

- form

- lineMode: -miterLimit

- paraStyle: fontName -> fontname, fontSize -> fontsize, -keepWithNext,
  -wordWrap, -border*

- blockTableStyle: -keepWithNext

- blockBackground: -colorsByRow, -colorsByCol

- -blockRowBackground

- -blockColBackground

- lineStyle: -join

- bulkData: +stripBlock, stripLines, stripFields, fieldDelim, recordDelim

- excelData

- frame: -*Padding, -showBoundary

