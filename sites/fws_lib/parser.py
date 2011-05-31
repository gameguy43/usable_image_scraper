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

import re
import time
from datetime import datetime
from html5lib import HTMLParser, treebuilders
import traceback
import json
import yaml
import types
import string
import scraper
import data_schema

def init_dict():
    metadict = {
        'id': 0,
        'subject' : None,
    }
    return metadict

def post_processing(data_dict, page_permalink=None):
    data_dict['page_permalink'] = scraper.id_to_page_permalink(data_dict['id'])
    return data_dict

def get_first_result_index_from_quick_search_results(html):
    parser = HTMLParser(tree=treebuilders.getTreeBuilder("beautifulsoup"))
    soup = parser.parse(html)
    block = soup.find(border="0", bgcolor="white") # isolate the table of data on the first result
    id_str = block.find('font').contents[0] #contents of first <font>
    # this should looke like: 'ID#:11901'
    # parse out the actual id and cast as int
    id = int(id_str.partition(':')[2])
    print id
    return id


def parse_quick_search(html):
    return html

def remove_surrounding_td_tags(str):
    # get the first one
    str = str.split("<td>")[1]
    split = str.split("</td>")
    str = split[len(split)-2]
    return str

def encode_all_nice(fieldvalue):
#    return unicode(remove_surrounding_td_tags(repr(str(fieldValue))))
    #return str(fieldvalue.encode("utf-8"))
    return unicode(fieldvalue)

def find_by_tag_and_contents(soup, tag, contents):
    for obj in soup.findAll(tag):
        if obj.contents and obj.contents[0] == contents:
            return obj
    return None

def get_text_within(html_blob):
    return ''.join(html_blob.findAll(text=True))
    

def parse_img_html_page(html):
    if not html or html == '':
        print "wait, the page appears blank. abort mission!"
        return None
    metadict = init_dict()
    # soupify the html
    parser = HTMLParser(tree=treebuilders.getTreeBuilder("beautifulsoup"))
    soup = parser.parse(html)
    if not soup:
        print "wait, we couldn't make a soup. i don't know WHY..."
        return None
    
    try:
        metadict['id'] = int(soup.find('input', {'type':'hidden', 'name': 'CISOPTR'})['value'])
    except:
        favorite_link_href = soup.find("a", {"title": u"Add to My Favorites"})['href']
        the_split = favorite_link_href.split("'")
        the_split.pop()
        metadict['id'] = int(the_split.pop())

    #TODO: this is kinda hackey but probably fine
    metadict['url_to_thumb_img'] = u'http://digitalmedia.fws.gov/cgi-bin/thumbnail.exe?CISOROOT=/natdiglib&CISOPTR=' + str(metadict['id'])

    hires_link = soup.find(text=lambda str: str.strip() == u'(Full Resolution Image Link)', recursive=True).parent.find('a')
    metadict['url_to_hires_img'] = hires_link['href']
    try:
        metadict['url_to_lores_img'] = u'http://digitalmedia.fws.gov' + soup.find("img", {"id" : "imagexy"})['src']
    except:
        metadict['url_to_lores_img'] = u'http://digitalmedia.fws.gov' + soup.find("input", {"type" : "image"})['src']

    data_table = soup.find("table", {"style": "border-top: 1px solid #cccccc"}).find("tbody")
    parsed_tuples = []
    for data_label_cell in data_table.findAll("td", {"width": "150"}):
        try:
            label = get_text_within(data_label_cell)
            print label
        except:
            continue
        data_cell = data_label_cell.findNextSibling("td")
        if label == 'Subject':
            data = data_cell.findAll(text=True)
        else:
            data = get_text_within(data_cell).strip()
        parsed_tuples.append((label, data))
    # now we have a list of tuples of the parsed metadata

    print parsed_tuples
    for label, data in parsed_tuples:
        field_key = data_schema.get_field_key_by_full_name(label)
        if not field_key:
            continue
        metadict[field_key] = data
        
    return metadict
    
def test_parse():
    f = open('./samples/20000.html')
    raw_html = f.read()
    import pprint
    pprint.pprint(parse_img(raw_html))
    f.close()

if __name__ == '__main__':
	test_parse()
