import settings
import monitor
import time
import socket

def printerFunc(metric, data, ts):
  print metric, data, ts

def submitterFunc(metric, data, ts):
  message = '%s %s %d\n' % (metric, data, ts)
  
  print 'sending message:\n%s' % message
  sock = socket.socket()
  sock.connect((settings.CARBON_SERVER, settings.CARBON_PORT))
  sock.sendall(message)
  sock.close()


if __name__ == '__main__':
  all_monitors = []
  for mon in settings.monitors:
    all_monitors.append(monitor.Monitor(mon['monitor'],
                                        mon['frequency'],
                                        mon['ts_name'],
                                        printerFunc))
  for m in all_monitors:
    m.monitor()
