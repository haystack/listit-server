import re,sys,time,operator,os,math, datetime
from django.template import loader, Context
from django.http import HttpResponse,HttpResponseRedirect, HttpResponseForbidden
from django.shortcuts import render_to_response
from django.http import Http404
from django.shortcuts import get_object_or_404, get_list_or_404
from django.conf.urls.defaults import *
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.template import RequestContext
from django.db.models import Q
from eyebrowse.forms import *
from eyebrowse.models import *
from cStringIO import StringIO
from PIL import Image
Image.init() # populates PIL fileformats
from django.core.files.uploadedfile import SimpleUploadedFile
from os.path import splitext
from django.db.models.signals import post_save
from jv3.models import Event ## from listit, ya.
from django.utils.simplejson import JSONEncoder, JSONDecoder
# beaker
from eyebrowse.beakercache import cache
# import annotate(Sum())
from django.db.models import Sum
from jv3.utils import json_response

def get_enduser_for_user(user):
    if EndUser.objects.filter(user=user).count() > 0:
        enduser = EndUser.objects.filter(user=user)[0]
    else:
        raise Http404('Internal error. Call brennan or emax. Something is wrong. Houston.')    
    return enduser

@login_required
def privacy_settings_page(request):
    user = get_object_or_404(User, username=request.user.username)
    enduser = get_enduser_for_user(user)
    
    first_name = ''
    last_name = ''
    email = ''
    location = ''
    tags = ''
    homepage = ''
    birthdate = ''
    gender = ''
    photo = ''
    try:
        first_name = enduser.user.first_name
        last_name = enduser.user.last_name
        email = enduser.user.email
        location = enduser.location
        homepage = enduser.homepage
        birthdate = enduser.birthdate
        photo = enduser.photo
        gender = enduser.gender
        tags = ' '.join(
            tag.name for tag in enduser.tags.all()
            )
    except:
        print sys.exc_info()

    form = ProfileSaveForm({
            'first_name': first_name,
            'last_name': last_name,
            'email': email,
            'location': location,
            'tags': tags,
            'homepage': homepage,
            'birthdate': birthdate,
            'gender': gender,
            'photo': photo
            })

    if request.method == 'POST':
        form = ProfileSaveForm(request.POST, request.FILES)
        if form.is_valid():
            user = _profile_save(request, form)  
            return HttpResponseRedirect('/settings/') 

        variables = RequestContext(request, {'form': form, 'error': True, 'request_user': request.user})
        return render_to_response('whitelist.html', variables)
               
    variables = RequestContext(request, {
        'form': form,
        'request_user': request.user
        })

    return render_to_response('whitelist.html', variables )


def _privacy_save(request, form):
    username = request.user.username
    user = get_object_or_404(User, username=username)
    privacysettings = user.privacysettings_set.all()[0] ## ?

    privacysettings.listmode = form.cleaned_data['listmode']
    privacysettings.exposure = form.cleaned_data['exposure']
    privacysettings.save()
    return user


## emax changed this because plugin needs to grab these
## @login_required
def get_privacy_urls(request):
    ## added by emax:
    import eyebrowse.plugin_views
    user = eyebrowse.plugin_views.authenticate_user(request)
    if user is None:
        return json_response({ "code":404, "error": "Username or password incorrect" }) 
        
    privacysettings = user.privacysettings_set.all()[0]
    
    lst = ""
    if privacysettings.listmode == "W":
        lst = []
        if privacysettings.whitelist is not None:
            lst = privacysettings.whitelist.split() 
    if privacysettings.listmode == "B":
        lst = []
        if privacysettings.blacklist is not None:            
            lst = privacysettings.blacklist.split()

    return json_response({ "code":200, "results": lst }) 

## @login_required
def delete_privacy_url(request):
    ## added by emax:
    import eyebrowse.plugin_views
    user = eyebrowse.plugin_views.authenticate_user(request)
    if user is None:
        return json_response({ "code":404, "error": "Username or password incorrect" }) 
    
    privacysettings = user.privacysettings_set.all()[0] 

    inpt = request.GET['input'].strip()

    if privacysettings.listmode == "W":
        privacysettings.whitelist = ' '.join([ x for x in privacysettings.whitelist.split() if not x == inpt])
    if privacysettings.listmode == "B":
        privacysettings.blacklist = ' '.join([ x for x in privacysettings.blacklist.split() if not x == inpt])

    privacysettings.save()
    return HttpResponseRedirect('/settings/')

## @login_required
def add_privacy_url(request):
    ## added by emax:
    import eyebrowse.plugin_views
    user = eyebrowse.plugin_views.authenticate_user(request)
    if user is None:
        return json_response({ "code":404, "error": "Username or password incorrect" }) 
    
    import urlparse    
    privacysettings = user.privacysettings_set.all()[0]

    listmode = privacysettings.listmode
    request_inpt = request.GET['input'].strip()
    
    if request_inpt.split(','):
        request_inpt = request_inpt.split(',')        

    for inpt in request_inpt:
        if inpt.startswith('http'):
            host = urlparse.urlparse(inpt)[1].strip()
        else:
            host = inpt
            if "/" in host:
                host = host[0:host.find("/")]

        val = {}

        if len(host) > 0:
            if privacysettings.listmode == "W":
                if privacysettings.whitelist is not None:
                    wlist = privacysettings.whitelist.split(' ')
                    if not host in wlist:
                        privacysettings.whitelist = ' '.join(wlist + [host])
                        val["host"] = host
                else:
                    privacysettings.whitelist = host
                    val["host"] = host
            
            if privacysettings.listmode == "B":
                if privacysettings.blacklist is not None:
                    if not host in privacysettings.blacklist.split():
                        privacysettings.blacklist = ' '.join(privacysettings.blacklist.split() + [host])
                        val["host"] = host
                else:
                    privacysettings.blacklist = host
                    val["host"] = host
            # Save 
            privacysettings.save()

    ## val will be non-null iff it's new
    return json_response(val,200)


def userprivacy(request):
    t = loader.get_template("user_privacy.html")
    c = Context({ 'username': request.user.username })

    return HttpResponse(t.render(c))


