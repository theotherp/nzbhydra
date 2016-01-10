import unittest

class TestVersioning(unittest.TestCase):
    
    def versiontuple(self, v):
        filled = []
        for point in v.split("."):
            filled.append(point.zfill(8))
        return tuple(filled)

    def testFindMovieIds(self):
        a = self.versiontuple("0.0.1a15")
        b = self.versiontuple("0.0.1b15")
        c = self.versiontuple("0.0.2a15")
        d = self.versiontuple("0.0.3a23")
        e = self.versiontuple("0.1.1a15")
        f = self.versiontuple("2.0.1a15")
        g = self.versiontuple("2.0.1b15")
        h = self.versiontuple("2.0.1b25")
        i = self.versiontuple("2.0.2b25")
        assert a < b
        assert b < c
        assert c < d
        assert d < e
        assert e < f
        assert f < g
        assert g < h
        assert h < i

            