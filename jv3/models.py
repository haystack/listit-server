from django.db import models
import django.contrib.auth.models as authmodels

# Create your models here.
class SPO(models.Model):
    owner = models.ForeignKey(authmodels.User,related_name='spo_owner')
    version = models.IntegerField(default=0)
    timestamp = models.TimeField(auto_now=True)
    subj = models.TextField()
    pred = models.TextField()
    obj = models.TextField()
    def __str__(self):
        return '%s.%s.%s' % (self.subj, self.pred, self.obj)
    class Admin:
        pass

    
