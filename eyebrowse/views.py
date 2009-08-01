import re,sys,time
from django.template import loader, Context
from django.http import HttpResponse
from django.http import HttpResponseRedirect
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
from PIL import Image
from os.path import splitext
from django.db.models.signals import post_save
from jv3.models import Event ## from listit, ya.
from django.utils.simplejson import JSONEncoder, JSONDecoder

def privacy_settings_page(request, username):
    if username != request.user.username:
        return HttpResponseRedirect('/')
    user = get_object_or_404(User, username=username)

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
    enduser = get_enduser_for_user(user)
    privacysettings = user.privacysettings_set.all()[0] ## ?

    privacysettings.listmode = form.cleaned_data['listmode']
    privacysettings.exposure = form.cleaned_data['exposure']
    privacysettings.save()

#     tag_names = form.cleaned_data['tags'].split()
#     for tag_name in tag_names:
#         tag, dummy = UserTag.objects.get_or_create(name=tag_name)
#         enduser.tags.add(tag) 
    return user


def get_privacy_urls(request, username):
    username = request.user.username
    user = get_object_or_404(User, username=username)
    enduser = get_enduser_for_user(user)
    privacysettings = user.privacysettings_set.all()[0] ## ?     
   
    print privacysettings

    if privacysettings.listmode == "W":
        list = privacysettings.whitelist.split()
    if privacysettings.listmode == "B":
        list = privacysettings.blacklist.split()

    return json_response({ "code":200, "results": list }) 

def userprivacy(request, username):
    t = loader.get_template("user_privacy.html")
    c = Context({ 'requestuser': request.user.username, 'username': username })

    return HttpResponse(t.render(c))

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

def moreinfo(request):
    t = loader.get_template("moreinfo.html")
    c = Context({ 'request_user': request.user.username })

    return HttpResponse(t.render(c))

def terms(request):
    t = loader.get_template("terms.html")
    c = Context({ 'request_user': request.user.username })

    return HttpResponse(t.render(c))

def list(request, username):
    user = get_object_or_404(User, username=username)
    enduser = get_enduser_for_user(user)
    is_friend = FriendRequest.objects.filter(
        from_friend=request.user,
        to_friend=user)    
    privacysettings = enduser.user.privacysettings_set.all()[0] ## ?
    exposure = privacysettings.exposure

    if request.user.id is not enduser.user.id:
        if exposure == 'N':
            return HttpResponseRedirect('/userprivacy/%s/'% enduser.user.username)
        if exposure == 'F':
            if not is_friend:
                return HttpResponseRedirect('/userprivacy/%s/'% enduser.user.username)
            pass
    t = loader.get_template("list.html")
    c = Context({ 'username': enduser.user.username, 'id': enduser.user.id })

    return HttpResponse(t.render(c))

def day(request, username):
    user = get_object_or_404(User, username=username)
    enduser = get_enduser_for_user(user)
    is_friend = FriendRequest.objects.filter(
        from_friend=request.user,
        to_friend=user)    
    privacysettings = enduser.user.privacysettings_set.all()[0] ## ?
    exposure = privacysettings.exposure
    request_user = request.user.username

    if request.user.id is not enduser.user.id:
        if exposure == 'N':
            return HttpResponseRedirect('/userprivacy/%s/'% enduser.user.username)
        if exposure == 'F':
            if not is_friend:
                return HttpResponseRedirect('/userprivacy/%s/'% enduser.user.username)
            pass
    t = loader.get_template("day.html")
    c = Context({ 'username': enduser.user.username, 'id': enduser.user.id, 'request_user': request_user })

    return HttpResponse(t.render(c))

def report(request, username):
    user = get_object_or_404(User, username=username)
    enduser = get_enduser_for_user(user)
    is_friend = FriendRequest.objects.filter(
        from_friend=request.user,
        to_friend=user)    
    privacysettings = enduser.user.privacysettings_set.all()[0] ## ?
    exposure = privacysettings.exposure
    request_user = request.user.username

    if request.user.id is not enduser.user.id:
        if exposure == 'N':
            return HttpResponseRedirect('/userprivacy/%s/'% enduser.user.username)
        if exposure == 'F':
            if not is_friend:
                return HttpResponseRedirect('/userprivacy/%s/'% enduser.user.username)
            pass
    t = loader.get_template("report.html")
    c = Context({ 'username': enduser.user.username, 'id': enduser.user.id, 'request_user': request_user })

    return HttpResponse(t.render(c))

