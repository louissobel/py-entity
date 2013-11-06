import re

DUNDER_MANGLE_RE = re.compile(r'__\w+?__|_Entity__\w+')
BOOTSTRAP_ATTRS = ('_ALIAS_', '_FIELDS_', '_o')

class Entity(dict):

    # list of fields to present
    _FIELDS_ = None
    _ALIAS_ = None

    def __init__(self, o=None):

        self._o = o

        # store this to save calls to __getattribute__
        klass = self.__class__

        # copy this down
        _ALIAS_ = klass._ALIAS_
        if _ALIAS_: # TODO check if it is a string?
            setattr(self, _ALIAS_, o)
        self._ALIAS_ = _ALIAS_

        # copy this down
        _FIELDS_ = klass._FIELDS_
        if _FIELDS_ is None:
            _FIELDS_ = []
        _FIELDS_ = tuple(_FIELDS_)

        for field in _FIELDS_:
            # Set it to None so that
            # PyObject_GetIter called on this dictionary
            # will list all the keys
            # we'll set the real value later using getitem

            # assert there's no collisions
            if field in BOOTSTRAP_ATTRS:
                raise ValueError("Collision in %s with reserved attribute name %s" % (
                    klass.__name__,
                    field,
                ))

            self[field] = None
        self._FIELDS_ = _FIELDS_

    def __getattr_from_class(self, klass, attr):
        try:
            # look it up this class
            value = klass.__dict__[attr]
        except KeyError:
            pass
        else:
            if callable(value):
                return lambda : value(self)
            else:
                return value

        # here if not in klass
        # im also willing to look it up in base
        # class that is an Entity! (recursion YAY)
        for base_klass in klass.__bases__:
            if issubclass(base_klass, Entity) and not base_klass is Entity:
                try:
                    return self.__getattr_from_class(base_klass, attr)
                except AttributeError:
                    pass

        raise AttributeError

    def __getitem__(self, attr):
        return getattr(self, attr)

    def __getattribute__(self, attr):
        # dunders and mangled get sent through
        if DUNDER_MANGLE_RE.match(attr):
            return object.__getattribute__(self, attr)

        # save these to avoid calls to __getattribute__
        # have to be above the dunder handling!
        __dict__ = self.__dict__
        klass = self.__class__

        # bootstrap
        if attr in BOOTSTRAP_ATTRS:
            return __dict__[attr]

        # load as local to save a recursive call to __getattribute__
        _ALIAS_, _FIELDS_, _o = [__dict__[a] for a in BOOTSTRAP_ATTRS]

        if _ALIAS_:
            if attr == _ALIAS_:
                return _o

        if not attr in _FIELDS_:
            raise AttributeError('Entity %s has no field %s' % (
                klass.__name__,
                attr,
            ))

        # Get the field!
        try:
            # try to get it from this klass or any Entity base classes
            value = self.__getattr_from_class(klass, attr)
        except AttributeError:
            # fine. try to proxy it then
            try:
                value = getattr(_o, attr)
            except AttributeError:
                raise AttributeError("Cannot find a value for attribute %r in %s" % (
                    attr,
                    klass.__name__,
                ))

        if callable(value):
            return value()
        else:
            return value

    def __dir__(self):
        return list(self._FIELDS_)

    def __iter__(self):
        return iter(self._FIELDS_)

    def __call__(self):
        return dict((k, self[k]) for k in self)

    def __rshift__(self, other):
        errstr = "Can only use >> entity shortcut with right hand side being {}"
        if not isinstance(other, dict):
            raise ValueError(errstr)
        if other:
            raise ValueError(errstr)

        return self()
