# Hook up our custom paragraph parser.
import pkg_resources

import z3c.rml.paraparser
import z3c.rml.rlfix

__version__ = pkg_resources.require('z3c.rml')[0].version

from reportlab.lib.styles import getSampleStyleSheet

SampleStyleSheet = getSampleStyleSheet()
