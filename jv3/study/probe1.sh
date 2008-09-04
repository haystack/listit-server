#!/bin/bash

export LISTIT_SERVER=/z/home/emax/listit-server/trunk/server
export DJANGO_SETTINGS_MODULE=settings
export PYTHONPATH=${LISTIT_SERVER}/

(cd ${LISTIT_SERVER}; python2.5 jv3/study/probe1.py)
