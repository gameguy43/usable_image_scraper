'''
Based heavily on multichill's set up wikimedia commons usgov image uploaders.
https://fisheye.toolserver.org/browse/multichill/bot/usgov?r=153
Thanks, multichill!
'''
import os
import sys
import re
import urllib2
import pywikibot
import StringIO
import hashlib
import base64
import pywikibotutils


resolution_to_use = 'hires'



class WikiUploader:
    def __init__(self, myscraper, testing=False):
        self.myscraper = myscraper
        self.testing = testing
        if testing:
            self.destination_site = pywikibot.getSite('test', 'test')
        else:
            self.destination_site = pywikibot.getSite('commons', 'commons')
        print self.destination_site

    def find_duplicate_images_on_wmc(self, photo=None):
        '''
        Takes the photo, calculates the SHA1 hash and asks the mediawiki api for a list of duplicates.
        '''
        site = self.destination_site
        hashObject = hashlib.sha1()
        hashObject.update(photo.getvalue())
        return site.getImagesFromAnHash(base64.b16encode(hashObject.digest()))

    def build_metadata_table(self, metadata):
        if not metadata or len(metadata.keys()) <=0:
            return u''
        retval = u''
        retval += u'{| class="wikitable"\n'
        retval += u'|-\n'
        retval += u'! Field Name \n'
        retval += u'! Field Value \n'
        for field in self.myscraper.imglib.data_schema.their_fields.keys():
            if metadata.get(field):
                retval += u'|-\n'
                retval += u'| ' + field + ' \n'
                retval += u'| ' + unicode(metadata[field]) + '\n'
        retval += u'|}\n'
        return retval
        

    def build_description(self, metadata):
        '''
        Create the description of the image based on the metadata
        '''
        id = metadata['id']
        desc = self.get_metadata_by_wmc_field('desc', metadata)
        date = self.get_metadata_by_wmc_field('date', metadata) # MM/DD/YYYY, ideally
        author = self.get_metadata_by_wmc_field('author', metadata) # MM/DD/YYYY, ideally
        #TODO
        categories = []

        #source = u'{{ID-USMil|' + metadata.get('navyid') + u'|Navy|url=http://www.navy.mil/view_single.asp?id=' + str(photo_id) + u'}}'
        source_template = self.myscraper.imglib.data_schema.wmc_stuff['source_template']
        source = u'{{' + source_template + u'|' + str(id) + u'}}'
        #license = u'{{PD-USGov-Military-Navy}}\n'
        license = u'{{' + self.myscraper.imglib.data_schema.wmc_stuff['license_template'] + u'}}'

        description = u''
        description = description + u'== {{int:filedesc}} ==\n'
        description = description + u'{{Information\n'
        description = description + u'|description={{en|1=' + desc + u'}}\n'
        description = description + u'|date=' + date + u'\n' 
        description = description + u'|source=' + source + u'\n'
        description = description + u'|author=' + author + u'\n'
        description = description + u'|permission=\n'
        description = description + u'|other_versions=\n'
        description = description + u'|other_fields=\n'
        description = description + u'}}\n'
        description = description + u'\n'
        description = description + u'== {{int:license}} ==\n'
        description = description + license + u'\n'
        description = description + u'\n'
        for category in categories:
            description = description + u'[[Category:' + category + u']]\n'


        metadata_table = self.build_metadata_table(metadata)
        description = description + u'== Orginal Metadata ==\n'
        description = description + u'This is the original metadata as reported on the source webpage\n'
        description = description + metadata_table
        #else:
        #	description = description + u'{{Uncategorized-navy}}\n'
        #description = description + u''
        return description

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


    def get_metadata_by_wmc_field(self, field, metadata):
        mapped_field = self.myscraper.imglib.data_schema.wmc_stuff['field_mappings'][field]
        return metadata[mapped_field]

    def build_title(self, metadata):
        '''
        Build a valid title for the image to be uploaded to.
        '''
        orig_title_snippet_length_cap = 120
        orig_title_snippet = self.get_metadata_by_wmc_field('title', metadata)
        if len(orig_title_snippet)>orig_title_snippet_length_cap:
            orig_title_snippet = orig_title_snippet[0 : orig_title_snippet_length_cap]

        prefix = self.myscraper.abbrev.upper()
        extension = self.myscraper.get_resolution_extension(resolution_to_use, metadata['id'])

        title = prefix + '_' + str(metadata['id']) + '_' + orig_title_snippet + '.' + extension
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
        #local_file_location = self.myscraper.get_resolution_local_image_location(resolution_to_use, metadata['id'])
        remote_file_location = self.myscraper.db.get_resolution_url(resolution_to_use, metadata['id'])

        #image_raw = open(local_file_location, 'r').read()
        image_raw = urllib2.urlopen(remote_file_location).read()

        image_stringio = StringIO.StringIO(image_raw)

        duplicates = self.find_duplicate_images_on_wmc(image_stringio)
        if duplicates:
            pywikibot.output(u'Found duplicate image at %s' % duplicates.pop())
            return

        title = self.build_title(metadata)
        description = self.build_description(metadata)

        bot = pywikibotutils.upload.UploadRobot(remote_file_location, description=description, useFilename=title, keepFilename=True, verifyDescription=False, targetSite=self.destination_site)
        bot.upload_image(debug=False)
