from beaker.cache import CacheManager
from beaker.util import parse_cache_config_options

cache_opts = {
    'cache.type': 'file',
    'cache.data_dir': 'cache/data',
    'cache.lock_dir': 'cache/lock',
    'cache.regions': 'short_term, long_term, to_from_url, top_users_long_term',
    'cache.short_term.type': 'file',
    # comment above line and uncomment 2 below lines to use memcached
    #'cache.short_term.type': 'ext:memcached', 
    #'cache.short_term.url': '127.0.0.1.1121', 
    'cache.short_term.expire': '7200', # 6 hours
    'cache.long_term.type': 'file',
    'cache.long_term.expire': '43200', # 12 hours '86400', 1 day
    'cache.to_from_url.type': 'file',
    'cache.to_from_url.expire': '43299', # 12 hours '86400', 1 day
    'cache.top_users_long_term.type': 'file',
    'cache.top_users_long_term.expire': '43200', # 12 hours '86400', 1 day
    }

cache = CacheManager(**parse_cache_config_options(cache_opts))
