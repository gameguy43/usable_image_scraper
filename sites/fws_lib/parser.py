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

def init_dict():
    metadict = {
        'id': 0,
        'title' : u"",
        'creator' : u"",
        'publisher' : u"",
        'type' : u"",
        'format' : u"",
        'source' : u"",
        'language' : u"",
        'rights' : u"",
        'audience' : u"",
        'date_created' : u"",
        'date_modified' : u"",
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
    # the lores image url
    # the description/caption
    '''
        metadict['id']: 0,
        metadict['title'] : u"",
        metadict['creator'] : u"",
        metadict['publisher'] : u"",
        metadict['type'] : u"",
        metadict['format'] : u"",
        metadict['source'] : u"",
        metadict['language'] : u"",
        metadict['rights'] : u"",
        metadict['audience'] : u"",
        metadict['date_created'] : u"",
        metadict['date_modified'] : u"",
        metadict['subject'] : None,
    '''

    # html table with the rest of the data

    #metadict['id'] = soup.find("form", {"name": "mainimage"}).find("input", {"name": "CISOPTR"})['value']

    data_table = soup.find("table", {"style": "border-top: 1px solid #cccccc"}).find("tbody")
    for data_label_cell in data_table.findAll("td", {"width": "150"}):
        try:
            label = data_label_cell.span.b.contents[0]
            print label
        except:
            continue

    '''
    metadict['url_to_lores_img'] = soup.find("",{"class": "tophoto"}).find("img")["src"]
    metadict['url_to_hires_img'] = find_by_tag_and_contents(data_table, "a", u"\u00BB Download original photo")['href']
    # TODO: for now, we just assume that the thumb image url follows a pattern
    # maybe we should really do a search for this image's id and scrape the thumb url off of the page. meh.
    metadict['url_to_thumb_img'] = string.replace(metadict['url_to_hires_img'], "original", "thumbnail")
    
    for data_label_cell in data_table.findAll("th"):
        try:
            label = data_label_cell.contents[0]
        except:
            continue
        if label == u"Location:":
            metadict['location'] = data_label_cell.findNextSibling("td").contents[0].strip()
        elif label == u'Photographer:':
            metadict['photographer'] = data_label_cell.findNextSibling("td").contents[0].strip()
        elif label == u'Photo Date:':
            metadict['photo_date'] = data_label_cell.findNextSibling("td").contents[0].strip()
        elif label == u'ID:':
            metadict['id'] = int(data_label_cell.findNextSibling("td").contents[0].strip())
        elif label == u'Original filename:':
            metadict['original_filename'] = data_label_cell.findNextSibling("td").contents[0].strip()
        elif label == u'Size:':
            metadict['size'] = data_label_cell.findNextSibling("td").contents[0].strip()
        elif label == u'Dimensions:':
            metadict['dimensions'] = data_label_cell.findNextSibling("td").contents[0].strip()
        elif label == u'Categories:':
            categories_td = data_label_cell.findNextSibling("td")
            categories_list = filter(lambda x: isinstance(x,unicode), categories_td.contents)
            categories_list = map(lambda x: x.strip(), categories_list)
            categories_list = filter(lambda x: len(x) > 0, categories_list)
            metadict['categories'] = categories_list
        elif label == u'Disasters:':
            disasters_td = data_label_cell.findNextSibling("td")
            disaster_links = disasters_td.findAll("a")
            disaster_tuples = map(lambda link: (link.contents[0],link['href']), disaster_links)
            metadict['disasters'] = disaster_tuples
    '''

    return metadict
    
def test_parse():
    f = open('./samples/20000.html')
    raw_html = f.read()
    import pprint
    pprint.pprint(parse_img(raw_html))
    f.close()

if __name__ == '__main__':
	test_parse()
