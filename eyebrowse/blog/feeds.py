from django.contrib.syndication.feeds import Feed
from eyebrowse.models import BlogPost
from django.contrib.syndication.feeds import Feed
from django.utils.feedgenerator import Atom1Feed

class RssFeed(Feed):
        title = "Eyebrowse Blog"
        link = "eyebrowse.csail.mit.edu/blog/"
        description = "updates"
        item_link = link

	def items(self):
                return BlogPost.objects.order_by('-date_created')[:10]

class AtomFeed(RssFeed):
        feed_type = Atom1Feed
	subtitle = RssFeed.description