def index(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        #if request.user.username:
        #    return HttpResponseRedirect('/settings/' + request.user.username)
        if form.is_valid():
            user = User.objects.create_user(
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password1'],
                email=form.cleaned_data['email']
                )
            enduser = EndUser()
            enduser.user = user  
            enduser.save()
            privacysettings = PrivacySettings()
            privacysettings.user = user
            privacysettings.save()
            return HttpResponseRedirect('/register/success/')
        variables = RequestContext(request, {'form': form, 'error': True})
        return render_to_response('index.html', variables)
    # normal registration form
    form = RegistrationForm()
    variables = RequestContext(request, {'form': form, 'request_user': request.user.username })
    return render_to_response('index.html', variables)

def faq(request):
    t = loader.get_template("faq.html")
    c = Context({ 'request_user': request.user.username })

    return HttpResponse(t.render(c))

def help(request):
    t = loader.get_template("help.html")
    c = Context({ 'request_user': request.user.username })

    return HttpResponse(t.render(c))

def about(request):
    t = loader.get_template("about.html")
    c = Context({ 'request_user': request.user.username })

    return HttpResponse(t.render(c))

def terms(request):
    t = loader.get_template("terms.html")
    c = Context({ 'request_user': request.user.username })

    return HttpResponse(t.render(c))

def day(request, username):
    user = get_object_or_404(User, username=username)
    enduser = get_enduser_for_user(user)
    request_user = request.user.username

    t = loader.get_template("day.html")
    c = Context({ 'username': enduser.user.username, 'id': enduser.user.id, 'request_user': request_user })

    return HttpResponse(t.render(c))

def report(request, username):
    user = get_object_or_404(User, username=username)
    enduser = get_enduser_for_user(user)
    request_user = request.user.username

    t = loader.get_template("report.html")
    c = Context({ 'username': enduser.user.username, 'id': enduser.user.id, 'request_user': request_user })

    return HttpResponse(t.render(c))

def graph(request, username):
    user = get_object_or_404(User, username=username)
    enduser = get_enduser_for_user(user)
    request_user = request.user.username

    if request_user:
        is_friend = request.user.to_friend_set.all().filter(from_friend=user)
    else: 
        is_friend = False;
        is_followed_by = False;

    t = loader.get_template("graph.html")
    c = Context({ 'username': enduser.user.username, 'id': enduser.user.id, 'photo': enduser.photo, 'request_user': request_user, 'is_friend': is_friend })
    return HttpResponse(t.render(c))

def ticker(request):
    t = loader.get_template("global.html")
    c = Context({ 'username': request.user.username, 'id': request.user.id, 'request_user': request.user.username })
    return HttpResponse(t.render(c))

def page_profile(request): 
    url = 'http://nytimes.com'
    if request.GET.has_key('url'):
        url = request.GET['url']
    
    variables = RequestContext(request, {
        'username': request.user.username,
        'request_user': request.user.username,
        'url': url
        })
    return render_to_response('webpage.html', variables)

def friends(request, username):
    user = get_object_or_404(User, username=username)
    enduser = get_enduser_for_user(user)

    friends = enduser.friends.all()
    friends_results = []
    for friend in friends:
        friends_results.append( {"username": friend.user.username, "number": Event.objects.filter(owner=friend.user,type="www-viewed").count()} )
    friends_results.sort(key=lambda x: -x["number"])
    
    request_user = request.user.username

    variables = RequestContext(request, {
        'username': username,
        'show_edit': username == request.user.username,
        'friends': friends_results,
        'request_user': request_user
        })
    return render_to_response('friends.html', variables)

def daybyday(request, username):
    request_user = request.user.username

    variables = RequestContext(request, {
        'username': username,
        'request_user': request_user
        })
    return render_to_response('daybyday.html', variables)

def users(request):    
    user = request.user
    friends_results = []
    friends = EndUser.objects.all()

    if request.user.username:
        user = get_object_or_404(User, username=request.user.username)

    for friend in friends:
        if user.username:
            is_friend = user.to_friend_set.all().filter(from_friend=friend)
            is_followed_by = user.friend_set.all().filter(to_friend=friend)
        else: 
            is_friend = False;
            is_followed_by = False;

        # not sure if this if else is necissary
        if friend.tags.all():
            tags = ' '.join(
                tag.name for tag in friend.tags.all()
                )
        else:
            tags = ""
            
        friends_results.append( {
                "username": friend.user.username, 
                "number": Event.objects.filter(owner=friend.user,type="www-viewed").count(), 
                "tags": tags, 
                "id": friend.user.id,
                "photo": friend.photo,
                "is_friend": is_friend,
                "location": friend.location,
                "website": friend.homepage,                
                "latest_view": PageView.objects.filter(user=friend).order_by("-startTime")[0:1],
                "followed_by": is_followed_by
                })

    friends_results.sort(key=lambda x: x["username"].lower())

    variables = RequestContext(request, {
        'users': friends_results,
        'request_user': request.user.username
        })
    return render_to_response('users.html', variables)

def user_page(request, username):
    user = get_object_or_404(User, username=username)
    enduser = get_enduser_for_user(user)

    if request.user.username:
        request_enduser = get_enduser_for_user(request.user)
        is_friend = user.to_friend_set.all().filter(from_friend=request.user)
    else: 
        is_friend = False;

    following = [friendship.to_friend for friendship in user.friend_set.all()]
    followers = [friendship.from_friend for friendship in user.to_friend_set.all()]

    privacysettings = enduser.user.privacysettings_set.all()[0] ## ?
    exposure = privacysettings.exposure

    if request.user.id is not enduser.user.id:
        if exposure == 'N':
            return HttpResponseRedirect('/userprivacy/%s/'% enduser.user.username)
        if exposure == 'F':
            if not is_friend:
                return HttpResponseRedirect('/userprivacy/%s/'% enduser.user.username)
            pass

    friends = enduser.friends.all()
    friends_results = []
    for friend in friends:
        friends_results.append( {"username": friend.user.username, "number": Event.objects.filter(owner=friend.user,type="www-viewed").count()} )
    friends_results.sort(key=lambda x: -x["number"])
    
    tags = ' '.join(
        tag.name for tag in enduser.tags.all()
        )

    bday = None
    
    if enduser.birthdate is not None:
        bday = int((int(time.time()) - int(time.mktime(time.strptime(str(enduser.birthdate), '%Y-%m-%d %H:%M:%S'))))/ 31556926)  # large number is seconds in a year

    variables = RequestContext(request, {
         'username': username,
         'show_edit': username == request.user.username,
         'following': following,
         'followers': followers,
         'is_friend': is_friend,
         'location': enduser.location,
         'homepage': enduser.homepage,
         'birthdate': bday,
         'photo': enduser.photo,
         'tags' : tags,
         'gender': enduser.gender,
         'id':enduser.user.id,
        'request_user': request.user.username
        })
    return render_to_response('user_page.html', variables)

def logout_page(request):
    logout(request)
    return HttpResponseRedirect('/')

def _create_enduser_for_user(user):
    enduser = EndUser()
    enduser.user = user
    enduser.save()
    privacysettings = PrivacySettings()
    privacysettings.user = user
    privacysettings.save()

def register_page(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = User.objects.create_user(
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password1'],
                email=form.cleaned_data['email']
                )
            _create_enduser_for_user(user)
            if 'invitation' in request.session:
                # Retrieve the invitation object.
                invitation = Invitation.objects.get(id=request.session['invitation'])
                # Create friendship from user to sender.
                friendship = FriendRequest(
                    from_friend=user,
                    to_friend=invitation.sender
                    )
                friendship.save()
                # Create friendship from sender to user.
                friendship = FriendRequest (
                    from_friend=invitation.sender,
                    to_friend=user
                    )
                friendship.save()
                # Delete the invitation from the database and session.
                invitation.delete()
                del request.session['invitation']
            ## CHECK THIS METHOD email_user(subject, message, from_email=None)
            ## Sends an e-mail to the user. If from_email is None, Django uses the DEFAULT_FROM_EMAIL.
                #template = get_template('thanks_email.txt')
                #subject = 'Thanks for registering'
                #context = Context({
                #     'name': 'The Watchme Team,
                #      'link': foolink,
                #      'sender': sender.username,
                #      })
                #message = template.render(context)
                #email_user(  ?????
                #       subject, message,
                #       settings.DEFAULT_FROM_EMAIL
                #       )
            return HttpResponseRedirect('/register/success/')
    else:
        form = RegistrationForm()
    variables = RequestContext(request, {'form': form})
    return render_to_response('register.html', variables)


def register_success_page(request):
    form = LoginForm()
    if request.method == 'POST':
        user = authenticate(username=request.POST['username'], password=request.POST['password'])
        if user is not None:
            if user.is_active:
                login(request, user)
                # success
                return HttpResponseRedirect('/settings/')
            else:
                # disabled account
                variables = RequestContext(request, {'form': form, 'error': True})
                return render_to_response('login.html', variables)
    else:
        variables = RequestContext(request, {'form': form})
        return render_to_response('registration/register_success.html', variables)
        
@login_required
def profile_save_page(request):
    user = get_object_or_404(User, username=request.user.username)
    enduser = get_enduser_for_user(user)
    friends = enduser.friends.all()
    friends_results = []
    for friend in friends:
        friends_results.append( {"username": friend.user.username, "number": Event.objects.filter(owner=friend.user,type="www-viewed").count()} )
    friends_results.sort(key=lambda x:-x["number"])

    if request.method == 'POST':
        form = ProfileSaveForm(request.POST, request.FILES)
        if form.is_valid():
            user = _profile_save(request, form)            
            return HttpResponseRedirect('/settings/')
                
    else:        
        first_name = ''
        last_name = ''
        email = ''
        location = ''
        tags = ''
        homepage = ''
        birthdate = ''
        gender = ''
        try:
            first_name = enduser.user.first_name
            last_name = enduser.user.last_name
            email = enduser.user.email
            location = enduser.location
            homepage = enduser.homepage
            birthdate = enduser.birthdate
            photo = enduser.photo
            gender = enduser.gender
            tags = ' '.join(
                tag.name for tag in enduser.tags.all()
                )
        except:
            print sys.exc_info()
        form = ProfileSaveForm({
                'first_name': first_name,
                'last_name': last_name,
                'email': email,
                'location': location,
                'tags': tags,
                'homepage': homepage,
                'birthdate': birthdate,
                'gender': gender,
                'photo': photo
                })
    variables = RequestContext(request, {
        'friends': friends_results,
        'form': form,
        'request_user': request.user
        })
    return render_to_response('profile_save.html', variables)

def _profile_save(request, form):
    username = request.user.username
    user = get_object_or_404(User, username=username)
    enduser = get_enduser_for_user(user)

    enduser.user.email = form.cleaned_data['email']
    enduser.user.save()

    enduser.location = ""
    if re.search(r'^(/w|/W|[^<>+?$%{}&])+$', form.cleaned_data['location']):        
        enduser.location = form.cleaned_data['location']

    enduser.birthdate = form.cleaned_data['birthdate']
    enduser.homepage = form.cleaned_data['homepage']
    enduser.gender = form.cleaned_data['gender']
    enduser.tags = ""

    tag_names = form.cleaned_data['tags'].split()
    for tag_name in tag_names:
        if re.search(r'^(/w|/W|[^<>+?$%{}&])+$', tag_name):
            tag, dummy = UserTag.objects.get_or_create(name=tag_name)
            enduser.tags.add(tag) 

    # save the image    
    if request.FILES:
        if enduser.photo:
            # this doesn't delete anything
            # should delete the image from the server as it will be replaced soon
            enduser.photo.delete()
        else:
            pass
        
        if True:
            # save the original image   
            img = request.FILES['photo']
            name = "%d.%s"% (enduser.user.id, img.name.strip().split(".")[-1])
            file_exts = ('.png', '.jpg', '.jpeg',)
            if splitext(img.name)[1].lower() not in file_exts:
                #print file_exts
                raise forms.ValidationError("Only following Picture types accepted: %s" % ", ".join([f.strip('.') for f in file_exts]))
            else:
                enduser.photo.save(name, img)

            # save the thumbnail            
            THUMBNAIL_SIZE = (69, 69)
            image = Image.open(enduser.photo)
            
            if image.mode not in ('L', 'RGB'):
                image = image.convert('RGB')
                
            # Without antialiasing the image pattern artifacts may result.
            image.thumbnail(THUMBNAIL_SIZE, Image.ANTIALIAS)
            
            # Save the thumbnail
            temp_handle = StringIO()
            image.save(temp_handle, 'JPEG', quality=90)
            temp_handle.seek(0)
                        
            # Save to the thumbnail field
            suf = SimpleUploadedFile(os.path.split(enduser.photo.name)[-1],
                                 temp_handle.read(), content_type='image/jpeg')

            enduser.photo.delete()
            enduser.photo.save(suf.name, suf)            

    enduser.save()
    return user

@login_required
def delete_url_entry(request):
    urlID = request.POST['ID'].strip()

    url_entry = PageView.objects.filter(id=urlID)
    url_entry.delete()

    return json_response({ "code":200 });

def friends_page(request, username):
    user = get_object_or_404(User, username=username)
    enduser = get_enduser_for_user(user)

    following = [friendship.to_friend for friendship in user.friend_set.all()]
    followers = [friendship.from_friend for friendship in user.to_friend_set.all()]

    variables = RequestContext(request, {
        'username': username,
        'following': following,
        'followers': followers,
        'show_user': True,
        'username': enduser.user.username,
        'request_user': request.user
        })
    return render_to_response('friends_page.html', variables)

@login_required
def friend_add(request): # this sends a friend request to the user
    if request.GET.has_key('username'):
        friend = get_object_or_404(User, username=request.GET['username'])
        friendship = FriendRequest(
            from_friend=request.user,
            to_friend=friend
            )
        try:
            friendship.save()             
            request.user.message_set.create(
                message='you are now following %s.' % friend.username
                )
        except:           
            friendship = FriendRequest(
                from_friend=friend,
                to_friend=request.user
                )
        
            friendship.save()
            request.user.message_set.create(
                message='you are now following %s.' % friend.username
                )
        return HttpResponseRedirect(
            '/friends/manage/%s/' % request.user.username
            )
    else:
        raise Http404('boo.')

@login_required
def friend_save(request):  # this saves the user as a friend in BOTH user's friends model
    if request.GET.has_key('username'):
        friend = get_object_or_404(User, username=request.GET['username'])
        enduser = get_enduser_for_user(request.user)        
        frienduser = get_enduser_for_user(friend)
        try:
            # save in each users profile
            enduser.friends.add(frienduser)
            # enduser.friends.save()
            # apparenly this does the trick w/o the save
        
            friendship = FriendRequest.objects.filter(
                 from_friend=friend,
                to_friend=request.user
                )
            if friendship:
                friendship.delete()
            # try again with the from_friend to_friend reversed
            else:
                friendship = FriendRequest.objects.filter(
                    from_friend=request.user,
                    to_friend=friend
                    )
                friendship.delete()
                
            request.user.message_set.create(
                message='you and %s are now friends.' % friend.username
                )
        except:
            request.user.message_set.create(
                message='%s is already your friend.' % friend.username
                )
        
        return HttpResponseRedirect(
            '/friends/%s/' % request.user.username
            )
    else:
        raise Http404('failz')

def friend_unfollow(request, username):
    if request.GET.has_key('friend'):
        friend = get_object_or_404(User, username=request.GET['friend'])
        enduser = get_enduser_for_user(request.user)        
        frienduser = get_enduser_for_user(friend)
        try:
            #following = [friendship.to_friend for friendship in user.friend_set.all()]
            
            # friendship = FriendRequest.objects.filter(
            #     from_friend=friend,
            #     to_friend=request.user
            #     )
            # if friendship:
            #     friendship.delete()
            # try again with the from_friend to_friend reversed
            # else:
            friendship = FriendRequest.objects.filter(
                from_friend=request.user,
                to_friend=friend
                )
            friendship.delete()
            
            request.user.message_set.create(
                message='you are no longer following %s.' % friend.username
                )
        except:
            request.user.message_set.create(
                message='%s failz.' % friend.username
                )
        
        return HttpResponseRedirect(
            '/friends/manage/%s/' % request.user.username
            )
    else:
        raise Http404('failz')



@login_required
def friend_invite(request):
    if request.method == 'POST':
        form = FriendInviteForm(request.POST)
        if form.is_valid():
            invitation = Invitation(
                name = form.clean_data['name'],
                email = form.clean_data['email'],
                code = User.objects.make_random_password(20),
                sender = request.user
                )
            invitation.save()
            try:
                invitation.send()
                request.user.message_set.create(
                    message='An invitation was sent to %s.' % invitation.email
                    )
            except:
                request.user.message_set.create(
                    message='There was an error while sending the invitation.'
                    )
            return HttpResponseRedirect('/friend/invite/')
    else:
        form = FriendInviteForm()
    variables = RequestContext(request, {
        'form': form
        })
    return render_to_response('friend_invite.html', variables)


def friend_accept(request, code):
    invitation = get_object_or_404(Invitation, code__exact=code)
    request.session['invitation'] = invitation.id
    return HttpResponseRedirect('/register/')



## hook for creating relevant Page objects when new jv3.Event objects get created
## by the listit server (which answers calls from listit)    
def create_www_pageviews_for_each_event(sender, created=None, instance=None, **kwargs):
    # print "post-save event for sender %s : %s " % (repr(sender),repr(instance.entityid)) ## debug!!
    if (created and instance is not None):
        if instance.entitytype == "schemas.Webpage" and instance.entityid is not None:
            ## print "post-save url: %s " % instance.entityid ## debug!!
            pageview = PageView.from_Event(instance)
            # print "Saving %s " % repr(pageview)
            pageview.save()
                
post_save.connect(create_www_pageviews_for_each_event, sender=Event)
                        
## ajax views for graphs, etc.

def _mimic_entity_schema_from_url(url):
    import urlparse
    prot, host, page, foo, bar, baz = urlparse.urlparse(url)
    return {"id":url, "host":host, "path": page, "type":"schemas.Webpage"}

def _get_pages_for_user(user,from_msec,to_msec):
    return PageView.objects.filter(user=user,startTime__gte=from_msec,endTime__lte=to_msec)

def _unpack_from_to_msec(request):
    return (request.GET.get('from',0), request.GET.get('to',long(time.mktime(time.localtime())*1000)))

def _unpack_times(request):
    return (long(request.GET['first_start']), long(request.GET['first_end']), long(request.GET['second_start']), long(request.GET['second_end']))

def _get_top_hosts_n(users,start,end):
    # print users
    time_per_host = _get_time_per_page(users,start,end,grouped_by=EVENT_SELECTORS.Host) 

    ordered_visits = [h for h in time_per_host.iteritems()]
    ordered_visits.sort(lambda u1,u2: int(u2[1] - u1[1]))
    return ordered_visits    

def get_title_from_evt(evt):
    foo =  JSONDecoder().decode(JSONDecoder().decode(evt.entitydata)[0]['data'])
    if foo.has_key('title'):
        return foo['title']
    return   

def round_time_to_day(time):
    new_time = int(math.floor(int(time) / 86400000) * 86400000)
    return new_time        

def round_time_to_half_day(time):
    new_time = int(math.floor(int(time) / 43200000) * 43200000)
    return new_time        


class EVENT_SELECTORS:
    class Page:
        @staticmethod
        def access(queryset):
            return [s[0] for s in queryset.values_list('url')]
        @staticmethod
        def filter_queryset(queryset,url):
            return queryset.filter(url=url)
    class Host:
        @staticmethod
        def access(queryset):
            return [s[0] for s in queryset.values_list('host')] # <- comparatively lame. # pretty badass too: [urlparse.urlparse(url[0])[1] for url in queryset.values_list('host')]
        @staticmethod
        def filter_queryset(queryset,host):
            return queryset.filter(host=host) #queryset.filter(entityid__contains="://%s/"%url)         ## tres. badass!!!

def _get_time_per_page(user,from_msec,to_msec,grouped_by=EVENT_SELECTORS.Page):
    import django.db.models.query
    if type(user) == django.db.models.query.QuerySet:
        mine_events = PageView.objects.filter(startTime__gte=from_msec,endTime__lte=to_msec)
    elif type(user) == list:
        mine_events = PageView.objects.filter(user__in=user,startTime__gte=from_msec,endTime__lte=to_msec)
    else:
        mine_events = PageView.objects.filter(user=user,startTime__gte=from_msec,endTime__lte=to_msec)
    
    uniq_urls  = set( grouped_by.access(mine_events) )
    times_per_url = {}
    for url in uniq_urls:
        # might be faster to define a variable here rather than doing filter 2x for the if and the reduce
        grouped_by_filtered = grouped_by.filter_queryset(mine_events,url).values_list('startTime','endTime')
        # to make sure not to reduce an empty item 
        if grouped_by_filtered:
            times_per_url[url] = long(reduce(lambda x,y: x+y, [ startend[1]-startend[0] for startend in grouped_by_filtered ] ))
        else:
            pass
    return times_per_url

def defang_pageview(pview):    
    return {"start" : long(pview.startTime), "end" : long(pview.endTime), "url" : pview.url, "host": pview.host, "title": pview.title, "id":pview.id, "user": pview.user.username } ## to slow "location":get_enduser_for_user(pview.user).location }

def get_web_page_views(request):
    from_msec_raw,to_msec_raw = _unpack_from_to_msec(request)

    #@cache.region('short_term')
    def fetch_data(from_msec, to_msec, user):
        hits =  _get_pages_for_user(user,from_msec,to_msec)
        return [ defang_pageview(evt) for evt in hits ]

    results = fetch_data(from_msec_raw, to_msec_raw, request.user)

    return json_response({ "code":200, "results": results });

def get_views_user(request, username):
    user = get_object_or_404(User, username=username)
    enduser = get_enduser_for_user(user)

    from_msec_raw,to_msec_raw = _unpack_from_to_msec(request)
    
    #@cache.region('short_term')
    def fetch_data(from_msec, to_msec, user):
        hits = _get_pages_for_user(user ,from_msec,to_msec)
        return [ defang_pageview(evt) for evt in hits ]

    results = fetch_data(from_msec_raw, to_msec_raw, user)

    return json_response({ "code":200, "results": results });


def get_recent_web_page_view_user(request, username, n):
    user = get_object_or_404(User, username=username)
    n = int(n)

    # gets unique pages
    phits = PageView.objects.filter(user=user).order_by("-startTime")

    if n < 0 or n is None:
        n = len(phits)

    uphit = uniq(phits,lambda x:x.title,n)
    
    results = [ defang_pageview(evt) for evt in uphit ]

    if request.GET.has_key('id'):
        urlID = int(request.GET['id'])
        filter_results = []
        for result in results:
            if int(result['id']) > urlID:
                filter_results.append(result)
        if len(filter_results) > 0:
            return json_response({ "code":200, "results": filter_results })
        else:
            return json_response({ "code":204 })

    return json_response({ "code":200, "results": results });


def get_user_profile_queries(request, username):
    user = get_object_or_404(User, username=username)

    @cache.region('long_term')
    def fetch_data(user):
        number = PageView.objects.filter(user=user).count()
        totalTime = PageView.objects.filter(user=user).aggregate(Sum('duration'))
        if number > 0:
            average = int((totalTime['duration__sum'])/1000)/int(number)
            return { 'number': number, 'totalTime': int(totalTime['duration__sum']/1000), 'average': average }
        return { 'number': 0, 'totalTime': 0, 'average': 0 }

    results = fetch_data(user)
    return json_response({ "code":200, "results": results });

def get_global_profile_queries(request):
    from_msec_raw,to_msec_raw = _unpack_from_to_msec(request)
    from_msec_rounded = round_time_to_day(from_msec_raw)
    to_msec_rounded = round_time_to_day(to_msec_raw)

    @cache.region('long_term')
    def fetch_data(from_msec, to_msec):
        totalTime  = PageView.objects.filter(startTime__gte=from_msec,endTime__lte=to_msec).aggregate(Sum('duration'))
        number =  PageView.objects.filter(startTime__gte=from_msec,endTime__lte=to_msec).count()
        if number > 0:
            average = int((totalTime['duration__sum'])/1000)/int(number)
            return { 'number': number, 'totalTime': int(totalTime['duration__sum']/1000), 'average': average }
        return { 'number': 0, 'totalTime': 0, 'average': 0 }

    results = fetch_data(from_msec_rounded, to_msec_rounded)
    return json_response({ "code":200, "results": results });

def get_page_profile_queries(request):
    inputURL = request.GET['url'].strip()
    from_msec_raw,to_msec_raw = _unpack_from_to_msec(request)
    from_msec_rounded = round_time_to_day(from_msec_raw)
    to_msec_rounded = round_time_to_day(to_msec_raw)

    @cache.region('long_term')
    def fetch_data(from_msec, to_msec, inputURL):
        totalTime  = PageView.objects.filter(url=inputURL,startTime__gte=from_msec,endTime__lte=to_msec).aggregate(Sum('duration'))
        number =  PageView.objects.filter(url=inputURL,startTime__gte=from_msec,endTime__lte=to_msec).count()
        if number > 0:
            average = int((totalTime['duration__sum'])/1000)/int(number)
            return { 'number': number, 'totalTime': int(totalTime['duration__sum']/1000), 'average': average }
        return { 'number': 0, 'totalTime': 0, 'average': 0 }

    results = fetch_data(from_msec_rounded, to_msec_rounded, inputURL)
    return json_response({ "code":200, "results": results });


def get_top_hosts(request, n):
    users = User.objects.all()
    n = int(n)

    from_msec_rounded = round_time_to_day((time.time()*1000) - (2629743*1000)) # 1 month)
    to_msec_rounded = round_time_to_day(time.time()*1000)

    @cache.region('long_term')
    def fetch_data(n, from_msec, to_msec):
        from_msec,to_msec = _unpack_from_to_msec(request)
        times_per_url = _get_time_per_page(users, from_msec, to_msec, grouped_by=EVENT_SELECTORS.Host)
        urls_ordered = times_per_url.keys()
        urls_ordered.sort(lambda u1,u2: int(times_per_url[u2] - times_per_url[u1]))
        return [(u, long(times_per_url[u])) for u in urls_ordered[0:n]]

    results = fetch_data(n, from_msec_rounded, to_msec_rounded)

    return json_response({ "code":200, "results": results }) 

    
def get_top_hosts_comparison(request, username, n):
    user_user = get_object_or_404(User, username=username)
    n = int(n)

    first_start,first_end,second_start,second_end = _unpack_times(request)
    first_start = round_time_to_day(first_start)
    first_end = round_time_to_day(first_end)
    second_start = round_time_to_day(second_start)
    second_end = round_time_to_day(second_end)

    @cache.region('long_term')
    def fetch_data(user, first_start, first_end, second_start, second_end):
        times_per_url_first = _get_top_hosts_n(user,first_start,first_end)
        times_per_url_second = _get_top_hosts_n(user,second_start,second_end)
        
        def index_of(what, where):
            try:
                return [ h[0] for h in where ].index(what)
            except:
                print sys.exc_info()
                pass
            return None

        results = []

        # if the first list is longer than the second list
        # this throws a  ValueError('list.index(x): x not in list',)
        for i in range(len(times_per_url_second)): ## iterate over the more recent dudes
            old_rank = index_of(times_per_url_second[i][0],times_per_url_first)
            if old_rank is not None:
                diff = - (i - old_rank)  # we want the gain not the difference
                results.append( times_per_url_second[i] + (diff,) )
            else:
                results.append( times_per_url_second[i] )

        return results[0:n]

    return_results = fetch_data(user_user, first_start,first_end,second_start,second_end)
        
    return json_response({ "code":200, "results": return_results }) 



def get_top_hosts_comparison_friends(request, username, n):    
    user = get_object_or_404(User, username=username)

    following = [friendship.to_friend for friendship in user.friend_set.all()]
    n = int(n)

    first_start,first_end,second_start,second_end = _unpack_times(request)
    first_start = round_time_to_day(first_start)
    first_end = round_time_to_day(first_end)
    second_start = round_time_to_day(second_start)
    second_end = round_time_to_day(second_end)

    @cache.region('long_term')
    def fetch_data(following, first_star, first_end, second_start, second_end):
        #print following
        times_per_url_first = _get_top_hosts_n(following,first_start,first_end)
        #print times_per_url_first
        times_per_url_second = _get_top_hosts_n(following,second_start,second_end)

        def index_of(what, where):
            try:
                return [ h[0] for h in where ].index(what)
            except:
                print sys.exc_info()
                pass
            return None

        results = []

        for i in range(len(times_per_url_second)): ## iterate over the more recent dudes
            old_rank = index_of(times_per_url_second[i][0],times_per_url_first)
            if old_rank is not None:
                diff = - (i - old_rank)  # we want the gain not the difference
                results.append(times_per_url_second[i] + (diff,) )
            else:
                results.append( times_per_url_second[i] )

        return results[0:n]

    return_results = fetch_data(following,first_start,first_end,second_start,second_end)
        
    return json_response({ "code":200, "results": return_results }) 


def get_urls_for_day_of_week(request, username):    
    user = get_object_or_404(User, username=username)
    
    first_start = round_time_to_day(_unpack_times(request))

    @cache.region('long_term')
    def fetch_data(user, first_start):
        users = User.objects.all()

        numDays = 49
        ## going to run through the past 50 days
        ## should be dynamic maybe use n

        #create the list of urls for each of the 
        return results

    return_results = fetch_data(user, first_start)
        
    return json_response({ "code":200, "results": return_results }) 


def get_day_of_week_graph_for_url(request):    
    inputURL = request.GET['url'].strip()

    @cache.region('long_term')
    def fetch_data(url, week):
        views = PageView.objects.filter(url=url)

        weekPts = [0,0,0,0,0,0,0]
        for view in views:
            weekday = datetime.datetime.fromtimestamp(view.startTime/1000).weekday()
            # returns the day of the week as an integer, where Monday is 0 and Sunday is 6. 
            weekPts[weekday] += 1

        return weekPts

    # to make caching have a unique id
    return_results = fetch_data(inputURL, "week")
        
    return json_response({ "code":200, "results": return_results }) 

def get_time_of_day_graph_for_url(request):    
    inputURL = request.GET['url'].strip()

    @cache.region('long_term')
    def fetch_data(url, day):
        views = PageView.objects.filter(url=url)
        hrPts = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]

        for view in views:
            hour = datetime.datetime.fromtimestamp(view.startTime/1000).hour
            hrPts[hour] += 1
            
        return hrPts

    # to make caching have a unique id
    return_results = fetch_data(inputURL, "day")
        
    return json_response({ "code":200, "results": return_results }) 


def get_day_of_week_graph_for_user(request):    
    username = request.GET['user'].strip()
    inputUser = get_object_or_404(User, username=username)

    @cache.region('long_term')
    def fetch_data(user, week):
        views = PageView.objects.filter(user=user)

        weekPts = [0,0,0,0,0,0,0]
        for view in views:
            weekday = datetime.datetime.fromtimestamp(view.startTime/1000).weekday()
            # returns the day of the week as an integer, where Monday is 0 and Sunday is 6. 
            weekPts[weekday] += 1

        return weekPts

    # to make caching have a unique id
    return_results = fetch_data(inputUser, "week")
        
    return json_response({ "code":200, "results": return_results }) 

def get_time_of_day_graph_for_user(request):    
    username = request.GET['user'].strip()
    inputUser = get_object_or_404(User, username=username)

    @cache.region('long_term')
    def fetch_data(user, day):
        views = PageView.objects.filter(user=user)
        hrPts = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]

        for view in views:
            hour = datetime.datetime.fromtimestamp(view.startTime/1000).hour
            hrPts[hour] += 1
            
        return hrPts

    # to make caching have a unique id
    return_results = fetch_data(inputUser, "day")
        
    return json_response({ "code":200, "results": return_results }) 

