from django.db import models
import django.contrib.auth.models as authmodels
import django.forms as forms
import django.contrib.admin.sites as sites
from django.contrib import admin
from django.conf import settings
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
    edited = models.DecimalField(max_digits=19,decimal_places=0)
    owner = models.ForeignKey(authmodels.User,related_name='note_owner',null=True)
    jid = models.IntegerField(default=0)
    version = models.IntegerField(default=0)
    contents = models.TextField(blank=True)
    ## we use a nullboolean field because that simplifies validation -- 
    deleted = models.NullBooleanField()
    ## what is this for?
    update_fields = ['contents','created','deleted','edited']
    def __unicode__(self):
        import utils
        return unicode('[%s-%d-v%d-%s] (%s/%s) %s' % (repr(self.owner.username), self.jid, self.version, repr(self.deleted), utils.decimal_time_to_str(self.created), utils.decimal_time_to_str(self.edited), self.contents[:30]))
##    return unicode('[%s-%d] %s/%s v.%d d? %s %s' % (repr(self.owner.username), self.jid,utils.decimal_time_to_str(self.created), utils.decimal_time_to_str(self.edited), self.version, repr(self.deleted), repr(utils.contents)[:20]))
#         except ValueError,e:
#            print e


    
# class NoteForm(forms.Form):
#     created = forms.DecimalField()
#     edited = forms.DecimalField()
#     contents = forms.CharField(required=False)
#     owner = FixedModelChoiceField( queryset=authmodels.User.objects,  cache_choices=True  )
#     jid = forms.IntegerField()
#     version = forms.IntegerField()
#     deleted = forms.NullBooleanField()

class NoteForm(forms.ModelForm):
    class Meta:
        model = Note
        pass
    pass

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

    def __unicode__(self):
        import utils
        return unicode('[%s] - %s - %s: %s %s' % (utils.decimal_time_to_str(self.when),self.username,repr(self.couhes),repr(self.first_name),repr(self.last_name)))
    
    def clone(self):
        ur = UserRegistration()
        ur.email = self.email
        ur.when = self.when
        ur.username = self.username
        ur.password = self.password
        ur.cookie = self.cookie
        ur.first_name = self.first_name
        ur.last_name = self.last_name
        ur.couhes = self.couhes
        return ur
    
try:
    admin.site.register(UserRegistration)
except sites.AlreadyRegistered,r:
    pass

class ChangePasswordRequest(models.Model):
    ## using decimal to make it easier to serialize to JSON than DateTime
    ## (and cant use Integer because it's too big!)
    when = models.DecimalField(max_digits=19,decimal_places=0)
    username = models.TextField()
    cookie = models.TextField()

try:
    admin.site.register(ChangePasswordRequest)
except sites.AlreadyRegistered,r:
    pass

class CouhesConsent(models.Model):
    owner = models.ForeignKey(authmodels.User,null=True)
    signed_date = models.DecimalField(max_digits=19,decimal_places=0)

try:
    admin.site.register(CouhesConsent)
except sites.AlreadyRegistered,r:
    pass
    
class ActivityLog(models.Model):
    owner = models.ForeignKey(authmodels.User,null=True)
    client = models.CharField(max_length=255,null=True)
    when = models.DecimalField(max_digits=19,decimal_places=0)
    action = models.TextField()
    noteid = models.IntegerField(null=True)
    noteText = models.TextField(blank=True,null=True)
    search = models.TextField(null=True)
    def __unicode__(self):
        import utils
        return unicode('[%s %s] - note:%s %s %s' % (repr(self.owner.username),utils.decimal_time_to_str(self.when),repr(self.noteid),self.action,self.search))

try:
    admin.site.register(ActivityLog)
except sites.AlreadyRegistered,r:
    pass

## server side activity logging
class ServerLog(models.Model):
    when = models.DecimalField(max_digits=19,decimal_places=0)
    user = models.ForeignKey(authmodels.User,null=True)
    host = models.TextField()
    url = models.TextField()
    action = models.TextField()
    request = models.TextField()
    info = models.TextField(null=True)
    # if the action is "user registration" then this is a pointer to that reg
    registration = models.ForeignKey(UserRegistration,null=True)
    # if the action is "change password requested" then this is a pointer to that reg
    changepasswordrequest = models.ForeignKey(ChangePasswordRequest,null=True)

try:
    admin.site.register(ServerLog)
except sites.AlreadyRegistered,r:
    pass

# introduced 9-4-2010 for saving the server from death.
class CachedLogStats(models.Model):
    user = models.ForeignKey(authmodels.User,null=True)
    client = models.CharField(max_length=255,null=True)
    maxdate = models.DecimalField(max_digits=19,decimal_places=0)
    count = models.DecimalField(max_digits=19,decimal_places=0)
    
# introduced 9-4-2010 for saving the server from death.
class CachedActivityLogStats(CachedLogStats):
    #start = models.ForeignKey(ActivityLog,null=True)
    #end = models.ForeignKey(ActivityLog,null=True)
    pass

class BugReport(models.Model):
    when = models.DecimalField(max_digits=19,decimal_places=0)
    username = models.TextField()
    description = models.TextField()
    def __unicode__(self):
        import utils
        return "[%s - %s]: %s" % (utils.decimal_time_to_str(self.when),self.username,self.description)
