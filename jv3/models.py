from django.db import models
import django.contrib.auth.models as authmodels
import django.forms as forms
import django.contrib.admin.sites as sites
from django.contrib import admin
import time


# Create your models here.
class SPO(models.Model):
    owner = models.ForeignKey(authmodels.User,related_name='spo_owner',null=True)
    version = models.IntegerField(default=0)
    timestamp = models.TimeField(auto_now=True,null=True)
    subj = models.TextField()
    pred = models.TextField()
    obj = models.TextField()
    def __str__(self):
        return '%s.%s.%s' % (self.subj, self.pred, self.obj)
    class Admin:
        list_display = ('owner', 'pk', 'version', 'subj', 'pred', 'obj')
        list_filter = ('owner', 'subj', 'pred', 'obj')
        pass
    
class FixedModelChoiceField(forms.ModelChoiceField):
    ## override clean() until Django ticket #7668 is resolved
    def clean(self, value):
        forms.Field.clean(self, value)
        if value in forms.fields.EMPTY_VALUES:
            return None
        try:
            value = self.queryset.get(pk=value.pk)
        except self.queryset.model.DoesNotExist:
            raise forms.util.ValidationError(self.error_messages['invalid_choice'])
        return value

class SPOForm(forms.Form):
    owner = FixedModelChoiceField(
        queryset=authmodels.User.objects,
        cache_choices=True
        )
    version = forms.IntegerField()
    subj = forms.CharField()
    pred = forms.CharField()
    obj = forms.CharField()

    def clean(self):
        return self.cleaned_data
    
## register these with the admin interface, circa django 1.0a
try:
    admin.site.register(SPO)
except sites.AlreadyRegistered,r:
    pass

class Note(models.Model):
    created = models.DecimalField(max_digits=19,decimal_places=0)
    owner = models.ForeignKey(authmodels.User,related_name='note_owner',null=True)
    jid = models.IntegerField(default=0)
    version = models.IntegerField(default=0)
    contents = models.TextField()
    ## we use a nullboolean field because that simplifies validation -- 
    deleted = models.NullBooleanField()
    ## what is this for?
    update_fields = ['contents','created','deleted'] 

class NoteForm(forms.Form):
    created = forms.DecimalField()
    contents = forms.CharField()
    owner = FixedModelChoiceField( queryset=authmodels.User.objects,  cache_choices=True  )
    jid = forms.IntegerField()
    version = forms.IntegerField()
    deleted = forms.NullBooleanField()

try:
    admin.site.register(Note)
except sites.AlreadyRegistered,r:
    pass

## created for new users -- and converted later to a real user
## when they confirm
class UserRegistration(models.Model):
    ## using decimal to make it easier to serialize to JSON than DateTime
    ## (and cant use Integer because it's too big!)
    when = models.DecimalField(max_digits=19,decimal_places=0)
    username = models.TextField(null=True)
    email = models.TextField()
    password = models.TextField()
    cookie = models.TextField()
    couhes = models.BooleanField()
    first_name = models.TextField(null=True)
    last_name = models.TextField(null=True)
    
try:
    admin.site.register(UserRegistration)
except sites.AlreadyRegistered,r:
    pass

def gen_cookie(cookiesize=25):
    import random
    randchar = lambda : chr(ord('a')+random.randint(0,25))
    return ''.join([ randchar() for i in range(cookiesize) ])                

class ChangePasswordRequest(models.Model):
    ## using decimal to make it easier to serialize to JSON than DateTime
    ## (and cant use Integer because it's too big!)
    when = models.DecimalField(max_digits=19,decimal_places=0)
    username = models.TextField()
    cookie = models.TextField()

def makeChangePasswordRequest(username):
    cpr = ChangePasswordRequest()
    cpr.when = int(time.time()*1000);
    cpr.username = username
    cpr.cookie = gen_cookie()
    cpr.save();
    return cpr        

try:
    admin.site.register(ChangePasswordRequest)
except sites.AlreadyRegistered,r:
    pass

class CouhesConsent(models.Model):
    owner = models.ForeignKey(authmodels.User,null=True)
    signed_date = models.IntegerField()

try:
    admin.site.register(CouhesConsent)
except sites.AlreadyRegistered,r:
    pass
    
class ActivityLog(models.Model):
    owner = models.ForeignKey(authmodels.User,null=True)
    when = models.DecimalField(max_digits=19,decimal_places=0)
    action = models.TextField()
    noteid = models.IntegerField(null=True)
    noteText = models.TextField(blank=True,null=True)

try:
    admin.site.register(ActivityLog)
except sites.AlreadyRegistered,r:
    pass


## server side activity logging
class ServerLog(models.Model):
    when = models.DecimalField(max_digits=19,decimal_places=0)
    user = models.ForeignKey(authmodels.User,null=True)
    address = models.IPAddressField()
    type = models.TextField()
    request = models.TextField()
    info = models.TextField(null=True)
    # if the action is "user registration" then this is a pointer to that reg
    registration = models.ForeignKey(UserRegistration,null=True)
    # if the action is "change password requested" then this is a pointer to that reg
    changepasswordrequest = models.ForeignKey(ChangePasswordRequest,null=True)

    def __init__(self,user,type,ip_address,request,info=None,changepasswdrequest=None,registration=None):
        super(ChangePasswordRequest,self).__init__();
        self.when = int(time.time()*1000);
        self.user = user
        self.ip_address = ip_address
        self.info = info
        self.request = request
        self.changepasswordrequest = changepasswdrequest
        self.registration = registration