def graph(request, username):
    user = get_object_or_404(User, username=username)
    enduser = get_enduser_for_user(user)
    is_friend = FriendRequest.objects.filter(
        from_friend=request.user,
        to_friend=user)    
    privacysettings = enduser.user.privacysettings_set.all()[0] ## ?
    exposure = privacysettings.exposure
    request_user = request.user.username

    if request.user.id is not enduser.user.id:
        if exposure == 'N':
            return HttpResponseRedirect('/userprivacy/%s/'% enduser.user.username)
        if exposure == 'F':
            if not is_friend:
                return HttpResponseRedirect('/userprivacy/%s/'% enduser.user.username)
            pass
    t = loader.get_template("graph.html")
    c = Context({ 'username': enduser.user.username, 'id': enduser.user.id, 'request_user': request_user })
    return HttpResponse(t.render(c))


def login_page(request):
    if request.method == 'POST':
        user = authenticate(username=request.POST['username'], password=request.POST['password'])
        if user is not None:
            if user.is_active:
                login(request, user)
                # success
                return HttpResponseRedirect('/profile/')
            else:
                # disabled account
                print "TOIOIS"

             #   return direct_to_template(request, 'inactive_account.html')
                variables = RequestContext(request, {'form': form, 'error': True})
                return render_to_response('login.html', variables)

        else:
            # invalid login
            print "TOIOIS"
            variables = RequestContext(request, {'form': form, 'error': True})
            return render_to_response('login.html', variables)
    #        return direct_to_template(request, 'invalid_login.html')
        
def logout_page(request):
    logout(request)
    return HttpResponseRedirect('/')

def add_privacy_url(request, username):
    if username != request.user.username:
        return HttpResponseRedirect('/')
    user = get_object_or_404(User, username=username)
    privacysettings = user.privacysettings_set.all()[0] ## ?
    listmode = privacysettings.listmode
    input = request.GET['input'].strip()

    if privacysettings.listmode == "W":
        list = privacysettings.whitelist.split()
        if not input in privacysettings.whitelist.split():
            privacysettings.whitelist = ' '.join(privacysettings.whitelist.split() + [input])
    if privacysettings.listmode == "B":
        list = privacysettings.blacklist.split()
        if not input in privacysettings.blacklist.split():
            privacysettings.blacklist = ' '.join(privacysettings.blacklist.split() + [input])

    # Save 
    privacysettings.save()
    return HttpResponseRedirect('/settings/%s/' % user.username)


def get_enduser_for_user(user):
    if EndUser.objects.filter(user=user).count() > 0:
        return EndUser.objects.filter(user=user)[0]
    raise Http404('Internal error. Call brennan or emax. Something is wrong. Houston.')
    

def user_page(request, username):
    user = get_object_or_404(User, username=username)
    enduser = get_enduser_for_user(user)
    is_friend = FriendRequest.objects.filter(
        from_friend=request.user,
        to_friend=user)    
    privacysettings = enduser.user.privacysettings_set.all()[0] ## ?
    exposure = privacysettings.exposure


    if request.user.id is not enduser.user.id:
        if exposure == 'N':
            return HttpResponseRedirect('/userprivacy/%s/'% enduser.user.username)
        if exposure == 'F':
            if not is_friend:
                return HttpResponseRedirect('/userprivacy/%s/'% enduser.user.username)
            pass

    friends = [friendship.to_friend for friendship in user.friend_set.all()]

    request_user = request.user.username
    first_name = enduser.user.first_name
    last_name = enduser.user.last_name
    location = enduser.location
    homepage = enduser.homepage
    birthdate = enduser.birthdate
    photo = enduser.photo
    gender = enduser.gender
    id = enduser.user.id

    variables = RequestContext(request, {
        'username': username,
        'show_edit': username == request.user.username,
        'friends': friends,
        'is_friend': is_friend,
        'first_name': first_name,
        'last_name': last_name,
        'location': location,
        'homepage': homepage,
        'birthdate': birthdate,
        'photo': photo,
        'gender': gender,
        'id':id,
        'request_user': request_user
        })
    return render_to_response('user_page.html', variables)

