import re,sys,time,operator,os, datetime
from django.template import loader, Context
from django.http import HttpResponse,HttpResponseRedirect, HttpResponseForbidden
from django.shortcuts import render_to_response
from django.http import Http404
from django.shortcuts import get_object_or_404, get_list_or_404
from django.conf.urls.defaults import *
from django.contrib.auth import logout
import django.contrib.auth.models as authmodels
from django.contrib.auth.decorators import login_required
from django.template import RequestContext
from django.db.models import Q
from eyebrowse.forms import *
from eyebrowse.models import *
from cStringIO import StringIO
from PIL import Image
import jv3.utils
Image.init() # populates PIL fileformats
from django.core.files.uploadedfile import SimpleUploadedFile
from os.path import splitext
from django.db.models.signals import post_save
from jv3.models import Event ## from listit, ya.
from django.utils.simplejson import JSONEncoder, JSONDecoder
from django.contrib.auth import authenticate, login
from jv3.utils import json_response

# zamiang browser
def zamiang_browser(request):
    t = loader.get_template("zamiang.html")
    c = Context({ 'username': request.user.username, 'id': request.user.id, 'request_user': request.user.username })
    return HttpResponse(t.render(c))

def _create_enduser_for_user(user, request):
    enduser = EndUser()
    enduser.user = user
    enduser.save()
    privacysettings = PrivacySettings()
    privacysettings.user = user
    privacysettings.save()

    username = request.POST['username']
    password = request.POST['password1']
    user = authenticate(username=username, password=password)
    if user is not None:
        if user.is_active:
            login(request, user)
            return
            # Redirect to a success page.
        else:
            # Return a 'disabled account' error message
            print "fail"
            pass
    else:
        # Return an 'invalid login' error message.
        print "fail more"
        pass


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
        return render_to_response('settings.html', variables)
               
    variables = RequestContext(request, {
        'form': form,
        'request_user': request.user
        })

    return render_to_response('settings.html', variables )


def _privacy_save(request, form):
    username = request.user.username
    user = get_object_or_404(User, username=username)
    privacysettings = user.privacysettings_set.all()[0] ## ?

    privacysettings.listmode = form.cleaned_data['listmode']
    privacysettings.exposure = form.cleaned_data['exposure']
    privacysettings.save()
    return user


def userprivacy(request):
    t = loader.get_template("user_privacy.html")
    c = Context({ 'username': request.user.username })

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
            _create_enduser_for_user(user, request)
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
    t = loader.get_template("ticker.html")
    c = Context({ 'username': request.user.username, 'id': request.user.id, 'request_user': request.user.username })
    return HttpResponse(t.render(c))

def pulse(request):
    t = loader.get_template("pulse.html")
    c = Context({ 'username': request.user.username, 'id': request.user.id, 'request_user': request.user.username })
    return HttpResponse(t.render(c))

def localviz(request):
    t = loader.get_template("localviz.html")
    c = Context({ 'username': request.user.username, 'id': request.user.id, 'request_user': request.user.username })
    return HttpResponse(t.render(c))

def addfeeds(request):
    t = loader.get_template("addfeeds.html")
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
    return render_to_response('page_stats.html', variables)

## OLD
def friends(request, username):
    user = get_object_or_404(User, username=username)
    enduser = get_enduser_for_user(user)

    following = [friendship.to_friend for friendship in user.friend_set.all()]
    followers = [friendship.from_friend for friendship in user.to_friend_set.all()]

    request_user = request.user.username

    variables = RequestContext(request, {
        'username': username,
        'show_edit': username == request.user.username,
        'following': following,
        'followers': followers,
        'request_user': request_user
        })
    return render_to_response('friends_page.html', variables)

def daybyday(request, username):
    request_user = request.user.username

    variables = RequestContext(request, {
        'username': username,
        'request_user': request_user
        })
    return render_to_response('daybyday.html', variables)

def users(request):    
    user = ""
    username = ""

    if request.user.username:
        user = get_object_or_404(User, username=request.user.username)
        username = request.user.username

    if not 'letter' in request.GET:
        letter = 'a'
    else:
        letter = request.GET['letter'].strip()

    friends_results = []
    friends = EndUser.objects.all()
  
    for friend in friends:
        if request.user.username:
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
                "letter": friend.user.username[0].lower(), 
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
        'request_user': username,
        'letter': letter,
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

def plugin_iframe(request):
    request_user = request.user.username

    t = loader.get_template("iframe.html")
    c = Context({ 'request_user': request_user })

    return HttpResponse(t.render(c))

def new_tab(request):
    request_user = request.user.username

    t = loader.get_template("newtab.html")
    c = Context({ 'request_user': request_user })

    return HttpResponse(t.render(c))


def register_page(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            un = form.cleaned_data['username']
            pw = form.cleaned_data['password1']
            user = User.objects.create_user(
                username=un,
                password=pw,
                email=form.cleaned_data['email']
                )
            _create_enduser_for_user(user, request)
            return HttpResponseRedirect('/register/success/')            
    else:
        form = RegistrationForm()
    variables = RequestContext(request, {'form': form})
    return render_to_response('registration/register.html', variables)


def register_success_page(request):
    form = LoginForm()
    if request.method == 'POST':
        user = authenticate(username=request.POST['username'], password=request.POST['password'])
        if user is not None:
            if user.is_active:
                login(request, user)
                # success
                return HttpResponseRedirect('/')
            else:
                # disabled account
                variables = RequestContext(request, {'form': form, 'error': True})
                return render_to_response('login.html', variables)

    variables = RequestContext(request, {
            'form': form,
            'username': request.user.username, 
            'request_user': request.user.username,
            })
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
            THUMBNAIL_SIZE = (160, 160)
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

def add_groups(request):
    username = request.user.username
    user = get_object_or_404(User, username=username)
    enduser = get_enduser_for_user(user)
    if request.POST.has_key('groups'):    
        groups = request.POST['groups'].split()
        #print groups

        for group in groups:
            if re.search(r'^(/w|/W|[^<>+?$%{}&])+$', group):
                tag, dummy = UserTag.objects.get_or_create(name=group)
                enduser.tags.add(tag) 

        enduser.save()
        result = ' '.join(
            tag.name for tag in enduser.tags.all()
            )

        return json_response({ "code":200, "results": result }) 
    return json_response({ "code":501 }) 

def friends_page(request, username):
    user = get_object_or_404(User, username=username)
    enduser = get_enduser_for_user(user)

    following = [friendship.to_friend for friendship in user.friend_set.all()]
    followers = [friendship.from_friend for friendship in user.to_friend_set.all()]

    friends = enduser.friends.all()
    friends_results = []
    for friend in friends:
        friends_results.append( {"username": friend.user.username, "number": Event.objects.filter(owner=friend.user,type="www-viewed").count()} )
    friends_results.sort(key=lambda x: -x["number"])

    variables = RequestContext(request, {
        'username': username,
        'following': following,
        'followers': followers,
        'friends': friends,
        'show_user': True,
        'username': enduser.user.username,
        'request_user': request.user
        })
    return render_to_response('friends.html', variables)

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


# SEARCH
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

