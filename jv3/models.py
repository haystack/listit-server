from django.db import models
import django.contrib.auth.models as authmodels
import django.forms as forms
import django.contrib.admin.sites as sites
from django.contrib import admin

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
    owner = models.ForeignKey(authmodels.User,related_name='note_owner',null=True)
    jid = models.IntegerField(default=0)
    version = models.IntegerField(default=0)
    modified  = models.IntegerField(default=0)
    created = models.IntegerField(default=0)
    contents = models.TextField()
    ## what is this for?
    update_fields = ['contents','created','modified']

class NoteForm(forms.Form):
    contents = forms.CharField()
    owner = FixedModelChoiceField( queryset=authmodels.User.objects,  cache_choices=True  )
    jid = forms.IntegerField()
    version = forms.IntegerField()
    modified  = forms.IntegerField() 
    created = forms.IntegerField()

try:
    admin.site.register(Note)
except sites.AlreadyRegistered,r:
    pass

class ActivityLog(models.Model):
    owner = models.ForeignKey(authmodels.User,null=True)
    when = models.IntegerField(default=0)
    action = models.TextField()
    noteid = models.IntegerField(null=True)
    noteText = models.TextField(blank=True,null=True)

class Sighting(models.Model):
    when = models.IntegerField()
    lat = models.FloatField()
    lon = models.FloatField()
    mph = models.FloatField()
    dirr = models.FloatField();
    
try:
    admin.site.register(Sighting)
except sites.AlreadyRegistered,r:
    pass


try:
    admin.site.register(ActivityLog)
except sites.AlreadyRegistered,r:
    pass
