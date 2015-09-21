import unittest
import profig


class MyTestCase(unittest.TestCase):
    
    def testProfigLists(self):
        cfg = profig.Config()
        cfg["a.list.test"] = ["a", "b"]
        cfg.write("test")
        print(cfg["test"])
    