import argparse
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
  sock.sendto(message.encode(), (private_keys.CARBON_SERVER,
                                 private_keys.CARBON_PORT))
  sock.close()

def main(argv):
  parser = argparse.ArgumentParser()
  parser.add_argument('-s', '--settings', type=str,
                      help="Settings file to use")
  parser.add_argument('--dry_run', action='store_true',
                      help="If set the collection will only print the data that would have been sent.")
  parser.add_argument('--daemon', action='store_true',
                      help="Run as a daemon that collects data every 5 minutes without exiting.")
  args = parser.parse_args()
  
  with open(args.settings, 'r') as fp:
    monitors = eval(fp.read())

  if args.dry_run:
    func = printerFunc
  else:
    func = submitterFunc

  while True:
    all_monitors = []
    for mon in monitors:
      curMon = monitor.Monitor(mon['monitor'],
                               mon['frequency'],
                               mon['ts_name'],
                               mon['config'],
                               func)
      curMon.monitor()
      
    if not args.daemon:
      return
    else:
      time.sleep(5*60)

if __name__ == '__main__':
  main(sys.argv)
