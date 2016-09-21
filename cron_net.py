import subprocess
import time
import socket
import time
import os
import pickle as pkl

CARBON_SERVER = 'dashboard.entrymissing.net'
CARBON_PORT = 2003
DATA_FILE = 'bw_data.pkl'

def measure_bandwidth():
  netstat = subprocess.Popen(['netstat', '-ibI', 'en0'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  stat_line = netstat.stdout.readlines()[1]
  in_bytes = float(stat_line.split()[6])
  out_bytes = float(stat_line.split()[7])

  time.sleep(5)

  netstat = subprocess.Popen(['netstat', '-ibI', 'en0'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  stat_line = netstat.stdout.readlines()[1]
  ib = (float(stat_line.split()[6]) - in_bytes) / 5
  ob = (float(stat_line.split()[7]) - out_bytes) / 5
  return ib, ob

def pull_data():
  netstat = subprocess.Popen(['netstat', '-ibI', 'en0'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  stat_line = netstat.stdout.readlines()[1]
  in_bytes = float(stat_line.split()[6])
  out_bytes = float(stat_line.split()[7])
  return out_bytes, in_bytes

def get_data():
  data = {}
  now = time.time()
  if os.path.exists(DATA_FILE):
    data = pkl.load(open(DATA_FILE, 'rb'))
    if now - data['ts'] > 60 * 5:
      data = {}
   
  if not data:
    sent, recv = pull_data()
    data['ts'] = now
    data['sent_bytes'] = sent
    data['recv_bytes'] = recv
    time.sleep(10)
 
  sent, recv = pull_data()
  now = time.time()
  time_diff = now - data['ts']
  sent_bytes = (sent - data['sent_bytes']) / time_diff
  recv_bytes = (recv - data['recv_bytes']) / time_diff
  data = {}
 
  data['ts'] = now
  data['sent_bytes'] = sent
  data['recv_bytes'] = recv
  pkl.dump(data, open(DATA_FILE, 'wb'))
   
  if sent_bytes < 0 or recv_bytes < 0:
    return 0, 0
  return sent_bytes, recv_bytes

def send_message(path, value):
  timestamp = int(time.time())
  message = '%s %s %d\n' % (path, value, timestamp)

  print 'sending message:\n%s' % message
  sock = socket.socket()
  sock.connect((CARBON_SERVER, CARBON_PORT))
  sock.sendall(message)
  sock.close()

def main():
  ob,ib = get_data()
  send_message('data.net.laptop.in', ib)
  send_message('data.net.laptop.out', ob)

if __name__ == '__main__':
  main()
