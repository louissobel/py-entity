import unittest

from pyentity import Entity, SuppressField

########################################
# Test Fixtures

class RepresentMe(object):

    haha = 'hehe'

    def __init__(self):
        self.foobar = 5

    def a_method(self, arg):
        return arg

    def a_value(self):
        return 100

    @property
    def a_property(self):
        return 'PROPERTASTIC'


class AuxObject(object):

    foobar = 5
    goobar = 10


class MainEntity(Entity):
    _FIELDS_ = [
        'snow',                 # class attr of the entity
        'haha',                 # class attr of the obj
        'foobar',               # instance attr of the attr
        'ent_method',           # method of the entity
        'ent_alias_method',     # method of the entity using the alias field
        'a_value',              # method of the obj
        'a_property',           # @property of the obj
        'aux_object_method',    # method of entity accessing aux_object
    ]

    _ALIAS_ = 'wrapped'
    _AUX_OBJECTS_ = ['aux_object']

    snow = 'COLD'
    fire = 'HOT'

    def ent_method(self):
        return self._o.a_method('echo')

    def ent_alias_method(self):
        return self.wrapped.a_method('echoWRAP')

    def aux_object_method(self):
        return self.aux_object.foobar

MAIN_EXPECTED_HASH = {
    'snow' : 'COLD',
    'haha' : 'hehe',
    'foobar' : 5,
    'ent_method' : 'echo',
    'ent_alias_method' : 'echoWRAP',
    'a_value' : 100,
    'a_property' : 'PROPERTASTIC',
    'aux_object_method' : 5,
}


class ChildEntity(MainEntity):
    _FIELDS_ = [
        'snow',                 # class attr of the base entity
        'haha',                 # class attr of the obj
        'foobar',               # instance attr of the attr
        'ent_method',           # method of the base entity
        'ent_alias_method',     # method of the base entity using the alias field
        'a_value',              # method of the obj
        'a_property',           # @property of the obj

        'subent_method',        # a method of the sub-entity
        'fire',                 # an attribute of the base entity that is overwritten
    ]

    _AUX_OBJECTS_ = [] # child overrides this

    fire = 'VERY HOT'

    def subent_method(self):
        return self.wrapped.a_method('SUB')

CHILD_EXPECTED_HASH = {
    'snow' : 'COLD',
    'haha' : 'hehe',
    'foobar' : 5,
    'ent_method' : 'echo',
    'ent_alias_method' : 'echoWRAP',
    'a_value' : 100,
    'a_property' : 'PROPERTASTIC',
    'fire' : 'VERY HOT',
    'subent_method': 'SUB',
}


class SuppressingEntity(Entity):

    _FIELDS_ = ['hello', 'foobar', 'a_value']

    hello = 7

    def foobar(self):
        if self._o.foobar < 1:
            raise SuppressField
        else:
            return self._o.foobar


class MultipleAuxObjectEntity(Entity):

    _FIELDS_ = ['aux1hit', 'aux2hit', 'objhit']
    _ALIAS_ = 'obj'
    _AUX_OBJECTS_ = ['aux1', 'aux2']

    def aux1hit(self):
        return self.aux1.foobar

    def aux2hit(self):
        return self.aux2.goobar

    def objhit(self):
        return self.obj.foobar

MULTIPLE_AUX_EXPECTED_HASH = {
    'aux1hit' : 5,
    'aux2hit' : 10,
    'objhit' : 5,
}


# Some broken entities
class BrokenEntity(Entity):
    _FIELDS_ = ['haha', 'idontexist']


class ChildBrokenEntity(BrokenEntity):
    pass


class ChildFixesEntity(BrokenEntity):
    _FIELDS_ = ['haha']


class ChildBreaksEntity(MainEntity):
    _FIELDS_ = ['idontexist']
    _AUX_OBJECTS_ = []

# some corner case entities
class NonStringAliasEntity(Entity):
    _FIELDS_ = ['foobar']
    _ALIAS_ = {}


class BadIdentifierAliasEntity(Entity):
    _FIELDS_ = ['foobar']
    _ALIAS_ = '$$$ dfkj dfjds'


class EmptyFieldsEntity(Entity):
    pass


class ReservedWordFieldEntity(Entity):
    _FIELDS_ = ['_FIELDS_']


class AliasAsAFieldEntity(Entity):
    _FIELDS_ = ['hello', 'wrapped', 'foo', 'bar']
    _ALIAS_ = 'wrapped'


class DunderInFieldEntity(Entity):
    _FIELDS_ = ['hello', '__dunder__']


class BadAuxTypeEntity(Entity):
    _FIELDS_ = ['foobar']
    _AUX_OBJECTS_ = 'string'


class ReservedWordAuxEntity(Entity):
    _FIELDS_ = ['foobar']
    _AUX_OBJECTS_ = ['_AUX_OBJECTS_']


