#
# For T2 running
#
import os, time, subprocess

def system(command):
  return subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)

# Check the cream02 queue, do not submit new jobs when over 2000 (limit is 2500)
def checkQueueOnCream02():
  try:
    queue = int(system('qstat -u $USER | wc -l'))
    if queue > 2000:
      print 'Too much jobs in queue (' + str(queue) + '), sleeping'
      time.sleep(500)
      checkQueueOnCream02()
  except:
    checkQueueOnCream02()

# Cream02 running
def launchCream02(command, logfile, checkQueue=False):
  if checkQueue: checkQueueOnCream02()
  print 'Launching ' + command + ' on cream02'
  qsubOptions = ['-v dir=' + os.getcwd() + ',command="' + command + '"',
                 '-q localgrid@cream02',
                 '-o ' + logfile,
                 '-e ' + logfile,
                 '-l walltime=15:00:00']
  try:    out = system('qsub ' + ' '.join(qsubOptions) + ' runOnCream02.sh')
  except: out = 'failed'
  try:    os.makedirs(os.path.dirname(logfile))
  except: pass
  if not out.count('.cream02.iihe.ac.be'):
    time.sleep(10)
    launchCream02(command, logfile)
