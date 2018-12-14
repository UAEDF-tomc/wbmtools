#! /usr/bin/env python

#
# Script to build the webpage used to inspect the L1 prescales
#
# Requirements (json files to be present in ../data):
#  - certified lumis
#  - pilup JSON
#  - json files produced by getRunData.py

#
# Paths to json files
#
certifiedLumis = {'2016' : 'Cert_271036-284044_13TeV_23Sep2016ReReco_Collisions16_JSON.txt',
                  '2017' : 'Cert_294927-306462_13TeV_EOY2017ReReco_Collisions17_JSON.txt',
                  '2018' : 'Cert_314472-325175_13TeV_PromptReco_Collisions18_JSON.txt'}

pileUpJSON       = {y : ('pileup_' + y + '.json')                  for y in ['2016', '2017', '2018']}
runInfoJSON      = {y : ('triggerData' + y + '_runInfo.json')      for y in ['2016', '2017', '2018']}
l1PrescalesJSON  = {y : ('triggerData' + y + '_l1prescales.json')  for y in ['2016', '2017', '2018']}
hltPrescalesJSON = {y : ('triggerData' + y + '_hltprescales.json') for y in ['2016', '2017', '2018']}


#
# Imports
#
import os, argparse, sys, copy, glob, shutil, time
from helpers import get_hlt_prescales, get_l1_prescales, andLumis, orLumis, subtractLumis, loadJSON, dumpJSON, getIntLumi, runRanges
from prescalePlot import prescalePlot

import json
#
# Analyze a given HLT path for a given year
#
def analyzePath(args):
  path, year, minRun, maxRun = args

  # Set prescales[key1][key2][...][run] += lumis and create keys when needed
  def appendLumis(dictionary, keys, run, lumis):
    for k in keys:
      dictionary = dictionary.setdefault(k, {})
    try:    dictionary[run] += lumis
    except: dictionary[run]  = lumis

  # Load the needed JSON
  goodLumis = loadJSON('../data/' + certifiedLumis[year])
  runsInfo  = loadJSON('../data/' + runInfoJSON[year])
  l1psData  = loadJSON('../data/' + l1PrescalesJSON[year])
  hltpsData = loadJSON('../data/' + hltPrescalesJSON[year])
  puData    = loadJSON('../data/' + pileUpJSON[year])

  # Possibility to restrict to specific run range if requested
  if minRun: goodLumis = {r : l for r, l in good_lumis.iteritems() if int(r) >= int(minRun)}
  if maxRun: goodLumis = {r : l for r, l in good_lumis.iteritems() if int(r) <= int(maxRun)}
  if minRun and maxRun: runSpec = 'Run ' + minRun + '-' + maxRun
  elif minRun:          runSpec = year + ', run ' + minRun + ' and above'
  elif maxRun:          runSpec = year + ', up to run ' + maxRun
  else:                 runSpec = year

  # Create dictionary prescales[path/seed][prescale][run] with lumi ranges
  prescales = {}
  for run in sorted(runsInfo.keys()):
    if minRun and int(run) < int(minRun): continue
    if maxRun and int(run) > int(maxRun): continue
    hltMenu  = runsInfo[run]['hlt_menu']
    trigMode = runsInfo[run]['trig_mode']
    psCols   = runsInfo[run]['ps_cols']

    prescaleMap = {path : get_hlt_prescales(hltpsData[hltMenu], path)}

    # if HLT path not found in this menu, put this run in the "not existing" group
    if not prescaleMap[path]: 
      appendLumis(prescales, [path, 'NotExisting'], run, [[1, 0xFFFFFFF]])
      continue

    # Get the OR of all L1 seeds
    l1OR = prescaleMap[path][-1]
    for l1trigger in l1OR.split(' OR '):
      prescaleMap[l1trigger] = get_l1_prescales(l1psData[trigMode], l1trigger.replace(' ', ''))

    # Loop over all prescale columns, and add their lumis to the correponding prescale for a path/seed
    for psColumn, lumis in psCols.iteritems():
      psIndex = int(psColumn)+2
      for trigger, pathPrescales in prescaleMap.iteritems():
        if not pathPrescales: continue
        prescale = pathPrescales[psIndex]
        appendLumis(prescales, [trigger, prescale], run, copy.deepcopy(lumis))

  # Check in which lumis the HLT path was off (prescale 0 or not existing) or on
  hltPathOff, hltPathOn = {}, {}
  for i in prescales[path]:
    if i in ['0', 'NotExisting']: hltPathOff.update(copy.deepcopy(prescales[path][i]))
    else:                         hltPathOn.update(copy.deepcopy(prescales[path][i]))

  # Some lumis were missing in the runInfo json, while they are present in the certified lumis; these have prescale column -1 in wbm which means all paths/seeds are unprescaled
  missingLumis = subtractLumis(goodLumis, orLumis(hltPathOn, hltPathOff))
  for trigger in prescales:
    try:    prescales[trigger]['1'] = orLumis(prescales[trigger]['1'], missingLumis)
    except: prescales[trigger]['1'] = missingLumis
  hltPathOn = andLumis(goodLumis, orLumis(hltPathOn, missingLumis))

  # Check if there are missing lumis for the seeds
  for trigger in [t for t in prescales if t != path]:
    prescales[trigger]['NotIncluded'] = copy.deepcopy(hltPathOn)
    for ps in [ps for ps in prescales[trigger].keys() if ps != 'NotIncluded']:
      if 'L1_SingleEG40' in trigger: 
        print prescales[trigger]['NotIncluded']
        print
        print 'Subtracting ' + ps
      prescales[trigger]['NotIncluded'] = subtractLumis(prescales[trigger]['NotIncluded'], prescales[trigger][ps])
    if 'L1_SingleEG40' in trigger:
      print prescales[trigger]['NotIncluded']
      print

  # Clean up: only keep lumis which are certified, do not show the L1 seeds for lumis where the HLT path is off
  for trigger in prescales:
    for ps in prescales[trigger].keys():
      prescales[trigger][ps] = andLumis(prescales[trigger][ps], goodLumis if trigger == path else hltPathOn)
      if not len(prescales[trigger][ps]): del prescales[trigger][ps]
      
  # Remove those seeds with only 0 and NotInclude
  for trigger in [t for t in prescales if t != path]:
    if trigger != path:
      nonZeroKeys = [k for k in prescales[trigger].keys() if k not in ['0', 'NotIncluded']]
      if not len(nonZeroKeys): del prescales[trigger]

  # Output to file
  topDir  = os.path.join('triggerPrescales', year)
  jsonDir = os.path.join('triggerPrescales', year, 'json', path)
  try:    os.makedirs(jsonDir)
  except: pass
  shutil.copy('index.php', 'triggerPrescales/index.php')
  shutil.copy('index.php', os.path.join(topDir, 'index.php'))

  div = prescalePlot(path, prescales, year, goodLumis, puData, runsInfo)
  with open('index.php') as template:
    with open(os.path.join(topDir, path + '.php'), 'w') as f:
      for line in template:
        if 'TITLE' in line:
          f.write('echo "Prescales for ' + path + ' (' + runSpec + ')";\n')
        elif 'DIV' in line:
          f.write(div + '\n')
        elif 'LISTSEEDS' in line:
          f.write('<div class="list2" style="margin-top: 2cm">\n<ul>\n')
          for trigger in sorted(prescales.keys()):
            if trigger==path: f.write('<li><b>' + trigger + '</b> (' + runSpec + ') <br>\n')
            else:             f.write('<li><b>' + trigger + '</b><br style="line-height:110%">\n')
            for ps in sorted(prescales[trigger].keys()):
              lumis = prescales[trigger][ps]
              dumpJSON(os.path.join(jsonDir, trigger + '_prescale' + str(ps) + '.json'), lumis)
              f.write('  ' + ('prescale ' if not 'No' in str(ps) else '') + str(ps) + ' <a href=' + os.path.join('json', path, trigger + '_prescale' + str(ps) + '.json') +'>(' + ('%.2f' % getIntLumi(lumis, puData)) + '/fb)</a>')
              f.write(' <small><small><small>active in runs ' + runRanges(lumis, goodLumis if trigger==path else hltPathOn) + '</small></small></small><br>\n')
            f.write('</li>\n')  
          f.write('</ul></div>\n')
        else:
          f.write(line)

