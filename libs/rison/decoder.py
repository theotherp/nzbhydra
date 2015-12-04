# encoding: utf-8

import re

from constants import NEXT_ID_RE, WHITESPACE


class ParserException(Exception):
    pass


class Parser(object):

    def __init__(self):
        self.string = None
        self.index = 0

    """
    This parser supports RISON, RISON-A and RISON-O.
    """
    def parse(self, string, format=str):
        if format in [list, 'A']:
            self.string = "!({0})".format(string)
        elif format in [dict, 'O']:
            self.string = "({0})".format(string)
        elif format is str:
            self.string = string
        else:
            raise ValueError("""Parse format should be one of str, list, dict,
                'A' (alias for list), '0' (alias for dict).""")

        self.index = 0

        value = self.read_value()
        if self.next():
            raise ParserException("unable to parse rison string %r" % (string,))
        return value

    def read_value(self):
        c = self.next()

        if c == '!':
            return self.parse_bang()
        if c == '(':
            return self.parse_open_paren()
        if c == "'":
            return self.parse_single_quote()
        if c in '-0123456789':
            return self.parse_number()

        # fell through table, parse as an id
        s = self.string
        i = self.index-1

        m = NEXT_ID_RE.match(s, i)
        if m:
            _id = m.group(0)
            self.index = i + len(_id)
            return _id

        if c:
            raise ParserException("invalid character: '" + c + "'")
        raise ParserException("empty expression")

    def parse_array(self):
        ar = []
        while 1:
            c = self.next()
            if c == ')':
                return ar

            if c is None:
                raise ParserException("unmatched '!('")

            if len(ar):
                if c != ',':
                    raise ParserException("missing ','")
            elif c == ',':
                raise ParserException("extra ','")
            else:
                self.index -= 1
            n = self.read_value()
            ar.append(n)

        return ar

    def parse_bang(self):
        s = self.string
        c = s[self.index]
        self.index += 1
        if c is None:
            raise ParserException('"!" at end of input')
        if c not in self.bangs:
            raise ParserException('unknown literal: "!' + c + '"')
        x = self.bangs[c]
        if callable(x):
            return x(self)

        return x

    def parse_open_paren(self):
        count = 0
        o = {}

        while 1:
            c = self.next()
            if c == ')':
                return o
            if count:
                if c != ',':
                    raise ParserException("missing ','")
            elif c == ',':
                raise ParserException("extra ','")
            else:
                self.index -= 1
            k = self.read_value()

            if self.next() != ':':
                raise ParserException("missing ':'")
            v = self.read_value()

            o[k] = v
            count += 1

    def parse_single_quote(self):
        s = self.string
        i = self.index
        start = i
        segments = []

        while 1:
            if i >= len(s):
                raise ParserException('unmatched "\'"')

            c = s[i]
            i += 1
            if c == "'":
                break

            if c == '!':
                if start < i-1:
                    segments.append(s[start:i-1])
                c = s[i]
                i += 1
                if c in "!'":
                    segments.append(c)
                else:
                    raise ParserException('invalid string escape: "!'+c+'"')

                start = i

        if start < i-1:
            segments.append(s[start:i-1])
        self.index = i
        return ''.join(segments)

    # Also any number start (digit or '-')
    def parse_number(self):
        s = self.string
        i = self.index
        start = i-1
        state = 'int'
        permitted_signs = '-'
        transitions = {
            'int+.': 'frac',
            'int+e': 'exp',
            'frac+e': 'exp'
        }

        while 1:
            if i >= len(s):
                i += 1
                break

            c = s[i]
            i += 1

            if '0' <= c <= '9':
                continue

            if permitted_signs.find(c) >= 0:
                permitted_signs = ''
                continue

            state = transitions.get(state + '+' + c.lower(), None)
            if state is None:
                break
            if state == 'exp':
                permitted_signs = '-'

        self.index = i - 1
        s = s[start:self.index]
        if s == '-':
            raise ParserException("invalid number")
        if re.search('[.e]', s):
            return float(s)
        return int(s)

    # return the next non-whitespace character, or undefined
    def next(self):
        s = self.string
        i = self.index
        c = None

        while 1:
            if i == len(s):
                return None
            c = s[i]
            i += 1
            if c not in WHITESPACE:
                break

        self.index = i
        return c

    bangs = {
        't': True,
        'f': False,
        'n': None,
        '(': parse_array
    }


def loads(s, format=str):
    return Parser().parse(s, format=format)