def get_hourly_daily_top_urls_user(request, username, n):
    n = int(n)
    inputUser = get_object_or_404(User, username=username)

    @cache.region('long_term')
    def fetch_data(user, n, baaaa):
        views = PageView.objects.filter(user=user)
        # super nasty still learning the ways of the python ninja
        hrPts = {0:{},1:{},2:{},3:{},4:{},5:{},6:{},7:{},8:{},9:{},10:{},11:{},12:{},13:{},14:{},15:{},16:{},17:{},18:{},19:{},20:{},21:{},22:{},23:{},24:{}}
        weekPts = {0:{},1:{},2:{},3:{},4:{},5:{},6:{}}

        for view in views:
            weekday = datetime.datetime.fromtimestamp(view.startTime/1000).weekday()
            hour = datetime.datetime.fromtimestamp(view.startTime/1000).hour
            
            if view.url in hrPts[hour]:
                hrPts[hour][view.url] += 1
            else:
                hrPts[hour][view.url] = 1

            if view.url in weekPts[weekday]:
                weekPts[weekday][view.url] += 1
            else:
                weekPts[weekday][view.url] = 1

        lResult = []
        for x in range(7):
            phlat = weekPts[x].items()
            phlat.sort(key=lambda(k,v2):-v2)
            lResult.append((x,phlat[:n]))

        rResult = []
        for x in range(24):
            phlat = hrPts[x].items()
            phlat.sort(key=lambda(k,v2):-v2)
            rResult.append((x,phlat[:n]))

        return [lResult,rResult]
    return_results = fetch_data(inputUser, n, "asdkjfhasd")
        
    return json_response({ "code":200, "results": return_results }) 


