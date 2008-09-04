
import django.contrib.auth.models
import jv3.utils
import jv3.study.emails

users = django.contrib.auth.models.User.objects.filter(email='emax@csail.mit.edu') # jv3.utils.find_even_id_consenting_users()
(subj,body) = jv3.study.emails.emails['p1-1-o']
jv3.utils.email_users(users,subj,body)

users = django.contrib.auth.models.User.objects.filter(email='emax@csail.mit.edu') # jv3.utils.find_odd_id_consenting_users(
(subj,body) = jv3.study.emails.emails['p1-1-e']
jv3.utils.email_users(users,subj,body)
