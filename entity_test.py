import unittest
import json

import entity


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


class MainEntity(entity.Entity):
    _FIELDS_ = [
        'snow',                 # class attr of the entity
        'haha',                 # class attr of the obj
        'foobar',               # instance attr of the attr
        'ent_method',           # method of the entity
        'ent_alias_method',     # method of the entity using the alias field
        'a_value',              # method of the obj
        'a_property',           # @property of the obj
    ]

    _ALIAS_ = 'wrapped'

    snow = 'COLD'
    fire = 'HOT'

    def ent_method(self):
        return self._o.a_method('echo')

    def ent_alias_method(self):
        return self.wrapped.a_method('echoWRAP')

MAIN_EXPECTED_HASH = {
    'snow' : 'COLD',
    'haha' : 'hehe',
    'foobar' : 5,
    'ent_method' : 'echo',
    'ent_alias_method' : 'echoWRAP',
    'a_value' : 100,
    'a_property' : 'PROPERTASTIC',
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


class SuppressingEntity(entity.Entity):

    _FIELDS_ = ['foobar']

    def foobar(self):
        if self._o.foobar < 1:
            raise entity.SuppressField
        else:
            return self._o.foobar


class BasicTestCase(unittest.TestCase):

    def runTest(self):
        obj = RepresentMe()
        ent = MainEntity(obj)

        self.assertEqual(ent(), MAIN_EXPECTED_HASH)


class CuteTestCase(unittest.TestCase):

    def runTest(self):
        obj = RepresentMe()
        ent = MainEntity(obj)

        self.assertEqual(ent>>{}, MAIN_EXPECTED_HASH)


class JSONTestCase(unittest.TestCase):

    def runTest(self):
        obj = RepresentMe()
        ent = MainEntity(obj)

        res = json.loads(json.dumps(ent()))
        self.assertEqual(res, MAIN_EXPECTED_HASH)


class ChildTestCase(unittest.TestCase):

    def runTest(self):
        obj = RepresentMe()
        cent = ChildEntity(obj)

        self.assertEqual(cent(), CHILD_EXPECTED_HASH)


class DirTest(unittest.TestCase):

    def runTest(self):
        obj = RepresentMe()
        ent = MainEntity(obj)

        self.assertEqual(sorted(dir(ent)), sorted(MainEntity._FIELDS_))


class SuppressingTestCase(unittest.TestCase):

    def runTest(self):
        obj = RepresentMe()
        ent = SuppressingEntity(obj)

        self.assertEqual(ent(), {'foobar' : 5})

        obj.foobar = 0
        self.assertEqual(ent(), {})


class SuppressingIterationTestCase(unittest.TestCase):

    def runTest(self):
        obj = RepresentMe()
        ent = SuppressingEntity(obj)

        self.assertEqual(list(ent), [('foobar', 5)])

        obj.foobar = 0
        self.assertEqual(list(ent), [])


if __name__ == "__main__":
    unittest.main()
