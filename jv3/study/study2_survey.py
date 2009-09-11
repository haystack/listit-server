
from django.contrib.auth.models import User
from jv3.models import *
from jv3.utils import *

em = User.objects.filter(email="emax@csail.mit.edu")[0]

INTERVIEWEES = ['emmanuel.ruellan@laposte.net', 'kubonagarei@gmail.com', 'LDD@LDowning.com', 'molly.haber@gmail.com', 'camera1776@yahoo.com', 'amykolo@brandeis.edu', 'jameschu7@gmail.com', 'manishgarg21@gmail.com', 'jamey.hicks@nokia.com', 'tonysr@gmail.com', 'listit@myhisham.otherinbox.com', 'tedbent@earthlink.net', 'adam.simantel@gmail.com', 'rgdarch@aol.com', 'gdtschuller@gmail.com', 'jleecasler@gmail.com', 'kennyosh@gmail.com', 'freemanj@columbus.rr.com', 'justacopy@gmail.com', 'jpjporras0@gmail.com', 'pascal.lemerrer@wanadoo.fr', 'leifer@fas.harvard.edu', 'jillar@mit.edu', 'henry.chang@dmjmhn.aecom.com', 'underthearrow@gmail.com', 'deepak@somatv.com', 'med@ipcbilling.com', 'mcgaheec@swbell.net', 'jjordan8@mac.com', 'cartoonita@yahoo.fr']

EMAIL_SUBJECT = "Complete a short survey for List-It, chance to win $20!"


EMAIL = """

Hi!

We're e-mailing you because you volunteered to participate in Notes for Science, MIT's note-taking research study.  We appreciate your participation in the study and thank you for helping us out!

Right now, we're wrapping up a phase of our research and are looking for your help in completing a short survey. 

Your information will be used to compile a research paper summarizing how different people organize their information in different ways.  This paper will, in turn, help designers be able to create better tools for people.  All of your information will be anonymized.

We're raffling off 15 $20 Amazon gift cards randomly to people who fill out the survey COMPLETELY by SUNDAY SEPTEMBER 13 at midnight EDT.

Here's the link to the survey: http://bit.ly/listit-survey

Questions?  Comments?  email listit@csail.mit.edu with subject [List-It Survey].  Thank you!

Thanks again,
Prof. David Karger and the List-It Team
"""


#print TO_SEND
#print "%d " % len(TO_SEND)e

TO_SEND = None

def _compute_send :
    global TO_SEND
    TO_SEND = set( [ u for u in User.objects.all() if is_consenting_study2(u) and (u.note_owner.all().count() > 10) and not (u.email in INTERVIEWEES) ] )

def test_send_plea():
    email_users([em],EMAIL_SUBJECT,EMAIL)

def send_pilots():
    global TO_SEND
    if TO_SEND is None:
        _compute_send()
    pilots = TO_SEND[0:30]
    email_users(pilots,EMAIL_SUBJECT,EMAIL)


    





