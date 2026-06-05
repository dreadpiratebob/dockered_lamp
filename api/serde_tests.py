from util.infrastructure.http import serialize_by_field_to_json, serialize_by_field_to_xml

class SimpleTest:
  def __init__(self, name:str, some_data:int, is_good:bool):
    self.name = name
    self.some_data = some_data
    self.is_good = is_good
  
  def __eq__(self, other:any) -> bool:
    return isinstance(other, SimpleTest) \
      and self.name == other.name \
      and self.some_data == other.some_data \
      and self.is_good == other.is_good
  
  def __ne__(self, other:any) -> bool:
    return not (self == other)
  
  def __hash__(self) -> int:
    return hash((self.name, self.some_data, self.is_good))
  
  def __repr__(self) -> str:
    return 'SimpleTest(%s)' % str(self)
  
  def __str__(self) -> str:
    return '%s (%s is good ? %s)' % (self.name, self.some_data, self.is_good)

def test_json():
  name = 'thing'
  some_data = 0
  is_good = True
  thing = SimpleTest(name, some_data, is_good)
  
  expected = '{"name": "%s", "some_data": %s, "is_good": %s}' % (name, some_data, is_good)
  actual = serialize_by_field_to_json(thing)
  
  if expected != actual:
    print('json failure:')
    print('expected: ', expected)
    print('  actual: ', actual)

def test_xml():
  name = 'thing'
  some_data = 0
  is_good = True
  thing = SimpleTest(name, some_data, is_good)
  
  expected = '<name>%s</name><some_data>%s</some_data><is_good>%s</is_good>' % (name, some_data, is_good)
  actual = serialize_by_field_to_xml(thing)
  
  if expected != actual:
    print('xml failure:')
    print('expected: ', expected)
    print('  actual: ', actual)



test_json()
print('')
test_xml()