try:
    admin.site.register(BugReport)
except sites.AlreadyRegistered,r:
    pass


## i want to move this guy to another file but i really don't have any idea
## how to point django to a file other than models.py
if hasattr(settings, "ACTIVITY_CONTEXT_MODELS") and settings.ACTIVITY_CONTEXT_MODELS:
    class Event(models.Model):
        owner = models.ForeignKey(authmodels.User)
        client = models.CharField(max_length=255,null=True)
        type = models.CharField(max_length=255)
        start = models.DecimalField(max_digits=19,decimal_places=0)
        end = models.DecimalField(max_digits=19,decimal_places=0)
        entityid = models.TextField()
        entitytype = models.CharField(max_length=255)
        entitydata = models.TextField()
        pass

    class CachedEventLogStats(CachedLogStats):
        # start = models.ForeignKey(Event,null=True)
        # end = models.ForeignKey(Event,null=True)
        pass        

if hasattr(settings, 'DEFINE_SURVEY') and settings.DEFINE_SURVEY:
    class SurveyQuestion(models.Model):
        user = models.ForeignKey(authmodels.User)
        qid = models.TextField()
        response = models.TextField(blank=True)
        def __unicode__(self):
            import utils
            return "[%s - %s]: %s" % (self.user.email,self.qid,self.response or "")

    class SurveyDoneDeclaration(models.Model):
        user = models.ForeignKey(authmodels.User)
        when = models.DecimalField(max_digits=19,decimal_places=0)
        def __unicode__(self):
            import utils
            return "[%s]: %s" % (self.user.email,self.when)

    try:
        admin.site.register(SurveyQuestion)
        admin.site.register(SurveyDoneDeclaration)
    except sites.AlreadyRegistered,r:
        pass


##  Redaction Models ##

class RedactedSkip(models.Model):
    # Keeps track of notes a user doesn't want to redact.
    owner = models.ForeignKey(authmodels.User,related_name='skipped_redacted_note_owner',null=True)
    jid = models.IntegerField(default=0)
    version = models.IntegerField(default=0)

class RedactedNote(models.Model):
    ## Original Note Data
    nCreated = models.DecimalField(max_digits=19,decimal_places=0)
    nEdited  = models.DecimalField(max_digits=19,decimal_places=0)
    nDeleted = models.NullBooleanField()

    owner = models.ForeignKey(authmodels.User,related_name='redacted_note_owner',null=True)
    created = models.DecimalField(max_digits=19,decimal_places=0)
    jid = models.IntegerField(default=0)
    version = models.IntegerField(default=0)
    contents = models.TextField(blank=True)
    
    noteType = models.CharField(max_length=50)
    points   = models.DecimalField(max_digits=19,decimal_places=0)

    update_fields = ['contents', 'created', 'origDeleted']
    def __unicode__(self):
        import utils
        return unicode('(%s-%s-%s) [User: %s, ID: %d, Ver: %s] (%s / %s) %s' % (
            self.origCreated, self.origEdited, self.origDeleted, repr(self.owner.username), self.jid, self.version,
            utils.decimal_time_to_str(self.created), self.noteType,
            self.contents[:30]))
        #return unicode('[%s-%d-v%d] (%s) %s' % (repr(self.owner.username), self.jid, self.version,
        #utils.decimal_time_to_str(self.created), self.contents[:30]))

# Stores mappings for types of words from originalWord to replacementWord,
# to maintain consistency across multiple saved redacted notes (ie, name = "bob" maps to "name_3" for owner 1
class WordMap(models.Model):
    owner    = models.ForeignKey(authmodels.User,related_name='word_map_owner',null=True)
    wordType = models.TextField(blank=True)
    privWord = models.TextField(blank=True) ## Private - not to be shown to others (original word in note)
    pubWord  = models.TextField(blank=True) ## Public  - word chosen to replace privWord
    def __unicode__(self):
        import utils
        return unicode('o:%s, type:%s, (%s / %s)' % (
            repr(self.owner.username), self.wordType, self.originalWord, self.replacementWord))


# Stores meta information about a redacted note's redacted-words
class WordMeta(models.Model):
    rNote      = models.ForeignKey(RedactedNote,related_name='redacted_word_meta',null=True)
    wordIndex  = models.DecimalField(max_digits=19,decimal_places=0)
    wordMap    = models.ForeignKey(WordMap, related_name='redacted_word_map')
    def __unicode__(self):
        import utils
        return unicode('(Note:%s), i:%s, map:%s' % (repr(self.redactedNote), self.wordIndex, self.wordMap))

## Register RedactedSkip, RedactedNote, WordMeta, WordMap
try:
    admin.site.register(RedactedSkip)
except sites.AlreadyRegistered,r:
    pass

try:
    admin.site.register(RedactedNote)
except sites.AlreadyRegistered,r:
    pass

try:
    admin.site.register(WordMap)
except sites.AlreadyRegistered,r:
    pass

try:
    admin.site.register(WordMeta)
except sites.AlreadyRegistered,r:
    pass


