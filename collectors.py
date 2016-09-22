import datetime
import gzip
import re
import os
import pickle as pkl
import subprocess
import time

import google_api_lib
import private_keys

class BaseCollector(object):
  def __init__(self, configs = {}, sec_since_last_collect = 60*5):
    self.configs = configs
    self.sec_since_last_collect = sec_since_last_collect

    # Load data for this class. If it doesn't exist init it.
    if not os.path.exists(self.get_storage_filename()):
      self.stored_data = self.init_storage_type()
    else:
      with gzip.open(self.get_storage_filename(), 'rb') as fp:
        self.stored_data = pkl.load(fp)

    self.setUp()

  def init_storage_type(self):
    return []
  
  def get_storage_filename(self):
    return 'data/%s.zip' % type(self).__name__
  
  def dump_data(self):
    with gzip.open(self.get_storage_filename(), 'wb') as fp:
      pkl.dump(self.stored_data, fp)

  def setUp(self):
    pass

  def collect_data(self):
    raise NotImplementedError("Subclasses should implement this!")


class BandwidthPsutilCollector(BaseCollector):
  def setUp(self):
    # Time after which we crop data from the local db
    self.MAX_DB_AGE = 14 * 24 * 3600
    
    # Time after which we consider it to be a discontinuity and a gap in data (i.e. the machine was off)
    self.GAP_TIME = 10 * 60
    
    # The prefix for this machine
    self.METRIC_PREFIX = '.desktop.'
    
    # Threshold at which we consider it as distraction (100 kByte)
    self.STREAM_THRESHOLD = 100 * 1024

  def init_storage_type(self):
    return {'last_raw_data': (0, 0, 0),
            'data': []}

  def pull_data(self):
    # Import the lib that may not be present everywhere
    import psutil

    psdata = psutil.net_io_counters(pernic=True)
    return psdata['Wi-Fi'][0], psdata['Wi-Fi'][1]

  def collect_data(self):
    # The return struct
    data_points = []

    # Grab data and precomputed values
    now = time.time()
    sent, recv = self.pull_data()
    latest_ts, latest_sent, latest_recv = self.stored_data['last_raw_data']
    
    # Add, prune and store the new raw data
    self.stored_data['last_raw_data'] = (now, sent, recv)
    while len(self.stored_data['data']) and (now - self.stored_data['data'][0][2]) > self.MAX_DB_AGE:
      self.stored_data['data'].pop(0)
    
    # Detect a discontinuity and set the values around that event to 0
    if (now - latest_ts) > self.GAP_TIME:
      data_points.append((self.METRIC_PREFIX + 'in', 0, latest_ts + self.GAP_TIME/2))
      data_points.append((self.METRIC_PREFIX + 'out', 0, latest_ts + self.GAP_TIME/2))
      data_points.append((self.METRIC_PREFIX + 'in', 0, now))
      data_points.append((self.METRIC_PREFIX + 'out', 0, now))
      
      # Store, dump and return
      self.stored_data['data'].extend(data_points)
      self.dump_data()
      return data_points
  
    # Calculate the bandwidth usage since the last timestamp in Bytes oer second
    time_diff = now - latest_ts
    sent_bytes = (sent - latest_sent) / time_diff
    recv_bytes = (recv - latest_recv) / time_diff
    
    # Check for a recv_ or send_ overflow
    if sent_bytes < 0 or recv_bytes < 0:
      return data_points
    
    # Store and dump
    data_points.append((self.METRIC_PREFIX + 'in', recv_bytes, now))
    data_points.append((self.METRIC_PREFIX + 'out', sent_bytes, now))
    self.stored_data['data'].extend(data_points)
    self.dump_data()
    
    # Compute the amount of time above threshold in last week
    time_above_threshold_7d = 0
    time_above_threshold_today = 0
    last_ts = self.stored_data['data'][0][2]
    
    # Todays day
    day_today =  datetime.datetime.fromtimestamp(now).day

    for d in self.stored_data['data']:
      if d[0].endswith('in'):
        if d[1] > self.STREAM_THRESHOLD:
          # Did the data point happen in the last week
          if (now - d[2]) < 7 * 24 * 60 *60:
            time_above_threshold_7d += (d[2] - last_ts)
          
            # Did the datapoint happen today
            if day_today == datetime.datetime.fromtimestamp(d[2]).day
              time_above_threshold_today += (d[2] - last_ts)
      
      last_ts = d[2]
    data_points.append((self.METRIC_PREFIX + 'consuming_7d', time_above_threshold_7d, now))
    data_points.append((self.METRIC_PREFIX + 'consuming_today', time_above_threshold_today, now))
    return data_points


class BandwidthNetstatCollector(BandwidthPsutilCollector):
  def pull_data(self):
    netstat = subprocess.Popen(['netstat', '-ibI', 'en0'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stat_line = netstat.stdout.readlines()[1]
    in_bytes = float(stat_line.split()[6])
    out_bytes = float(stat_line.split()[7])
    return sent_bytes, recv_bytes

  def setUp(self):
    super(BandwidthNetstatCollector, self).setUp()
    # Overwrite prefix for this machine
    self.METRIC_PREFIX = '.laptop.'

    
class PingCollector(BaseCollector):
  MAX_LINES = 1000

  def collect_data(self):
    cmd = [ 'fping', '-c', str(self.configs['num_pings']) ] + self.configs['ping_targets']
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
  def collect_data(self):
    data = []

    res = google_api_lib.get_last_location()
    for loc in self.configs['locations']:
      if res and res[0] == 'entered' and res[1] == loc:
        data.append(('.current_location.' + loc, self.sec_since_last_collect, res[2]))
      else:
        data.append(('.current_location.' + loc, 0, res[2]))
    
    res = google_api_lib.time_spent_at_locations()
    for loc in self.configs['locations']:
      if loc in res:
        data.append(('.time_at_7d.' + loc, res[loc], time.time()))
      else:
        data.append(('.time_at_7d.' + loc, 0, time.time()))
    
    res = google_api_lib.count_calendar_events_days('Social', num_days = 7)
    data.append(('.num_social_7d', res, time.time()))
    res = google_api_lib.combined_time_for_query(query = 'Social')
    data.append(('.time_social_7d', res, time.time()))

    res = google_api_lib.count_calendar_events_days('Awesome', num_days = 7)
    data.append(('.num_awesome_7d', res, time.time()))
    
    return data


class EMailCollector(BaseCollector):
  def collect_data(self):
    res = google_api_lib.get_gmail_length_of_query()
    res.extend(google_api_lib.get_oldest_inbox_mail())
    data_points = []
    for r in res:
      data_points.append((self.configs['prefix'] + '.' + r[0], r[1], r[2]))
    return data_points
