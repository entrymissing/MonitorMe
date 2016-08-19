import random
import time
import oauth2
import imaplib
import re
import subprocess
import datetime
import email

import google_api_lib
import private_keys


class BaseCollector(object):
  def __init__(self, configs = {}):
    self.setUp(configs)

  def setUp(self, configs):
    pass

  def collect_data(self):
    raise NotImplementedError("Subclasses should implement this!")


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
        data_points.append(['.' + target + '_loss', loss, time.time()])
        data_points.append(['.' + target + '_avg', avg, time.time()])
    return data_points


class CalendarCollector(BaseCollector):
  def setUp(self, configs = {}):
    self.locations = configs.get('locations', ['work', 'home'])

  def collect_data(self):
    service = google_api_lib.connect_to_api()
    res = google_api_lib.get_last_location(service)
    data = []
    for loc in self.locations:
      if res and res[0] == 'entered' and res[1] == loc:
        data.append(('.location.' + loc, 1, res[2]))
      else:
        data.append(('.location.' + loc, 0, res[2]))
    return data


class EMailCollector(BaseCollector):
  def setUp(self, configs = {}):
    # Just copy all configs around in the base constructor
    self.email = configs.get('email', '')
    self.prefix = configs.get('prefix', 'private')
    self.sent_folder = configs.get('sent_folder', '[Google Mail]/Sent Mail')

  def collect_data(self):
    resp = oauth2.RefreshToken(private_keys.GOOGLE_CLIENT_ID,
                               private_keys.GOOGLE_CLIENT_SECRET,
                               private_keys.GOOGLE_REFRESH_TOKEN)
    AT = resp['access_token']
    auth_string = oauth2.GenerateOAuth2String(self.email, AT, base64_encode=False)
    imap_conn = imaplib.IMAP4_SSL('imap.gmail.com')
    imap_conn.authenticate('XOAUTH2', lambda x: auth_string)

    data_points = []

    imap_conn.select('INBOX')
    rv, data = imap_conn.search(None, "ALL")
    if rv != 'OK':
      inbox_size = 0
    else:
      inbox_size = len(data[0].split())
    data_points.append((self.prefix + '.inbox_size', inbox_size, time.time()))

    sent_last_1h_count = 0
    sent_last_12h_count = 0
    sent_last_24h_count = 0
    imap_conn.select(self.sent_folder)
    date = (datetime.date.today() - datetime.timedelta(1)).strftime("%d-%b-%Y")
    rv, data = imap_conn.uid('search', None, '(SENTSINCE {date})'.format(date=date))
    if rv == 'OK':
      for uids in data:
        for u in uids.split():
          type, content = imap_conn.uid('fetch', u, '(RFC822)')
          curMail = email.message_from_string(content[0][1])
          mail_ts = time.mktime(email.utils.parsedate(curMail['Date']))
          if (time.time() - mail_ts) < 60 * 60 * 24:
            sent_last_24h_count += 1
          if (time.time() - mail_ts) < 60 * 60 * 12:
            sent_last_12h_count += 1
          if (time.time() - mail_ts) < 60 * 60 * 1:
            sent_last_1h_count += 1
    data_points.append((self.prefix + '.sent_last_1h', sent_last_1h_count, time.time()))
    data_points.append((self.prefix + '.sent_last_12h', sent_last_12h_count, time.time()))
    data_points.append((self.prefix + '.sent_last_24h', sent_last_24h_count, time.time()))

    imap_conn.logout()
    return data_points