def get_top_hosts_comparison_global(request, n):    
    n = int(n)

    first_start,first_end,second_start,second_end = _unpack_times(request)
    first_start = round_time_to_day(first_start)
    first_end = round_time_to_day(first_end)
    second_start = round_time_to_day(second_start)
    second_end = round_time_to_day(second_end)

    @cache.region('long_term')
    def fetch_data(first_start, first_end, second_start, second_end):
        users = User.objects.all()

        times_per_url_first = _get_top_hosts_n(users,first_start,first_end)
        times_per_url_second = _get_top_hosts_n(users,second_start,second_end)

        def index_of(what, where):
            try:
                return [ h[0] for h in where ].index(what)
            except:
                print sys.exc_info()
                pass
            return None

        results = []

        for i in range(len(times_per_url_second)): ## iterate over the more recent dudes
            old_rank = index_of(times_per_url_second[i][0],times_per_url_first)
            if old_rank is not None:
                diff = - (i - old_rank)  # we want the gain not the difference
                results.append(times_per_url_second[i] + (diff,) )
            else:
                results.append( times_per_url_second[i] )

        return results[0:n]

    return_results = fetch_data(first_start,first_end,second_start,second_end)
        
    return json_response({ "code":200, "results": return_results }) 

def get_top_urls_following(request, username, n):
    user = get_object_or_404(User, username=username)
    enduser = get_enduser_for_user(user)
    following = [friendship.to_friend for friendship in user.friend_set.all()]

    n = int(n)
    first_start,first_end,second_start,second_end = _unpack_times(request)
    times_per_url_first = _get_top_n(user,first_start,first_end)
    times_per_url_second = _get_top_n(user,second_start,second_end)

    for friend in following:
        friend_user = get_object_or_404(User, username=friend.username)
        times_per_url_first.append(_get_top_n(friend_user,first_start,first_end))
        times_per_url_second.append(_get_top_n(friend_user,first_start,first_end))

    def index_of(what, where):
        try:
            return [ h[0] for h in where ].index(what)
        except:
            print sys.exc_info()
            pass
        return None

    results = []
    for i in range(len(times_per_url_second)): ## iterate over the more recent dudes
        old_rank = index_of(times_per_url_second[i][0],times_per_url_first)
        if old_rank is not None:
            diff = - (i - old_rank)  # we want the gain not the difference
            results.append(times_per_url_second[i] + (diff,) )
        else:
            results.append( times_per_url_second[i] )

    return json_response({ "code":200, "results": results[0:n] })