class AuxFieldCollisionEntity(Entity):
    _FIELDS_ = ['foobar', 'foo']
    _AUX_OBJECTS_ = ['foo']


class DunderInAuxObjectsEntity(Entity):
    _FIELDS_ = ['foobar']
    _AUX_OBJECTS_ = ['__dunder__']


class InvalidIdentifierAuxObjectsEntity(Entity):
    _FIELDS_ = ['foobar']
    _AUX_OBJECTS_ = ['BAD IDENTIFIER BAD IDENTIFER $#@)(  3290908 )']


class AliasAuxObjectsCollisionEntity(Entity):
    _FIELDS_ = ['foobar']
    _ALIAS_ = 'lolol'
    _AUX_OBJECTS_ = ['lolol']


########################################
# Test Cases

class BasicTestCase(unittest.TestCase):

    def runTest(self):
        obj = RepresentMe()
        aux = AuxObject()
        ent = MainEntity(obj, aux_object=aux)

        self.assertEqual(ent(), MAIN_EXPECTED_HASH)


class CuteTestCase(unittest.TestCase):

    def runTest(self):
        obj = RepresentMe()
        aux = AuxObject()
        ent = MainEntity(obj, aux_object=aux)

        a = {}
        self.assertEqual(ent>>a, MAIN_EXPECTED_HASH)
        self.assertEqual(a, MAIN_EXPECTED_HASH)


class ChildTestCase(unittest.TestCase):

    def runTest(self):
        obj = RepresentMe()
        cent = ChildEntity(obj)

        self.assertEqual(cent(), CHILD_EXPECTED_HASH)


class DirTest(unittest.TestCase):

    def runTest(self):
        obj = RepresentMe()
        aux = AuxObject()
        ent = MainEntity(obj, aux_object=aux)

        self.assertEqual(sorted(dir(ent)), sorted(MainEntity._FIELDS_))


class SuppressingTestCase(unittest.TestCase):

    def runTest(self):
        obj = RepresentMe()
        ent = SuppressingEntity(obj)

        self.assertEqual(ent(), {
            'hello' : 7,
            'foobar' : 5,
            'a_value' : 100,
        })

        obj.foobar = 0
        self.assertEqual(ent(), {
            'hello' : 7,
            'a_value' : 100,
        })


class SuppressingIterationTestCase(unittest.TestCase):

    def runTest(self):
        obj = RepresentMe()
        ent = SuppressingEntity(obj)

        self.assertEqual(list(ent), [
            ('hello', 7),
            ('foobar', 5),
            ('a_value', 100),
        ])

        obj.foobar = 0
        self.assertEqual(list(ent), [
            ('hello', 7),
            ('a_value', 100),
        ])


class MultipleAuxTestCase(unittest.TestCase):

    def runTest(self):
        obj = RepresentMe()
        aux1 = AuxObject()
        aux2 = AuxObject()
        ent = MultipleAuxObjectEntity(obj, aux1=aux1, aux2=aux2)

        self.assertEqual(ent(), MULTIPLE_AUX_EXPECTED_HASH)

class BrokenEntityTestCase(unittest.TestCase):

    def runTest(self):
        obj = RepresentMe()
        ent = BrokenEntity(obj)

        with self.assertRaisesRegexp(AttributeError, 'Cannot find') as ae:
            ent()

class BrokenChildEntityTestCase(unittest.TestCase):

    def runTest(self):
        obj = RepresentMe()
        ent = ChildBrokenEntity(obj)

        with self.assertRaisesRegexp(AttributeError, 'Cannot find') as ae:
            ent()

class ChildFixesEntityTestCase(unittest.TestCase):

    def runTest(self):
        obj = RepresentMe()
        ent = ChildFixesEntity(obj)

        # should not throw
        ent()


class ChildBreaksEntityTestCase(unittest.TestCase):

    def runTest(self):
        obj = RepresentMe()
        ent = ChildBreaksEntity(obj)

        with self.assertRaisesRegexp(AttributeError, 'Cannot find') as ae:
            ent()


class MissingAuxObjectTestCase(unittest.TestCase):

    def runTest(self):
        obj = RepresentMe()
        aux1 = AuxObject()

        with self.assertRaisesRegexp(TypeError, 'aux2'):
            MultipleAuxObjectEntity(obj, aux1=aux1)

class UnexpectedAuxObjectTestCase(unittest.TestCase):

    def runTest(self):
        obj = RepresentMe()
        aux1 = AuxObject()
        aux2 = AuxObject()
        aux3 = AuxObject()

        with self.assertRaisesRegexp(TypeError, 'aux3'):
            MultipleAuxObjectEntity(obj, aux1=aux1, aux2=aux2, aux3=aux3)

class GetAttrSimpleTestCase(unittest.TestCase):

    def runTest(self):
        obj = RepresentMe()
        aux = AuxObject()
        ent = MainEntity(obj, aux_object=aux)
        self.assertEqual(ent.snow, 'COLD')
        self.assertEqual(ent.haha, 'hehe')


