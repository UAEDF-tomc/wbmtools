# Need a CMSSW release to have python available
scramv1 project CMSSW CMSSW_10_2_0
cd CMSSW_10_2_0/src
eval `scram runtime -sh`
cd -

#install the packages for wbmtools
python -m virtualenv virenv
source virenv/bin/activate
pip install -r requirements.txt
deactivate
cd -
