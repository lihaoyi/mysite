import struct
import functools
import base64
import json
import cPickle
import hashlib
import marshal
import zlib
import random
from datetime import datetime
import Image
import ImageOps
import StringIO
import urllib2
#import memcache
import os

class Lib:
   @staticmethod
   def logTo(msg, file):
      f = open(file, 'a');
      f.write(str(datetime.now()) + "\t" + str(msg) + "\n");
      
def log(msg):
   Lib.logTo(msg, 'log.txt');

def schedlog(msg):
   Lib.logTo(msg, 'schedlog.txt');
   
   

tasks = {}   
def scheduled(minute=None, hour=None, day=None):
   def wrap(func):
      tasks[func] = (minute, hour, day)
      return func    
   return wrap

class t(dict):
   def __getattr__(self, n):
      try:  return self[n]
      except KeyError: raise AttributeError("Named tuple has no such member: " + str(n))
   
   def __setattr__(self, n, v):
      self[n] = v
      
   def __init__(self,**kwargs):
      self.update(kwargs)
      
   def __call__(self, **kwargs):
      a = self.__class__(**self)
      a.update(kwargs)
      return a
   def __hash__(self):
      return hash(frozenset(self.items()))

class XUtils:
   @staticmethod
   def randB64ID():
      r = random.getrandbits
      return base64.b64encode(struct.pack("HHH", r(16), r(16), r(16)), "-_")
      
   @staticmethod
   def hash(thing):
      return hex(hash(cPickle.dumps(thing, 2)))
   
   @staticmethod
   def weakHash(thing):
      return hex(hash(str(thing)))
   
   
   @staticmethod     
   def encode(thing):
      return base64.b64encode(zlib.compress(json.dumps(thing)))
      
   @staticmethod     
   def decode(thing):
      return json.loads(zlib.decompress(base64.b64decode(thing)))

def watch(checker):
   def watcher(meta, *args, **kwargs):
      file = checker(*args, **kwargs)
      return watchFile(meta, file, *args, **kwargs)
   return watcher
   
def watchFile(meta, file, *args, **kwargs):
   
   latest = os.stat(file).st_mtime
   if meta != None and meta == latest:
      return False, meta
   else:
      return True, latest

class CacheMissError(Exception):
   def __init__(self, value):
      self.args = (value,)
   def __repr__(self):
      return self.args
      
class cache(object):
   def __init__(self, invalidator=None):
      self.invalidator = invalidator or (lambda *args, **kwargs: (False, False))
      
   def __call__(self, func):
      @functools.wraps(func)
      def wrapper(*args, **kwargs):
         
         key = XUtils.hash(str(func.__name__)) + XUtils.hash(args) + XUtils.hash(kwargs)
         meta = XLoad.load("meta" + key)
         newmeta = None
         value = None
         try:
            result, newmeta = self.invalidator(meta, *args, **kwargs)
            if result: 
               raise CacheMissError("invalidated")
            value = XLoad.load(key)
            if value == None: 
               raise CacheMissError("no value in cache for " + str(key) + " " + str(args)+ " " + XUtils.hash(args))
         except CacheMissError, e:
            
            value = func(*args, **kwargs)
            
            XLoad.save(key, value)
            
         if newmeta != meta:
            XLoad.save("meta" + key, newmeta)
         return value
      return wrapper

class XImage:
   @staticmethod
   def prepSizedImage(source, width, height):
      
      hash = XUtils.hash((source.encode(), width, height))
      bucket = "media/temp/" + hash 
      basename = os.path.basename(source)
      if os.path.splitext(basename)[1] == "":
         basename = basename + ".png"
      newSource = bucket + "/" + basename
     
     
      if not os.path.exists(newSource) or (not source.startswith("http") and os.stat(source).st_mtime > os.stat(newSource).st_mtime):
         
         try:
            os.makedirs(bucket)
         except OSError:
            if os.path.isdir(bucket): pass
            else: raise
            
         image = None

         if source.startswith("http"): 
            image = Image.open(StringIO.StringIO(urllib2.urlopen(source).read())) 
         else: 
            image = Image.open(source)
            
         baseWidth, baseHeight = image.size
         if height or width:
            if not height: height = width * baseHeight / baseWidth
            if not width: width = height * baseWidth / baseHeight
            if width != baseWidth and height != baseHeight:
               image = image.convert("RGBA")
               image = ImageOps.fit(image, (width, height), Image.ANTIALIAS, 0, (0.5, 0.5))
         else:
            width, height = image.size        
         image.save(newSource)

      source = newSource      
      return source
      
      

class XLoad:
   lm = {}
   #mc = memcache.Client(['127.0.0.1:11211'], debug=0)
   @staticmethod
   def save(key, value):
      
      key = base64.b64encode(key)
      XLoad.lm[key] = (value)
      #XLoad.mc.set(key, value)
   
   @staticmethod
   def load(key):
      key = base64.b64encode(key)
      try: return (XLoad.lm[key])
      except: pass# return XLoad.mc.get(key)
         
   
   @staticmethod
   @cache(watchFile)
   def loadRaw(source):
      return open(source).read() 
   