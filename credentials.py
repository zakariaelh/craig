from getpass import getpass

EMAIL_AUTH = {
	'email': 'YOUR_EMAIL',
	'password' : getpass(prompt='Email Password: ')
}

AWS_AUTH = {
	"host" : "YOUR_AWS_INSTANCE",
	"port" : 5432,
	"user" : "USERNAME",
	"password" : getpass(prompt='AWS Database Password: '),
	"database" : "DATABASE_NAME"
}

API_KEY = "YOUR_API_KEY"