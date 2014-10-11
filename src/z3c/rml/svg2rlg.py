#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
svg2rlg is a tool to convert from SVG to reportlab graphics.

License : BSD

version 0.3
"""
import os
import re
import six
from gzip import GzipFile

from xml.etree import cElementTree

from reportlab.graphics import renderPDF

from reportlab.graphics.shapes import Drawing, Group, String, Line, Rect, Image
from reportlab.graphics.shapes import Circle, Ellipse, Polygon, PolyLine, Path
from reportlab.graphics.shapes import mmult

from reportlab.lib.units import pica, toLength
import reportlab.lib.colors as colors

class SVGError(Exception):
    pass

EOF = object()

class Lexer:
    """
    This style of implementation was inspired by this article:

        http://www.gooli.org/blog/a-simple-lexer-in-python/
    """
    Float = r'[-\+]?(?:(?:\d*\.\d+)|(?:\d+\.)|(?:\d+))(?:[Ee][-\+]?\d+)?'
    Int = r'[-\+]?\d+'

    lexicon = None
    ignore = None
    callbacks = None

    def __init__(self):
        lexicon = self.lexicon

        # create internal names for group matches
        groupnames = dict(('lexer_%d' % idx, item[0]) for idx,item in enumerate(lexicon))
        self.groupnames = groupnames

        # assemble regex parts to one regex
        igroupnames = dict((value,name) for name,value in six.iteritems(groupnames))

        regex_parts = ('(?P<%s>%s)' % (igroupnames[cls], regs) for cls,regs in lexicon)

        self.regex_string = '|'.join(regex_parts)
        self.regex = re.compile(self.regex_string)

    def lex(self, text):
        """
        Yield (token_type, data) tokens.
        The last token will be (EOF, None) where EOF
        """
        regex = self.regex
        groupnames = self.groupnames

        ignore = self.ignore or set()
        callbacks = self.callbacks or dict()

        position = 0
        size = len(text)

        while position < size:
            match = regex.match(text, position)
            if match is None:
                raise SVGError('Unknown token at position %d' %  position)

            position = match.end()
            cls = groupnames[match.lastgroup]
            value = match.group(match.lastgroup)

            if cls in ignore:
                continue

            if cls in callbacks:
                value = callbacks[cls](self, value)

            yield (cls, value)

        yield (EOF, None)

# Parse SVG length units
length_pattern = \
r"""
    ^                           # match start of line
    \s*                         # ignore whitespace
    (?P<value>[-\+]?\d*\.?\d*([eE][-\+]?\d+)?)  # match float or int value
    (?P<unit>.+)?               # match any chars
    \s*                         # ignore whitespace
    $                           # match end of line
