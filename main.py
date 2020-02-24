import json 

from base import HousingCrawler
from mail_service import MailService
from credentials import EMAIL_AUTH


def main(limit=None):
	# get input data 
	with open("input.json", "r") as f:
		input_ = json.load(f)

	all_filters = 
	destination = input_.get('destination')
	mode = input_.get('mode')
	receiver = input_.get('receiver')

	# create dictionary for all listings to be sent by mail 
	d_listings = dict()

	for i, filter_ in enumerate(all_filters):
		# create dict of listings for filter_ 
		d_links = dict()
		hc = HousingCrawler(
		    filters=filter_, 
		    destination=destination,
		    mode=mode,
		    limit=limit
		    )
		hc.run_all()

		d_links['title'] = filter_.get('title')
		d_links['links'] = hc.url_considered

		d_listings[i] = d_links

	# pull out the links of the listings to consider 
	# set up mail connection 
	mail = MailService(
		sender_auth=EMAIL_AUTH, 
		receiver=receiver
		)

	mail.create_and_send_all_msg(
		d_listings=d_listings
	)

if __name__ == "__main__":
	main()
