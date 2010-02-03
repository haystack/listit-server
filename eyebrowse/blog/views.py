import re
from django.template import loader, Context
from django.http import HttpResponse
from eyebrowse.models import BlogPost
from django.conf.urls.defaults import *


MONTH_NAMES = ('', 'January', 'Feburary', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December')



def blog(request):
    posts = BlogPost.objects.all()

    t = loader.get_template("blog.html")
    c = Context({ 'posts': posts, 'request_user': request.user.username})

    return HttpResponse(t.render(c))


def singlepost(request, year, month, slug2):
    posts, pagedata = init()
    post = posts.get(date_created__year=year,
                     date_created__month=int(month),
                     slug=slug2,)
    t = loader.get_template("singlepost.html")
    c = Context({ 'post': post, 'request_user': request.user.username })
    return HttpResponse(t.render(c))


def create_archive_data(posts):
    archive_data = []
    count = {}
    mcount = {}
    for post in posts:
        year = post.date_created.year
        month = post.date_created.month
        if year not in count:
            count[year] = 1
            mcount[year] = {}
        else:
            count[year] += 1
        if month not in mcount[year]:
                mcount[year][month] = 1
        else:
            mcount[year][month] += 1
    for year in sorted(count.iterkeys(), reverse=True):
        archive_data.append({'isyear': True,
                             'year': year,
                             'count': count[year],})
        for month in sorted(mcount[year].iterkeys(), reverse=True):
            archive_data.append({'isyear': False,
                                 'yearmonth': '%d/%02d' % (year, month),
                                 'monthname': MONTH_NAMES[month],
                                 'count': mcount[year][month],})
    return archive_data


def init():
    posts = BlogPost.objects.all()
    tag_data = create_tag_data(posts)
    archive_data = create_archive_data(posts)
    pagedata = {'version': '0.0.5',
                'BlogPost': posts,
                'tag_counts': tag_data,
                'archive_counts': archive_data,}
    return posts, pagedata

def create_tag_data(posts):
    tag_data = []
    count = {}
    for post in posts:
        tags = re.split(" ", post.tags)
        for tag in tags:
            if tag not in count:
                count[tag] = 1
            else:
                count[tag] += 1
        for tag, count in sorted(count.iteritems(), key=lambda(k, v): (v, k), reverse=True):
            tag_data.append({'tag': tag,
                             'count': count,})
        return tag_data



