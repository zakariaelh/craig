import datetime

import firebase_admin
from firebase_admin import credentials, db
from credentials import DB_URL


class FirebaseDataService(object):
    def __init__(self, firebasekey_path):
        self.firebasekey_path = firebasekey_path
        self.default_app = None
        if len(firebase_admin._apps) == 0:
            self.connect()

    def connect(self):
        """init firebase app"""
        cred = credentials.Certificate(self.firebasekey_path)
        default_app = firebase_admin.initialize_app(
            credential=cred,
            options={'databaseURL': DB_URL}
        )
        self.default_app = default_app

    def update_data(self, db_name, data=None):
        assert isinstance(data, (dict, type(None)))

        ref = db.reference(db_name)
        ref.update(data)

    def format_df(self, df, key_column='key', add_date=True):
        """
        Converts a pd DataFrame to a dict with keys (key_column + datetime.today (optional))
        :param df: pd DataFrame
        :param key_column: the name of the column that should represent the key
        :param add_date: add date if True to key
        """
        # add date to df
        df['datestr'] = datetime.datetime.today().strftime('%Y%m%d')
        if add_date:
            # the databse key is the keycolumn + date
            df['db_key'] = df['datestr'] + df[key_column].astype(str)
        else:
            df['db_key'] = df[key_column].astype(str)
        dict_res = df.set_index('db_key').T.to_dict()
        return dict_res
