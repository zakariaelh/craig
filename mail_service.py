import logging 
import smtplib
import datetime
from email.message import Message

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
		smtpserver=smtplib.SMTP("smtp.gmail.com",587)
		# shake hands 
		smtpserver.ehlo()
		smtpserver.starttls()
		smtpserver.ehlo()
		# login 
		smtpserver.login(self.sender_email, self.sender_password)
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
		assert isinstance(msg['From'], str)
		assert isinstance(msg['To'], str)
		# test if connection is open
		if not self.test_conn_open(self.smtpserver):
			self.connect()
		# send email 
		self.smtpserver.sendmail(
			from_addr=msg['From'],
			to_addrs=msg['To'],
			msg=msg.as_string()
			)
		logging.info(
			{
			'msg': 'email sent to {} From {} successfully'.format(
				msg['To'],
				msg['From']
				)
			}
			)
		# close connection was message is sent
		self.smtpserver.close()

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
		msg = Message()
		msg['Subject'] = 'Listings for {}'.format(today_date)
		msg['From'] = sender_email
		msg['To'] = receiver_email
		msg.add_header('Content-Type','text/html')
		msg.set_payload(msg_text)
		return msg 

	@staticmethod
	def test_conn_open(smtpserver):
		"""
		Test if connection is still open.
		"""
		try:
			status = smtpserver.noop()[0]
		except:
			status = -1
		return True if status == 250 else False

	@staticmethod
	def create_html_list(l_links):
		l_li = list(map(lambda x: '<li>{}</li>'.format(x), l_links))
		return '\n'.join(l_li)






