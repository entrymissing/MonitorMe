import psutil
import time
import socket
import pickle as pkl
import os
import private_keys

DATA_FILE = 'C:\\Users\\David\\Dropbox\\Projects\\MonitorMe\\data\\bw_data.pkl'
METRIC_PREFIX = 'data.net.desktop.'
MAX_DB_TIME = 7 * 60

def pull_data():
  psdata = psutil.net_io_counters(pernic=True)
  return psdata['Wi-Fi'][0], psdata['Wi-Fi'][1]

def get_data():
  data = {}
  data_points = []
  now = time.time()

  if os.path.exists(DATA_FILE):
    data = pkl.load(open(DATA_FILE, 'rb'))
    
    # Check if there is a data disconuity
    if now - data['ts'] > MAX_DB_TIME:
      data_points.append((METRIC_PREFIX + 'in', 0, data['ts'] + 120))
      data_points.append((METRIC_PREFIX + 'out', 0, data['ts'] + 120))
      data_points.append((METRIC_PREFIX + 'in', 0, now - 120))
      data_points.append((METRIC_PREFIX + 'out', 0, now - 120))
      data = {}
  
  # Fake historic data by counting next 10 seconds
  if not data:
    sent, recv = pull_data()
    data['ts'] = now
    data['sent_bytes'] = sent
    data['recv_bytes'] = recv
    time.sleep(10)

  # Get current data and com
  sent, recv = pull_data()
  now = time.time()
  time_diff = now - data['ts']
  sent_bytes = (sent - data['sent_bytes']) / time_diff
  recv_bytes = (recv - data['recv_bytes']) / time_diff

  # Create the new data package and write it to disk
  data = {}
  data['ts'] = now
  data['sent_bytes'] = sent
  data['recv_bytes'] = recv
  pkl.dump(data, open(DATA_FILE, 'wb'))
  
  # Check for a recv_ or send_ overflow
  if sent_bytes < 0 or recv_bytes < 0:
    return data_points
  
  data_points.append((METRIC_PREFIX + 'in', recv_bytes, now))
  data_points.append((METRIC_PREFIX + 'out', sent_bytes, now))
  return data_points

def submitterFunc(metric, data, ts):
  message = '%s %s %d\n' % (metric, data, ts)
  
  print('sending message: %s' % message)
  sock = socket.socket()
  sock.connect((private_keys.CARBON_SERVER,
                private_keys.CARBON_PORT))
  sock.sendto(message.encode('utf-8'), (private_keys.CARBON_SERVER, private_keys.CARBON_PORT))
  sock.close()

def main():
  data_points = get_data()
  print(data_points)
  for d in data_points:
    submitterFunc(d[0], d[1], d[2]) 
  
if __name__ == '__main__':
  main()
