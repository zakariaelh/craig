from base import HousingCrawler
from mail_service import MailService
from credentials import EMAIL_AUTH

# uber and dropbox coordinates 
UBER = (37.775905, -122.418339)
DROPBOX = (37.766622, -122.392408)
DESTINATION = {
    "Uber": UBER,
    "Dropbox": DROPBOX
}
MODE=["cycling", "transit", "walking"]

FILTERS_2BD = {
    'price_min': 3500,
    'price_max': 5500,
    'min_bedrooms': 2,
    'max_bedrooms': 2,
    'min_ft2': 700,
}
FILTERS_3BD = {
    'price_min': 4000,
    'price_max': 7000,
    'min_bedrooms': 3,
    'max_bedrooms': 3,
    'min_ft2': 12,
}

# list of receivers 
LIST_RECEIVER = ['elhjouji.zakaria@gmail.com'] #, 'lisafwalz@gmail.com']

def test_main():
	# check if email connection can be established 
	# set up mail connection 
	mail = MailService(
		sender_auth=EMAIL_AUTH, 
		receiver=LIST_RECEIVER
		)

	mail.connect()
	
	# 3 bedrooms obj
	hc3 = HousingCrawler(
    filters=FILTERS_3BD, 
    destination=DESTINATION,
    mode=MODE,
    limit=3
    )
	# pull data for three bedrooms 
	hc3.run_all()

	# 2 bedrooms obj
	hc2 = HousingCrawler(
    filters=FILTERS_2BD, 
    destination=DESTINATION,
    mode=MODE,
    limit=3
	)
	# pull data for 2 bedrooms 
	hc2.run_all()

	# pull out the links of the listings to consider 
	l_links_2 = hc2.url_considered
	l_links_3 = hc3.url_considered
	mail.create_and_send_all_msg(
	    l_links_2=l_links_2,
	    l_links_3=l_links_3
	)

if __name__ == "__main__":
	test_main()
