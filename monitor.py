import collectors
import time

class Monitor(object):
    def __init__(self, monitor_name, frequency,
                 ts_name, report_callback):
        self._monitor = getattr(collectors, monitor_name)()
        self.frequency = frequency
        self.ts_name = ts_name
        self._last_start = 0
        self._report_callback = report_callback
        self._done = True

    def report_data(self):
        self._last_start = time.time()
        self._done = False
        data, ts = self._monitor.collect_data()
        self._report_callback(self.ts_name, data, ts)
        self._done = True
    
    def monitor(self):
        if (time.time() - self._last_start) > self.frequency:
            self.report_data()