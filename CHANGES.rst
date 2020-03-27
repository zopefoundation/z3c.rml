=======
CHANGES
=======

3.10.0 (2020-03-27)
-------------------

- Added ``inFill`` property to ``<linePlot>`` which will fill the area below
  the line makign it effectively an area plot.

- Added ability to specify the ``labelTextFormat`` property of ``<xValueAxis>``
  and ``<yValueAxis>`` to be a reference to a function via a Python path.

- Added an example from Stack Overflow that exercises the new features. See
  ``tag0linePlot.rml``.

- Remove Python 3.6 support and add 3.8.


3.9.1 (2019-10-04)
------------------

- Adding textTransform implementation.


3.9.0 (2019-07-19)
------------------

- Create a proper, parsable DTD. Add a test that verifies its validity.

- Updated `rml.dtd`.

- ``strandLabels`` does not support text content. That was accidentally
  asserted due to bad schema inheritance.


3.8.0 (2019-06-24)
------------------

- Unified ``paraStyle`` and ``spanStyle`` even more.

- Extended ``<spanStyle>`` to support underline and strike as well.

- Simplified implemnetation of strike and underline style implementation. It
  is also the more correct implementation.


3.7.0 (2019-06-14)
------------------

- Drop support for running tests using ``python setup.py test``.

- Drop Python 3.5 support.

- Extended ``<paraStyle>``:

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


3.6.3 (2019-04-11)
------------------

- Added missing ``lineBelowDash``, ``lineAboveDash``, ``lineLeftDash``,
  ``lineRightDash`` attributes


3.6.2 (2019-03-27)
------------------

- Fix num2words (missing import, two digit dashes)

- Added test to check what happens with text not in tags
  (e.g. not in a ``<para>`` tag)


3.6.1 (2018-12-01)
------------------

- Add Python 3.7 Trove classifier.


3.6.0 (2018-12-01)
------------------

- Upgraded to support Python 3.7

- Allow ``<place>`` to contain ``<fixedSize>``, which allows content to be
  fitted into the place boundaries.


3.5.1 (2018-10-09)
------------------

- Upgraded to support Reportlab 3.5.9


3.5.0 (2018-04-10)
------------------

- Honor the order of attribute choices in the docs.

- Abstracted span styles out of base paragraph style, so that attributes can
  be reused.

- Remove all default values for ``SpanStyle`` styles, so that all values can
  be inherited from the paragraph.

- Support for package-relative ``src`` values in ``<para>`` ``<img>`` tags.


3.4.0 (2018-04-09)
------------------

- Drop Python 3.4 support.

- Feature: Support for ``<span style="NAME">`` and corresponding
  ``<spanStyle>`` styles.

- Bug: ``attr.Sequence``'s ``min_length`` and ``max_length`` was ineffective



3.3.0 (2017-12-06)
------------------

- Add support for non-rml header and footer statements
  This is to be able to support export to Open Document Format.

- Dropped Support for Python 3.3


3.2.0 (2017-01-08)
------------------

- Improve ``IntegerSequence`` field to return ranges using lists of two
  numbers instead of listing them all out.

- Extended ``IntegerSequence`` to allow specification of first number and
  lower/upper bound inclusion.

- Updated ``ConcatenationPostProcessor`` to handle the new integer sequence
  data structure. Since this is so much more efficient for the merging
  library, there was a 5x improvement when including PDFs with page ranges.

- Implemented a PdfTk-based concatenation post-processor. PdfTk is very fast,
  but unfortunatelya lot of the gain is lost, since the outline must be merged
  in manually. The PdfTk post-processor can be enabled by::

    from z3c.rml import pdfinclude
    pdfinclude.IncludePdfPages.ConcatenationPostProcessorFactory = \
        pdfinclude.PdfTkConcatenationPostProcessor

- Fix initial blank page when PDF inclusion is first flowable. [Kyle MacFarlane]

- Support for Python 3.5 [Kyle MacFarlane]

- attr.getFileInfo() crashed if the context element wasn't parsed.


3.1.0 (2016-04-04)
------------------

- Feature: Added new paragraph style attributes ``splitLongWords``,
  ``underlineProportion``, and ``bulletAnchor``.

- Feature: Added ``topPadder`` directive. Patch by Alvin Gonzales.

- Bug: Default SVG fill is black. Patch by Alvin Gonzales.

- Bug: Fixes drawing incorrectly showing when the SVG `viewBox` is not
  anchored at coordinate (0, 0). Patch by Alvin Gonzales.

