import re
from django.db import models
from django.contrib import admin
from django.contrib.sitemaps import Sitemap
from django.template import loader, Context
from django.conf.urls.defaults import *
from eyebrowse.models import *
from django.core.mail import send_mail
from django.template.loader import get_template
from django.conf import settings
from django.contrib.auth.models import User

GENDER_CHOICES = (
    ('M', 'Male'),
    ('F', 'Female'),
    ('R', 'Robot'),
)

LOGGING_LIST_MODE = (
    ('W', 'Log Only'),
    ('B', 'Log All Except'),
)

EXPOSURE_CHOICES = (
    ('N', 'Nobody'),
    ('F', 'Friends'),
    ('P', 'Public'),
)

class UserTag(models.Model):
    name = models.CharField(max_length=120, unique=True)

    def __str__(self):
        return self.name

class Group(models.Model):
    name = models.CharField(max_length=250,unique=True, primary_key=True)    
    description = models.TextField(blank=True, null=True)    
    photo = models.ImageField(upload_to=settings.EYEBROWSE_PROFILE_UPLOAD_DIR)
    tags = models.ManyToManyField(UserTag) # not sure if i can use this but it seems ok
    other_settings = models.TextField(blank=True, null=True)   ## just in case!!

class EndUser(models.Model):
    user = models.ForeignKey(User, unique=True, primary_key=True)    
    location = models.CharField(max_length=250, blank=True, null=True)
    tags = models.ManyToManyField(UserTag)
    photo = models.ImageField(upload_to=settings.EYEBROWSE_PROFILE_UPLOAD_DIR)
    homepage = models.URLField(blank=True, null=True)
    birthdate = models.DateTimeField(blank=True, null=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)

    friends = models.ManyToManyField('self')

    def __str__(self):
        return '%s enduser' % (self.user.username)

class PrivacySettings(models.Model):
    user = models.ForeignKey(User, unique=True, primary_key=True)
    whitelist = models.TextField(blank=True, null=True)
    blacklist = models.TextField(blank=True, null=True)    
    listmode = models.CharField(max_length=1, choices=LOGGING_LIST_MODE, default="B")
    exposure = models.CharField(max_length=1, choices=EXPOSURE_CHOICES, default="P")
    other_settings = models.TextField(blank=True, null=True)   ## just in case!!

class FriendRequest(models.Model):
    from_friend = models.ForeignKey(
        User, related_name='friend_set'
        )
    to_friend = models.ForeignKey(
        User, related_name='to_friend_set'
        )
    def __str__(self):
        return '%s, %s' % (
            self.from_friend.username,
            self.to_friend.username
            )
    class Admin:
        pass
    class Meta:
        unique_together = (('to_friend', 'from_friend'), )

class PageTag(models.Model):
    name = models.CharField(max_length=64, unique=True)    

class Page(models.Model):
    title = models.CharField(max_length=100,null=True)
    url = models.URLField(verify_exists=False)
    host = models.CharField(max_length=255,null=True)  ## uh huh a little arbitrary
    path = models.CharField(max_length=512,null=True)
    tags = models.ManyToManyField(PageTag)

    def set_host_path(self,url):
        ## sets host and path parameters by parsin' them out
        import urlparse
        self.url = url
        scheme, self.host, self.path, foo, bar, baz = urlparse.urlparse(url)

class PageView(models.Model):    
    user = models.ForeignKey(EndUser)
    duration = models.DecimalField(max_digits=14, decimal_places=0)
    startTime = models.DecimalField(max_digits=14, decimal_places=0)
    endTime = models.DecimalField(max_digits=14, decimal_places=0)
    title = models.CharField(max_length=100,null=True)
    url = models.URLField(verify_exists=False)
    host = models.CharField(max_length=255,null=True)
    path = models.CharField(max_length=512,null=True)
    tags = models.ManyToManyField(PageTag)

    @staticmethod
    def from_url(user,url,start,end):
        ## sets host and path parameters by parsin' them out
        import urlparse
        newview = PageView()
        newview.url = url
        scheme, newview.host, newview.path, foo, bar, baz = urlparse.urlparse(url)
        newview.user = user
        newview.startTime = start
        newview.endTime = end
        newview.duration = end - start # usually. but we cache it cuz sql is dumb.
        return newview
    
    @staticmethod
    def from_Event(evt):
        import eyebrowse.views
        pv = self.from_url( evt.owner, evt.entityid, evt.start, evt.end )
        pv.title = eyebrowse.views.get_title_from_evt(evt)
        return pv

#for color labeling of visualizations
class ColorPair(models.Model):
    user = models.ForeignKey(User)
    page = models.ForeignKey(Page)
    color = models.CharField(max_length=250)
    
    def __str__(self):
        return '%s, %s' % (
            self.page, self.color
            )

class Invitation(models.Model):
    name = models.CharField(max_length=50)
    email = models.EmailField()
    code = models.CharField(max_length=20)
    sender = models.ForeignKey(User)
    def __str__(self):
        return '%s, %s' % (self.sender.username, self.email)
    class Admin:
        pass
    
    def send(self):
        subject = 'Invitation to join FOO'
        link = 'http://%s/friend/accept/%s/' % (
            settings.SITE_HOST,
            self.code
            )
        template = get_template('invitation_email.txt')
        context = Context({
            'name': self.name,
            'link': link,
            'sender': self.sender.username,
            })
        message = template.render(context)
        send_mail(
            subject, message,
            settings.DEFAULT_FROM_EMAIL, [self.email]
            )
