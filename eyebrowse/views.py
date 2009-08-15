import re,sys,time,operator,os,math
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

#TEMPORARY
def pluginhover(request):
    t = loader.get_template("plugin_hover.html")
    c = Context({ 'request_user': request.user.username })

    return HttpResponse(t.render(c))

#TEMPORARY
def pluginlogin(request):
    t = loader.get_template("client_login.html")
    c = Context({ 'request_user': request.user.username })

    return HttpResponse(t.render(c))

def get_enduser_for_user(user):
    if EndUser.objects.filter(user=user).count() > 0:
        enduser = EndUser.objects.filter(user=user)[0]
    else:
        raise Http404('Internal error. Call brennan or emax. Something is wrong. Houston.')    
    return enduser


def privacy_settings_page(request, username):
    user = get_object_or_404(User, username=username)
    if username != request.user.username:
        return HttpResponseForbidden('Only %s can edit this profile' % username)

    privacysettings = user.privacysettings_set.all()[0] ## ?

    listmode = privacysettings.listmode
    exposure = privacysettings.exposure
    
    form = PrivacySaveForm({
            'exposure': exposure,
            'listmode': listmode,
            })

    if request.method == 'POST':
        form = PrivacySaveForm(request.POST)
        if form.is_valid():
            user = _privacy_save(request, form)  
            return HttpResponseRedirect(
                '/profile/%s/' % request.user.username
                )
        variables = RequestContext(request, {'form': form, 'error': True, 'request_user': request.user})
        return render_to_response('whitelist.html', variables)
    variables = RequestContext(request, {'form': form, 'list':list, 'request_user': request.user })
    return render_to_response('whitelist.html', variables )

def _privacy_save(request, form):
    username = request.user.username
    user = get_object_or_404(User, username=username)
    privacysettings = user.privacysettings_set.all()[0] ## ?

    privacysettings.listmode = form.cleaned_data['listmode']
    privacysettings.exposure = form.cleaned_data['exposure']
    privacysettings.save()

    return user


def get_privacy_urls(request, username):
    username = request.user.username
    user = get_object_or_404(User, username=username)
    privacysettings = user.privacysettings_set.all()[0] ## ?     
    
    if privacysettings.listmode == "W":
        list = privacysettings.whitelist.split()  ## redefin'in a reserved keyword since 2009.. CHANGE 'list' TO SOMETHING ELSE! plz. kthx
    if privacysettings.listmode == "B":
        list = privacysettings.blacklist.split()

    return json_response({ "code":200, "results": list }) 

def delete_privacy_url(request, username):
    if username != request.user.username:
        return HttpResponseRedirect('/userprivacy/%s/'% username)
    user = get_object_or_404(User, username=username)
    privacysettings = user.privacysettings_set.all()[0] ## ?
    listmode = privacysettings.listmode
    input = request.GET['input'].strip()

    if privacysettings.listmode == "W":
        privacysettings.whitelist = ' '.join([ x for x in privacysettings.whitelist.split() if not x == input])
    if privacysettings.listmode == "B":
        privacysettings.blacklist = ' '.join([ x for x in privacysettings.blacklist.split() if not x == input])

    privacysettings.save()
    return HttpResponseRedirect('/settings/%s/' % user.username)

def add_privacy_url(request, username):
    if username != request.user.username:
        return HttpResponseRedirect('/userprivacy/%s/'% username)
    user = get_object_or_404(User, username=username)
    privacysettings = user.privacysettings_set.all()[0] ## ?
    listmode = privacysettings.listmode
    input = request.GET['input'].strip()

    if privacysettings.listmode == "W":
        if privacysettings.whitelist is not None:
            if not input in privacysettings.whitelist.split():
                privacysettings.whitelist = ' '.join(privacysettings.whitelist.split() + [input])
        else:
            privacysettings.whitelist = input
    if privacysettings.listmode == "B":
        if privacysettings.blacklist is not None:
            if not input in privacysettings.blacklist.split():
                privacysettings.blacklist = ' '.join(privacysettings.blacklist.split() + [input])
        else:
            privacysettings.blacklist = input
    # Save 
    privacysettings.save()
    return HttpResponseRedirect('/settings/%s/' % user.username)


