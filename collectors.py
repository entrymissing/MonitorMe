import random
import time
import oauth2
import imaplib
import re
import subprocess

import private_keys


class BaseCollector(object):
  def __init__(self, configs = {}):
    self.setUp(configs)

  def setUp(self, configs):
    pass
    
  def collect_data(self):
    raise NotImplementedError("Subclasses should implement this!")

        
class RandomCollector(BaseCollector):
  def collect_data(self):
    return ['', random.randint(0, 100), time.time()]

        
class PingCollector(BaseCollector):
  MAX_LINES = 1000

  def setUp(self, configs = {}):
    self.ping_targets = configs.get('ping_targets', ['google.com'])
    self.num_pings = configs.get('num_pings', 5)

  def collect_data(self):
    cmd = [ 'fping', '-c', str(self.num_pings) ] + self.ping_targets
    ping_proc = subprocess.Popen(cmd, bufsize=256, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
  
    data_points = []
  
    for l in range(self.MAX_LINES):
      raw_line = ping_proc.stdout.readline()
      if raw_line == '':
        break

      m = re.match('([^ ]*)\s* : xmt/rcv/%loss = \d+/\d+/(\d+)%, min/avg/max = (.*)/(.*)/(.*)', raw_line)
      if m:
        target = m.group(1).replace('.', '_')
        loss = int(m.group(2))
        min = float(m.group(3))
        avg = float(m.group(4))
        max = float(m.group(5))
        data_points.append(['.' + target + '_min', min])
        data_points.append(['.' + target + '_loss', loss])
        data_points.append(['.' + target + '_avg', avg])
        data_points.append(['.' + target + '_max', max])
    return data_points

    
class EMailCollector(BaseCollector):
  def collect_data(self):
    resp = oauth2.RefreshToken(private_keys.GOOGLE_CLIENT_ID,
                               private_keys.GOOGLE_CLIENT_SECRET,
                               private_keys.GOOGLE_REFRESH_TOKEN)
    AT = resp['access_token']
    auth_string = oauth2.GenerateOAuth2String('entrymissing@gmail.com', AT, base64_encode=False)
    imap_conn = imaplib.IMAP4_SSL('imap.gmail.com')
    imap_conn.authenticate('XOAUTH2', lambda x: auth_string)
    imap_conn.select('INBOX')
  
    rv, data = imap_conn.search(None, "ALL")
    if rv != 'OK':
      imap_conn.logout()
      return [('.inbox.len', 0, time.time())]
    imap_conn.logout()
    return [('.inbox.len', len(data[0].split()), time.time())]