import unittest2 as unittest
import scraper
import config
import os

class TestFEMAParserFunctions(unittest.TestCase):
    def setUp(self):
        # TODO: instantiate a database?
        # instantiate a scraper 
        self.test_lib = 'cdc_phil'
        self.myscraper = scraper.mkscraper(self.test_lib)

    '''
    def test_db_creation(self):
        db = myscraper.get_or_create_db()
        # TODO: assert things about the database
        # has the right tables
        # insert something and then grab it out
    '''

    def test_scrape(self):
        self.myscraper.scrape_indeces(range(10)[1:])
        # check that we have all 10 thumb and lores image files
        self.assertEqual(len(os.listdir(config.data_root_dir + config.image_databases[self.test_lib]['data_subdir'] + config.thumb_subdir)),10)
        # check that we have 10 rows in the database
        # TODO. trash the below.
        db = myscraper.get_or_create_db()
        
        # manually check that a specific one of the rows has all the right content? maybe
        #TODO
        


#TODO: case: * grab the highest index in the database
# maybe. or just make this a test that lives in the individual image libraries

if __name__ == '__main__':
    unittest.main()
