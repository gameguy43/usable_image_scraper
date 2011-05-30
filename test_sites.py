import unittest2 as unittest
import scraper
import config
import urllib

def generate_TestSiteClass_for_site(site):
    class TestSite(unittest.TestCase):
        # TODO: write a test to assert that we've found all of the metadata fields
        def setUp(self):
            self.maxDiff = None
            # instantiate a scraper 
            self.myscraper = scraper.mkscraper(site, test=True)
            self.imglib = self.myscraper.imglib

            self.use_live_page = False

        ##### INTERFACE STUFF--just make sure we have the right functions
        def test_id_to_page_permalink(self):
            id = 1
            url = self.imglib.scraper.id_to_page_permalink(id) 
            self.assertTrue(isinstance(url, str))

        def test_highest_id_parser(self):
            highest_id = self.imglib.scraper.get_highest_id()
            self.assertTrue(isinstance(highest_id, int))

        def test_repr_as_html(self):
            from django.conf import settings
            settings.configure(DEBUG=True, TEMPLATE_DEBUG=True)
            for id, x in self.imglib.tests.known_metadata_mappings.items():
                html = self.myscraper.get_image_html_repr(id)
                #TODO: test that the html actually contains all of the data
                self.assertTrue(isinstance(html, unicode) or isinstance(html, str))
        #### END INTERFACE STUFF

        def test_parser_correctness(self):
            for id, known_metadata in self.imglib.tests.known_metadata_mappings.items():
                url_to_live_page = self.imglib.scraper.id_to_page_permalink(id) 
                path_to_local_copy = 'sites/' + config.image_databases[site]['python_lib'] + "/samples/" + str(id) + ".html"
                expected_output = known_metadata
                        
                if self.use_live_page:
                    html =  urllib.urlopen(url_to_live_page)
                else:
                    fp = open(path_to_local_copy,'r')
                    html = fp.read()
                actual_output = self.imglib.parser.parse_img_html_page(html)
                
                self.assertDictEqual(actual_output, expected_output)
                '''
                #if we were using the poopy old version of unittest:
                keys_to_compare = set(actual_output.itervalues()).union(set(self.expected_output.itervalues()))
                for key in keys_to_compare:
                    print key
                    self.assertEqual(actual_output[key],self.expected_output[key])
                '''
            

    return TestSite


def test_these_sites(sites):
    for site in sites:
        TestSite = generate_TestSiteClass_for_site(site)
        suite = unittest.TestLoader().loadTestsFromTestCase(TestSite)
        unittest.TextTestRunner(verbosity=2).run(suite)
        

if __name__ == '__main__':
    # either we want to test one site:
    sites = ['fws']
    # or we want to test all of them
    #sites = config.image_databases.keys()

    test_these_sites(sites)
