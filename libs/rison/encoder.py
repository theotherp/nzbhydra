import re

from utils import quote
from constants import ID_OK_RE


class Encoder(object):

    def __init__(self):
        pass

    @staticmethod
    def encoder(v):
        if isinstance(v, list):
            return Encoder.list
        elif isinstance(v, (str, basestring)):
            return Encoder.string
        elif isinstance(v, bool):
            return Encoder.bool
        elif isinstance(v, (float, int)):
            return Encoder.number
        elif isinstance(v, type(None)):
            return Encoder.none
        elif isinstance(v, dict):
            return Encoder.dict
        else:
            raise AssertionError('Unable to encode type: {0}'.format(type(v)))

    @staticmethod
    def encode(v):
        encoder = Encoder.encoder(v)
        return encoder(v)

    @staticmethod
    def list(x):
        a = ['!(']
        b = None
        for i in range(len(x)):
            v = x[i]
            f = Encoder.encoder(v)
            if f:
                v = f(v)
                if isinstance(v, (str, basestring)):
                    if b:
                        a.append(',')
                    a.append(v)
                    b = True
        a.append(')')
        return ''.join(a)

    @staticmethod
    def number(v):
        return str(v).replace('+', '')

    @staticmethod
    def none(_):
        return '!n'

    @staticmethod
    def bool(v):
        return '!t' if v else '!f'

    @staticmethod
    def string(v):
        if v == '':
            return "''"

        if ID_OK_RE.match(v):
            return v

        def replace(match):
            if match.group(0) in ["'", '!']:
                return '!' + match.group(0)
            return match.group(0)

        v = re.sub(r'([\'!])', replace, v)

        return "'" + v + "'"

    @staticmethod
    def dict(x):
        a = ['(']
        b = None
        ks = sorted(x.keys())
        for i in ks:
            v = x[i]
            f = Encoder.encoder(v)
            if f:
                v = f(v)
                if isinstance(v, (str, basestring)):
                    if b:
                        a.append(',')
                    a.append(Encoder.string(i))
                    a.append(':')
                    a.append(v)
                    b = True

        a.append(')')
        return ''.join(a)


def encode_array(v):
    if not isinstance(v, list):
        raise AssertionError('encode_array expects a list argument')
    r = dumps(v)
    return r[2, len(r)-1]


def encode_object(v):
    if not isinstance(v, dict) or v is None or isinstance(v, list):
        raise AssertionError('encode_object expects an dict argument')
    r = dumps(v)
    return r[1, len(r)-1]


def encode_uri(v):
    return quote(dumps(v))


def dumps(string):
    return Encoder.encode(string)
