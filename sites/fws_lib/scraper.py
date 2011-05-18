################################################################################
################################################################################
#####################                                  #########################
#####################         Release Our Data         #########################
#####################                                  #########################
#####################       a HelloSilo Project        #########################
#####################       <ROD@hellosilo.com>        #########################
################################################################################
##                                                                            ##  
##     Copyright 2010                                                         ##
##                                                                            ##  
##         Parker Phinney   @gameguy43   <parker@madebyparker.com>            ##
##         Seth Woodworth   @sethish     <seth@sethish.com>                   ##
##                                                                            ##
##                                                                            ##
##     Licensed under the GPLv3 or later,                                     ##
##     see PERMISSION for copying permission                                  ##
##     and COPYING for the GPL License                                        ##
##                                                                            ##
################################################################################
################################################################################

import cookielib
import string
import urllib
import urllib2
import parser



def id_to_page_permalink(id):
    return "http://digitalmedia.fws.gov/cdm4/item_viewer.php?CISOROOT=/natdiglib&CISOPTR=" + str(id) + "&CISOBOX=1&REC=1"


'''
def get_me_a_cookie():
	# this post data doesn't seem to really matter, as long as it is correctly formed
	quicksearch_page_post_values = {
		'formaction':	'SEARCH',
		'illustrations':	'on',
		'keywords':	'liver',
		'keywordstext':	'liver',
		'photos':	'on',
		'searchtype':	'photo|illustration|video',
		'video':	'on',
	}
	urlopen = urllib2.urlopen
	Request = urllib2.Request
	cj = cookielib.LWPCookieJar()
	# This is a subclass of FileCookieJar
	# that has useful load and save methods

	# Now we need to get our Cookie Jar
	# installed in the opener;
	# for fetching URLs
	# we get the HTTPCookieProcessor
	# and install the opener in urllib2
	opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
	urllib2.install_opener(opener)
	# fake a user agent, some websites (like google) don't like automated exploration
	txheaders =  {'User-agent' : 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'}

	# we have to step through the landing page and the search results pages in order to access an individual image's page
	# otherwise the site gives us session errors
	# so we go ahead and do that, picking up the necessary cookies along the way
	req = Request('http://phil.cdc.gov/phil/home.asp', None, txheaders)
	#cj.save(COOKIEFILE)                     # save the cookies 
	handle = urlopen(req)
	req = Request('http://phil.cdc.gov/phil/quicksearch.asp', urllib.urlencode(quicksearch_page_post_values), txheaders)
	#cj.save(COOKIEFILE)                     # save the cookies again
	handle = urlopen(req)
	
	print "Fetched and stored new cookie."
	return cj
'''

def get_highest_id(floor=0):
    #TODO: this is a terrible band-aid solution.
    # fws image search doesnt order by id by default--it seems to order alphabetically.
    # a real solution would be to take a floor parameter and take a guess above it (+10,000, say)
    # and then use binary search to see if we get a hit between the guess and the floor
    # that's kind of expensive, though. and it's not fool proof (what if there are just huge gaps?)
    return 12500
    search_url = 'http://www.fema.gov/photolibrary/photo_search.do'
    post_payload = {
        'CISOBOX2': '',
        'ddlMediaFormat': 'JPG',
        'CISOROOT': 'all',
        'CISORESTMP': '/cdm4/results.php',
        'CISOVIEWTMP':'/cdm4/item_viewer.php',
        'CISOMODE':'grid',
        'CISOGRID' : 'thumbnail,A,1;title,A,1;subjec,A,0;descri,200,0;none,A,0;20;title;',
        'CISOBIB' : 'title,A,1,N;subjec,A,0,N;descri,200,0,N;date,A,0,N;20',
        'CISOTHUMB' : '20 (4x5);relevancy,none,none,none,none',
        'CISOFIELD2' : 'CISOSEARCHALL',
        'CISOOP2' : 'all',
        'CISOFIELD1' : 'format',
        'CISOOP1' : 'any',
        'CISOBOX1' : 'JPG ',
        'CISOFIELD3' : 'subjec',
        'CISOOP3' : 'none',
        'CISOBOX3' : '',
        'CISOFIELD4' : 'subjec',
        'CISOOP4': 'none',
        'CISOBOX4' : '',
        'History' : 'on',
    }
    urlopen = urllib2.urlopen
    Request = urllib2.Request
    cj = cookielib.LWPCookieJar()
    # This is a subclass of FileCookieJar
    # that has useful load and save methods

    # Now we need to get our Cookie Jar
    # installed in the opener;
    # for fetching URLs
    # we get the HTTPCookieProcessor
    # and install the opener in urllib2
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
    urllib2.install_opener(opener)
    # fake a user agent, some websites (like google) don't like automated exploration
    txheaders =  {'User-agent' : 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'}

    # we have to step through the landing page and the search results pages 
    # otherwise the site gives us session errors
    # so we go ahead and do that, picking up the necessary cookies along the way
    #req = Request('http://phil.cdc.gov/phil/home.asp', None, txheaders)
    #handle = urlopen(req)

    req = Request(search_url, urllib.urlencode(post_payload), txheaders)
    handle = urlopen(req)

    search_results_html = handle.read()

    return parser.get_first_result_index_from_quick_search_results(search_results_html)


def scrape_out_img_page(id, cj=None):
    url_to_scrape = id_to_page_permalink(id)

    urlopen = urllib2.urlopen
    Request = urllib2.Request
    if cj:
        # Now we need to get our Cookie Jar
        # installed in the opener;
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
        urllib2.install_opener(opener)

    # fake a user agent, some websites (like google) don't like automated exploration
    txheaders =  {'User-agent' : 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'}

    # finally, we can grab the actual image's page
    req = Request(url_to_scrape, None, txheaders)
    handle = urlopen(req)

    html = handle.read() #returns the page
    return html


def is_session_expired_page(html):
	if string.count("Your session information is no longer valid. ", html) == 0:
		return False
	else:
		return True


if __name__ == '__main__':
    id = 1
    scrape_out_img_page(id)
