import unittest2 as unittest
import urllib

import parser

known_good_indeces = [1, 2, 3, 20000]

known_metadata_mappings = {
    20000 : {
        'photo_date' : u"12/05/2005",
        'desc' : u"La Place, LA,  December 5, 2005 - Santa will have to land on the lawn: Shawna and Donnie White won't let a little hurricane damage spoil Christmas. They decorated their home even as they await FEMA assistance to help cover roof repairs.  Photo by Greg Henshall / FEMA", 
        'location' : u"La Place, Louisiana",
        'original_filename' : u"LA_1603_La Place Christmas_0211a.jpg",
        'size' : u"5,004.5 KB",
        'photographer' : u"Greg Henshall",
        'id' : 20000,
        'dimensions' : u"1768x2728",
        'url_to_lores_img':  u'http://www.fema.gov/photodata/low/20000.jpg',
        'url_to_hires_img':  u'http://www.fema.gov/photodata/original/20000.jpg',
        'url_to_thumb_img':  u'http://www.fema.gov/photodata/thumbnail/20000.jpg',
        
        'categories' : [
            u"Miscellaneous",
            u"Hurricane/Tropical Storm"
            ],
        'disasters' : [
            (u"Louisiana Hurricane Rita (DR-1607)",u"http://www.fema.gov/news/event.fema?id=5025"),
            (u"Louisiana Hurricane Katrina (DR-1603)",u"http://www.fema.gov/news/event.fema?id=4808")
            ],
        },
}



class TestFEMAParserFunctions(unittest.TestCase):
    # TODO: write a test to assert that we've found all of the metadata fields
    def setUp(self):
        self.maxDiff = None
        self.use_live_page = True

    def test_highest_id_parser(self):
        highest_id = parser.get_highest_id()

    def test_id_to_page_permalink(self):
       self.assertTrue(isinstance(parser.id_to_page_permalink(id), str))

    def test_parser_correctness(self):
        for id, known_metadata in known_metadata_mappings.items():
            url_to_live_page = "http://www.fema.gov/photolibrary/photo_details.do?id=" + str(id)
            path_to_local_copy = "samples/" + str(id) + ".html"
            expected_output = known_metadata
                    
            if self.use_live_page:
                html =  urllib.urlopen(url_to_live_page)
            else:
                fp = open(path_to_local_copy,'r')
                html = fp.read()
            actual_output = parser.parse_img(html)
            
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
