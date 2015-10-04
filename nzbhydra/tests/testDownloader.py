
def testThatNzbGetTestWorks():
    from nzbhydra.downloader import Nzbget
    nzbget = Nzbget()
    assert nzbget.test()