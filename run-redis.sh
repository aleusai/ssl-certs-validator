#!/bin/bash

# This script has been taken from https://github.com/miguelgrinberg/flasky-with-celery and it is an example of how to 
# start redis (a docker solution is also available). The github repo above also provided the starting guidelines to 
# have celery work in factory mode with Flask: I recommend you also look at the repo above! 

if [ ! -d redis-stable/src ]; then
    curl -O http://download.redis.io/redis-stable.tar.gz
    tar xvzf redis-stable.tar.gz
    rm redis-stable.tar.gz
fi
cd redis-stable
make
src/redis-server
