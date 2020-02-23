import logging 
import smtplib
import datetime

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from credentials import SENDGRID_API_KEY

from constants import MSG_SHELL

logging.root.setLevel(logging.DEBUG)

class MailService(object):
	def __init__(self, sender_auth, receiver):
		"""
		:param sender_auth: dict with sender_email and sender password
		:param receiver: list or str of the receiver email(s) 
		"""
		assert isinstance(sender_auth, dict), "Sender Auth must be a dict"
		assert all(elem in ['email', 'password']  for elem in sender_auth.keys()), "sender_auth must contain at least ['email', 'password'] as keys"
		assert type(receiver) in [str, list], "receiver arg is either a list or str"
		self.sender_auth = sender_auth
		self.sender_email = sender_auth['email']
		self.sender_password = sender_auth['password']
		self.receiver = [receiver] if isinstance(receiver, str) else receiver
		# mail server 
		self.smtpserver = None

	def connect(self):
		# connect to gmail server through 587 port 
		smtpserver = SendGridAPIClient(SENDGRID_API_KEY)

		self.smtpserver = smtpserver
		logging.info({'msg': 'Connection Established'})

	def create_all_msg_cls(self, msg_text):
		"""
		Creates a list of messages to be sent to all receivers.
		"""
		m_msg = map(lambda x: self.create_msg_cls(
				sender_email=self.sender_email,
				receiver_email=x,
				msg_text=msg_text
			), self.receiver)
		l_msg = list(m_msg)
		return l_msg

	def send_all_msg(self, l_msg):
		"""
		Sends list of messages at once.
		"""
		l_msg = [l_msg] if not isinstance(l_msg, list) else l_msg
		for msg in l_msg:
			self.send_msg(msg)


	def send_msg(self, msg):
		"""
		Sends email to sender, receiverspecified in msg object

		:param msg: email.message.Message cls 
		"""
		if self.smtpserver is None:
			self.connect()

		# send email 

		self.smtpserver.send(msg)

		logging.info(
			{
			'msg': 'email sent From: {} to {} successfully'.format(
				msg.from_email.email,
				msg.personalizations[0].tos[0].get('email'),
				)
			}
			)

	def create_and_send_all_msg(self, l_links_2, l_links_3):
		"""
		Writes and sends all messages to all recipients
		"""
		# write message 
		msg_text = self.write_msg(l_links_2, l_links_3)
		# create message class
		l_msg = self.create_all_msg_cls(msg_text)
		# send all messages
		self.send_all_msg(l_msg)

	@classmethod
	def write_msg(cls, l_links_2, l_links_3):
		# create html list of links 
		if len(l_links_2):
			l_links_2_html = cls.create_html_list(l_links_2)
		else: 
			l_links_2_html = 'No listings are available for this category'
		# same applies to links_3 
		if len(l_links_3):
			l_links_3_html = cls.create_html_list(l_links_3)
		else: 
			l_links_3_html = 'No listings are available for this category'
		return MSG_SHELL.format(l_li_2=l_links_2_html, l_li_3=l_links_3_html)


	@staticmethod 
	def create_msg_cls(sender_email, receiver_email, msg_text):
		assert all(isinstance(x, str) for x in [sender_email, receiver_email, msg_text]), 'all input must be a string'
		# today's date as a string 
		today_date = datetime.date.today().strftime("%Y-%m-%d")
		# create Message 
		msg = Mail(
			from_email= sender_email,
			to_emails=receiver_email,
			subject= 'Listings for {}'.format(today_date),
			html_content=msg_text
			)
		return msg 


	@staticmethod
	def create_html_list(l_links):
		l_li = list(map(lambda x: '<li>{}</li>'.format(x), l_links))
		return '\n'.join(l_li)






