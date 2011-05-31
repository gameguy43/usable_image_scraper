'''
Based heavily on multichill's set up wikimedia commons usgov image uploaders.
https://fisheye.toolserver.org/browse/multichill/bot/usgov?r=153
Thanks, multichill!
'''
#import pywikipedia
#import pywikipedia.wikipedia
#import pywikipedia.upload
#import pywikipedia.config
#pyqikipedia.config
import os
import sys
import re



'''
abs_filename = os.path.abspath(__file__)
abs_path, filename = os.path.split(abs_filename)
print abs_path


sys.path.append(abs_path + '/pywikipedia/')
'''

'''
import pywikibot.wikipedia
import pywikibot.upload
import pywikibot.config
'''
import pywikibot
import StringIO
import hashlib
import base64
import pywikibotutils


resolution_to_use = 'lores'



class WikiUploader:
    def __init__(self, myscraper, testing=False):
        self.myscraper = myscraper
        if testing:
            self.destination_site = pywikibot.getSite('commons', 'commons')
        else:
            self.destination_site = pywikibot.getSite('commons', 'commons')

    def find_duplicate_images_on_wmc(self, photo = None, site = pywikibot.getSite(u'commons', u'commons')):
        '''
        Takes the photo, calculates the SHA1 hash and asks the mediawiki api for a list of duplicates.

        '''
        hashObject = hashlib.sha1()
        hashObject.update(photo.getvalue())
        return site.getImagesFromAnHash(base64.b16encode(hashObject.digest()))

    def build_description(self, metadata):
        '''
        Create the description of the image based on the metadata
        '''
        description = u''
        description += 'testing'

        # TODO: be sure to include a link back to the original source!!!
        '''
        description = description + u'== {{int:filedesc}} ==\n'
        description = description + u'{{Information\n'
        description = description + u'|description={{en|1=' + metadata.get('description') + u'}}\n'
        description = description + u'|date=' + metadata.get('date') + u'\n' # MM/DD/YYYY
        #description = description + u'|source={{Navy News Service|' + str(photo_id) + u'}}\n'
        description = description + u'|source={{ID-USMil|' + metadata.get('navyid') + u'|Navy|url=http://www.navy.mil/view_single.asp?id=' + str(photo_id) + u'}}\n'
        description = description + u'|author=' + metadata.get('author') + u'\n'
        description = description + u'|permission=\n'
        description = description + u'|other_versions=\n'
        description = description + u'|other_fields=\n'
        description = description + u'}}\n'
        description = description + u'\n'
        description = description + u'== {{int:license}} ==\n'
        description = description + u'{{PD-USGov-Military-Navy}}\n'
        description = description + u'\n'
        if not metadata.get('ship')==u'':
            description = description + getShipCategory(metadata.get('ship')) + u'\n'
        else:
            description = description + u'[[Category:Images from US Navy, location ' + metadata.get('location') + u']]\n'
        #else:
        #	description = description + u'{{Uncategorized-navy}}\n'
        #description = description + u''
        '''

        return description


    def build_title(self, metadata):
        '''
        Build a valid title for the image to be uploaded to.
        '''
        '''
        description = metadata['shortdescription']
        if len(description)>120:
            description = description[0 : 120]
        '''
        prefix = self.myscraper.abbrev.upper()
        extension = self.myscraper.get_resolution_extension(resolution_to_use, metadata['id'])

        title = prefix + '_' + str(metadata['id']) + '.' + extension
        title = unicode(title)

        title = re.sub(u"[<{\\[]", u"(", title)
        title = re.sub(u"[>}\\]]", u")", title)
        title = re.sub(u"[ _]?\\(!\\)", u"", title)
        title = re.sub(u",:[ _]", u", ", title)
        title = re.sub(u"[;:][ _]", u", ", title)
        title = re.sub(u"[\t\n ]+", u" ", title)
        title = re.sub(u"[\r\n ]+", u" ", title)
        title = re.sub(u"[\n]+", u"", title)
        title = re.sub(u"[?!]([.\"]|$)", u"\\1", title)
        title = re.sub(u"[&#%?!]", u"^", title)
        title = re.sub(u"[;]", u",", title)
        title = re.sub(u"[/+\\\\:]", u"-", title)
        title = re.sub(u"--+", u"-", title)
        title = re.sub(u",,+", u",", title)
        title = re.sub(u"[-,^]([.]|$)", u"\\1", title)
        title = title.replace(u" ", u"_")
        title = title.replace(u"__", u"_")
        title = title.replace(u"..", u".")
        title = title.replace(u"._.", u".")
        
        #print title
        return title

    def upload_to_wikicommons_if_unique(self, metadata):
        local_file_location = self.myscraper.get_resolution_local_image_location(resolution_to_use, metadata['id'])

        image_raw = open(local_file_location, 'r').read()
        image_stringio = StringIO.StringIO(image_raw)

        duplicates = self.find_duplicate_images_on_wmc(image_stringio)
        if duplicates:
            pywikibot.output(u'Found duplicate image at %s' % duplicates.pop())
            return

        image_url = self.myscraper.db.get_resolution_url(resolution_to_use, metadata['id'])

        title = self.build_title(metadata)
        description = self.build_description(metadata)

        bot = pywikibotutils.upload.UploadRobot(image_url, description=description, useFilename=title, keepFilename=True, verifyDescription=False, targetSite=self.destination_site)
        bot.upload_image(debug=False)