def get_views_url(request):
    from_msec,to_msec = _unpack_from_to_msec(request)
    url = request.GET['url'].strip()

    results = PageView.objects.filter(url=url,startTime__gte=from_msec,endTime__lte=to_msec)

    return json_response({ "code":200, "results": [ defang_pageview(evt) for evt in results ] } )


def _get_graph_points_for_results(results, to_msec, from_msec, n):
    interp = (to_msec - from_msec) / n
    counts = int(math.floor((to_msec - from_msec) / interp))
    ttData = [0]*(counts + 1) # total time spent per time block
    avgDataNum = [0]*(counts + 1) # number of websites per time block
    def get_date_array():
        foo = [0]*(counts + 1)
        for count in range(0, counts):
            foo[count] = from_msec + (interp * count)
        return foo
    dateArray = get_date_array()

    # gets total time on websites per time block(count)
    for result in results:
        for count in range(0, counts):
            if count >= counts:
                if result.startTime > dateArray[count]:
                    ttData[count] += int(result.endTime - result.startTime)
                    avgDataNum[count] += 1
                else:
                    pass
            else:
                if result.startTime > dateArray[count] and result.startTime < dateArray[count + 1]:
                    ttData[count] += int(result.endTime - result.startTime)
                    avgDataNum[count] += 1
                else:
                    pass
                    
    def get_avg_data():
        foo = [0]*counts
        for count in range(0, counts): 
            foo[count] = ttData[count] / (avgDataNum[count] + 1)
        return foo
    avgData = get_avg_data()

    return { "avgData": avgData, "ttData": ttData }


