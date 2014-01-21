import re
import keyword

DUNDER_MANGLE_RE = re.compile(r'__\w+?__|_Entity__\w+')
IDENTIFIER_RE = re.compile(r'^[_a-zA-Z]\w*$')
BOOTSTRAP_ATTRS = ('_ALIAS_', '_FIELDS_', '_o', '_AUX_OBJECTS_')

def is_legal_identifier(ident):
    """
    Checks if a given string is a legal identifer
    """
    return IDENTIFIER_RE.match(ident) and not keyword.iskeyword(ident)

class SuppressField(Exception):
    pass

class Entity(object):

    # list of fields to present
    _FIELDS_ = None

    # alias for the wrapped object `_o`
    _ALIAS_ = None

    # list of required aux objects
    _AUX_OBJECTS_ = None

    def __init__(self, obj=None, **kwargs):

        # store this to save calls to __getattribute__
        klass = self.__class__

        # copy this down
        _ALIAS_ = klass._ALIAS_

        if _ALIAS_ is not None:
            if not isinstance(_ALIAS_, basestring):
                raise ValueError('_ALIAS_ %r must be a basestring' % _ALIAS_)
            if not is_legal_identifier(_ALIAS_):
                raise ValueError('_ALIAS_ %r must be a legal identifier' % _ALIAS_)

            setattr(self, _ALIAS_, obj)

        # copy this down
        _FIELDS_ = klass._FIELDS_
        if _FIELDS_ is None:
            _FIELDS_ = []
        _FIELDS_ = tuple(_FIELDS_)

        for field in _FIELDS_:
            # assert there's no collisions
            if field in BOOTSTRAP_ATTRS:
                raise ValueError("Collision in %s with reserved attribute name %s" % (
                    klass.__name__,
                    field,
                ))

            if _ALIAS_ and field == _ALIAS_:
                raise ValueError("Collication in %s between alias %s and fields" % (
                    klass.__name__,
                    _ALIAS_,
                ))

            if field.startswith('__'):
                raise ValueError("Fields cannot begin with double underscore")

        # copy this down
        _AUX_OBJECTS_ = klass._AUX_OBJECTS_
        if _AUX_OBJECTS_ is None:
            _AUX_OBJECTS_ = []

        if not isinstance(_AUX_OBJECTS_, list):
            raise ValueError("_AUX_OBJECTS_ must be a list")

        for aux_object_name in _AUX_OBJECTS_:
            # make sure
            # - not reserved
            # - doesn't collide with _FIELDS_
            # - doesn't collid with _ALIAS_
            if aux_object_name in BOOTSTRAP_ATTRS:
                raise ValueError("Collision in %s with reserved attribute name %s and aux object" % (
                    klass.__name__,
                    aux_object_name,
                ))

            if aux_object_name in _FIELDS_:
                raise ValueError("Collision in %s between field %s and aux object" % (
                    klass.__name__,
                    aux_object_name,
                ))

            if _ALIAS_ and aux_object_name == _ALIAS_:
                raise ValueError("Collision in %s between alias %s and aux object" % (
                    klass.__name__,
                    aux_object_name,
                ))

            if aux_object_name.startswith('__'):
                raise ValueError("aux object cannot begin with double underscore")

            if not is_legal_identifier(aux_object_name):
                raise ValueError("aux object %s is not a legal identifier" % aux_object_name)

        _AUX_OBJECTS_ = set(_AUX_OBJECTS_)
        aux_dict = {}
        received_aux_objects = set()

        for k, v in kwargs.items():
            if k in _AUX_OBJECTS_:
                aux_dict[k] = v
            else:
                raise TypeError("Unexpected aux object: %s" % k)

            received_aux_objects.add(k)

        missing = _AUX_OBJECTS_ - received_aux_objects
        if missing:
            raise TypeError("Missing aux object: %s" % missing.pop())

        # store these away
        self._o = obj
        self._ALIAS_ = _ALIAS_
        self._FIELDS_ = _FIELDS_

        self._AUX_OBJECTS_ = aux_dict

    def __reset_inner(self):
        """
        Clears out the inner dictionary, then fills it
        by calling __resolve_attr on all the fields in _FIELDS_

        If SuppressField is thrown for any field, that field is not
        added to the dictionary
        """
        new_inner = {}
        for field in self._FIELDS_:
            try:
                value = self.__resolve_attr(field)
            except SuppressField:
                pass
            else:
                new_inner[field] = value

        self.__inner = new_inner

    def __resolve_attr(self, attr):
        """
        Resolves an Attribute
         - if it is __dunder__, call object.__getattribute__
         - if it is __Mangled_method, call object.__getattribute__
         - if it a bootstrap attribute (_FIELDS_, _ALIAS_, _o, _AUX_OBJECTS_), return it from __dict__
         - if _ALIAS_ is set and the attribute is that alias, return the _o wrapped object
         - if the attribute is in _AUX_OBJECTS_, return it

         - assert that it is a valid Field (in _FIELDS_)
         - recursively check this and base classes for its presence using __getattr_from_class
         - try and proxy it the _o wrapped object
         - if a callable, call it

        Throws an AttributeError if ultimately unable to find it
        Can also throw a SuppressField exception if we want to suppress that field
        """
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
        _ALIAS_, _FIELDS_, _o, _AUX_OBJECTS_ = [__dict__[a] for a in BOOTSTRAP_ATTRS]

        if _ALIAS_:
            if attr == _ALIAS_:
                return _o

        if attr in _AUX_OBJECTS_:
            return _AUX_OBJECTS_[attr]

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

    def __getattr_from_class(self, klass, attr):
        """
        Check for attr in the __dict__ of klass
        If found,
            if it's a callable, bind self to it and return it (bootleg bound method)
            otherwise just return it

        Otherwise, call this method recursively on any Entity-subclasses that
        are a baseclass of klass.

        Will raise AttributeError if unable to find attr anywhere.
        """
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
        """
        If attr is in _FIELDS_, will pass it to getattr
        Otherwise raised KeyError
        """
        # Only allow __getitem__ for unsuppressed fields
        if not attr in self._FIELDS_:
            raise KeyError(attr)
        else:
            return getattr(self, attr)

    def __getattribute__(self, attr):
        """
        Calls __resolve_attr, turning a SuppressField exception into an AttributeError
        """
        try:
            # Have to go the the Class here to avoid infinite recursion
            return Entity.__resolve_attr(self, attr)
        except SuppressField:
            raise AttributeError("Field %s is suppressed in %s" % (
                attr,
                self.__class__.__name__,
            ))

    def __dir__(self):
        return list(self._FIELDS_)

    def __call__(self):
        # iter calls __iter__
        return dict(iter(self))

    def __rshift__(self, other):
        errstr = "Can only use >> entity shortcut with right hand side being empty dict"
        if not isinstance(other, dict):
            raise ValueError(errstr)
        if other:
            raise ValueError(errstr)

        other.update(self())
        return other

    def __iter__(self):
        """
        Yields field, value pairs
        for non-supressed fields in order of _FIELDS_
        """
        self.__reset_inner()

        # Cache this locally
        __inner = self.__inner
        for field in self._FIELDS_:
            if field in __inner:
                yield (field, __inner[field])