"""

length_match = re.compile(length_pattern, re.X).match

def parseLength(length):
    """
    Convert length to reportlab points.
    """
    match = length_match(length)
    if match is None:
        raise SVGError("Not a valid length unit: '%s'" % length)

    value = match.group('value')
    unit = match.group('unit') or ''

    if not value:
        raise SVGError("Not a valid length unit: '%s'" % length)

    if not unit:
        if value[0] == 'e' or value[0] == 'E':
            return float('1' + value)
        else:
            return float(value)

    elif unit in ('em', 'ex', 'px', '%'):
        # ignoring relative units
        return float(value)

    elif unit == 'pc':
        return toLength(value + 'pica')

    elif unit in ('mm', 'cm', 'in', 'i', 'pt', 'pica'):
        return toLength(length)

    else:
        raise SVGError("Unknown unit '%s'" % unit)

# Parse SVG color definitions
color_pattern = \
r"""
^(
    (?P<named>
        \w+
    ) |

    (?P<hex>
        [#]
        (?P<hex_r>[a-zA-Z0-9]{2})
        (?P<hex_rg>[a-zA-Z0-9]{2})
        (?P<hex_rb>[a-zA-Z0-9]{2})
    ) |

    (?P<hexshort>
        [#]
        (?P<hexshort_r>[a-zA-Z0-9])
        (?P<hexshort_g>[a-zA-Z0-9])
        (?P<hexshort_b>[a-zA-Z0-9])
    ) |

    (?P<rgbint>
        [rR][gG][bB]
        \(
        (?P<rgbint_r>\d{1,3})
        ,\s?
        (?P<rgbint_g>\d{1,3})
        ,\s?
        (?P<rgbint_b>\d{1,3})
        \)
    ) |

    (?P<rgb>
        [rR][gG][bB]
        \(
        (?P<rgb_r>\d+\.?\d*)
        \%
        ,\s?
        (?P<rgb_g>\d+\.?\d*)
        \%
        ,\s?
        (?P<rgb_b>\d+\.?\d*)
        \%
        \)
    )
)$
"""

color_match = re.compile(color_pattern, re.X).match

NAMEDCOLOURS = {
    # expanded named colors from SVG spc
           'aliceblue' : colors.HexColor('#f0f8ff'),
        'antiquewhite' : colors.HexColor('#faebd7'),
                'aqua' : colors.HexColor('#00ffff'),
          'aquamarine' : colors.HexColor('#7fffd4'),
               'azure' : colors.HexColor('#f0ffff'),
               'beige' : colors.HexColor('#f5f5dc'),
              'bisque' : colors.HexColor('#ffe4c4'),
               'black' : colors.HexColor('#000000'),
      'blanchedalmond' : colors.HexColor('#ffebcd'),
                'blue' : colors.HexColor('#0000ff'),
          'blueviolet' : colors.HexColor('#8a2be2'),
               'brown' : colors.HexColor('#a52a2a'),
           'burlywood' : colors.HexColor('#deb887'),
           'cadetblue' : colors.HexColor('#5f9ea0'),
          'chartreuse' : colors.HexColor('#7fff00'),
           'chocolate' : colors.HexColor('#d2691e'),
               'coral' : colors.HexColor('#ff7f50'),
      'cornflowerblue' : colors.HexColor('#6495ed'),
            'cornsilk' : colors.HexColor('#fff8dc'),
             'crimson' : colors.HexColor('#dc143c'),
                'cyan' : colors.HexColor('#00ffff'),
            'darkblue' : colors.HexColor('#00008b'),
            'darkcyan' : colors.HexColor('#008b8b'),
       'darkgoldenrod' : colors.HexColor('#b8860b'),
            'darkgray' : colors.HexColor('#a9a9a9'),
           'darkgreen' : colors.HexColor('#006400'),
            'darkgrey' : colors.HexColor('#a9a9a9'),
           'darkkhaki' : colors.HexColor('#bdb76b'),
         'darkmagenta' : colors.HexColor('#8b008b'),
      'darkolivegreen' : colors.HexColor('#556b2f'),
          'darkorange' : colors.HexColor('#ff8c00'),
          'darkorchid' : colors.HexColor('#9932cc'),
             'darkred' : colors.HexColor('#8b0000'),
          'darksalmon' : colors.HexColor('#e9967a'),
        'darkseagreen' : colors.HexColor('#8fbc8b'),
       'darkslateblue' : colors.HexColor('#483d8b'),
       'darkslategray' : colors.HexColor('#2f4f4f'),
       'darkslategrey' : colors.HexColor('#2f4f4f'),
       'darkturquoise' : colors.HexColor('#00ced1'),
          'darkviolet' : colors.HexColor('#9400d3'),
            'deeppink' : colors.HexColor('#ff1493'),
         'deepskyblue' : colors.HexColor('#00bfff'),
             'dimgray' : colors.HexColor('#696969'),
             'dimgrey' : colors.HexColor('#696969'),
          'dodgerblue' : colors.HexColor('#1e90ff'),
           'firebrick' : colors.HexColor('#b22222'),
         'floralwhite' : colors.HexColor('#fffaf0'),
         'forestgreen' : colors.HexColor('#228b22'),
             'fuchsia' : colors.HexColor('#ff00ff'),
           'gainsboro' : colors.HexColor('#dcdcdc'),
          'ghostwhite' : colors.HexColor('#f8f8ff'),
                'gold' : colors.HexColor('#ffd700'),
           'goldenrod' : colors.HexColor('#daa520'),
                'gray' : colors.HexColor('#808080'),
               'green' : colors.HexColor('#008000'),
         'greenyellow' : colors.HexColor('#adff2f'),
                'grey' : colors.HexColor('#808080'),
            'honeydew' : colors.HexColor('#f0fff0'),
             'hotpink' : colors.HexColor('#ff69b4'),
           'indianred' : colors.HexColor('#cd5c5c'),
              'indigo' : colors.HexColor('#4b0082'),
               'ivory' : colors.HexColor('#fffff0'),
               'khaki' : colors.HexColor('#f0e68c'),
            'lavender' : colors.HexColor('#e6e6fa'),
       'lavenderblush' : colors.HexColor('#fff0f5'),
           'lawngreen' : colors.HexColor('#7cfc00'),
        'lemonchiffon' : colors.HexColor('#fffacd'),
           'lightblue' : colors.HexColor('#add8e6'),
          'lightcoral' : colors.HexColor('#f08080'),
           'lightcyan' : colors.HexColor('#e0ffff'),
'lightgoldenrodyellow' : colors.HexColor('#fafad2'),
           'lightgray' : colors.HexColor('#d3d3d3'),
          'lightgreen' : colors.HexColor('#90ee90'),
           'lightgrey' : colors.HexColor('#d3d3d3'),
           'lightpink' : colors.HexColor('#ffb6c1'),
         'lightsalmon' : colors.HexColor('#ffa07a'),
       'lightseagreen' : colors.HexColor('#20b2aa'),
        'lightskyblue' : colors.HexColor('#87cefa'),
      'lightslategray' : colors.HexColor('#778899'),
      'lightslategrey' : colors.HexColor('#778899'),
      'lightsteelblue' : colors.HexColor('#b0c4de'),
         'lightyellow' : colors.HexColor('#ffffe0'),
                'lime' : colors.HexColor('#00ff00'),
           'limegreen' : colors.HexColor('#32cd32'),
               'linen' : colors.HexColor('#faf0e6'),
             'magenta' : colors.HexColor('#ff00ff'),
              'maroon' : colors.HexColor('#800000'),
    'mediumaquamarine' : colors.HexColor('#66cdaa'),
          'mediumblue' : colors.HexColor('#0000cd'),
        'mediumorchid' : colors.HexColor('#ba55d3'),
        'mediumpurple' : colors.HexColor('#9370db'),
      'mediumseagreen' : colors.HexColor('#3cb371'),
     'mediumslateblue' : colors.HexColor('#7b68ee'),
   'mediumspringgreen' : colors.HexColor('#00fa9a'),
     'mediumturquoise' : colors.HexColor('#48d1cc'),
     'mediumvioletred' : colors.HexColor('#c71585'),
        'midnightblue' : colors.HexColor('#191970'),
           'mintcream' : colors.HexColor('#f5fffa'),
           'mistyrose' : colors.HexColor('#ffe4e1'),
            'moccasin' : colors.HexColor('#ffe4b5'),
         'navajowhite' : colors.HexColor('#ffdead'),
                'navy' : colors.HexColor('#000080'),
             'oldlace' : colors.HexColor('#fdf5e6'),
               'olive' : colors.HexColor('#808000'),
           'olivedrab' : colors.HexColor('#6b8e23'),
              'orange' : colors.HexColor('#ffa500'),
           'orangered' : colors.HexColor('#ff4500'),
              'orchid' : colors.HexColor('#da70d6'),
       'palegoldenrod' : colors.HexColor('#eee8aa'),
           'palegreen' : colors.HexColor('#98fb98'),
       'paleturquoise' : colors.HexColor('#afeeee'),
       'palevioletred' : colors.HexColor('#db7093'),
          'papayawhip' : colors.HexColor('#ffefd5'),
           'peachpuff' : colors.HexColor('#ffdab9'),
                'peru' : colors.HexColor('#cd853f'),
                'pink' : colors.HexColor('#ffc0cb'),
                'plum' : colors.HexColor('#dda0dd'),
          'powderblue' : colors.HexColor('#b0e0e6'),
              'purple' : colors.HexColor('#800080'),
                 'red' : colors.HexColor('#ff0000'),
           'rosybrown' : colors.HexColor('#bc8f8f'),
           'royalblue' : colors.HexColor('#4169e1'),
         'saddlebrown' : colors.HexColor('#8b4513'),
              'salmon' : colors.HexColor('#fa8072'),
          'sandybrown' : colors.HexColor('#f4a460'),
            'seagreen' : colors.HexColor('#2e8b57'),
            'seashell' : colors.HexColor('#fff5ee'),
              'sienna' : colors.HexColor('#a0522d'),
              'silver' : colors.HexColor('#c0c0c0'),
             'skyblue' : colors.HexColor('#87ceeb'),
           'slateblue' : colors.HexColor('#6a5acd'),
           'slategray' : colors.HexColor('#708090'),
           'slategrey' : colors.HexColor('#708090'),
                'snow' : colors.HexColor('#fffafa'),
         'springgreen' : colors.HexColor('#00ff7f'),
           'steelblue' : colors.HexColor('#4682b4'),
                 'tan' : colors.HexColor('#d2b48c'),
                'teal' : colors.HexColor('#008080'),
             'thistle' : colors.HexColor('#d8bfd8'),
              'tomato' : colors.HexColor('#ff6347'),
           'turquoise' : colors.HexColor('#40e0d0'),
              'violet' : colors.HexColor('#ee82ee'),
               'wheat' : colors.HexColor('#f5deb3'),
               'white' : colors.HexColor('#ffffff'),
          'whitesmoke' : colors.HexColor('#f5f5f5'),
              'yellow' : colors.HexColor('#ffff00'),
         'yellowgreen' : colors.HexColor('#9acd32'),
}

def parseColor(color):
    """
    Convert SVG color to reportlab color
    """
    if color == 'none':
        return None

    elif color == 'currentColor':
        return "currentColor"

    elif color == 'transparent':
        return colors.Color(0.,0.,0.,0.)

    match = color_match(color)
    if match is None:
        raise SVGError("Not a valid color definition: '%s'" % color)

    info = match.groupdict()

    if info['named'] is not None:
        if not color in NAMEDCOLOURS:
            raise SVGError("Not a valid named color: '%s'" % color)

        return NAMEDCOLOURS[color]

    elif info['hex'] is not None:
        return colors.HexColor(color)

    elif info['hexshort'] is not None:
        r = 2*info['hexshort_r']
        g = 2*info['hexshort_g']
        b = 2*info['hexshort_b']

        return colors.HexColor('#%s%s%s' % (r,g,b))

    elif info['rgbint'] is not None:
        r = int(info['rgbint_r'])
        g = int(info['rgbint_g'])
        b = int(info['rgbint_b'])

        if r > 255 or g > 255 or b > 255:
            raise SVGError("RGB value outside range: '%s'" % color)

        return colors.Color(r/255., g/255., b/255.)

    elif info['rgb'] is not None:
        r = float(info['rgb_r'])
        g = float(info['rgb_g'])
        b = float(info['rgb_b'])

        if r > 100 or g > 100 or b > 100:
            raise SVGError("RGB value outside range: '%s'" % color)

        return colors.Color(r/100., g/100., b/100.)

class SVGStyle(Lexer):
    """
    Break SVG inline style into tokens
    """
    name = object()
    value = object()
    delimiter = object()
    comment = object()

    lexicon = ( \
        (delimiter   , r'[ :;\n]'),
        (comment     , r'/\*.+\*/'),
        (name        , r'[\w\-#]+?(?=:)'),
        (value       , r'[\w\-#\.\(\)%,][\w \-#\.\(\)%,]*?(?=[;])'),
    )

    ignore = frozenset((delimiter,comment))

    def __init__(self):
        Lexer.__init__(self)

    def parse(self, text):
        """
        Parse a string of SVG <path> data.
        """
        if six.PY2:
            next = self.lex(text + ';').next
        else:
            next = self.lex(text + ';').__next__
        styles = {}

        while True:
            token, value = next()
            if token == EOF:
                break

            name = value.rstrip(':')

            token, value = next()

            if token == EOF:
                raise SVGError('expected value in style definition')

            if name in styles:
                raise SVGError('style redefined')

            styles[name] = value

        return styles


parseStyle = SVGStyle()

class SVGTransform(Lexer):
    """
    Break SVG transform into tokens.
    """
    numfloat = object()
    numint = object()
    string = object()
    skip = object()

    numbers = frozenset((numfloat, numint))

    lexicon = ( \
        (numfloat   , Lexer.Float),
        (numint     , Lexer.Int),
        (string     , r'\w+'),
        (skip       , r'[\(\), \n]'),
    )

    ignore = frozenset((skip,))

    callbacks = {
        numfloat    : lambda self,value: float(value),
        numint      : lambda self,value: float(value)
    }

    def __init__(self):
        Lexer.__init__(self)

    def assertion(self, condition, msg = ''):
        if not condition:
            raise SVGError(msg)

    def iterparse(self, text):
        """
        Parse a string of SVG transform data.
        """
        assertion = self.assertion
        if six.PY2:
            next = self.lex(text).next
        else:
            next = self.lex(text).__next__
        numbers = self.numbers
        string = self.string

        token, value = next()
        while token != EOF:
            assertion(token is string, 'Expected string')

            transform = value

            if transform == 'matrix':
                token, a = next()
                assertion(token in numbers, 'Expected number')

                token, b = next()
                assertion(token in numbers, 'Expected number')

                token, c = next()
                assertion(token in numbers, 'Expected number')

                token, d = next()
                assertion(token in numbers, 'Expected number')

                token, e = next()
                assertion(token in numbers, 'Expected number')

                token, f = next()
                assertion(token in numbers, 'Expected number')

                yield (transform, (a,b,c,d,e,f))

            elif transform == 'translate':
                token, tx = next()
                assertion(token in numbers, 'Expected number')

                token, value = next()
                ty = value
                if not token in numbers:
                    ty = 0.

                yield (transform, (tx, ty))

                if not token in numbers:
                    continue

            elif transform == 'scale':
                token, sx = next()
                assertion(token in numbers, 'Expected number')

                token, value = next()
                sy = value
                if not token in numbers:
                    sy = sx

                yield (transform, (sx, sy))

                if not token in numbers:
                    continue

            elif transform == 'rotate':
                token, angle = next()
                assertion(token in numbers, 'Expected number')

                token, value = next()
                cx = value

                if token in numbers:
                    token, value = next()
                    assertion(token in numbers, 'Expected number')

                    cy = value

                    yield (transform, (angle,(cx,cy)))

                else:
                    yield (transform, (angle,None))
                    continue

            elif transform == 'skewX' or transform == 'skewY':
                token, value = next()
                angle = value
                assertion(token in numbers, 'Expected number')

                yield (transform, (angle,))

            else:
                raise SVGError("unknown transform '%s'" % transform)

            # fetch next token
            token, value = next()

parseTransform = SVGTransform()

class SVGPath(Lexer):
    """
    Break SVG path data into tokens.

    The SVG spec requires that tokens are greedy.
    This lexer relies on Python's regexes defaulting to greediness.
    """
    numfloat = object()
    numint = object()
    numexp = object()
    string = object()
    skip = object

    lexicon = ( \
        (numfloat   , Lexer.Float),
        (numint     , Lexer.Int),
        (numexp     , r'(?:[Ee][-\+]?\d+)'),
        (string     , r'[AaCcHhLlMmQqSsTtVvZz]'),
        (skip       , r'[, \n]'),
    )

    ignore = frozenset((skip,))

    callbacks = {
        numfloat    : lambda self,value: float(value),
        numint      : lambda self,value: float(value),
        numexp      : lambda self,value: float('1.'+value)
    }

    numbers = frozenset((numfloat, numint, numexp))

    def __init__(self):
        Lexer.__init__(self)

    def assertion(self, condition, msg = ''):
        if not condition:
            raise SVGError(msg)

    def iterparse(self, text):
        """
        Parse a string of SVG <path> data.
        """
        assertion = self.assertion
        numbers = self.numbers
        string = self.string

        if six.PY2:
            next = self.lex(text).next
        else:
            next = self.lex(text).__next__

        token, value = next()
        while token != EOF:
            assertion(token is string, 'Expected string in path data')
            cmd = value
            CMD = value.upper()

            # closePath
            if CMD in 'Z':
                token, value = next()
                yield (cmd, (None,))

            # moveTo, lineTo, curve, smoothQuadraticBezier, quadraticBezier, smoothCurve
            elif CMD in 'CMLTQS':
                coords = []
                token, value = next()
                while token in numbers:
                    last = value

                    token, value = next()
                    assertion(token in numbers, 'Expected number in path data')

                    coords.append((last,value))

                    token, value = next()

                if CMD == 'C':
                    assertion(len(coords) % 3 == 0, 'Expected coordinate triplets in path data')

                yield (cmd, tuple(coords))

            # horizontalLine or verticalLine
            elif CMD in 'HVhv':
                coords = []
                token, value = next()
                assertion(token in numbers, 'Expected number')

                while token in numbers:
                    coords.append(value)
                    token, value = next()

                yield (cmd, tuple(coords))

            # ellipticalArc
            elif CMD == 'A':
                token, rx = next()
                #assertion(token in numbers and value > 0, 'expected positive number in path data')
                rx = value

                token, ry = next()
                #assertion(token in numbers and ry > 0, 'expected positive number in path data')

                token, rotation = next()
                #assertion(token in numbers, 'expected number in path data')

                token, largearc = next()
                #assertion(token is int and largearc in (0,1), 'expected 0 or 1 in path data')

                token, sweeparc = next()
                #assertion(token is int and sweeparc in (0,1), 'expected 0 or 1 in path data')

                token, x = next()
                #assertion(token in numbers, 'expected number in path data')

                token, y = next()
                #assertion(token in numbers, 'expected number in path data')

                yield (cmd, ((rx,ry), rotation, largearc, sweeparc, (x,y)))

                token, value = next()

            else:
                raise SVGError("cmd '%s' in path data not supported" % cmd)

parsePath = SVGPath()

def parseDashArray(array):
    if array == 'none':
        return None

    return map(parseLength, re.split('[ ,]+', array))

def parseOpacity(value):
    try:
        opacity = float(value)
    except ValueError:
        raise SVGError('expected float value')

    # clamp value
    opacity = min(max(opacity, 0.), 1.)

    return opacity

def parseAnchor(value):
    if not value or value == 'none':
        return 'start'

    if value not in ('start', 'middle', 'end'):
        raise SVGError("unknown '%s' alignment" % value)

    return value

# map svg font names to reportlab names
FONTMAPPING = {
    "sans-serif"    : "Helvetica",
    "serif"         : "Times-Roman",
    "monospace"     : "Courier"
}

# map svg style to repotlab attributes and converters
STYLES = {
    "fill"              : ("fillColor",         parseColor),
    "stroke"            : ("strokeColor",       parseColor),
    "stroke-width"      : ("strokeWidth",       parseLength),
    "stroke-linejoin"   : ("strokeLineJoin",    lambda style: {"miter":0, "round":1, "bevel":2}[style]),
    "stroke-linecap"    : ("strokeLineCap",     lambda style: {"butt":0, "round":1, "square":2}[style]),
    "stroke-dasharray"  : ("strokeDashArray",   parseDashArray),
    "fill-opacity"      : ('fillOpacity',       parseOpacity),
    "stroke-opacity"    : ('strokeOpacity',     parseOpacity),
    "font-family"       : ("fontName",          lambda name: FONTMAPPING.get(name, 'Helvetica')),
    "font-size"         : ("fontSize",          parseLength),
    "text-anchor"       : ("textAnchor",        parseAnchor),
}

STYLE_NAMES = frozenset(list(STYLES.keys()) + ['color',])
STYLES_FONT = frozenset(('font-family','font-size','text-anchor'))

class Renderer:
    LINK = '{http://www.w3.org/1999/xlink}href'

    SVG_DEFS        = '{http://www.w3.org/2000/svg}defs'
    SVG_ROOT        = '{http://www.w3.org/2000/svg}svg'
    SVG_A           = '{http://www.w3.org/2000/svg}a'
    SVG_G           = '{http://www.w3.org/2000/svg}g'
    SVG_SYMBOL      = '{http://www.w3.org/2000/svg}symbol'
    SVG_USE         = '{http://www.w3.org/2000/svg}use'
    SVG_RECT        = '{http://www.w3.org/2000/svg}rect'
    SVG_CIRCLE      = '{http://www.w3.org/2000/svg}circle'
    SVG_ELLIPSE     = '{http://www.w3.org/2000/svg}ellipse'
    SVG_LINE        = '{http://www.w3.org/2000/svg}line'
    SVG_POLYLINE    = '{http://www.w3.org/2000/svg}polyline'
    SVG_POLYGON     = '{http://www.w3.org/2000/svg}polygon'
    SVG_PATH        = '{http://www.w3.org/2000/svg}path'
    SVG_TEXT        = '{http://www.w3.org/2000/svg}text'
    SVG_TSPAN       = '{http://www.w3.org/2000/svg}tspan'
    SVG_IMAGE       = '{http://www.w3.org/2000/svg}image'

    SVG_NODES = frozenset((SVG_ROOT, SVG_A, SVG_G, SVG_SYMBOL, SVG_USE, SVG_RECT,
                           SVG_CIRCLE, SVG_ELLIPSE, SVG_LINE, SVG_POLYLINE,
                           SVG_POLYGON, SVG_PATH, SVG_TEXT, SVG_IMAGE))

    def __init__(self, filename):
        self.filename = filename
        self.level = 0
        self.styles = {}
        self.mainGroup = Group()
        self.drawing = None
        self.root = None

    def render(self, node, parent = None):
        if parent == None:
            parent = self.mainGroup

        # ignore if display = none
        display = node.get('display')
        if display == "none":
            return

        if node.tag == self.SVG_ROOT:
            self.level += 1

            if not self.drawing is None:
                raise SVGError('drawing already created!')

            self.root = node

            # default styles
            style = {
                'color':'none',
                'fill':'none',
                'stroke':'none',
                'font-family':'Helvetica',
                'font-size':'12'
            }

            self.styles[self.level] = style

            # iterate children
            for child in node:
                self.render(child, self.mainGroup)

            # create drawing
            width = node.get('width', '100%')
            height = node.get('height', '100%')

            if node.get("viewBox"):
                try:
                    minx, miny, width, height = node.get("viewBox").split()
                except ValueError:
                    raise SVGError("viewBox values not valid")

            if width.endswith('%') and height.endswith('%'):
                # handle relative size
                wscale = parseLength(width) / 100.
                hscale = parseLength(height) / 100.

                xL,yL,xH,yH =  self.mainGroup.getBounds()
                self.drawing = Drawing(xH*wscale + xL, yH*hscale + yL)

            else:
                self.drawing = Drawing(parseLength(width), parseLength(height))

            height = self.drawing.height
            self.mainGroup.scale(1, -1)
            self.mainGroup.translate(0, -height)
            self.drawing.add(self.mainGroup)

            self.level -= 1

            return self.drawing

        elif node.tag in (self.SVG_G, self.SVG_A, self.SVG_SYMBOL):
            self.level += 1

            # set this levels style
            style = self.styles[self.level - 1].copy()
            style = self.nodeStyle(node, style)
            self.styles[self.level] = style

            group = Group()

            # iterate children
            for child in node:
                self.render(child, group)

            parent.add(group)

            transforms = node.get('transform')
            if transforms:
                for op in parseTransform.iterparse(transforms):
                    self.applyTransformOnGroup(group, op)

            self.level -= 1

        elif node.tag == self.SVG_USE:
            self.level += 1

            # set this levels style
            style = self.styles[self.level - 1].copy()
            style = self.nodeStyle(node, style)
            self.styles[self.level] = style

            group = Group()

            # link id
            link_id = node.get(self.LINK).lstrip('#')

            # find linked node in defs section
            target = None
            for defs in self.root.getiterator(self.SVG_DEFS):
                for element in defs:
                    if element.get('id') == link_id:
                        target = element
                        break

            if target is None:
                raise SVGError("Could not find use node '%s'" % link_id)

            self.render(target, group)

            parent.add(group)

            # apply transform
            transforms = node.get('transform')
            if transforms:
                for op in parseTransform.iterparse(transforms):
                    self.applyTransformOnGroup(group, op)

            # apply 'x' and 'y' attribute as translation of defs object
            if node.get('x') or node.get('y'):
                dx = parseLength(node.get('x','0'))
                dy = parseLength(node.get('y','0'))

                self.applyTransformOnGroup(group, ('translate', (dx,dy)))

            self.level -= 1

        elif node.tag == self.SVG_LINE:
            # get coordinates
            x1 = parseLength(node.get('x1', '0'))
            y1 = parseLength(node.get('y1', '0'))
            x2 = parseLength(node.get('x2', '0'))
            y2 = parseLength(node.get('y2', '0'))

            shape = Line(x1, y1, x2, y2)
            self.addShape(parent, node, shape)

        elif node.tag == self.SVG_RECT:
            # get coordinates
            x = parseLength(node.get('x', '0'))
            y = parseLength(node.get('y', '0'))
            width = parseLength(node.get('width'))
            height = parseLength(node.get('height'))

            rx = parseLength(node.get('rx', '0'))
            ry = parseLength(node.get('ry', '0'))

            shape = Rect(x, y, width, height, rx=rx, ry=ry)
            self.addShape(parent, node, shape)

        elif node.tag == self.SVG_CIRCLE:
            cx = parseLength(node.get('cx', '0'))
            cy = parseLength(node.get('cy', '0'))
            r = parseLength(node.get('r'))

            if r > 0.:
                shape = Circle(cx, cy, r)
                self.addShape(parent, node, shape)

        elif node.tag == self.SVG_ELLIPSE:
            cx = parseLength(node.get('cx', '0'))
            cy = parseLength(node.get('cy', '0'))
            rx = parseLength(node.get('rx'))
            ry = parseLength(node.get('ry'))

            if rx > 0. and ry > 0.:
                shape = Ellipse(cx, cy, rx, ry)
                self.addShape(parent, node, shape)

        elif node.tag == self.SVG_POLYLINE:
            # convert points
            points = node.get('points').strip()
            if len(points) == 0:
                return

            points = map(parseLength, re.split('[ ,]+', points))

            # Need to use two shapes, because standard RLG polylines
            # do not support filling...
            group = Group()
            shape = Polygon(points)
            self.applyStyleToShape(shape, node)
            shape.strokeColor = None
            group.add(shape)

            shape = PolyLine(points)
            self.applyStyleToShape(shape, node)
            group.add(shape)

            self.addShape(parent, node, group)

        elif node.tag == self.SVG_POLYGON:
            # convert points
            points = node.get('points').strip()
            if len(points) == 0:
                return

            points = map(parseLength, re.split('[ ,]+', points))

            shape = Polygon(points)
            self.addShape(parent, node, shape)

        elif node.tag == self.SVG_IMAGE:
            x = parseLength(node.get('x', '0'))
            y = parseLength(node.get('y', '0'))
            width = parseLength(node.get('width', '0'))
            height = parseLength(node.get('height', '0'))

            # link id
            link_id = node.get(self.LINK)

            filename = os.path.join(os.path.dirname(self.filename), link_id)
            shape = Image(x, y, width, height, filename)

            self.addShape(parent, node, shape)

        elif node.tag == self.SVG_TEXT:
            # Todo:
            # - rotation not handled
            # - baseshift not handled
            # - embedded span node not handled
            #
            def parsePos(node, subnode, name, default = '0'):
                values = subnode.get(name)
                if values is None:
                    if not node is None:
                        values = node.get(name, default)
                    else:
                        values = default

                return map(parseLength, values.split())

            def getPos(values, i, default = None):
                if i >= len(values):
                    if default is None:
                        return values[-1]
                    else:
                        return default
                else:
                    return values[i]

            def handleText(node, subnode, text):
                # get position variables
                xs = parsePos(node, subnode, 'x')
                dxs = parsePos(node, subnode, 'dx')
                ys = parsePos(node, subnode,'y')
                dys = parsePos(node, subnode,'dy')

                if sum(map(len, (xs,ys,dxs,dys))) == 4:
                    # single value
                    shape = String(xs[0] + dxs[0], -ys[0] - dys[0], text)
                    self.applyStyleToShape(shape, subnode)
                    group.add(shape)

                else:
                    # multiple values
                    for i,c in enumerate(text):
                        x = getPos(xs, i)
                        dx = getPos(dxs, i, 0)
                        y = getPos(ys, i)
                        dy = getPos(dys, i, 0)

                        shape = String(x + dx, -y -dy, c)
                        self.applyStyleToShape(shape, subnode)
                        group.add(shape)

            if node.text and node.text.strip():
                group = Group()

                handleText(None, node, node.text.strip())

                group.scale(1, -1)

                self.addShape(parent, node, group)

            if len(node) > 0:
                group = Group()

                self.level += 1

                # set this levels style
                style = self.styles[self.level - 1].copy()
                nodestylestyle = self.nodeStyle(node, style)
                self.styles[self.level] = nodestylestyle

                for subnode in node:
                    if subnode.tag == self.SVG_TSPAN:
                        handleText(node, subnode, subnode.text.strip())

                self.level -= 1

                group.scale(1, -1)
                self.addShape(parent, node, group)


        elif node.tag == self.SVG_PATH:
            def convertQuadratic(Q0, Q1, Q2):
                C1 = (Q0[0] + 2./3*(Q1[0] - Q0[0]), Q0[1] + 2./3*(Q1[1] - Q0[1]))
                C2 = (C1[0] + 1./3*(Q2[0] - Q0[0]), C1[1] + 1./3*(Q2[1] - Q0[1]))
                C3 = Q2
                return C1[0], C1[1], C2[0], C2[1], C3[0], C3[1]

            def prevCtrl(lastOp, lastArgs, currentX, currentY):
                # fetch last controll point
                if lastOp in 'CScsQqTt':
                    x, y = lastArgs[-2]

                    # mirror about current point
                    return currentX + (currentX-x), currentY + (currentY-y)

                else:
                    # defaults to current point
                    return currentX, currentY

            # store sub paths in 'paths' list
            shape = Path()

            # keep track of current point and path start point
            startX, startY = 0.,0.
            currentX, currentY = 0.,0.

            # keep track of last operation
            lastOp = None
            lastArgs = None

            # avoid empty path data
            data = node.get('d')
            if data is None or len(data) == 0:
                return

            for op, args in parsePath.iterparse(data):
                if op == 'z' or op == 'Z':
                    # close path or subpath
                    shape.closePath()

                    # next sub path starts at begining of current path
                    currentX, currentY = startX, startY

                elif op == 'M':
                    # moveto absolute
                    if not lastOp is None and lastOp not in ('z', 'Z'):
                        # close sub path
                        shape.closePath()

                    x, y = args[0]
                    shape.moveTo(x, y)

                    startX, startY = x, y

                    # multiple moveto arge result in line
                    for x, y in args[1:]:
                        shape.lineTo(x, y)

                    currentX, currentY = x, y

                elif op == 'm':
                    if not lastOp is None and lastOp not in ('z', 'Z'):
                        # close sub path
                        shape.closePath()

                    # moveto relative
                    rx, ry = args[0]
                    x, y = currentX + rx, currentY + ry
                    shape.moveTo(x, y)

                    startX, startY = x, y
                    currentX, currentY = x, y

                    # multiple moveto arge result in line
                    for rx, ry in args[1:]:
                        x, y = currentX + rx, currentY + ry
                        shape.lineTo(x, y)
                        currentX, currentY = x, y

                elif op == 'L':
                    # lineto absolute
                    for x,y in args:
                        shape.lineTo(x, y)

                    currentX, currentY = x, y

                elif op == 'l':
                    # lineto relative
                    for rx,ry in args:
                        x, y = currentX + rx, currentY + ry
                        shape.lineTo(x, y)
                        currentX, currentY = x, y

                elif op == 'V':
                    # vertical line absolute
                    for y in args:
                        shape.lineTo(currentX, y)

                    currentY = y

                elif op == 'v':
                    # vertical line relative
                    for ry in args:
                        y = currentY + ry
                        shape.lineTo(currentX, y)
                        currentY = y

                elif op == 'H':
                    # horisontal line absolute
                    for x in args:
                        shape.lineTo(x, currentY)

                    currentX = x

                elif op == 'h':
                    # horisontal line relative
                    for rx in args:
                        x = currentX + rx
                        shape.lineTo(x, currentY)

                    currentX = x

                elif op == 'C':
                    # cubic bezier absolute
                    for i in range(len(args)//3):
                        x1, y1 = args[i*3 + 0]
                        x2, y2 = args[i*3 + 1]
                        x3, y3 = args[i*3 + 2]

                        shape.curveTo(x1, y1, x2, y2, x3, y3)

                    currentX, currentY = x3, y3

                elif op == 'c':
                    # cubic bezier relative
                    for i in range(len(args)//3):
                        x1, y1 = args[i*3 + 0]
                        x1, y1 = x1 + currentX, y1 + currentY

                        x2, y2 = args[i*3 + 1]
                        x2, y2 = x2 + currentX, y2 + currentY

                        x3, y3 = args[i*3 + 2]
                        x3, y3 = x3 + currentX, y3 + currentY

                        shape.curveTo(x1, y1, x2, y2, x3, y3)

                        currentX, currentY = x3, y3

                    lastOp = op
                    lastArgs = (x1, y1), (x2, y2), (x3, y3)
                    continue

                elif op == 'S':
                    # shorthand cubic bezier absolute
                    for i in range(len(args)//2):
                        x1, y1 = prevCtrl(lastOp, lastArgs, currentX, currentY)

                        x2, y2 = args[i*2 + 0]
                        x3, y3 = args[i*2 + 1]

                        shape.curveTo(x1, y1, x2, y2, x3, y3)

                        lastOp = op
                        lastArgs = (x2, y2), (x3, y3)

                        currentX, currentY = x3, y3

                    continue

                elif op == 's':
                    # shorthand cubic bezier relative
                    for i in range(len(args)//2):
                        x1, y1 = prevCtrl(lastOp, lastArgs, currentX, currentY)

                        x2, y2 = args[i*2 + 0]
                        x2, y2 = x2 + currentX, y2 + currentY

                        x3, y3 = args[i*2 + 1]
                        x3, y3 = x3 + currentX, y3 + currentY

                        shape.curveTo(x1, y1, x2, y2, x3, y3)

                        currentX, currentY = x3, y3

                        lastOp = op
                        lastArgs = (x1, y1), (x2, y2), (x3, y3)

                    continue

                elif op == 'Q':
                    # quadratic bezier absolute
                    for i in range(len(args)//2):
                        x1, y1 = currentX, currentY
                        x2, y2 = args[i*2 + 0]
                        x3, y3 = args[i*2 + 1]

                        ctrls = convertQuadratic((x1, y1), (x2, y2), (x3, y3))

                        shape.curveTo(*ctrls)

                        currentX, currentY = x3, y3

                    lastOp = op
                    lastArgs = (x2, y2), (x3, y3)
                    continue

                elif op == 'q':
                    # quadratic bezier relative
                    for i in range(len(args)//2):
                        x1, y1 = currentX, currentY

                        x2, y2 = args[i*2 + 0]
                        x2, y2 = x2 + currentX, y2 + currentY

                        x3, y3 = args[i*2 + 1]
                        x3, y3 = x3 + currentX, y3 + currentY

                        ctrls = convertQuadratic((x1, y1), (x2, y2), (x3, y3))

                        shape.curveTo(*ctrls)
                        currentX, currentY = x3, y3

                    lastOp = op
                    lastArgs = (x2, y2), (x3, y3)
                    continue

                elif op == 'T':
                    # shorthand quadratic bezier absolute
                    for i in range(len(args)):
                        x1, y1 = currentX, currentY
                        x2, y2 = prevCtrl(lastOp, lastArgs, currentX, currentY)
                        x3, y3 = args[i]

                        ctrls = convertQuadratic((x1, y1), (x2, y2), (x3, y3))
                        shape.curveTo(*ctrls)

                        currentX, currentY = x3, y3

                        lastOp = op
                        lastArgs = (x2, y2), (x3, y3)

                    continue


                elif op == 't':
                    # shorthand quadratic bezier relative
                    for i in range(len(args)):
                        x1, y1 = currentX, currentY
                        x2, y2 = prevCtrl(lastOp, lastArgs, currentX, currentY)

                        x3, y3 = args[i]
                        x3, y3 = x3 + currentX, y3 + currentY

                        ctrls = convertQuadratic((x1, y1), (x2, y2), (x3, y3))
                        shape.curveTo(*ctrls)

                        currentX, currentY = x3, y3

                        lastOp = op
                        lastArgs = (x2, y2), (x3, y3)

                    continue

                elif op == 'A' or op == 'a':
                    # elliptic arc missing
                    continue

                lastOp = op
                lastArgs = args

            # check if fill applies to path
            fill = None
            if node.get('fill'):
                # inline style
                fill = node.get('fill')
            else:
                # try local style
                if node.get('style'):
                    style = parseStyle.parse(node.get('style'))

                    if 'fill' in style:
                        fill = style['fill']

                # try global style
                if fill is None:
                    style = self.styles[self.level]

                    if 'fill' in style:
                        fill = style['fill']
                    else:
                        fill = 'none'

            # hack because RLG has no "semi-closed" paths...
            if lastOp == 'z' or lastOp == 'Z' or fill == 'none':
                self.addShape(parent, node, shape)

            else:
                group = Group()

                strokeshape = shape.copy()
                self.addShape(group, node, strokeshape, fill = 'none')

                shape.closePath()
                self.addShape(group, node, shape, stroke = 'none')

                self.addShape(parent, node, group)


    def addShape(self, parent, node, shape, **kwargs):

        self.applyStyleToShape(shape, node, **kwargs)

        transform = node.get('transform')
        if transform:
            # transform can only be applied to a group
            if isinstance(node, Group):
                group = node
            else:
                group = Group()

            for op in parseTransform.iterparse(transform):
                self.applyTransformOnGroup(group, op)

            if not isinstance(node, Group):
                group.add(shape)

            parent.add(group)

        else:
            parent.add(shape)

        return shape

    def nodeStyle(self, node, style = None):
        if style is None:
            style = {}

        # update with local style
        if node.get('style'):
            localstyle = parseStyle.parse(node.get('style'))
            for name, value in six.iteritems(localstyle):
                style[name] = value

        # update with inline style
        for name in STYLE_NAMES:
            value = node.get(name)
            if value:
                style[name] = value

        return style

    def applyStyleToShape(self, shape, node, **kwargs):
        # fetch global styles for this level
        globalstyle = self.styles[self.level]

        # update with node style
        localstyle = self.nodeStyle(node)

        for name in STYLES:
            # avoid text styles if not a String subclass
            if not isinstance(shape, String) and name in STYLES_FONT:
                continue

            value = None
            if name in kwargs:
                value = kwargs[name]
            elif name in localstyle:
                value = localstyle[name]
            elif name in globalstyle:
                value = globalstyle[name]
            else:
                continue

            # handle 'currentColor'
            if value == 'currentColor':
                if 'color' in localstyle:
                    value = localstyle['color']
                elif 'color' in globalstyle:
                    value = globalstyle['color']

            # fetch shape attribute name and converter
            attrname, converter = STYLES[name]

            # Sett attribute of shape
            if hasattr(shape, attrname):
                setattr(shape, attrname, converter(value))

        # defaults
        if isinstance(shape, String):
            if shape.fillColor is None:
                shape.fillColor = colors.black

        elif isinstance(shape, (Line, PolyLine)):
            if shape.strokeColor is None:
                shape.strokeColor = colors.black

        elif isinstance(shape, (Rect, Circle, Ellipse, Polygon)):
            if shape.fillColor is None and shape.strokeColor is None:
                shape.strokeColor = colors.black

    def applyTransformOnGroup(self, group, transform):
        op, args = transform

        if op == 'scale':
            group.scale(*args)

        elif op == 'translate':
            group.translate(*args)

        elif op == 'rotate':
            if len(args) == 2:
                angle, center = args
                if center:
                    cx, cy = center
                    group.translate(cx, cy)
                    group.rotate(angle)
                    group.translate(-cx, -cy)
                else:
                    group.rotate(angle)

        elif op == "skewX":
            angle = args[0]
            group.skew(angle, 0)

        elif op == "skewY":
            angle = args[0]
            group.skew(0, angle)

        elif op == "matrix":
            group.transform = mmult(group.transform, args)

def readFile(filename):
    """
    Open svg file and return root xml object
    """
    GZIPMAGIC = '\037\213'

    try:
        fh = open(filename, 'rb')
    except IOError:
        raise SVGError("could not open file '%s' for reading" % filename)

    # test for gzip compression
    magic = fh.read(2)
    fh.close()

    if magic == GZIPMAGIC:
        svg = cElementTree.parse(GzipFile(filename, 'r'))
    else:
        svg = cElementTree.parse(filename)

    root = svg.getroot()

    if not root.tag == Renderer.SVG_ROOT:
        raise SVGError("Expected SVG fragment as root object")

    return root

def svg2rlg(filename):
    """
    Open svg file and return reportlab drawing object
    """
    xml = readFile(filename)
    renderer = Renderer(filename)

    return renderer.render(xml)

if __name__ == "__main__":
    import sys
    import os

    #sys.argv.append('compliance/paths-data-15-t.svg')

    source = sys.argv[1]
    path, filename = os.path.split(source)
    name, ext = os.path.splitext(filename)

    drawing = svg2rlg(source)
    drawing.save(formats=['pdf'],outDir='.',fnRoot=name)

    os.startfile(name + '.pdf')
