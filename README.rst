===================================================
``z3c.rml`` -- An alternative implementation of RML
===================================================

.. image:: https://img.shields.io/pypi/v/z3c.rml.svg
   :target: https://pypi.org/project/z3c.rml/
   :alt: Latest Version

.. image:: https://img.shields.io/pypi/pyversions/z3c.rml.svg
   :target: https://pypi.org/project/z3c.rml/
   :alt: Supported Python versions

.. image:: https://github.com/zopefoundation/z3c.rml/actions/workflows/tests.yml/badge.svg
   :target: https://github.com/zopefoundation/z3c.rml/actions/workflows/tests.yml
   :alt: Build Status

.. image:: https://coveralls.io/repos/github/zopefoundation/z3c.rml/badge.svg?branch=master
   :target: https://coveralls.io/github/zopefoundation/z3c.rml?branch=master

This is an alternative implementation of ReportLab's RML PDF generation XML
format. Like the original implementation, it is based on ReportLab's
``reportlab`` library.

You can read all about ``z3c.rml`` and see many examples on how to use it,
see the `RML Reference`_

.. _RML Reference: https://github.com/zopefoundation/z3c.rml/blob/master/src/z3c/rml/rml-reference.pdf?raw=true


Install on pip::

	pip install z3c.rml

z3c.rml is then available on the commandline as z3c.rml.::

	$ z3c.rml --help
	usage: rml2pdf [-h]
	               xmlInputName [outputFileName] [outDir]
	               [dtdDir]

	Converts file in RML format into PDF file.

	positional arguments:
	  xmlInputName    RML file to be processed
	  outputFileName  output PDF file name
	  outDir          output directory
	  dtdDir          directory with XML DTD (not yet supported)

	optional arguments:
	  -h, --help      show this help message and exit

	Copyright (c) 2007 Zope Foundation and Contributors.

Save this file as file.rml::

	<!DOCTYPE document SYSTEM "rml.dtd">
	<document filename="example_01.pdf">
	 <template showBoundary="1"> <!--Debugging is now turned on, frame outlines -->
	 <!--will appear on the page -->
	 <pageTemplate id="main">
	 <!-- two frames are defined here: -->
	 <frame id="first" x1="100" y1="400" width="150" height="200"/>
	 <frame id="second" x1="300" y1="400" width="150" height="200"/>
	 </pageTemplate>
	 </template>
	 <stylesheet>
	 <!-- still empty...-->
	 </stylesheet>
	 <story>
	 <para>
	 Welcome to RML.
	 </para>
	 </story>
	</document>


Then run::

	$ z3c.rml file.rml

The output will be example_01.pdf as defined in the document

Codewise you can do::

	from z3c.rml import rml2pdf
	rml2pdf.go('file.rml','file.pdf')