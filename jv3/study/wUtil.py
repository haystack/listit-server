import os,sys
import re as re
from django.contrib.auth.models import User
from datetime import datetime as dd  # Stacked Bar Graph Function Helpers


## Models ##

user_from_email = lambda mail: User.objects.filter(email=mail)[0]


## String##
str_sum_words = lambda str: len([w for w in re.compile('\s').split(str) if len(w.strip())>0])
str_sum_lines = lambda str: len([w for w in re.compile('\n').split(str) if len(w.strip())>0])

str_to_words = lambda str: [w for w in re.compile('\s').split(str) if len(w.strip())>0]
str_to_lines = lambda str: [w for w in re.compile('\n').split(str) if len(w.strip())>0]

ave_words_per_line = lambda str: float(str_sum_words(str))/float(str_sum_lines(str)) if str_sum_lines(str) != 0 else 0


## Time ##
msecToDate = lambda msec : dd.fromtimestamp(float(msec)/1000.0)