def get_graph_points_url(request, n):
    from_msec_raw,to_msec_raw = _unpack_from_to_msec(request)
    from_msec_rounded = round_time_to_day(from_msec_raw)
    to_msec_rounded = round_time_to_day(to_msec_raw)
    url = request.GET['url'].strip()
    n = int(n) # number of points on the graph

    @cache.region('to_from_url')
    def fetch_data(to_msec, from_msec, url):
        results = PageView.objects.filter(url=url,startTime__gte=from_msec,endTime__lte=to_msec)
        return _get_graph_points_for_results(results, to_msec, from_msec, n)

    results = fetch_data(to_msec_rounded, from_msec_rounded, url)
    return json_response({ "code":200, "results": results } )


def get_graph_points_user(request, username, n):
    user = User.objects.filter(username=username)
    from_msec_raw,to_msec_raw = _unpack_from_to_msec(request)
    from_msec_rounded = round_time_to_day(from_msec_raw)
    to_msec_rounded = round_time_to_day(to_msec_raw)
    n = int(n) # number of points on the graph

    @cache.region('to_from_url')
    def fetch_data(to_msec, from_msec, user):
        results = PageView.objects.filter(user=user,startTime__gte=from_msec,endTime__lte=to_msec)
        return _get_graph_points_for_results(results, to_msec, from_msec, n)

    results = fetch_data(to_msec_rounded, from_msec_rounded, user)
    return json_response({ "code":200, "results": results } )


