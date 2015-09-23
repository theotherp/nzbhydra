import unittest
import profig


class Ex1(Exception):
    pass


class Ex2(Exception):
    pass

try:
    raise Ex1()
except Ex1:
    print("Caught ex1 and will raise 2")
    raise Ex2()
except Ex2:
    print("Caught ex2")