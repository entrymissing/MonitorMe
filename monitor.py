import datetime
import time
import os
import pickle as pkl

import collectors

class Monitor(object):
  def __init__(self, monitor_name, ts_name, config, report_callback):
    self._monitor = getattr(collectors, monitor_name)(config)
    self.ts_name = ts_name
    self._last_start = 0
    self._report_callback = report_callback
    self._done = True

  def report_data(self):
    self._last_start = time.time()
    self._done = False
    data = self._monitor.collect_data()
    for name_ext, val, ts in data:
      self._report_callback(self.ts_name + name_ext, val, ts)
    self._done = True
    
  def monitor(self):
    self.report_data()