def userprivacy(request, username):
    t = loader.get_template("user_privacy.html")
    c = Context({ 'requestuser': request.user.username, 'username': username })

    return HttpResponse(t.render(c))


def index(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
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

    t = loader.get_template("graph.html")
    c = Context({ 'username': enduser.user.username, 'id': enduser.user.id, 'request_user': request_user })
    return HttpResponse(t.render(c))

def world(request): # confusing name fix this
    t = loader.get_template("global.html")
    c = Context({ 'username': request.user.username, 'id': request.user.id, 'request_user': request.user.username })
    return HttpResponse(t.render(c))

def page_profile(request): 
    variables = RequestContext(request, {
        'username': request.user.username,
        'request_user': request.user.username
        })
    return render_to_response('webpage.html', variables)

def friends(request, username):
    user = get_object_or_404(User, username=username)
    enduser = get_enduser_for_user(user)

    friends = enduser.friends.all()
    friends_results = []
    for friend in friends:
        friends_results.append( {"username": friend.user.username, "number": Event.objects.filter(owner=friend.user,type="www-viewed").count()} )
    friends_results.sort(key=lambda x:(x["username"], x["number"]))
    
    request_user = request.user.username

    variables = RequestContext(request, {
        'username': username,
        'show_edit': username == request.user.username,
        'friends': friends_results,
        'request_user': request_user
        })
    return render_to_response('friends.html', variables)

def user_page(request, username):
    user = get_object_or_404(User, username=username)
    enduser = get_enduser_for_user(user)

    if request.user.username:
        request_enduser = get_enduser_for_user(request.user)
        is_friend = user.friend_set.all().filter(id=request.user.id)
    else: 
        is_friend = False;

    followers = [friendship.to_friend for friendship in user.friend_set.all()]
    following = [friendship.from_friend for friendship in user.to_friend_set.all()]

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
    friends_results.sort(key=lambda x:(x["username"], x["number"]))
    
    tags = ' '.join(
        tag.name for tag in enduser.tags.all()
        )
    
    variables = RequestContext(request, {
         'username': username,
         'show_edit': username == request.user.username,
         'following': following,
         'followers': followers,
         'is_friend': is_friend,
         'first_name': enduser.user.first_name,
         'last_name': enduser.user.last_name,
         'location': enduser.location,
         'homepage': enduser.homepage,
         'birthdate': enduser.birthdate,
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
                return HttpResponseRedirect('/profile/')
            else:
                # disabled account
             #   return direct_to_template(request, 'inactive_account.html')
                variables = RequestContext(request, {'form': form, 'error': True})
                return render_to_response('login.html', variables)

    else:
        variables = RequestContext(request, {'form': form})
        return render_to_response('registration/register_success.html', variables)
    #        return direct_to_template(request, 'invalid_login.html')
        
@login_required
def profile_save_page(request, username):
    if username != request.user.username:
        return HttpResponseRedirect('/')
    user = get_object_or_404(User, username=username)
    enduser = get_enduser_for_user(user)
    #friends = [friendship.to_friend for friendship in user.friend_set.all()]
    friends = enduser.friends.all()
    friends_results = []
    for friend in friends:
        friends_results.append( {"username": friend.user.username, "number": Event.objects.filter(owner=friend.user,type="www-viewed").count()} )
    friends_results.sort(key=lambda x:(x["username"], x["number"]))


    if request.method == 'POST':
        form = ProfileSaveForm(request.POST, request.FILES)
        if form.is_valid():
            user = _profile_save(request, form)            
            return HttpResponseRedirect(
                '/profile/%s/' % request.user.username
                )
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

    enduser.location = form.cleaned_data['location']
    enduser.birthdate = form.cleaned_data['birthdate']
    enduser.homepage = form.cleaned_data['homepage']
    enduser.gender = form.cleaned_data['gender']

    tag_names = form.cleaned_data['tags'].split()
    for tag_name in tag_names:
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
        try:
            # save the original image   
            img = request.FILES['photo']
            name = "%d.%s"% (enduser.user.id, img.name.strip().split(".")[-1])
            file_exts = ('.png', '.jpg', '.jpeg',)
            if splitext(img.name)[1].lower() not in file_exts:
                print file_exts
                raise forms.ValidationError("Only following Picture types accepted: %s"
                                            % ", ".join([f.strip('.') for f in file_exts]))
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
        except:
            print sys.exc_info()
            pass

    enduser.save()
    return user

@login_required
def delete_url_entry(request):
    enduser = get_enduser_for_user(request.user)        

    inputURL = request.POST['URL'].strip()
    #inputPage = Page.objects.filter(url=inputURL)
    #url_entry = PageView.objects.filter(user=enduser.user.username).filter(page=inputPage)
    url_entry = Event.objects.filter(owner=enduser.user,type="www-viewed",entityid=inputURL)

    for url in url_entry:
        url.delete()

    # TEMPORARY until i get it to remove all the same events from the page
    return json_response({ "code":200 });


def friends_page(request, username):
    if username != request.user.username:
        return HttpResponseRedirect('/userprivacy/%s/'% username)
    user = get_object_or_404(User, username=username)
    enduser = get_enduser_for_user(user)

    followers = [friendship.to_friend for friendship in user.friend_set.all()]
    following = [friendship.from_friend for friendship in user.to_friend_set.all()]

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
       # except:
       #     request.user.message_set.create(
       #         message='%s is already your friend.' % friend.username
       #         )
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
    print "post-save event for sender %s : %s " % (repr(sender),repr(instance.entityid)) ## debug!!
    if (created and instance is not None):
        if instance.entitytype == "schemas.Webpage" and instance.entityid is not None:
            print "post-save url: %s " % instance.entityid ## debug!!
            pageview = PageView.from_Event(instance)
            pageview.save()
                
post_save.connect(create_www_pageviews_for_each_event, sender=Event)

def json_response(dict_obj):
    return HttpResponse(JSONEncoder().encode(dict_obj), "text/json")
                        
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
    return {"start" : long(pview.startTime), "end" : long(pview.endTime), "url" : pview.url, "host": pview.host, "title": pview.title}

#@login_required
def get_web_page_views(request):
    from_msec_raw,to_msec_raw = _unpack_from_to_msec(request)
    from_msec_rounded = round_time_to_day(from_msec_raw)
    to_msec_rounded = round_time_to_day(to_msec_raw)

    @cache.region('short_term')
    def fetch_data(from_msec, to_msec, user):
        hits =  _get_pages_for_user(request.user,from_msec,to_msec)
        return [ defang_pageview(evt) for evt in hits ]

    results = fetch_data(from_msec_rounded, to_msec_rounded, request.user)

    return json_response({ "code":200, "results": results });

def get_web_page_views_user(request, username):
    user = get_object_or_404(User, username=username)
    enduser = get_enduser_for_user(user)

    from_msec_raw,to_msec_raw = _unpack_from_to_msec(request)
    from_msec_rounded = round_time_to_day(from_msec_raw)
    to_msec_rounded = round_time_to_day(to_msec_raw)

    @cache.region('short_term')
    def fetch_data(from_msec, to_msec, user):
        hits = _get_pages_for_user(user ,from_msec,to_msec)
        return [ defang_pageview(evt) for evt in hits ]

    results = fetch_data(from_msec_rounded, to_msec_rounded, user)

    return json_response({ "code":200, "results": results });


# ****should not have to sort to return recent view***** that is crazzzy expensive
def get_recent_web_page_view_user(request, username, n):
    user = get_object_or_404(User, username=username)
    n = int(n)
    #from_msec_raw,to_msec_raw = _unpack_from_to_msec(request)
    results = PageView.objects.filter(user=user).order_by('-startTime')[:n]
    return json_response({ "code":200, "results": [ defang_pageview(evt) for evt in results ] });

def get_user_profile_queries(request, username):
    user = get_object_or_404(User, username=username)

    @cache.region('short_term')
    def fetch_data(user):
        number = PageView.objects.filter(user=user).count()
        totalTime = PageView.objects.filter(user=user).aggregate(Sum('duration'))
        average = int((totalTime['duration__sum'])/1000)/int(number)
        return { 'number': number, 'totalTime': int(totalTime['duration__sum']/1000), 'average': average }

    results = fetch_data(user)
    return json_response({ "code":200, "results": results });

def get_global_profile_queries(request):
    from_msec_raw,to_msec_raw = _unpack_from_to_msec(request)
    from_msec_rounded = round_time_to_day(from_msec_raw)
    to_msec_rounded = round_time_to_day(to_msec_raw)

    #@cache.region('long_term')
    def fetch_data(from_msec, to_msec):
        totalTime  = PageView.objects.filter(startTime__gte=from_msec,endTime__lte=to_msec).aggregate(Sum('duration'))
        number =  PageView.objects.filter(startTime__gte=from_msec,endTime__lte=to_msec).count()
        average = int((totalTime['duration__sum'])/1000)/int(number)
        return { 'number': number, 'totalTime': int(totalTime['duration__sum']/1000), 'average': average }

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
        average = int((totalTime['duration__sum'])/1000)/int(number)
        return { 'number': number, 'totalTime': int(totalTime['duration__sum']/1000), 'average': average }

    results = fetch_data(from_msec_rounded, to_msec_rounded, inputURL)
    return json_response({ "code":200, "results": results });


def get_top_hosts(request, n):
    users = User.objects.all()
    n = int(n)
    from_msec,to_msec = _unpack_from_to_msec(request)
    times_per_url = _get_time_per_page(users,from_msec,to_msec,grouped_by=EVENT_SELECTORS.Host)
    urls_ordered = times_per_url.keys()
    urls_ordered.sort(lambda u1,u2: int(times_per_url[u2] - times_per_url[u1]))

    #_mimic_entity_schema_from_url
    return json_response({ "code":200, "results": [(u, long(times_per_url[u])) for u in urls_ordered[0:n]] }) 

    
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

def get_top_urls_following(request, n):
    user = get_object_or_404(User, username=username)
    enduser = get_enduser_for_user(user)
    following = [friendship.from_friend for friendship in user.to_friend_set.all()]

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


# gets ranked list of the urls gone to before and after the url passed in the request
def get_to_from_url(request, n):
    from_msec_raw,to_msec_raw = _unpack_from_to_msec(request)
    from_msec_rounded = round_time_to_day(from_msec_raw)
    to_msec_rounded = round_time_to_day(to_msec_raw)
    url = request.GET['url'].strip()
    n = int(n)

    @cache.region('long_term')
    def fetch_data(from_msec, to_msec):
        accesses = PageView.objects.filter(url=url,startTime__gte=from_msec,endTime__lte=to_msec)
        pre = {}
        next = {}
        for access in accesses:
            try:
                # get the page we logged IMMEDIATELY before access for the particular access's user in question
                prev_access = PageView.objects.filter(startTime__lt=access.startTime,user=access.user).order_by("-startTime")[0]
                pre[prev_access.url] = pre.get(prev_access.url,0) + 1
            except:
                pass
            try:
                # get the page we logged IMMEDIATELY before access for the particular access's user in question
                next_access = PageView.objects.filter(startTime__gt=access.startTime,user=access.user).order_by("startTime")[0]
                next[next_access.url] = next.get(next_access.url,0) + 1
            except:
                pass
            
        def sort_by_counts(count_dict):
            l = count_dict.items()
            l.sort(key=lambda x: -x[1])
            return l
        
        pre_sorted = sort_by_counts(pre)
        next_sorted = sort_by_counts(next)
        
        return { 'pre':pre_sorted[:10], 'next':next_sorted[:10] }

    return_results = fetch_data(from_msec_rounded, to_msec_rounded)

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
    
    ## this needs to sort by the diff
    ## results.sort(lambda u1,u2: int(times_per_url_second[u2] - times_per_url[u1]))
            
    return json_response({ "code":200, "results": results[0:n] }) ## [(u, long(times_per_url[u])) for u in urls_ordered[0:n]] })


def get_top_users(request, n):
    users = User.objects.all();
    n = int(n)
    from_msec,to_msec = _unpack_from_to_msec(request)

    from_msec_rounded = round_time_to_day(from_msec)
    to_msec_rounded = round_time_to_day(to_msec)

    @cache.region('long_term')
    def fetch_data(from_msec, to_msec):
        results = []
        for user in users:
            results.append( {"user": user.username, "number": PageView.objects.filter(user=user,startTime__gte=from_msec,endTime__lte=to_msec).count() } )
            
        results.sort(key=lambda x:(x["number"], x["user"]))
        return results[0:n]
        
    return_results = fetch_data(from_msec_rounded, to_msec_rounded)

    return json_response({ "code":200, "results": return_results })

def get_top_users_for_url(request, n):
    users = User.objects.all();
    n = int(n)
    from_msec,to_msec = _unpack_from_to_msec(request)
    get_url = request.GET['url'].strip()

    from_msec_rounded = round_time_to_day(from_msec)
    to_msec_rounded = round_time_to_day(to_msec)

    @cache.region('long_term')
    def fetch_data(from_msec, to_msec, url):
        results = []
        for user in users:
            number = PageView.objects.filter(user=user,url=url,startTime__gte=from_msec,endTime__lte=to_msec).count()
            results.append( {"user": user.username, "number": number } )
            
        results.sort(key=lambda x:(x["user"], x["number"]))
        return results[0:n]

    return_results = fetch_data(from_msec_rounded, to_msec_rounded, get_url)

    return json_response({ "code":200, "results": return_results })

def get_most_recent_urls(request, n):
    n = int(n)
    
    from_msec,to_msec = _unpack_from_to_msec(request)
    
    hits = PageView.objects.filter(startTime__gte=from_msec,endTime__lte=to_msec).order_by("-startTime")

    if n > 0:
        return json_response({ "code":200, "results": [ defang_pageview(evt) for evt in hits[0:n] ] });
    else:
        return json_response({ "code":200, "results": [ defang_pageview(evt) for evt in hits ] });

def get_users_most_recent_urls(request, username, n):
    users = User.objects.filter(username=username)
    if len(users) == 0:
        return json_response({"code":401,"message":"Unknown user %s" % username})
    user = users[0]    
    n = int(n)

    from_msec,to_msec = _unpack_from_to_msec(request)

    hits = _get_pages_for_user(user,from_msec,to_msec)
   # print "Got a request to do it from %d to %d (got %d) " % (int(from_msec),int(to_msec),len(hits))    

    return json_response({ "code":200, "results": [ defang_pageview(evt) for evt in hits[0:n] ] });    

# complex to cache as will have to re-run if they start following more users        
def get_following_views(request, username):
    user = get_object_or_404(User, username=username)
    enduser = get_enduser_for_user(user)
    following = [friendship.from_friend for friendship in user.to_friend_set.all()]

    from_msec,to_msec = _unpack_from_to_msec(request)
    from_msec_rounded = round_time_to_day(from_msec)
    to_msec_rounded = round_time_to_day(to_msec)

    # potentially i can just not pass it the 'following' param hrmz
    @cache.region('long_term')
    def fetch_data(from_msec, to_msec, user, following):
        friends_results = []

        for friend in following:
            friend_user = get_object_or_404(User, username=friend.username)
            events = PageView.objects.filter(user=friend_user,startTime__gte=from_msec,endTime__lte=to_msec)
            friends_results.append( {"username": friend.username, "events": [ defang_pageview(evt) for evt in events ] } )
            
        # add the request.user
        user_events = PageView.objects.filter(user=user,startTime__gte=from_msec,endTime__lte=to_msec)
        friends_results.append( {"username": enduser.user.username, "events": [ defang_pageview(evt) for evt in user_events ] } )

        friends_results.sort(key=lambda x:(x["username"], x["username"]))
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
