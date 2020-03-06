from getpass import getpass

EMAIL_AUTH = {
	'email': 'elhjouji.zakaria@gmail.com',
	'password' : None
}

DB_URL = 'https://craig-885d7.firebaseio.com/'
DB_NAME = 'data_listings_final'

FIREBASE_KEY_PATH = './firebase_key.json'

SENDER_EMAIL = 'elhjouji.zakaria@gmail.com'

AWS_AUTH = {
	"host" : "YOUR_AWS_INSTANCE",
	"port" : 5432,
	"user" : "YOUR_USERNAME",
	"password" : None, #getpass(prompt='AWS Database Password: '),
	"database" : "YOUR_DATABASE_NAME"
}

API_KEY = "YOUR_API_KEY"