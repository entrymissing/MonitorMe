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

  if len(argv) > 1:
    func = printerFunc
  else:
    func = submitterFunc

  all_monitors = []
  for mon in monitors:
    curMon = monitor.Monitor(mon['monitor'],
                             mon['frequency'],
                             mon['ts_name'],
                             mon['config'],
                             func)
    curMon.monitor()

if __name__ == '__main__':
  main(sys.argv[1:])