def get_graph_points_global(request, n):
    from_msec_raw,to_msec_raw = _unpack_from_to_msec(request)
    from_msec_rounded = round_time_to_day(from_msec_raw)
    to_msec_rounded = round_time_to_day(to_msec_raw)
    n = int(n) # number of points on the graph

    @cache.region('to_from_url')
    def fetch_data(to_msec, from_msec):
        results = PageView.objects.filter(startTime__gte=from_msec,endTime__lte=to_msec)
        return _get_graph_points_for_results(results, to_msec, from_msec, n)

    results = fetch_data(to_msec_rounded, from_msec_rounded)
    return json_response({ "code":200, "results": results } )


# gets ranked list of the urls gone to before and after the url passed in the request
def get_to_from_url(request, n):
    from_msec_raw,to_msec_raw = _unpack_from_to_msec(request)
    #from_msec_rounded = round_time_to_day(from_msec_raw)
    to_msec_rounded = round_time_to_day(to_msec_raw)
    url = request.GET['url'].strip()

    # added this to check if url exists in the logs
    if  len(PageView.objects.filter(url=url)) < 1:
        # fail silently 
        return json_response({ "code":200, "results": {'pre':"", 'next':"", 'pre_titles': "" , 'next_titles' : "" } })
    n = int(n)

    @cache.region('to_from_url')
    def fetch_data(to_msec, url):
        accesses = PageView.objects.filter(url=url)#,startTime__gte=from_msec,endTime__lte=to_msec)
        pre = {}
        next = {}
        titles = {}
        for access in accesses:
            try:
                # get the page we logged IMMEDIATELY before access for the particular access's user in question
                prev_access = PageView.objects.filter(startTime__lt=access.startTime,user=access.user).order_by("-startTime")[0]
                if prev_access.url != url:
                    pre[prev_access.url] = pre.get(prev_access.url,0) + 1
                    if prev_access.title is not None:
                        titles[prev_access.url] = prev_access.title
                    else:
                        titles[prev_access.url] = prev_access.url
                else:
                    pass
            except:
                pass
            try:
                # get the page we logged IMMEDIATELY before access for the particular access's user in question
                next_access = PageView.objects.filter(startTime__gt=access.startTime,user=access.user).order_by("startTime")[0]
                if next_access.url != url:
                    next[next_access.url] = next.get(next_access.url,0) + 1
                    if next_access.title is not None:
                        titles[next_access.url] = next_access.title
                    else:
                        titles[next_access.url] = next_access.url
                else:
                    pass
            except:
                pass
            
        def sort_by_counts(count_dict):
            l = count_dict.items()
            l.sort(key=lambda x: -x[1])
            return l
        
        pre_sorted = sort_by_counts(pre)
        next_sorted = sort_by_counts(next)

        return { 'pre':pre_sorted[:7], 'next':next_sorted[:7], 'pre_titles': [ titles[x[0]] for x in pre_sorted[:7] ] , 'next_titles' : [ titles[x[0]] for x in next_sorted[:7] ] }

    return_results = fetch_data(to_msec_rounded, url)

    #hopefully this will be out of the cache
    if request.GET.has_key('username'):
        username = request.GET['username']
        friend_stats = {'top_friend': get_top_friend_for_url(request, username), 'num_friends': get_number_friends_logged_url(request, username) }
    
        return json_response({ "code":200, "results": return_results, "friend_stats": friend_stats })
        
    return json_response({ "code":200, "results": return_results })


def get_trending_urls(request, n):
    user = User.objects.all();
    user = user[0] ## again this is fail not sure how to iterate through the users esp if they have not logged anything
    n = int(n)
    first_start,first_end,second_start,second_end = _unpack_times(request)
    times_per_url_first = _get_top_n(user,first_start,first_end)
    times_per_url_second = _get_top_n(user,second_start,second_end)
    
    def index_of(what, where):
        try:
            return [ h[0] for h in where ].index(what)
        except:
            print sys.exc_info()
            pass
        return None

    results = []
    for i in range(len(times_per_url_second)): ## iterate over the more recent dudes
        old_rank = index_of(times_per_url_second[i][0],times_per_url_first)
        if old_rank is not None:
            diff = - (i - old_rank)  # we want the gain not the difference
            results.append(times_per_url_second[i] + (diff,) )
        else:
            results.append( times_per_url_second[i] )
                
    return json_response({ "code":200, "results": results[0:n] }) ## [(u, long(times_per_url[u])) for u in urls_ordered[0:n]] })

    