- Test: Updated versions.cfg to reference the latest releases of all
  dependencies.

- Bug: Avoid raising an exception of PdfReadWarning when including PDFs.
  Patch by Adam Groszer.


3.0.0 (2015-10-02)
------------------

- Support for python 3.3 and 3.4

- Add 'bulletchar' as a valid unordered bullet type.

- Added nice help to rml2pdf script.

- Allow "go()" to accept input and output file objects.

- Fix "Unresolved bookmark" issue.

- Fix Issue #10.


2.9.3 (2015-09-18)
------------------

- Support transparent images in <image> tag


2.9.2 (2015-06-16)
------------------

- Fix spelling "nineth" to "ninth".


2.9.1 (2015-06-15)
------------------

- Add missing file missing from brow-bag 2.9.0 release.


2.9.0 (2015-06-15)
------------------

- Added support for more numbering schemes for ordered lists. The following
  new `bulletType` values are supported:

  * 'l' - Numbers as lower-cased text.
  * 'L' - Numbers as upper-cased text.
  * 'o' - Lower-cased ordinal with numbers converted to text.
  * 'O' - Upper-cased ordinal with numbers converted to text.
  * 'r' - Lower-cased ordinal with numbers.
  * 'R' - Upper-cased ordinal with numbers.

2.8.1 (2015-05-05)
------------------

- Added `barBorder` attribute to ``barCode`` and ``barCodeFlowable``
  tags. This attribute controls the thickness of a white border around a QR
  code.

2.8.0 (2015-02-02)
------------------

- Get version of reference manual from package version.

- Added the ability to specify any set of characters as the "bullet content"
  like it is supported by ReportLab.

- Fixed code to work with ReportLab 3.1.44.

2.7.2 (2014-10-28)
------------------

- Now the latest PyPDF2 versions are supported.


2.7.1 (2014-09-10)
------------------

- Fixed package name.


2.7.0 (2014-09-10)
------------------

- Added ``bulletType`` sypport for the ``listStyle`` tag.

- Added "bullet" as a valid unordered list type value.


2.6.0 (2014-07-24)
------------------

- Implemented ability to use the ``mergePage`` tag inside the ``pageTemplate``
  tag. This way you can use a PDF as a background for a page.

- Updated code to work with ReportLab 3.x, specifically the latest 3.1.8. This
  includes a monkeypatch to the code formatter for Python 2.

- Updated code to work with PyPDF2 1.21. There is a bug in 1.22 that prohibits
  us from upgrading fully.

- Changed buildout to create a testable set of scripts on Ubuntu. In the
  process all package versions were nailed for testing.


2.5.0 (2013-12-10)
------------------

- Reimplamented ``includePdfPages`` directive to use the new PyPDF2 merger
  component that supports simple appending of pages. Also optimized page
  creation and minimized file loading. All of this resulted in a 95% speedup.


2.4.1 (2013-12-10)
------------------

- Fixed a bug when rendering a table with the same style twice. Unfortuantely,
  Reportlab modifies a style during usage, so that a copy mustbe created for
  each use. [Marcin Nowak]


2.4.0 (2013-12-05)
------------------

- Switch from ``pyPdf`` to the newer, maintained ``PyPDF2`` library.


2.3.1 (2013-12-03)
------------------

- Report correct element during error reporting.

- ``registerFontFamily`` never worked until now, since the directive was not
  properly registered.


2.3.0 (2013-09-03)
------------------

- Added ``title``, ``subject``, ``author``, and ``creator`` attributes to
  ``document`` element. Those are set as PDF annotations, which are now
  commonly used to hint viewers window titles, etc. (Those fields are not
  available in RML2PDF.)


2.2.1 (2013-08-06)
------------------

- Make the number of max rendering passes configurable by exposing the setting
  in the API.

- Added `align` attribute to ``img`` tag.


2.2.0 (2013-07-08)
------------------

- Added a new console script "rml2pdf" that renders an RML file to PDF.

- Added ``preserveAspectRatio`` to ``img`` tag flowable. The attribute was
  already supported for the ``image`` tag.


2.1.0 (2013-03-07)
------------------

- Implemented all PDF viewer preferences. [Kyle MacFarlane]

  * HideToolbar
  * HideMenubar
  * HideWindowUI
  * FitWindow
  * CenterWindow
  * DisplayDocTitle
  * NonFullScreenPageMode
  * Direction
  * ViewArea
  * ViewClip
  * PrintArea
  * PrintClip
  * PrintScaling

  They are all available via the ``docinit`` tag.

