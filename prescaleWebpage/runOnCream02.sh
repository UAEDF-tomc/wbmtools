#!/bin/bash
PYTHONUNBUFFERED=TRUE
cd $dir
cd ../CMSSW_10_2_0/src/
source $VO_CMS_SW_DIR/cmsset_default.sh
eval `scram runtime -sh`
cd ../../
source virenv/bin/activate
cd $dir
eval $command
