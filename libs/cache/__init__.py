import hashlib
import pickle

# local dependencies
from .version import __version__


class Cache:
    """
    Creates a cache decorator factory.

        cache = Cache(a_cache_client)

    Positional Arguments:
    backend    This is a cache backend that must have "set" and "get"
               methods defined on it.  This would typically be an
               instance of, for example, `pylibmc.Client`.

    Keyword Arguments:
    enabled    If `False`, the backend cache will not be used at all,
               and your functions will be run as-is, even when you call
               `.cached()`.  This is useful for development, when the
               function may be changing rapidly.
               Default: True

    bust       If `True`, the values in the backend cache will be
               ignored, and new data will be calculated and written
               over the old values.
               Default: False

    """

    def __init__(self, backend=None, **default_options):
        self.backend = backend or LocalCache()
        self.default_options = default_options

    def __call__(self, key=None, **kw):
        """
        Returns the decorator itself
            @cache("mykey", ...)
            def expensive_method():
                # ...

            # or in the absence of decorators

            expensive_method = cache("mykey", ...)(expensive_method)

        Positional Arguments:

        key    (string) The key to set

        Keyword Arguments:

        The decorator takes the same keyword arguments as the Cache
        constructor.  Options passed to this method supercede options
        passed to the constructor.

        """

        opts = self.default_options.copy()
        opts.update(kw)

        def _cache(fn):
            k = key or '<cache>/%s' % fn.__name__
            return CacheWrapper(self.backend, k, fn, **opts)

        return _cache


class CacheWrapper:
    """
    The result of using the cache decorator is an instance of
    CacheWrapper.

    Methods:

    get       (aliased as __call__) Get the value from the cache,
              recomputing and caching if necessary.

    cached    Get the cached value.  In case the value is not cached,
              you may pass a `default` keyword argument which will be
              used instead.  If no default is present, a `KeyError` will
              be thrown.

    refresh   Re-calculate and re-cache the value, regardless of the
              contents of the backend cache.
    """

    def __init__(self, backend, key, calculate,
                 bust=False, enabled=True, default='__absent__', **kw):
        self.backend = backend
        self.key = key
        self.calculate = calculate
        self.default = default

        self.bust = bust
        self.enabled = enabled

        self.options = kw

    def _has_default(self):
        return self.default != '__absent__'

    def _get_cached(self, *a, **kw):
        if not self.enabled:
            return self.calculate(*a, **kw)

        key = _prepare_key(self.key, *a, **kw)
        cached = self.backend.get(key)

        if cached is None:
            raise KeyError

        return _unprepare_value(cached)

    def cached(self, *a, **kw):
        try:
            return self._get_cached(*a, **kw)
        except KeyError as e:
            if self._has_default():
                return self.default
            else:
                raise e

    def refresh(self, *a, **kw):
        fresh = self.calculate(*a, **kw)
        if self.enabled:
            key = _prepare_key(self.key, *a, **kw)
            value = _prepare_value(fresh)
            self.backend.set(key, value, **self.options)

        return fresh

    def get(self, *a, **kw):
        if self.bust:
            return self.refresh(*a, **kw)

        try:
            return self._get_cached(*a, **kw)
        except KeyError:
            return self.refresh(*a, **kw)

    def __call__(self, *a, **kw):
        return self.get(*a, **kw)

_CACHE_NONE = '___CACHE_NONE___'


def _prepare_value(value):
    if value is None:
        return _CACHE_NONE

    return value


def _unprepare_value(prepared):
    if prepared == _CACHE_NONE:
        return None

    return prepared


def _prepare_key(key, *args, **kwargs):
    """
    if arguments are given, adds a hash of the args to the key.
    """

    if not args and not kwargs:
        return key

    items = kwargs.items()
    items.sort()
    hashable_args = (args, tuple(items))
    args_key = hashlib.md5(pickle.dumps(hashable_args)).hexdigest()

    return "%s/args:%s" % (key, args_key)


class LocalCache:
    def __init__(self):
        self._cache = {}

    def set(self, key, val, **kw):
        self._cache[key] = val

    def get(self, key):
        return self._cache.get(key)


class NullCache:
    def set(self, key, val, **kw):
        pass

    def get(self, key):
        return None
