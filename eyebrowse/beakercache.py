from beaker.cache import CacheManager
from beaker.util import parse_cache_config_options

CACHE_EXPIRY = '10800' ## for debug
CACHE_EXPIRY_ST = '10800' ## 3 hours
CACHE_EXPIRY_LT = '86400' ## 1 day
CACHE_EXPIRY_VLT = '604800' ## 1 week
#CACHE_EXPIRY_ST = '3600' ## 3 hours
#CACHE_EXPIRY_LT = '43200' ## 12 hours

cache_opts = {
    'cache.type': 'file',

    #'cache.data_dir': '/Users/brennanmoore/listit-server/server/cache/data',
    #'cache.lock_dir': '/Users/brennanmoore/listit-server/server/cache/lock',
    'cache.data_dir': '/biggie/eyebrowse/workspace/trunk/server/eyebrowse/cache/data',
    'cache.lock_dir': '/biggie/eyebrowse/workspace/trunk/server/eyebrowse/cache/lock',

    'cache.regions': 'short_term, long_term, to_from_url, top_users_long_term',
    'cache.short_term.type': 'file',
    # comment above line and uncomment 2 below lines to use memcached
    #'cache.short_term.type': 'ext:memcached', 
    #'cache.short_term.url': '127.0.0.1.1121', 
    'cache.short_term.expire': CACHE_EXPIRY_ST,
    'cache.long_term.type': 'file',
    'cache.long_term.expire': CACHE_EXPIRY_LT,
    'cache.to_from_url.type': 'file',
    'cache.to_from_url.expire': CACHE_EXPIRY_VLT,
    'cache.top_users_long_term.type': 'file',
    'cache.top_users_long_term.expire': CACHE_EXPIRY_LT
    }

cache = CacheManager(**parse_cache_config_options(cache_opts))
