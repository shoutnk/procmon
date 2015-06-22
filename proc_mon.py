import os.path
import sys
import time
from datetime import datetime

import send # Send a mail (subject, text)


pids = {}
blocked = 5
listFile = 'proc_list'

p = os.popen('stat --printf=\'%Y\' /proc/1', 'r')
booted = int(p.readline())

class ProcInfo:
  def __init__ (self, pid):
    self.pid = pid
    proc = '/proc/' + str(pid)

    # Command
    with open(proc + '/cmdline', 'r') as f:
      line = f.readline()
      self.cmd = " ".join(line.split('\x00'))

    # Start Time
    with open(proc + '/stat', 'r') as f:
      line = f.readline()
      ticks = int(line.split()[21]) / 100
      self.starttime = booted + ticks

    # Nohup.out
    self.realpath = os.path.realpath(proc + '/cwd')
    self.nohup = self.realpath + '/nohup.out'

  def getNohup(self):
    output = ''
    if os.path.isfile(self.nohup):
      with open(self.nohup, 'rb') as f:
        output = f.read()
    return output

  def getCmd(self):
    return self.cmd

  def getInfo(self):
    starttime = self.starttime
    lasttime  = time.time()

    start  = datetime.fromtimestamp(starttime).strftime('%Y-%m-%d %H:%M:%S')
    finish = datetime.fromtimestamp(lasttime).strftime('%Y-%m-%d %H:%M:%S')

    running = lasttime - starttime
    tm, ts  = divmod(running, 60)
    th, tm  = divmod(tm, 60)
    running = '%d:%02d:%02d' % (th, tm, ts)

    text = 'PID: %d\nCommand: %s\nStart time: %s\nFinish time: %s\nRunning time: %s\n' \
              % (self.pid, self.cmd, start, finish, running)

    return text


while True:
  # Read list file
  with open(listFile, 'r') as f:
    while True:
      pid = f.readline()
      if not pid:  break

      # Ignore invalid inputs (e.g., typo)
      try:
        pid = int(pid)
      except ValueError:
        continue

      # Add to global list
      # Ignore non-exist processes
      if pid not in pids:
        if os.path.exists('/proc/'+str(pid)):
          pids[pid] = ProcInfo(pid)

  keys = [k for k in pids]
  # Find finished processes
  for pid in keys:
    if not os.path.exists('/proc/'+str(pid)):
      fin     = pids[pid]
      subject = fin.getCmd()  + ' is done'
      text    = fin.getInfo() + fin.getNohup()
      send.sendMail(subject, text)
      pids.pop(pid, None)

  # Rewrite list file
  with open(listFile, 'w') as f:
    if len(pids) > 0:
        f.write('\n'.join(map(str, pids)))
        f.write('\n')
    else:
        f.write('')

  # Wait
  time.sleep(blocked)
