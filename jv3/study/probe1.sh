#!/bin/bash

export LISTIT_SERVER=/var/listit/workspace/trunk/server
export DJANGO_SETTINGS_MODULE=settings
export PYTHONPATH=${LISTIT_SERVER}/

date > /tmp/ran.out

(cd ${LISTIT_SERVER}; python2.4 jv3/study/probe1.py)
