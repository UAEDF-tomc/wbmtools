#! /usr/bin/env python

year = '2016'
path = 'HLT_Ele25_eta2p1_WPTight_Gsf'

import json, glob, os, copy
from helpers import loadJSON, dumpJSON, subtractLumis, orLumis, andLumis, getIntLumi

def makeLowestSeedsPage(year, path):
  jsonDir = os.path.join('triggerPrescales', year, 'json', path)
  puData  = loadJSON('../data/pileup_' + year + '.json')

  def lowestSeeds(l1SeedType):
    hasLowerSeed = {}
    isLowestSeed = {}
    for f in sorted(glob.glob(os.path.join(jsonDir, l1SeedType + '*prescale1.json'))):
      l1Seed = f.split('/')[-1].split('_prescale')[0].replace('er', '')
      lumis = subtractLumis(loadJSON(f), hasLowerSeed)
      if not len(lumis): continue
      try:    isLowestSeed[l1Seed] += lumis  # in case both 'er' and non-'er' should be added
      except: isLowestSeed[l1Seed]  = lumis
      hasLowerSeed = orLumis(hasLowerSeed, copy.deepcopy(lumis))  # copy is important here
    return isLowestSeed

  nonIsoSeeds = lowestSeeds('L1_SingleEG')
  isoSeeds    = lowestSeeds('L1_SingleIsoEG')
  try:    os.makedirs(os.path.join(jsonDir, 'lowestSeeds'))
  except: pass

  with open('index.php') as template:
    with open(os.path.join(jsonDir, 'lowestSeeds', 'lowestSeeds.php'), 'w') as f:
      for line in template:
        if 'TITLE' in line:
          f.write('echo "Lowest L1 seed (iso and non-iso) thresholds for ' + path + ' (' + year + ')";\n')
        elif 'DIV' in line:
          f.write('\n')
        elif 'LISTSEEDS' in line:
          for isoSeed in sorted(isoSeeds.keys()):
            for nonIsoSeed in sorted(nonIsoSeeds.keys()):
              lumis = andLumis(isoSeeds[isoSeed], nonIsoSeeds[nonIsoSeed])
              if not len(lumis): continue
              id = (isoSeed + '_' + nonIsoSeed).replace('L1_Single', '')
              dumpJSON(os.path.join(jsonDir, 'lowestSeeds', id + '.json'), lumis)
              f.write('<li>' + id + ' <a href=' + id + '.json>(' + ('%.2f' % getIntLumi(lumis, puData)) + '/fb)</a><br>\n')
        else:
          f.write(line)

