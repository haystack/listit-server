from django.db import models
import django.contrib.auth.models as authmodels
import django.forms as forms
import django.contrib.admin.sites as sites
from django.contrib import admin

# Create your models here.

class Sighting(models.Model):
    when = models.IntegerField()
    lat = models.FloatField()
    lon = models.FloatField()
    mph = models.FloatField()
    dirr = models.FloatField()
    
try:
    admin.site.register(Sighting)
except sites.AlreadyRegistered,r:
    pass
