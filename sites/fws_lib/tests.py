import unittest2 as unittest
import urllib

import parser
import scraper

known_good_indeces = [1, 2, 3, 11874, 1234]

known_metadata_mappings = {
    1234 : {
        'url_to_lores_img': u'http://digitalmedia.fws.gov/cgi-bin/getimage.exe?CISOROOT=/natdiglib&CISOPTR=1234&DMSCALE=66.66667&DMWIDTH=700&DMHEIGHT=700&DMX=0&DMY=0&DMTEXT=%20walrus&REC=1&DMTHUMB=1&DMROTATE=0',
        'url_to_hires_img': u'',
        'id' : 1234,
        'title' : u"Shoreline Vegetation",
        'creator' : u"U.S. Fish and Wildlife Service",
        'publisher' : u"U.S. Fish and Wildlife Service",
        'type' : u"Still image",
        'format' : u"JPG",
        'source' : u"AK/RO/02641",
        'language' : u"English",
        'rights' : u"Public domain",
        'audience' : u"General",
        'date_created' : u"2008-04-18",
        'date_modified' : u"2008-04-18",
        'subject' : [
            u"Scenics",
            u"Landscapes",
            u"Vegetation",
            u"Wildlife refuges",
            u"Koyukuk National Wildlife Refuge",
            ],
        },
    }
'''
11878 : {
    'title' : u"Bull Walrus Swimming",
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
    'subject' : [
        u"",
        u"",
        u"",
        u"",
        u"",
        ],
    },
'''
'''
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
'subject' : [
    u"",
    u"",
    u"",
    u"",
    u"",
    ],
'''



class TestParserFunctions(unittest.TestCase):
    # TODO: write a test to assert that we've found all of the metadata fields
    def setUp(self):
        self.maxDiff = None
        self.use_live_page = False

    def test_parser_correctness(self):
        for id, known_metadata in known_metadata_mappings.items():
            url_to_live_page = scraper.id_to_page_permalink(id)
            path_to_local_copy = "samples/" + str(id) + ".html"
            expected_output = known_metadata
                    
            if self.use_live_page:
                html =  urllib.urlopen(url_to_live_page).read()
            else:
                fp = open(path_to_local_copy,'r')
                html = fp.read()
            actual_output = parser.parse_img_html_page(html)
            
            self.assertDictEqual(actual_output, expected_output)
            '''
            #if we were using the poopy old version of unittest:
            keys_to_compare = set(actual_output.itervalues()).union(set(self.expected_output.itervalues()))
            for key in keys_to_compare:
                print key
                self.assertEqual(actual_output[key],self.expected_output[key])
            '''

if __name__ == '__main__':
    unittest.main()
