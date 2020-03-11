# using SendGrid's Python Library
# https://github.com/sendgrid/sendgrid-python
# import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from credentials import SENDGRID_API_KEY

assert SENDGRID_API_KEY is not None, 'add api key'

message = Mail(
    from_email='elhjouji.zakaria@gmail.com',
    to_emails='elhjouji.zakaria@gmail.com',
    subject='Sending with Twilio SendGrid is Fun',
    html_content='<strong>and easy to do anywhere, even with Python</strong>')


sg = SendGridAPIClient(SENDGRID_API_KEY)
response = sg.send(message)
print(response)
