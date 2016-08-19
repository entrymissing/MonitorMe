import socket
import sys
import time

import monitor
import private_keys

def printerFunc(metric, data, ts):
  print(metric, data, ts)

def submitterFunc(metric, data, ts):
  message = '%s %s %d\n' % (metric, data, ts)
  
  print('sending message: %s' % message)
  sock = socket.socket()
  sock.connect((private_keys.CARBON_SERVER,
                private_keys.CARBON_PORT))
  sock.sendall(message)
  sock.close()

def main(argv):
  with open(argv[0], 'r') as fp:
    monitors = eval(fp.read())

  all_monitors = []
  for mon in monitors:
    all_monitors.append(monitor.Monitor(mon['monitor'],
                                        mon['frequency'],
                                        mon['ts_name'],
                                        mon['config'],
                                        printerFunc))
  while True:
    for m in all_monitors:
      m.monitor()
    time.sleep(60)

if __name__ == '__main__':
  main(sys.argv[1:])