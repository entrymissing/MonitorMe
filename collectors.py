import random
import time
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
    res = google_api_lib.get_last_location()
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
    res = google_api_lib.get_gmail_length_of_query()
    res.extend(google_api_lib.get_oldest_inbox_mail())
    data_points = []
    for r in res:
      data_points.append((self.prefix + '.' + r[0], r[1], r[2]))
    return data_points
