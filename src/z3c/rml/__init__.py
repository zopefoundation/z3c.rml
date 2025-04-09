# Hook up our custom paragraph parser.
import importlib.metadata

from reportlab.lib.styles import getSampleStyleSheet

import z3c.rml.paraparser
import z3c.rml.rlfix  # noqa: F401 imported but unused


__version__ = importlib.metadata.version("z3c.rml")

del importlib.metadata


SampleStyleSheet = getSampleStyleSheet()
