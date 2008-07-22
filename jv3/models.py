from django.db import models
import django.contrib.auth.models as authmodels
import django.forms as forms

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
    
