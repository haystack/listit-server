from beaker.cache import CacheManager
from beaker.util import parse_cache_config_options

CACHE_EXPIRY = '3600' ## for debug
CACHE_EXPIRY_ST = '3600' ## 3 hours
CACHE_EXPIRY_LT = '43200' ## 12 hours
#CACHE_EXPIRY_ST = '3600' ## 3 hours
#CACHE_EXPIRY_LT = '43200' ## 12 hours

cache_opts = {
    'cache.type': 'file',
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
    'cache.to_from_url.expire': CACHE_EXPIRY_LT,
    'cache.top_users_long_term.type': 'file',
    'cache.top_users_long_term.expire': CACHE_EXPIRY_LT
    }

cache = CacheManager(**parse_cache_config_options(cache_opts))
