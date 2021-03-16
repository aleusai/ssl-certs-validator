export PYTHONPATH=`pwd` 
export USERNAME=$USERNAME
export PASSWORD=$PASSWORD
#export CA_PEM_FILE=IncludedRootsPEM.txt
pytest -vv
