import logging
# import smtplib
import datetime

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from sendgrid.helpers.mail.cc_email import Cc
from credentials import SENDGRID_API_KEY

from constants import MSG_SHELL, MSG_LINKS, MAIL_COLUMNS, STYLE

logging.root.setLevel(logging.DEBUG)


class MailService(object):
    def __init__(self, sender_email, receiver_email, cc=None):
        """
        :param sender_auth: dict with sender_email and sender password
        :param receiver: list or str of the receiver email(s) 
        :param cc: list of str for the emails to cc 
        """
        self.sender_email = sender_email
        self.receiver_email = receiver_email
        self.cc = cc
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
        assert isinstance(self.receiver_email, list)
        m_msg = map(lambda x: self.create_msg_cls(
            sender_email=self.sender_email,
            receiver_email=x,
            msg_text=msg_text
        ), self.receiver_email)
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

    def create_and_send_all_msg(self, d_listings):
        """
        Writes and sends all messages to all recipients
        """
        # write message
        msg_text = self.write_msg(d_listings)
        # create message class
        # make the first email main received and the rest None
        msg = self.create_msg_cls(
            sender_email=self.sender_email,
            receiver_email=self.receiver_email,
            cc=self.cc,
            msg_text=msg_text
        )
        # send all messages
        self.send_all_msg(msg)

    @classmethod
    def write_msg(cls, d_listings):
        # create html list of links
        assert isinstance(d_listings, dict)

        body = ""

        for i, d_links in d_listings.items():
            # for each group of links, we create a paragraphe and append to body
            # title (if no title was provided call it generic name category i)
            title = d_links.get("title") if d_links.get(
                "title") is not None else "Category {}".format(i)
            # get the html format of links
            l_links = d_links.get('links')
            df_res = d_links.get('df')

            if len(l_links) > 0:
                # body_links = cls.create_html_list(l_links)
                body_links = cls.create_html_table(
                    df=df_res, cols=MAIL_COLUMNS)
            else:
                body_links = 'No listings are available for this category'
            # create paragraph
            pgph = MSG_LINKS.format(title=title, body_links=body_links)

            body += '\n' + pgph

        msg = MSG_SHELL.format(body=body, style=STYLE)
        return msg

    @staticmethod
    def create_html_table(df, cols):
        """
        Takes pd DataFrame with columns ['url', 'id'] and converts it into html table with hyperlink

        :params df: pd DataFrame with ['url', 'id']
        :params cols: list of columns to select

        :output: html_Table
        """
        assert all([i in df.columns for i in cols]
                   ), 'all cols must be in df columns'

        # convert url to hyperlink
        df['url'] = df[['url', 'id']].apply(
            lambda x: "<a href={}>{}</a>".format(x.url, x.id), axis=1)

        # select columns of interest
        temp = df[cols]

        # convert to html
        html_table = temp.to_html(render_links=True, escape=False)

        return html_table

    @staticmethod
    def create_msg_cls(sender_email, receiver_email, msg_text, cc=None):
        # today's date as a string
        today_date = datetime.date.today().strftime("%Y-%m-%d")
        # create Message
        msg = Mail(
            from_email=sender_email,
            to_emails=receiver_email,
            subject='Listings for {}'.format(today_date),
            html_content=msg_text
        )
        if cc is not None:
            msg.add_cc(MailService.create_cc_objects(cc))
        return msg

    @staticmethod
    def create_cc_objects(cc):
        """Turn cc string email into Sendgrit cc object"""
        if isinstance(cc, list):
            return [Cc(email) for email in cc]
        elif isinstance(cc, str):
            return Cc(cc)
        else:
            raise 'cc input must be either a string or list'

    @staticmethod
    def create_html_list(l_links):
        l_li = list(map(lambda x: '<li>{}</li>'.format(x), l_links))
        return '\n'.join(l_li)