def get_top_users(request, n):
    users = User.objects.all();
    n = int(n)
    from_msec,to_msec = _unpack_from_to_msec(request)

    from_msec_rounded = round_time_to_half_day(from_msec)
    to_msec_rounded = round_time_to_half_day(to_msec)
    
    # this is to give the cache a unique reference
    bozon = "bozon"

    @cache.region('top_users_long_term')
    def fetch_data(from_msec, to_msec, bozon):
        results = []
        for user in users:
            results.append( {"user": user.username, "number": PageView.objects.filter(user=user,startTime__gte=from_msec,endTime__lte=to_msec).count() } )

        results.sort(key=lambda x:-x["number"])
        return results[0:n]
        
    return_results = fetch_data(from_msec_rounded, to_msec_rounded, bozon)

    return json_response({ "code":200, "results": return_results })


def get_top_users_for_url(request, n):
    users = User.objects.all();
    n = int(n)
    from_msec,to_msec = _unpack_from_to_msec(request)
    get_url = request.GET['url'].strip()

    from_msec_rounded = round_time_to_half_day(from_msec)
    to_msec_rounded = round_time_to_half_day(to_msec)

    barbar = "foo" # to keep cache unique
    @cache.region('top_users_long_term')
    def fetch_data(from_msec, to_msec, url, barbar):
        results = []
        for user in users:
            number = PageView.objects.filter(user=user,url=url,startTime__gte=from_msec,endTime__lte=to_msec).count()
            results.append( {"user": user.username, "number": number } )

        results.sort(key=lambda x: -x["number"])

        return results[0:n]

    return_results = fetch_data(from_msec_rounded, to_msec_rounded, get_url, barbar)

    return json_response({ "code":200, "results": return_results })

def get_top_friend_for_url(request, username):
    user = get_object_or_404(User, username=username)
    users = [friendship.to_friend for friendship in user.friend_set.all()]
    
    get_url = request.GET['url'].strip()

    barbar = "top friend for url" # to keep cache unique
    @cache.region('top_users_long_term')
    def fetch_data( url, username):
        results = []
        for user in users:
            number = PageView.objects.filter(user=user,url=url).count()
            results.append( {"user": user.username, "number": number } )

        results.sort(key=lambda x: -x["number"])
        return results[0:1]

    return_results = fetch_data(get_url, username)
    return return_results
    #return json_response({ "code":200, "results": return_results })

def get_top_friend_for_url_json(request, username):
    user = get_object_or_404(User, username=username)
    users = [friendship.to_friend for friendship in user.friend_set.all()]
    
    get_url = request.GET['url'].strip()

    barbar = "top friend for url" # to keep cache unique
    @cache.region('top_users_long_term')
    def fetch_data( url, username):
        results = []
        for user in users:
            number = PageView.objects.filter(user=user,url=url).count()
            results.append( {"user": user.username, "number": number } )

        results.sort(key=lambda x: -x["number"])
        return results[0:1]

    return_results = fetch_data(get_url, username)
    return json_response({ "code":200, "results": return_results })

def get_number_friends_logged_url(request, username):
    user = get_object_or_404(User, username=username)
    users = [friendship.to_friend for friendship in user.friend_set.all()]

    get_url = request.GET['url'].strip()    

    @cache.region('top_users_long_term')
    def fetch_data(url, username):
        results = []
        number = 0
        for user in users:
            if PageView.objects.filter(user=user,url=url).count() > 0:
                number += 1

        return number
    return_results = fetch_data(get_url, username)
    return return_results
    #return json_response({ "code":200, "results": return_results })

## emax added this to be fancy
def uniq(lst,key=lambda x: x,n=None):
    result = []
    keys = []
    for ii in range(len(lst)):
        xi = lst[ii]
        ki = key(xi)
        if ki not in keys:
            keys.append(ki)
            result.append(xi)
        if n is not None and len(result) >= n:
            return result
    
    return result        

## get most recent urls now returns elements with distinct titles. no repeats!
def get_most_recent_urls(request, n):
    n = int(n)

    # gets unique pages
    phits = PageView.objects.filter().order_by("-startTime")

    if n < 0 or n is None:
        n = len(phits)

    uphit = uniq(phits,lambda x:x.title,n)
    
    results = [ defang_pageview(evt) for evt in uphit ]

    if request.GET.has_key('id'):
        urlID = int(request.GET['id'])
        filter_results = []
        for result in results:
            if int(result['id']) > urlID:
                filter_results.append(result)
        if len(filter_results) > 0:
            return json_response({ "code":200, "results": filter_results })
        else:
            return json_response({ "code":204 })

    return json_response({ "code":200, "results": results })


def get_users_most_recent_urls(request, username, n):
    user = get_object_or_404(User, username=username)
    n = int(n)

    from_msec,to_msec = _unpack_from_to_msec(request)

    hits = _get_pages_for_user(user,from_msec,to_msec)

    return json_response({ "code":200, "results": [ defang_pageview(evt) for evt in hits[0:n] ] });    

def get_following_views(request, username):
    user = get_object_or_404(User, username=username)
    enduser = get_enduser_for_user(user)
    following = [friendship.to_friend for friendship in user.friend_set.all()]

    from_msec,to_msec = _unpack_from_to_msec(request)
    from_msec_rounded = round_time_to_day(from_msec)
    to_msec_rounded = round_time_to_day(to_msec)

    # potentially i can just not pass it the 'following' param hrmz
    @cache.region('long_term')
    def fetch_data(from_msec, to_msec, user, following):
        friends_results = []

        # add the request.user
        user_events = PageView.objects.filter(user=user,startTime__gte=from_msec,endTime__lte=to_msec)
        friends_results.append( {"username": enduser.user.username, "events": [ defang_pageview(evt) for evt in user_events ] } )
        
        # add friends
        for friend in following:
            #friend_user = get_object_or_404(User, username=friend.username)
            events = PageView.objects.filter(user=friend,startTime__gte=from_msec,endTime__lte=to_msec)
            friends_results.append( {"username": friend.username, "events": [ defang_pageview(evt) for evt in events ] } )
            
        #friends_results.sort(key=lambda x:(x["username"], x["username"]))
        return friends_results

    results = fetch_data(from_msec_rounded, to_msec_rounded, user, following)

    return json_response({ "code":200, "results": results });    
        
# search stuff down here
def user_search_page(request):
    form = UserSearchForm()
    bookmarks = []
    show_results = False
    if request.GET.has_key('query'):
        show_results = True
        query = request.GET['query'].strip()
        if query:
            keywords = query.split()
            q = Q()
            for keyword in keywords:
                q = q & Q(title__icontains=keyword)
            form = SearchForm({'query' : query})
            bookmarks = EndUser.objects.filter(q)[:10]
            
    variables = RequestContext(request, { 'form': form,
                                          'show_results': show_results,
                                          'show_tags': True,
                                          'show_user': True
                                          })
    if request.GET.has_key('ajax'):
        return render_to_response('search_results.html', variables)
    else:
        return render_to_response('search.html', variables)

def get_closest_url(request):
    url = request.GET['url']
    ## finds the urls that best match the given url. if there
    ## is an exact match, only returns that.
    if PageView.objects.filter(url=url).count() > 0:
        return json_response({ "code":200, "results": [url] });
    
    hits = list(set([ url['url'] for url in PageView.objects.filter(url__contains=url).values('url') ]))
    hits.sort( lambda x,y: len(x)-len(y) )
    return json_response({ "code":200, "results": hits });
    
