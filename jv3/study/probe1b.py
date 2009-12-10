
import django.contrib.auth.models
import jv3.utils
import jv3.study.emails

TEST = False
users = None

if TEST:
    users = django.contrib.auth.models.User.objects.filter(email="emax@csail.mit.edu")
else:
    users = jv3.utils.find_even_id_consenting_users()
    
(subj,body) = jv3.study.emails.emails['p1-2-o']
jv3.utils.email_users(users,subj,body)

if TEST:
    users = django.contrib.auth.models.User.objects.filter(email="emax@csail.mit.edu")
else:
    users = jv3.utils.find_odd_id_consenting_users()

(subj,body) = jv3.study.emails.emails['p1-2-e']
jv3.utils.email_users(users,subj,body)
