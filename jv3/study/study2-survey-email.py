
from django.contrib.auth.models import User
from jv3.models import *
from jv3.utils import *

INTERVIEWEES = ['emmanuel.ruellan@laposte.net', 'kubonagarei@gmail.com', 'LDD@LDowning.com', 'molly.haber@gmail.com', 'camera1776@yahoo.com', 'amykolo@brandeis.edu', 'jameschu7@gmail.com', 'manishgarg21@gmail.com', 'jamey.hicks@nokia.com', 'tonysr@gmail.com', 'listit@myhisham.otherinbox.com', 'tedbent@earthlink.net', 'adam.simantel@gmail.com', 'rgdarch@aol.com', 'gdtschuller@gmail.com', 'jleecasler@gmail.com', 'kennyosh@gmail.com', 'freemanj@columbus.rr.com', 'justacopy@gmail.com', 'jpjporras0@gmail.com', 'pascal.lemerrer@wanadoo.fr', 'leifer@fas.harvard.edu', 'jillar@mit.edu', 'henry.chang@dmjmhn.aecom.com', 'underthearrow@gmail.com', 'deepak@somatv.com', 'med@ipcbilling.com', 'mcgaheec@swbell.net', 'jjordan8@mac.com', 'cartoonita@yahoo.fr']

EMAIL = """
Hi!

We are collecting information surrounding how people organize their lives and use List-It.  

Your information will be used to compile a research paper summarizing how different people organize their information in different ways.  This paper will, in turn, help designers be able to create better tools for people.  All of your information will be anonymized.

We're raffling off 15 $20 Amazon gift cards randomly to people who fill out the survey COMPLETELY by SUNDAY SEPTEMBER 13 at midnight EDT.

Questions?  Comments?  email listit@csail.mit.edu with subject [List-It Survey].  Thank you!

Here's the link: http://bit.ly/listit-survey

Thanks again,
Prof. David Karger and the List-It Team
"""

TO_SEND = set( [ u for u in User.objects.all() if is_consenting_study2(u) and (u.notes_owner.all().count() > 20) and not (u.email in INTERVIEWEES) ] )

print TO_SEND
print "%d " % len(TO_SEND)


