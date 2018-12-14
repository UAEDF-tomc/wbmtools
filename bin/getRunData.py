#!/usr/bin/env python
import sys
import math
import time
import json
import os
import wbmtools.wbmutil as wbmutil
from wbmtools.wbmparser import WBMParser


def convert_to_ranges(vals):
    vals.sort()
    ranges = []
    prev_val = -1
    start_val = -1
    for val in vals:
        if val - prev_val > 1:
            if prev_val != -1 :
                ranges.append([start_val,prev_val])
            start_val = val
        prev_val = val
    
    ranges.append([start_val,prev_val])
    return ranges

class FileSuffexes:
    def __init__(self):
        self.run_info = "_runInfo.json"
        self.l1_prescales = "_l1prescales.json"
        self.hlt_prescales = "_hltprescales.json"

def read_json_data(file_name,args):
    if args.update and args.recreate:
        print "--update and --recreate are mutually exclusive options"
        sys.exit() 
    json_data={}
    if args.update and os.path.isfile(file_name):
        with open(file_name) as f:
            json_data = json.load(f)
    elif args.update and not os.path.isfile(file_name):
        print "--update option chosen but file ",file_name,"does not exist"
        sys.exit()
    return json_data
        
            

import argparse
parser = argparse.ArgumentParser(description='dumps informatation about the runs ')
parser.add_argument('--runs',required=False,nargs="+",help='runs to output')
parser.add_argument('--grl',required=False,help='good lumi list')
parser.add_argument('--out_basename','-o',help='output base name (outputs <out_basename>_runInfo.json, <out_basename>_l1prescales.json, <out_basename>_hltprescales.json',required=True)
parser.add_argument('--update','-u',action='store_true',help='updates an existing files')
parser.add_argument('--recreate',action='store_true',help='re-creates an existing file')
args = parser.parse_args()

wbmparser=WBMParser()

runs = []

if args.runs is not None and args.grl is not None:
    print "args error, --runs and --grl are mutually exclusive options"
    sys.exit()
if args.runs is not None:
    runs = args.runs
if args.grl is not None:
    with open(args.grl) as f:
        good_lumis = json.load(f)
        runs = good_lumis.keys()
if runs == []:
    runs=wbmutil.get_runs_from_fills("2018.01.01","2019.01.01",wbmparser)
runs.sort()

runs_data = read_json_data(args.out_basename+FileSuffexes().run_info,args)
l1_prescale_data = read_json_data(args.out_basename+FileSuffexes().l1_prescales,args)
hlt_prescale_data = read_json_data(args.out_basename+FileSuffexes().hlt_prescales,args)


bad_runs = []
bad_runs_lumi = []
nr_runs = len(runs)
pre_time = time.time()

for index,run in enumerate(runs):
    if run in runs_data: continue
    cur_time = time.time()
    print "processing {} ({}/{}), time taken: {:.1f}".format(run,index+1,nr_runs,cur_time-pre_time)
    pre_time=cur_time
    run_data={}
    ps_col_data ={}

    try:
        runinfo=wbmutil.get_run_info(run,wbmparser)
    except IndexError:
        print "  error reading run info for run",run
        bad_runs.append(run)
        continue

    try:
        lumis_by_ps = wbmutil.get_lumis_vs_pscol( run,wbmparser)    
        ps_cols = lumis_by_ps.keys();
        ps_cols.sort()
        for ps_col in ps_cols:
            if ps_col != -1: 
                ls_ranges=convert_to_ranges(lumis_by_ps[ps_col])
                ps_col_data[ps_col] = ls_ranges 
    except IndexError:
        print "  error reading lumi section info for run",run
        bad_runs_lumi.append(run)

    run_data["ps_cols"] = ps_col_data
    run_data["hlt_menu"] = runinfo["hltMenu"]
    run_data["l1_key"] = runinfo["l1Key"]
    run_data["l1_menu"] = runinfo["l1Menu"]
    run_data["trig_mode"] = runinfo["trigKey"]
    run_data["fill"] = runinfo["fill"]
    run_data["lumi"] = runinfo["lumi"]
    run_data["start"] = runinfo["start"]
    run_data["end"] = runinfo["end"]
    run_data["cmssw_version"] = runinfo["cmsswVersion"]
    runs_data[run] = run_data

    trig_mode = run_data['trig_mode']
    if trig_mode not in l1_prescale_data:
        l1_prescale_set = wbmutil.get_prescale_set(run,wbmparser)
        l1_prescale_data[trig_mode] = l1_prescale_set

    hlt_menu = run_data['hlt_menu']
    if hlt_menu not in hlt_prescale_data:
        hlt_prescale_set = wbmutil.get_hltprescales(trig_mode,wbmparser)
        hlt_prescale_data[hlt_menu] = hlt_prescale_set



with open(args.out_basename+FileSuffexes().run_info, 'w') as outfile:
    json.dump(runs_data, outfile,sort_keys = True)
with open(args.out_basename+FileSuffexes().l1_prescales, 'w') as outfile:
    json.dump(l1_prescale_data, outfile)
with open(args.out_basename+FileSuffexes().hlt_prescales, 'w') as outfile:
    json.dump(hlt_prescale_data, outfile)

print "badruns: ",bad_runs
print "badrunslumi: ",bad_runs_lumi