def register_page(request):
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

@login_required
def profile_save_page(request, username):
    if username != request.user.username:
        return HttpResponseRedirect('/')
    user = get_object_or_404(User, username=username)
    if EndUser.objects.filter(user=user).count() > 0:
        enduser = EndUser.objects.filter(user=user)[0]
    else:
        enduser = EndUser()
        enduser.user = user    
    friends = [friendship.to_friend for friendship in user.friend_set.all()]

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
        'friends': friends,
        'form': form,
        'request_user': request.user
        })
    return render_to_response('profile_save.html', variables)

def _profile_save(request, form):
    username = request.user.username
    user = get_object_or_404(User, username=username)
    enduser = get_enduser_for_user(user)

    enduser.user.first_name = form.cleaned_data['first_name']
    enduser.user.last_name = form.cleaned_data['last_name']
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
    try:
        #image = Image.open(request.FILES['photo'])
        #size = 128, 128
        #image.thumbnail(size, Image.ANTIALIAS)
        img = request.FILES['photo']
        name = "%d.%s"% (enduser.user.id, img.name.strip().split(".")[-1])
        file_exts = ('.png', '.jpg', '.jpeg',)
        if splitext(img.name)[1].lower() not in file_exts:
            print file_exts
            raise forms.ValidationError("Only following Picture types accepted: %s"
                                        % ", ".join([f.strip('.') for f in file_exts]))
        else:
            enduser.photo.save(name, img)
    except:
        print sys.exc_info()
        pass
    enduser.save()
    return user
    
def friends_page(request, username):
    user = get_object_or_404(User, username=username)
    friends = [friendship.to_friend for friendship in user.friend_set.all()]
    variables = RequestContext(request, {
        'username': username,
        'friends': friends,
        'show_user': True
        })
    return render_to_response('friends_page.html', variables)

@login_required
def friend_add(request):
    if request.GET.has_key('username'):
        friend = get_object_or_404(User, username=request.GET['username'])
        friendship = FriendRequest(
            from_friend=request.user,
            to_friend=friend
            )
        try:
            friendship.save()
            request.user.message_set.create(
                message='%s was added to your friend list.' % friend.username
                )
        except:
            request.user.message_set.create(
                message='%s is already a friend of yours.' % friend.username
                )
        return HttpResponseRedirect(
            '/friends/%s/' % request.user.username
            )
    else:
        raise Http404('boo.')

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
                                          'bookmarks': bookmarks,
                                          'show_results': show_results,
                                          'show_tags': True,
                                          'show_user': True
                                          })
    if request.GET.has_key('ajax'):
        return render_to_response('search_results.html', variables)
    else:
        return render_to_response('search.html', variables)


## hook for creating relevant Page objects when new jv3.Event objects get created
## by the listit server (which answers calls from listit)    
def create_www_pages_for_each_event(sender, created=None, instance=None, **kwargs):
    print "post-save event for sender %s : %s " % (repr(sender),repr(instance.entityid)) ## debug!!
    if (created and instance is not None):
        if instance.entitytype == "schemas.Webpage" and instance.entityid is not None:
            print "post-save url: %s " % instance.entityid ## debug!!
            p,createdpage = Page.objects.get_or_create(url=instance.entityid)
            if createdpage:
                p.set_host_path(instance.entityid)
                p.save()
                
post_save.connect(create_www_pages_for_each_event, sender=Event)

def json_response(dict_obj):
    return HttpResponse(JSONEncoder().encode(dict_obj), "text/json")
                        
## ajax views for graphs, etc.

def _mimic_entity_schema_from_url(url):
    import urlparse
    prot, host, page, foo, bar, baz = urlparse.urlparse(url)
    return {"id":url, "host":host, "path": page, "type":"schemas.Webpage"}

