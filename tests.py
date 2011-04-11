import unittest2 as unittest
import scraper
import config
import os

class TestScraperFunctions(unittest.TestCase):
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

    #TODO: test the scraping from hd functionality

    def test_scrape(self):
        known_good_indeces = range(10)[1:8]
        subdir_to_find_thumbs = config.data_root_dir + config.image_databases[self.test_lib]['data_subdir'] + config.thumb_subdir + '000XX'
        self.myscraper.scrape_indeces(known_good_indeces)
        # check that we have all 10 thumb and lores image files
        self.assertEqual(len(os.listdir(subdir_to_find_thumbs)),len(known_good_indeces))
        # check that we have the right number of rows in the database
        # TODO. trash the below.
        rows = self.myscraper.metadata_table.all()
        self.assertEqual(len(known_good_indeces), len(rows))
        
        # manually check that a specific one of the rows has all the right content? maybe
        #TODO
        


#TODO: case: * grab the highest index in the database
# maybe. or just make this a test that lives in the individual image libraries

if __name__ == '__main__':
    unittest.main()
