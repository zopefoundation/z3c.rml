# Hook up our custom paragraph parser.
import pkg_resources

import z3c.rml.paraparser
import z3c.rml.rlfix  # noqa: F401 imported but unused


__version__ = pkg_resources.require('z3c.rml')[0].version

from reportlab.lib.styles import getSampleStyleSheet


SampleStyleSheet = getSampleStyleSheet()
