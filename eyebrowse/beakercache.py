from beaker.cache import CacheManager
from beaker.util import parse_cache_config_options

cache_opts = {
    'cache.type': 'file',
    'cache.data_dir': 'cache/data',
    'cache.lock_dir': 'cache/lock',
    'cache.regions': 'short_term, long_term',
    'cache.short_term.type': 'ext:memcached',
    'cache.short_term.url': '127.0.0.1.1121',
    'cache.short_term.expire': '1200',
    'cache.long_term.type': 'file',
    'cache.long_term.expire': '86400',
    }

cache = CacheManager(**parse_cache_config_options(cache_opts))
