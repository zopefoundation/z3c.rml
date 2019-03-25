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
# FOR A PARTLAR PURPOSE.
#
##############################################################################
"""Testing Number2Words.
"""
import unittest
from z3c.rml import num2words


class Number2WordsTests(unittest.TestCase):

    def test_num2words(self):
        for item in NUM2WORDS.strip().splitlines():
            num, expected = item.split(' ', 1)
            out = num2words.num2words(int(num))
            self.assertEqual(out, expected)

    def test_num2words_ordinal(self):
        for item in NUM2WORDS_ORDINAL.strip().splitlines():
            num, expected = item.split(' ', 1)
            out = num2words.num2words(int(num), ordinal=True)
            self.assertEqual(out, expected)


NUM2WORDS = """
0 Zero
1 One
2 Two
3 Three
4 Four
5 Five
6 Six
7 Seven
8 Eight
9 Nine
10 Ten
11 Eleven
12 Twelve
13 Thirteen
14 Fourteen
15 Fifteen
16 Sixteen
17 Seventeen
18 Eighteen
19 Nineteen
20 Twenty
21 Twenty-One
22 Twenty-Two
23 Twenty-Three
24 Twenty-Four
25 Twenty-Five
26 Twenty-Six
27 Twenty-Seven
28 Twenty-Eight
29 Twenty-Nine
30 Thirty
31 Thirty-One
40 Forty
49 Forty-Nine
50 Fifty
56 Fifty-Six
60 Sixty
66 Sixty-Six
70 Seventy
74 Seventy-Four
80 Eighty
89 Eighty-Nine
90 Ninety
91 Ninety-One
99 Ninety-Nine
100 One Hundred
101 One Hundred One
102 One Hundred Two
103 One Hundred Three
104 One Hundred Four
201 Two Hundred One
302 Three Hundred Two
403 Four Hundred Three
504 Five Hundred Four
605 Six Hundred Five
706 Seven Hundred Six
807 Eight Hundred Seven
908 Nine Hundred Eight
999 Nine Hundred Ninety-Nine
1000 One Thousand
1001 One Thousand One
1111 One Thousand One Hundred Eleven
20000 Twenty Thousand
300000 Three Hundred Thousand
4000010 Four Million Ten
4242424242 Four Billion Two Hundred Forty-Two Million Four Hundred Twenty-Four Thousand Two Hundred Forty-Two
363636363636 Three Hundred Sixty-Three Billion Six Hundred Thirty-Six Million Three Hundred Sixty-Three Thousand Six Hundred Thirty-Six
"""

NUM2WORDS_ORDINAL = """
0 Zeroth
1 First
2 Second
3 Third
4 Fourth
5 Fifth
6 Sixth
7 Seventh
8 Eighth
9 Ninth
10 Tenth
11 Eleventh
12 Twelfth
13 Thirteenth
14 Fourteenth
15 Fifteenth
16 Sixteenth
17 Seventeenth
18 Eighteenth
19 Nineteenth
20 Twentieth
21 Twenty-First
22 Twenty-Second
23 Twenty-Third
24 Twenty-Fourth
25 Twenty-Fifth
26 Twenty-Sixth
27 Twenty-Seventh
28 Twenty-Eighth
29 Twenty-Ninth
30 Thirtieth
31 Thirty-First
40 Fortieth
49 Forty-Ninth
50 Fiftieth
56 Fifty-Sixth
60 Sixtieth
66 Sixty-Sixth
70 Seventieth
74 Seventy-Fourth
80 Eightieth
89 Eighty-Ninth
90 Ninetieth
91 Ninety-First
99 Ninety-Ninth
100 One Hundredth
101 One Hundred First
102 One Hundred Second
103 One Hundred Third
104 One Hundred Fourth
201 Two Hundred First
302 Three Hundred Second
403 Four Hundred Third
504 Five Hundred Fourth
605 Six Hundred Fifth
706 Seven Hundred Sixth
807 Eight Hundred Seventh
908 Nine Hundred Eighth
999 Nine Hundred Ninety-Ninth
1000 One Thousandth
1001 One Thousand First
1111 One Thousand One Hundred Eleventh
20000 Twenty Thousandth
300000 Three Hundred Thousandth
4000010 Four Million Tenth
4242424242 Four Billion Two Hundred Forty-Two Million Four Hundred Twenty-Four Thousand Two Hundred Forty-Second
363636363636 Three Hundred Sixty-Three Billion Six Hundred Thirty-Six Million Three Hundred Sixty-Three Thousand Six Hundred Thirty-Sixth
"""


def test_suite():
    suite = unittest.TestSuite([unittest.makeSuite(Number2WordsTests)])
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
