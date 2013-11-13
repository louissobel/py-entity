py-entity
========

Basic Python Entities
----------------------

An entity is useful for preparing models for an API or view.

Allows view or API UI specific logic to be removed from models.

### Example

We have some object..

```python
class GeorgeWashington(object):
    id = 1776
    first_name = 'George'
    last_name = 'Washington'
    phone_number = '(202) 456-1111'
    phone_number_private = True
    email = 'prez1@whouse.gov'
    accomplishments = ['president', 'general', 'quarter model', 'woodworking']
    birthday = datetime.datetime(1732, 2, 22, 0, 0)
```

Converting this object to json would take a bit of work. We need to write
some kind of `to_dictionary` method, or a custom encoder. There will stil
probably be an issue with the `datetime` (not JSON-encodable) as well as
the fact that we want to conditionally include the `phone_number`, as long
as `phone_number_private` is not `True`.

Using an `Entity`:

```python
class UserEntity(pyentity.Entity):
    _FIELDS_ = [
        'id',
        'name',
        'phone_number',
        'email',
        'accomplishments',
        'birthday',
    ]
    _ALIAS_ = 'user'

    def name(self):
        return "%s %s" % (self.user.first_name, self.user.last_name)

    def birthday(self):
        return self.user.birthday.isoformat()

    def phone_number(self):
        if self.user.phone_number_private:
            raise pyentity.SuppressField
        return self.user.phone_number
```

Then,

```python
george_entity = UserEntity(GeorgeWashington())
print json.dumps(george_entity(), indent=2)
```

```javascript
{
  "email": "prez1@whouse.gov", 
  "accomplishments": [
    "president", 
    "general", 
    "quarter model", 
    "woodworking"
  ], 
  "id": 1776, 
  "birthday": "1732-02-22T00:00:00", 
  "name": "George Washington"
}
```

Somtimes, we want to have different views over the same data. One may be a detailed
description of an object, but some other may just be a summary. Entity inheritance helps here.

```python
class SummaryEntity(UserEntity):
    _FIELDS_ = ['name', 'email']
```

Then,

```python
summary_entity = SummaryEntity(GeorgeWashington())
print json.dumps(summary_entity(), indent=2)
```

```javascript
{
  "name": "George Washington", 
  "email": "prez1@whouse.gov"
}
```