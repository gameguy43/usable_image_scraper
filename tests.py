import unittest2 as unittest

class TestFEMAParserFunctions(unittest.TestCase):
    def setUp(self):
        # instantiate a database
        import scraper
        import libs.cdc_phil_lib as imglib
        self.imglib = imglib
        import config
        self.myscraper = scraper.Scraper(imglib)

    def test_db_creation(self):
        db = myscraper.get_or_create_db()
        # TODO: assert things about the database
        # has the right tables
        # insert something and then grab it out

    def test_scrape(self):
        self.myscraper.scrape_range(1,10)
        # check that we have all 10 thumb and lores image files
        self.assertEqual(len(os.listdir(config.THUMB_IMG_DIR)),10)
        # check that we have 10 rows in the database
        db = myscraper.get_or_create_db()
        
        # manually check that a specific one of the rows has all the right content? maybe
        #TODO
        


#TODO: case: * grab the highest index in the database
# maybe. or just make this a test that lives in the individual image libraries

if __name__ == '__main__':
    unittest.main()
