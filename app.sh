#export CA_PEM_FILE=$CA_PEM_FILE
export PUSH_GATEWAY_SERVER=http://localhost:9091
export USERNAME=$USERNAME
export PASSWORD=$PASSWORD
. ./env.sh
python3 app.py 
