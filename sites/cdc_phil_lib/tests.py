import unittest2 as unittest

known_good_indeces = [1,2,3,4,5,6,7]

known_metadata_mappings = {
    1 : {
        u'id' : 1,
        u'desc' : u'<b>Data tape storage room</b><p>Data tape storage room, NCHS.</p>',
        u'provider' :  u'CDC',
        u'creation' : '',
        u'credit' : u'',
        u'links' : u'',
#        u'categories' : u'',
        u'page_permalink' : u'http://phil.cdc.gov/phil/details.asp?pid=1',
        u'copyright' : u'<b>None</b> - This image is in the public domain and thus free of any copyright restrictions. As a matter of courtesy we request that the content provider be credited and notified in any public or private usage of this image.',
    },
}




'''
CDC Organization
    Locations
            CDC Buildings and Facilities

            MeSH
                Anthropology, Education, Sociology and Social Phenomena
                        Social Sciences
                                    Government
                                                    Government Agencies
                                                                        United States Dept. of Health and Human Services
                                                                                                United States Public Health Service
                                                                                                                            Centers for Disease Control and Prevention (U.S.)
                                                                                                                                Health Care
                                                                                                                                        Health Care Economics and Organizations
                                                                                                                                                    Organizations
                                                                                                                                                                    Government Agencies
                                                                                                                                                                                        United States Dept. of Health and Human Services
                                                                                                                                                                                                                United States Public Health Service
                                                                                                                                                                                                                                            Centers for Disease Control and Prevention (U.S.)
'''

class TestScraperLibFunctions(unittest.TestCase):
    def setUp(self):
        pass

    def test_parse(self):
        pass

if __name__ == '__main__':
    unittest.main()
