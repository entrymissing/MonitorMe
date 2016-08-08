import random
import time
import oauth2
import imaplib

import private_keys

class BaseCollector(object):
    def collect_data(self):
        raise NotImplementedError("Subclasses should implement this!")

class RandomCollector(BaseCollector):
    def collect_data(self):
        return random.randint(0, 100), time.time()

class EMailCollector(BaseCollector):
  def collect_data(self):
    resp = oauth2.RefreshToken(private_keys.GOOGLE_CLIENT_ID, private_keys.GOOGLE_CLIENT_SECRET, private_keys.GOOGLE_REFRESH_TOKEN)
    AT = resp['access_token']
    auth_string = oauth2.GenerateOAuth2String('entrymissing@gmail.com', AT, base64_encode=False)
    imap_conn = imaplib.IMAP4_SSL('imap.gmail.com')
    imap_conn.authenticate('XOAUTH2', lambda x: auth_string)
    imap_conn.select('INBOX')
  
    rv, data = imap_conn.search(None, "ALL")
    if rv != 'OK':
      print "No messages found!"
      imap_conn.logout()
      return 0
    imap_conn.logout()
    print data
    return len(data[0].split()), time.time()