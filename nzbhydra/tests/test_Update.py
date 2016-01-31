import os
import unittest
class TestVersioning(unittest.TestCase):
    
    def versiontuple(self, v):
        filled = []
        for point in v.split("."):
            filled.append(point.zfill(8))
        return tuple(filled)

    def testCompareVersions(self):
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

    
    def testThatVersionAndChangelogContainSameVersion(self):
        main_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        changelogMd = os.path.join(main_dir, "changelog.md")
        with open(changelogMd, "r") as f:
            changelog = f.read()
        versionTxt = os.path.join(main_dir, "version.txt")
        with open(versionTxt, "r") as f:
            version = f.read()
        versionInChangelog = changelog[changelog.index("###"):changelog.index("###") + 20]
        #Very crude but hey, it works
        assert version in versionInChangelog
        
        
    