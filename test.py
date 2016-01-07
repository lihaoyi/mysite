class Object(object):
   def __get__(self, owner, objtype):
      return 
      
   def __getattr__(self, name):
      return functools.partial(getattr(self.page, "template def: " + name), self.page)

class Thing(object):
   object = Object()
   
myThing = Thing()
setattr(myThing, 'mo o', lambda self: self)

print myThing