- Added SVG support to the ``image`` and ``imageAndFlowables`` tags. [Kyle
  MacFarlane]

  Approach: Convert the drawing to a PIL ``Image`` instance and pass that
  around just like a regular image. The big problem is that in the conversion
  from ``Drawing`` to ``Image`` stroke width can often get messed up and
  become too thick. I think this is maybe down to how scaling is done but you
  can avoid it by editing the SVGs you want to insert. You also lose any
  transparency and get a white background. Basically you no longer really have
  a vector graphic but instead a 300 DPI bitmap that is automatically scaled
  to the correct size with little quality loss.

- Added ability to look for font files in packages using the standard
  "[package.path]/dir/filename" notation. [Kyle MacFarlane]

- Documented the ``pageSize`` versus ``pagesize`` attribute difference on
  ``template`` and ``pageTemplate`` elements compared to RML2PDF. [Kyle
  MacFarlane]

- ``namedString`` element now evaluates its contents so you can use things
  like ``pageNumber`` inside of it. [Kyle MacFarlane]

- Implemented ``evalString`` using Python's ``eval()`` with builtins
  disabled. [Kyle MacFarlane]

- ``getName`` element now checks if it has a default attribute. This is used
  as a width measurement for a first pass or as the actual value if the
  reference isn't resolved after the second pass. [Kyle MacFarlane]

- ``getName`` element now supports forward references. This means you can now
  do things like "Page X of Y". This only works in the ``drawString`` and
  ``para`` elements. [Kyle MacFarlane]

- General performance improvements. [Kyle MacFarlane]

- Improved performance by not applying a copy of the default style to every
  table cell and also by not even trying to initialise the attributes if lxml
  says they don't exist. [Kyle MacFarlane]

- ``MergePostProcessor`` class did not copy document info and table of
  contents (aka Outlines) of ``inputFile1``. That meant that if you used any
  ``includePdfPages`` or ``mergePage`` directives you lost any ``outlineAdd``
  directive effect. [Alex Garel]

- Fixed any failing tests, including the ones failing on Windows. [Kyle
  MacFarlane]

- Fixed the table borders not printing or even appearing in some
  viewers. [Kyle MacFarlane]

- Updated ``bootstrap.py`` and ``buildout.cfg`` to work with the latest
  version of ``zc.buildout``.

- Updated build to use latest version of lxml.


2.0.0 (2012-12-21)
------------------