class GetAttrBootstrapTestCase(unittest.TestCase):

    def runTest(self):
        obj = RepresentMe()
        aux = AuxObject()
        ent = MainEntity(obj, aux_object=aux)
        self.assertEqual(ent._ALIAS_, 'wrapped')
        self.assertEqual(ent._o, obj)


class GetAttrBadFieldTestCase(unittest.TestCase):

    def runTest(self):
        obj = RepresentMe()
        aux = AuxObject()
        ent = MainEntity(obj, aux_object=aux)

        with self.assertRaisesRegexp(AttributeError, 'no field'):
            ent.idontexist


class GetAttrAliasTestCase(unittest.TestCase):

    def runTest(self):
        obj = RepresentMe()
        aux = AuxObject()
        ent = MainEntity(obj, aux_object=aux)
        self.assertEqual(ent.wrapped, obj)


class GetAttrAuxObjectTestCase(unittest.TestCase):

    def runTest(self):
        obj = RepresentMe()
        aux = AuxObject()
        ent = MainEntity(obj, aux_object=aux)
        self.assertEqual(ent.aux_object, aux)


class GetAttrSuppressedTestCase(unittest.TestCase):

    def runTest(self):
        obj = RepresentMe()
        ent = SuppressingEntity(obj)

        self.assertEqual(ent.foobar, 5)

        obj.foobar = 0
        with self.assertRaisesRegexp(AttributeError, 'suppressed'):
            ent.foobar


class GetItemNotAFieldTestCase(unittest.TestCase):

    def runTest(self):
        ent = EmptyFieldsEntity()
        with self.assertRaisesRegexp(KeyError, 'bloop'):
            ent['bloop']


class GetItemWorkingTestCase(unittest.TestCase):

    def runTest(self):
        obj = RepresentMe()
        aux = AuxObject()
        ent = MainEntity(obj, aux_object=aux)
        self.assertEqual(ent['foobar'], 5)

# some corner case tests
class NonStringAliasTestCase(unittest.TestCase):

    def runTest(self):
        with self.assertRaisesRegexp(ValueError, 'basestring'):
            NonStringAliasEntity()


class BadIdentifierAliasTestCase(unittest.TestCase):

    def runTest(self):
        with self.assertRaisesRegexp(ValueError, 'legal identifier'):
            BadIdentifierAliasEntity()


class EmptyFieldsTestCase(unittest.TestCase):

    def runTest(self):
        ent = EmptyFieldsEntity()
        self.assertEqual(ent(), {})


class ReservedWordFieldTestCase(unittest.TestCase):

    def runTest(self):
        with self.assertRaisesRegexp(ValueError, 'reserved attribute'):
            ReservedWordFieldEntity()


class AliasAsAFieldTestCase(unittest.TestCase):

    def runTest(self):
        with self.assertRaisesRegexp(ValueError, 'between'):
            AliasAsAFieldEntity()


class DunderInFieldTestCase(unittest.TestCase):

    def runTest(self):
        with self.assertRaisesRegexp(ValueError, 'double underscore'):
            DunderInFieldEntity()


class BadAuxTypeTestCase(unittest.TestCase):

    def runTest(self):
        with self.assertRaisesRegexp(ValueError, 'list'):
            BadAuxTypeEntity()


class ReservedWordAuxTextCase(unittest.TestCase):

    def runTest(self):
        with self.assertRaisesRegexp(ValueError, 'reserved attribute'):
            ReservedWordAuxEntity()


class AuxFieldCollisionTestCase(unittest.TestCase):

    def runTest(self):
        with self.assertRaisesRegexp(ValueError, 'Collision'):
            AuxFieldCollisionEntity()


class DunderInAuxObjectsTestCase(unittest.TestCase):

    def runTest(self):
        with self.assertRaisesRegexp(ValueError, 'double underscore'):
            DunderInAuxObjectsEntity()


class InvalidIdentifierAuxObjectsTestCase(unittest.TestCase):

    def runTest(self):
        with self.assertRaisesRegexp(ValueError, 'legal identifier'):
            InvalidIdentifierAuxObjectsEntity()


class AliasAuxObjectsCollisionTestCase(unittest.TestCase):

    def runTest(self):
        with self.assertRaisesRegexp(ValueError, 'Collision'):
            AliasAuxObjectsCollisionEntity()

class CuteWrongArgTypeTestCase(unittest.TestCase):

    def runTest(self):
        ent = EmptyFieldsEntity()
        with self.assertRaisesRegexp(ValueError, 'right hand side being empty dict'):
            ent>>"not a string"


class CuteNotEmptyDictionaryTestCase(unittest.TestCase):

    def runTest(self):
        ent = EmptyFieldsEntity()
        with self.assertRaisesRegexp(ValueError, 'right hand side being empty dict'):
            ent>>{'im a' : 'non-empty dictionary'}

if __name__ == "__main__":
    unittest.main()
