import datetime
import json
import pyentity

# Some object, looks like..
class GeorgeWashington(object):
    id = 1776
    first_name = 'George'
    last_name = 'Washington'
    phone_number = '(202) 456-1111'
    phone_number_private = True
    email = 'prez1@whouse.gov'
    accomplishments = ['president', 'general', 'quarter model', 'woodworking']
    birthday = datetime.datetime(1732, 2, 22, 0, 0)

# An entity...
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

# Then..
george_entity = UserEntity(GeorgeWashington())
print json.dumps(george_entity(), indent=2)
# {
#   "email": "prez1@whouse.gov", 
#   "accomplishments": [
#     "president", 
#     "general", 
#     "quarter model", 
#     "woodworking"
#   ], 
#   "id": 1776, 
#   "birthday": "1732-02-22T00:00:00", 
#   "name": "George Washington"
# }

# Notice that the phone_number field has been suppressed


# Entities can inherit from others...
class SummaryEntity(UserEntity):
    _FIELDS_ = ['name', 'email']

summary_entity = SummaryEntity(GeorgeWashington())
print json.dumps(summary_entity(), indent=2)
# {
#   "name": "George Washington", 
#   "email": "prez1@whouse.gov"
# }