#
# Get all HLT paths which include some EGamma object
#
def getAllPaths(year):
  paths = []
  for hltData in loadJSON('../data/' + hltPrescalesJSON[year]).values():
    for hlt in hltData:
      if 'HLT_' in hlt[1] and any(x in hlt[1] for x in ['Ele', 'Pho', 'ele', 'pho', 'SC']):
       paths.append(hlt[1].split('_v')[0])
  return list(set(paths))


#
# Main function
#
if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument('--year',       default=None,  help="Select 2016, 2017, 2018. Default None produces all of them")
  parser.add_argument('--path',       default=None,  help="Select path. Default None produces all of them")
  parser.add_argument('--minRun',     default=None,  help="Do not consider runs below this run number")
  parser.add_argument('--maxRun',     default=None,  help="Do not consider runs above this run number")
  parser.add_argument('--cores',      default=1,     help="Run on multiple cores")
  parser.add_argument('--useCluster', default=False, help="Run using pbs cluster", action='store_true')
  parser.add_argument('--overwrite',  default=False, help="Overwrite existing pages", action='store_true')
  args = parser.parse_args()

  if not args.year: years = ['2016', '2017', '2018']
  else:             years = [args.year]

  jobs = []
  for year in years:
    if not args.path: paths = getAllPaths(year)
    else:             paths = [args.path]

    for path in paths:
      if not args.overwrite and (os.path.exists(os.path.join('triggerPrescales', year, path + '.php'))): 
        print 'Found already php file for ' + path + ' (' + year + '), skipping'
        continue
      jobs.append((path, year, args.minRun, args.maxRun))
      print 'Added job for ' + path + ' (' + year + ')'

  if args.useCluster:
    from jobSubmitter import launchCream02
    for i, job in enumerate(jobs):
      path, year, minRun, maxRun = job
      if ' ' in path: continue
      command = './makePrescaleWebpage.py --path=' + path + ' --year=' + year + (' --overwrite' if args.overwrite else '')
      if minRun: command += ' --minRun=' + minRun
      if maxRun: command += ' --maxRun=' + maxRun
      logFile = './log/' + path + '_' + year + '.log'
      launchCream02(command, logFile, checkQueue=(i%100==0))
  elif int(args.cores) > 1:
    from multiprocessing import Pool
    pool = Pool(processes=int(args.cores))
    pool.map(analyzePath, jobs)
    pool.close()
    pool.join()
  else:
    map(analyzePath, jobs)