- Implemented ``saveState`` and ``restoreState`` directives. (LP #666194)

- Implemented ``storyPlace`` directive. (LP #665941)

- Implemented ``clip`` attribute of ``path`` directive. See RML example 041.

- Added ``h4``, ``h5``, and ``h6`` directives.

- Implemented ``codesnippet`` directive.

- Implemented ``pageBreakBefore``, ``frameBreakBefore``, ``textTransform``,
  and ``endDots`` attributes for paragraph styles.

- Added ``maxLineLength`` and ``newLineChars`` attributes to the ``pre``
  directive.

- Implemented ``pageNumber`` element for all ``draw*String`` elements.

- Implemented ``NamedString`` directive.

- Implemented ``startIndex`` and ``showIndex`` directive. Also hooked up
  ``index`` in paragraphs properly. You can now create real book indexes.

- Implemented ``ol``, ``ul``, and ``li`` directives, which allow highly
  flexible lists to be created. Also implemented a complimentary ``listStyle``
  directive.

- Implemented the following doc-programming directives:

    * docAssert
    * docAssign
    * docElse
    * docIf
    * docExec
    * docPara
    * docWhile

- Added ``encName`` attribute to ``registerCidFont`` directive.

- Renamed ``bookmark`` to ``bookmarkPage``.

- Created a new canvas directive called ``bookmark``.

- Added ``img`` directive, which is a simple image flowable.

- Implemented crop marks support fully.

- Added ``pageLayout`` and ``pageMode`` to ``docInit`` directive.

- Implemented all logging related directives.

- Implemented ``color`` directive inside the ``initialize`` directive.

- Renamed ``pdfInclude`` to documented ``includePdfPages`` and added `pages`
  attribute, so that you can only include specific pages.

- Don't show "doc" namespace in reference snippets.

- Create a list of RML2PDF and z3c.rml differences.

- Implemented the ``ABORT_ON_INVALID_DIRECTIVE`` flag, that when set ``True``
  will raise a ``ValueError`` error on the first occurence of a bad tag.

- Implemented ``setFontSize`` directive for page drawings.

- Implemented ``plugInGraphic`` which allows inserting graphics rendered in
  Python.

- Added `href` and `destination` to table cells and rectangles.

- Bug: Due to a logic error, bad directives were never properly detected and
  logged about.

- Bug: Overwriting the default paragraph styles did not work properly.

- Bug: Specifying a color in any tag inside the paragraph would fail, if the
  color was a referenced name.

- Bug: Moved premature ``getName`` evaluation into runtime to properly handle
  synamic content now. This is now properly done for any paragraph and
  draw string variant.

- Bug: Fixed DTD generator to properly ignore Text Nodes as attributes. Also
  text nodes were not properly documented as element PCDATA.


1.1.0 (2012-12-18)
------------------

- Upgrade to ReportLab 2.6. This required some font changes and several
  generated PDFs did not match, since some default fonts changed to sans-serif.

- Added ``pdfInclude`` directive from Alex Garel. (LP #969399).

- Switched to Pillow (from PIL).

- Switched RML highlighting in RML Reference from SilverCity to Pygments.

- Bug: Addressed a bug in ReportLab 2.6 that disallowed 3-D pie charts from
  rendering.

- Bug: Properly reset pdfform before rendering a document.

- Bug: Reset fonts properly before a rendering.


1.0.0 (2012-04-02)
------------------

- Using Python's ``doctest`` module instead of depreacted
  ``zope.testing.doctest``.


0.9.1 (2010-07-22)
------------------

- I found a more complete paragraph border patch from Yuan Hong. Now the DTD
  is updated, the border supports a border radius and the tag-para.rml sample
  has been updated.


0.9.0 (2010-07-22)
------------------

- Upgraded to ReportLab 2.4. This required some font changes and several
  generated PDFs did not match, since some default fonts changed.

- Upgraded to latest lxml. This only required a trivial change. Patch by Felix
  Schwarz.

- Implemented ``linePlot3D`` directive. Patch by Faisal Puthuparackat.

- Added paragraph border support. Patch by Yuan Hong.

- Bug: Fixed version number in reference.pt. Patch by Felix Schwarz.

- Bug: Write PDF documents in binary mode. Patch by Felix Schwarz.


0.8.0 (2009-02-18)
------------------

- Bug: Use python executable as a part of the subprocess command.

- Add support for RML's `pageNumber` element.


0.7.3 (2007-11-10)
------------------

- Make sure that the output dir is included in the distribution.


0.7.2 (2007-11-10)
------------------

- Upgraded to work with ReportLab 2.1 and lxml 1.3.6.

- Fix sub-process tests for a pure egg setup.


0.7.1 (2007-07-31)
------------------

- Bug: When the specified page size (within the ``pageInfo`` element) was a
  word or set thereof, the processing would fail. Thanks to Chris Zelenak for
  reporting the bug and providing a patch.


0.7.0 (2007-06-19)
------------------

- Feature: Added a Chinese PDF sample file to ``tests/expected`` under the
  name ``sample-shipment-chinese.pdf``.

- Feature: Added another tag that is commonly needed in projects. The
  ``<keepTogether>`` tag will keep the child flowables in the same frame.
  When necessary, the frame break will be automatic. Patch by Yuan Hong.

- Feature: Added the "alignment" attribute to the ``blockTable``
  directive. This attribute defines the horizontal alignment for a table that
  is not 100% in width of the containing flowable. Patch by Yuan Hong.

- Feature: When creating Chinese PDF documents, the normal TTF for Chinese
  printing is 'simsun'. However, when bold text is neeed, we switch to
  'simhei'. To properly register this, we need the
  ``reportlab.lib.fonts.addMapping`` function. This is missing in the reportlab
  RML specification, so a new directive has been defined::

    <addMapping faceName="simsun" bold="1" italic="0" psName="simhei" />

  Patch by Yuan Hong.

- Feature: The ``para`` and ``paraStyle`` directive now support the "wordWrap"
  attribute, which allows for selecting a different wrod wrapping
  algorithm. This is needed because some far-East Asian languages do not use
  white space to separate words. Patch by Yuan Hong.

- Bug: Handle Windows drive letters correctly. Report and fix by Yuan Hong.


0.6.0 (2007-06-19)
------------------

- Bug: Fixed setup.py to include all dependencies.

- Bug: Added test to show that a blocktable style can be applied multiple
  times. A user reported that this is not working, but I could not replicate
  the problem.

- Update: Updated the expected renderings to ReportLab 2.1. There were some
  good layout fixes that broke the image comparison.


0.5.0 (2007-04-01)
------------------

- Initial Release
