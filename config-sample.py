image_databases = {
    "cdc_phil": {
        'python_lib': 'cdc_phil_lib',
        'data_subdir': 'cdc_phil/', #trailing slash
        'data_table_prefix': 'cdc_phil_',
        'long_name' : "The Center for Disease Control's Public Health Image Library",
        'homepage' : "http://phil.cdc.gov/",
        'code_url' : "https://github.com/gameguy43/cdc_phil_lib",
        },
    "fema": {
        'python_lib': 'fema_lib',
        'data_subdir': 'fema/', #trailing slash
        'data_table_prefix': 'fema_',
        'long_name' : "The Fema Photo library",
        'homepage' : "http://www.fema.gov/photolibrary/",
        'code_url' : "https://github.com/gameguy43/fema_lib",
        },
    }

## Set these as needed locally
data_root_dir = '/home/pyrak/workspace/usable_images/usable_image_scraper/data/'
thumb_subdir = 'thumbs/'
lores_subdir = 'lores/'
hires_subdir = 'hires/'
html_subdir = 'html/'
max_daemons = 50
#max_daemons = 1
import sites
img_libraries_metalib = sites

data_db_host = ''
data_db_db = data_root_dir + 'metadata.sqlite'
data_db_user = ''
data_db_pass = ''

db_url = 'sqlite:///' + data_db_db