def _get_pages_for_user(user,from_msec,to_msec):
    return Event.objects.filter(owner=user,type="www-viewed",start__gte=from_msec,end__lte=to_msec)

def _unpack_from_to_msec(request):
    return (request.GET.get('from',0), request.GET.get('to',long(time.mktime(time.localtime())*1000)))

def _unpack_times(request):
    return (long(request.GET['first_start']), long(request.GET['first_end']), long(request.GET['second_start']), long(request.GET['second_end']))

def _get_top_n(user,start,end):
    time_per_host = _get_time_per_page(user,start,end,grouped_by=EVENT_SELECTORS.Host)
    ordered_visits = [h for h in time_per_host.iteritems()]
    ordered_visits.sort(lambda u1,u2: int(u2[1] - u1[1]))
    return ordered_visits    

def get_title_from_evt(evt):
    foo =  JSONDecoder().decode(JSONDecoder().decode(evt.entitydata)[0]['data'])
    if foo.has_key('title'):
        return foo['title']
    return   


class EVENT_SELECTORS:
    class Page:
        @staticmethod
        def access(queryset):
            return [s[0] for s in queryset.values_list('entityid')]
        @staticmethod
        def filter_queryset(queryset,url):
            return queryset.filter(entityid=url)
    class Host:
        @staticmethod
        def access(queryset):
            import urlparse
            return [urlparse.urlparse(url[0])[1] for url in queryset.values_list('entityid')]
        @staticmethod
        def filter_queryset(queryset,url):
            return queryset.filter(entityid__contains="://%s/"%url)        


def _get_time_per_page(user,from_msec,to_msec,grouped_by=EVENT_SELECTORS.Page):
    mine_events = _get_pages_for_user(user, from_msec, to_msec)
    uniq_urls  = set( grouped_by.access(mine_events) )
    times_per_url = {}
    for url in uniq_urls:
        times_per_url[url] = long(reduce(lambda x,y: x+y, [ startend[1]-startend[0] for startend in grouped_by.filter_queryset(mine_events,url).values_list('start','end') ] ))
    return times_per_url

#@login_required
def get_web_page_views(request):
    ## gimme get parameters :
    ## from: start time
    ## to: end time

    if request.user is None:
          ## the person is asking us for access to another user's activity log.
        return json_response({"code":401,"message":"Access forbidden, please log in first"})

    from_msec,to_msec = _unpack_from_to_msec(request)

    defang_event = lambda evt : {"start" : long(evt.start), "end" : long(evt.end), "url" : evt.entityid, "entity": _mimic_entity_schema_from_url(evt.entityid), "title": get_title_from_evt(evt)}
    hits = _get_pages_for_user(request.user,from_msec,to_msec)
    print "Got a request to do it from %d to %d (got %d) " % (int(from_msec),int(to_msec),len(hits))    
    
    return json_response({ "code":200, "results": [ defang_event(evt) for evt in hits ] });

def get_web_page_views_user(request, username):
    ## gimme get parameters :
    ## from: start time
    ## to: end time
    user = get_object_or_404(User, username=username)
    enduser = get_enduser_for_user(user)

    from_msec,to_msec = _unpack_from_to_msec(request)

    defang_event = lambda evt : {"start" : long(evt.start), "end" : long(evt.end), "url" : evt.entityid, "entity": _mimic_entity_schema_from_url(evt.entityid), "title": get_title_from_evt(evt)}
    hits = _get_pages_for_user(user ,from_msec,to_msec)

    print "Got a request to do it from %d to %d (got %d) " % (int(from_msec),int(to_msec),len(hits))    
    
    return json_response({ "code":200, "results": [ defang_event(evt) for evt in hits ] });

#@login_required
def get_time_per_page(request):
    if request.user is None:
          ## the person is asking us for access to another user's activity log.
        return json_response({"code":401,"message":"Access forbidden, please log in first"})
    from_msec,to_msec = _unpack_from_to_msec(request)
    times_per_url = _get_time_per_page(request.user,from_msec,to_msec)    
    return json_response({ "code":200, "results": times_per_url })
        
