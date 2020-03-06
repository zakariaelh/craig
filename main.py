import json 

from base import HousingCrawler
from mail_service import MailService
from credentials import EMAIL_AUTH


def main(limit=None):
	# get input data 
	with open("/home/zakariaelhjouji/craig/input.json", "r") as f:
		input_ = json.load(f)

	all_filters = input_.get('filters')
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

		# import ipdb; ipdb.set_trace()
		d_links['title'] = filter_.get('title')
		d_links['links'] = hc.url_considered
		d_links['df'] = hc.df_res[hc.df_res.score > 0].copy()

		d_listings[i] = d_links

	# set the first email as main receiver and cc the rest 
	if len(receiver) > 1:
		receiver_email = receiver[0]
		cc = receiver[1:]

	# call mail service and send messages 
	mail = MailService(
		sender_email=SENDER_EMAIL, 
		receiver_email=receiver_email,
		cc = cc
		)

	mail.create_and_send_all_msg(
		d_listings=d_listings
	)


if __name__ == "__main__":
	main()
