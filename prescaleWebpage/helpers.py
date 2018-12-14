import json
from FWCore.PythonUtilities.LumiList import LumiList

#
# Load and dump JSON functions
#
def loadJSON(jsonFile):
  with open(jsonFile) as f:
    return json.load(f)

def dumpJSON(jsonFile, data):
  with open(jsonFile, 'w') as f:
    json.dump(data, f)


#
# Get HLT/L1 prescales functions
#
def get_pathname_from_ps_tbl(entry):
  hlt_path = entry.split()[0]
  return hlt_path.split('_v')[0]

def get_hlt_prescales(prescaleTable, pathname):
  for line in prescaleTable:
    if get_pathname_from_ps_tbl(line[1]) == pathname:
      return line
  return None

def get_l1_prescales(l1PrescaleTable, l1Seed):
  for line in l1PrescaleTable:
    if line[1] == l1Seed:
      return line
  return None


#
# opertations using compactlists, using CMSSW json tools
#
def andLumis(grl1, grl2):
  lumis1 = LumiList(compactList=grl1)
  lumis2 = LumiList(compactList=grl2)
  return (lumis1 & lumis2).compactList

def orLumis(grl1, grl2):
  lumis1 = LumiList(compactList=grl1)
  lumis2 = LumiList(compactList=grl2)
  return (lumis1 | lumis2).compactList

def subtractLumis(grl1, grl2):
  lumis1 = LumiList(compactList=grl1)
  lumis2 = LumiList(compactList=grl2)
  return (lumis1-lumis2).compactList


# Get luminosity for given compactList (or also as dictionary building up the int. lumi for each run/lumi)
def getIntLumi(compactList, puData, getDict=False):
  lumiSinceStart = {}
  intLumi = 0
  for run in sorted(compactList.keys(), key=lambda i : int(i)):
    for lumiRange in compactList[run]:
      for lumi in range(lumiRange[0], lumiRange[1]+1):
        for entry in puData[run]:
          if lumi==entry[0]: 
            intLumi += float(entry[1])
            lumiSinceStart[(int(run), lumi)] = intLumi/1e9
  if getDict: return lumiSinceStart
  else:       return intLumi/1e9

# Print active run ranges of compactList
def runRanges(compactList, goodLumis):
  allRuns      = sorted([int(r) for r in goodLumis.keys()])
  selectedRuns = sorted([int(r) for r in compactList.keys()])
  runRanges    = []
  for r in selectedRuns:
    if len(runRanges) and allRuns[allRuns.index(r)-1] == runRanges[-1][1]: runRanges[-1][1] = r
    else:                                                                  runRanges.append([r, r])
  runRanges = [str(runs[0]) if runs[0]==runs[1] else (str(runs[0]) + '-' + str(runs[1])) for runs in runRanges]
  return ', '.join(runRanges)

