## File for emailing for misc participation
from django.contrib.auth.models import User
from django.core.mail import EmailMessage

consentSubj = "[List-it] Chrome Beta Announcement"
consentBody = """

"""

nonConsentSubj = "[List-it] Chrome Beta Announcement"
nonConsentBody = """

"""



def bin_users(users):
    bins = [[]]*100
    for user in users:
        bins[user.id % 100].append(user)
    return bins

def get_consenting_bins():
    return bin_users([us for us in User.objects.all() if is_consenting_study2(us)])

def get_nonconsenting_bins():
    return bin_users([us for us in User.objects.all() if not is_consenting_study2(us)])

def email_bin(i, isConsenting):
    print "Sending emails to bin %s, consenting: %s"%(i, isConsenting)
    if isConsenting:
        bins = get_consenting_bins()
        bin = bins[i]
        send_mail_to_bin(bin, isConsenting)
    else:
        bins = get_nonconsenting_bins()
        bin = bins[i]
        send_mail_to_bin(bin, isConsenting)

def send_mail_to_bin(bin, isConsenting):
    global consentSubj, consentBody
    global nonConsentSubj, nonConsentBody
    for user in bin:
        emailSubj = consentSubj if isConsenting else nonConsentSubj
        emailBody = consentBody if isConsenting else nonConsentBody
        email = EmailMessage(consentSubj, consentEmail, 'listit-noreply@csail.mit.edu',
                             [user.email], headers= {'Reply-To':'listit@csail.mit.edu'})
        ## email.send()
        pass
    print "Done sending emails"
        
