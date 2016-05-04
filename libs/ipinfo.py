#!/usr/bin/env python

# Gets info on IP address (IPv4 or IPv6) from http://ipinfo.io/
# Source: https://github.com/sanderjo/ipinfo.git
# GPL3

'''
Based on this public API from http://ipinfo.io/ :

$ curl http://ipinfo.io/31.21.30.159/json
{
  "ip": "31.21.30.159",
  "hostname": "No Hostname",
  "city": "",
  "region": "",
  "country": "NL",
  "loc": "52.3667,4.9000",
  "org": "AS31615 T-mobile Netherlands bv."
}
'''

import json
import urllib
import re
baseurl = 'http://ipinfo.io/'    # no HTTPS supported (at least: not without a plan)



def ispublic(ipaddress):
    return not isprivate(ipaddress)

def isprivate(ipaddress):

    if ipaddress.startswith("::ffff:"): 
        ipaddress=ipaddress.replace("::ffff:", "")

    # IPv4 Regexp from https://stackoverflow.com/questions/30674845/
    if re.search(r"^(?:10|127|172\.(?:1[6-9]|2[0-9]|3[01])|192\.168)\..*", ipaddress):
        # Yes, so match, so a local or RFC1918 IPv4 address
        return True

    if ipaddress == "::1":
        # Yes, IPv6 localhost
        return True

    return False


def getall(ipaddress):
    url = '%s%s/json' % (baseurl, ipaddress)
    try:
        urlresult = urllib.urlopen(url)
        jsonresult = urlresult.read()          # get the JSON
        parsedjson = json.loads(jsonresult)    # put parsed JSON into dictionary
        return parsedjson
    except:
        return None


def country_and_org(ipaddress):
    allinfo = getall(ipaddress)    # one lookup
    try:
        # FYI: the first word in allinfo['org'] is the ASN, which we skip
        return allinfo['country'] + ' --- ' + allinfo['org'].split(' ', 1)[1]
    except:
        return ""

def country_and_org_as_list(ipaddress):
    allinfo = getall(ipaddress)    # one lookup
    try:
        # FYI: the first word in allinfo['org'] is the ASN, which we skip
        return [ allinfo['country'], allinfo['org'].split(' ', 1)[1] ]
    except:
        return ['','']

if __name__ == '__main__':

    # Some examples:

    print getall('31.21.30.159')
    print country_and_org('31.21.30.159')

    print getall('192.168.0.1')
    print country_and_org('192.168.0.1')

    print country_and_org('2a00:1450:4013:c01::64')
    print country_and_org('::ffff:194.109.6.92')

    print ' --- '.join(country_and_org_as_list('31.21.30.159'))
    print ' --- '.join(country_and_org_as_list('31.21.30.'))





