from getpass import getpass

EMAIL_AUTH = {
	'email': 'ehjouji.zakaria@gmail.com',
	'password' : getpass(prompt='Email Password: ')
}

AWS_AUTH = {
	"host" : "craigsinstance.crlkdruusfz3.us-east-1.rds.amazonaws.com",
	"port" : 5432,
	"user" : "zakariae",
	"password" : getpass(prompt='AWS Database Password: '),
	"database" : "craigsdb"
}

API_KEY = "YOUR_API_KEY"