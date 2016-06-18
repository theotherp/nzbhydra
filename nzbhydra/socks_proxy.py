# coding=utf-8


# Module for SOCKS support

# Function to set the SOCKS proxy
# Returns public IP address via SOCKS proxy (if succesful), None otherwise

def setSOCKSproxy(sockshost,socksport):
    import socket
    import urllib2

    try:
        import socks # Tip: "sudo pip install PySocks"
    except:
        print "Python module 'socks' not found. Not setting SOCKS proxy."
        return None
    
    socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS5, sockshost, socksport)
    socket.socket = socks.socksocket

    try:
        return urllib2.urlopen('http://ipinfo.io/ip').read().rstrip()
    except:
        return None