def get_top_pages(request,username, n):  # should have n here but i removed it temporarally 
    user = User.objects.filter(username=username)
    n = int(n)
    if request.user is None:
          ## the person is asking us for access to another user's activity log.
        return json_response({"code":401,"message":"Access forbidden, please log in first"})
    from_msec,to_msec = _unpack_from_to_msec(request)
    times_per_url = _get_time_per_page(request.user,from_msec,to_msec)
    urls_ordered = times_per_url.keys()
    urls_ordered.sort(lambda u1,u2: int(times_per_url[u2] - times_per_url[u1]))

    #_mimic_entity_schema_from_url
    return json_response({ "code":200, "results": [(u, long(times_per_url[u])) for u in urls_ordered[0:n]] }) 

    
def get_top_hosts(request,username, n):  # should have n here but i removed it temporarally 
    user = User.objects.filter(username=username)
    n = int(n)
    if request.user is None:
          ## the person is asking us for access to another user's activity log.
        return json_response({"code":401,"message":"Access forbidden, please log in first"})
    from_msec,to_msec = _unpack_from_to_msec(request)
    times_per_url = _get_time_per_page(request.user,from_msec,to_msec,grouped_by=EVENT_SELECTORS.Host)
    urls_ordered = times_per_url.keys()
    urls_ordered.sort(lambda u1,u2: int(times_per_url[u2] - times_per_url[u1]))

    print urls_ordered
    #_mimic_entity_schema_from_url
    return json_response({ "code":200, "results": [(u, long(times_per_url[u])) for u in urls_ordered[0:n]] }) 

    
def get_top_hosts_comparison(request, username, n): 
    users = User.objects.filter(username=username)
    if len(users) == 0:
        return json_response({"code":401,"message":"Unknown user %s" % username})

    user = users[0]
    n = int(n)

    first_start,first_end,second_start,second_end = _unpack_times(request)
    
    times_per_url_second = _get_top_n(user,second_start,second_end)
    # this fails for some reason
    times_per_url_first = _get_top_n(user,first_start,first_end)
    
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

    
def get_top_urls(request, n):
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

## DOESNT WORK
def get_top_users(request, n):
    user = User.objects.all();

    return 

def get_most_recent_urls(request, n):
    users = User.objects.all();
    n = int(n)
    from_msec,to_msec = _unpack_from_to_msec(request)
     

    defang_event = lambda evt : {"start" : long(evt.start), "end" : long(evt.end), "url" : evt.entityid, "entity": _mimic_entity_schema_from_url(evt.entityid), "title": get_title_from_evt(evt)}
    for user in users:
        hits = _get_pages_for_user(users[0],from_msec,to_msec) ## not sure how to do this so i set user to be the 1st user
    #print "Got a request to do it from %d to %d (got %d) " % (int(from_msec),int(to_msec),len(hits))
#    print [ evt.entitydata for evt in hits ]
    #print [ JSONDecoder().decode(JSONDecoder().decode(evt.entitydata)[0]['data'])['title'] for evt in hits if JSONDecoder().decode(JSONDecoder().decode(evt.entitydata)[0]['data']).has_key('title') ]
    return json_response({ "code":200, "results": [ defang_event(evt) for evt in hits[0:n] ] });

def get_users_most_recent_urls(request, username, n):
    users = User.objects.filter(username=username)
    if len(users) == 0:
        return json_response({"code":401,"message":"Unknown user %s" % username})
    user = users[0]    
    n = int(n)

    from_msec,to_msec = _unpack_from_to_msec(request)

    defang_event = lambda evt : {"start" : long(evt.start), "end" : long(evt.end), "url" : evt.entityid, "entity": _mimic_entity_schema_from_url(evt.entityid), "title": get_title_from_evt(evt)}
    hits = _get_pages_for_user(user,from_msec,to_msec)
    print "Got a request to do it from %d to %d (got %d) " % (int(from_msec),int(to_msec),len(hits))    

    return json_response({ "code":200, "results": [ defang_event(evt) for evt in hits[0:n] ] });

    
        


        
