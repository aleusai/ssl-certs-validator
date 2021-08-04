#!/usr/bin/env python
# This script has been taken from https://github.com/miguelgrinberg/flasky-with-celery. 
# The github repo above also provided the starting guidelines to
# have celery work in factory mode with Flask: I recommend you also look at the repo above!

import os
from app import celery, create_app

app = create_app()
app.app_context().push()
