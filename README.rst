===================================================
``z3c.rml`` -- An alternative implementation of RML
===================================================

.. image:: https://img.shields.io/pypi/v/z3c.rml.svg
   :target: https://pypi.org/project/z3c.rml/
   :alt: Latest Version

.. image:: https://img.shields.io/pypi/pyversions/z3c.rml.svg
   :target: https://pypi.org/project/z3c.rml/
   :alt: Supported Python versions

.. image:: https://travis-ci.com/zopefoundation/z3c.rml.svg?branch=master
   :target: https://travis-ci.com/zopefoundation/z3c.rml
   :alt: Build Status

.. image:: https://coveralls.io/repos/github/zopefoundation/z3c.rml/badge.svg?branch=master
   :target: https://coveralls.io/github/zopefoundation/z3c.rml?branch=master

This is an alternative implementation of ReportLab's RML PDF generation XML
format. Like the original implementation, it is based on ReportLab's
``reportlab`` library.

You can read all about ``z3c.rml`` and see many examples on how to use it,
see the `RML Reference`_

.. _RML Reference: https://github.com/zopefoundation/z3c.rml/blob/master/src/z3c/rml/rml-reference.pdf?raw=true

Outputting the actual pdf:

.. code-block:: python

   from z3c.rml import rml2pdf
    rml2pdf.go(xmlInputName, outputFileName)
    
View a demo `here <https://blog.alec.id.au/adventure-into-reportlab-and-rml/>`_.
