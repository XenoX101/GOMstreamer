# -*- coding: utf-8 -*-

'''
Copyright 2010 Simon Potter, Tomáš Heřman

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

 http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
'''

import urllib2
import cookielib
import urllib
import StringIO
import re
import os
import sys
from optparse import OptionParser
from string import Template
def main():

    global debug
    debug = False  # Set this to true to print debugging information

    # Application locations and parameters for different operating systems.
    # May require changing on OSX, can't test.
    vlcOSX = '/Applications/VLC.app/Contents/MacOS/VLC "--http-caching=$cache" "$url"'
    vlcLinux = 'vlc "--http-caching=$cache" "$url"'

    # Collecting options parsed in from the command line
    parser = OptionParser()
    parser.add_option("-p", "--password", dest = "password", help = "Password to your GomTV account")
    parser.add_option("-e", "--email", dest = "email", help = "Email your GomTV account uses")
    parser.add_option("-b", action = "store_true", dest = "hq", help = "Use better quality stream")
    parser.add_option("-s", action = "store_false", dest = "hq", help = "Use lower quality stream (Default)")
    parser.add_option("-c", "--command", dest = "command", help = "Custom command to run")
    parser.add_option("-d", "--buffer-time", dest = "cache", help = "Cache size in [ms]")

    # Setting parameters
    parser.set_defaults(hq = False)  # I don't have a premium account to test otherwise

    # Determining which VLC command to use based on the OS that this script is being run on
    if os.uname()[0] == 'Darwin':
        parser.set_defaults(command = vlcOSX)
    else:
        parser.set_defaults(command = vlcLinux)

    parser.set_defaults(cache = 30000)  # Caching 30s by default
    (options, args) = parser.parse_args()

    # Stopping if email and password are defaults found in run.sh
    if options.email == "youremail@example.com" and options.password == "PASSWORD":
        print "Enter in your GOMtv email and password into run.sh."
        print "This script will not work correctly without a valid account."
        sys.exit(1)

    gomtvURL = "http://www.gomtv.net"
    gomtvLiveURL = gomtvURL + "/2011gslsponsors1/live/"
    gomtvSignInURL = gomtvURL + "/user/loginCheck.php"
    values = {
             'cmd': 'login',
             'returl': '%2F',
             'mb_username': options.email,
             'mb_password': options.password
             }

    data = urllib.urlencode(values)
    cookiejar = cookielib.LWPCookieJar()
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookiejar))

    # Signing into GOMTV
    request = urllib2.Request(gomtvSignInURL, data)
    urllib2.install_opener(opener)
    response = urllib2.urlopen(request)

    # Collecting data on the Live streaming page
    request = urllib2.Request(gomtvLiveURL)
    response = urllib2.urlopen(request)
    urls = parseURLs(response.read())

    if len(urls) == 0:
        print "Unable to find URLs on the Live streaming page. Is the stream available?"
        sys.exit(404)  # Giving a status of 404 due to no streams found

    if debug:
        print "Printing URLs on Live page:"
        print urls
        print ""

    # If we can use the HQ stream URL, use that instead of the SQ stream
    if options.hq:
        url = parseHQStreamURL(urls)
    else:
        url = parseSQStreamURL(urls)

    if url == None:
        print "Unable to parse the stream URL from the set of URLs."
        print "This may have occurred if you chose an HQ stream without a"
        print "premium account."

        if debug:
            print "urls:"
            print urls
            print "Stream URL:", url

        sys.exit(1)

    if debug:
        print "Printing the listed stream url"
        print url
        print ""

    # Grab the response of the URL listed on the Live page for a stream
    request = urllib2.Request(url)
    response = urllib2.urlopen(request)
    responseData = response.read()

    if debug:
        print "Response:"
        print responseData
        print ""

    # Find out the URL found in the response
    url = parseStreamURL(responseData)

    if url == None:
        print "Unable to parse the URL to find the HTTP video stream."
        print "url:", url
        print ""
        sys.exit(1)

    command = Template(options.command)
    commandArgs = {
                  'cache': options.cache,
                  'url': url
                  }
    cmd = command.substitute(commandArgs)

    print "Stream URL:", url
    print ""
    print "VLC command:", cmd
    print ""
    print "Playing stream via VLC..."
    os.system(cmd)

def parseURLs(response):

    if debug:
        print "Response:"
        print response
        print ""

    patternGOMCMD = r"gomcmd://[^;]+;"
    commands = re.findall(patternGOMCMD, response)
    return map(parseHTTPofCmd, commands)

def parseHTTPofCmd(item):
    patternHTTP = r"(http://[^;]+)';"
    return re.search(patternHTTP, item).group(1)

# Probably works, can't test though
def parseHQStreamURL(urls):
    hqStreamPattern = r".*HQ.*"
    return parseStreamFileURL(urls, hqStreamPattern)

def parseSQStreamURL(urls):
    lqStreamPattern = r".*SQ.*"
    return parseStreamFileURL(urls, lqStreamPattern)

def parseStreamFileURL(urls, pattern):
    for url in urls:
        if re.match(pattern, url):
            return url

def parseStreamURL(response):

    streamPattern = r'<REF href= "([^"]*)"/>'
    regexResult = re.search(streamPattern, response).group(1)

    # Collected the gomcmd URL, now need to extract the correct HTTP URL
    # from the string
    patternHTTP = r"(http%3a.+)&quot;"
    regexResult = re.search(patternHTTP, regexResult).group(0)

    # Found URL, just need to fix URL characters
    regexResult = re.sub(r'%3[Aa]', ':', regexResult) # Fixing :
    regexResult = re.sub(r'%3[Ff]', '?', regexResult) # Fixing ?
    regexResult = re.sub(r'%3[Dd]', '=', regexResult) # Fixing =
    regexResult = re.sub(r'%26', '&', regexResult) # Fixing &
    regexResult = re.sub(r'%2[Ff]', '/', regexResult) # Fixing /
    regexResult = re.sub(r'&amp;', '&', regexResult) # Removing amp;
    regexResult = re.sub(r'&quot;', '', regexResult) # Removing &quot;
    return regexResult

# Actually run the script
if __name__ == "__main__":
    main()
