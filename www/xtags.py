import re
import types 
import copy
import os
import inspect
import functools
import traceback
from collections import defaultdict
import cProfile
import json
import itertools
import time

from library import *

# Controller
# include()
# XCompiler
# Attr
# XTag
#   StringTag
#   BaseTag
#   ContFlowTag
#     ForTag
#     IfTag
#     ElseTag
#       ElforTag
#       ElifTag    
#   DefTag
#   JumpTag
#     TemplateTag
#     enclosedTag   
#     ControllerTag


class Ajax:

   @staticmethod  
   def ajaxify(func):      
      def ajaxed(request, *args, **kwargs): 
         try:
            starttime = time.time()
            tree = func(request, *args, **kwargs) 
            
            Ajax.fill(tree[0])
            HTML = tree[0].html[0]
            newMeta = Ajax.strip(tree[0])[0]
            if 'ajax' in request.POST:
               
               oldMeta = request.POST['ajax']
               oldMeta = XUtils.decode(oldMeta)
               deltas = []
               Ajax.recurse(newMeta, oldMeta, deltas, "")
               newMeta = XUtils.encode(Ajax.strip2(newMeta))
               
               response = json.dumps(t(delta = deltas, skeleton=newMeta))
               return response
            else:
               HTML= "<!DOCTYPE html>" + HTML
               

               newMeta = XUtils.encode(Ajax.strip2(newMeta))
               HTML += "<input type=\"hidden\" value=\""+newMeta +"\" id=\"skeleton\"/>"
               response = HTML
               return response
         except BaseException, e:
             if not hasattr(e, "xtagTrace"): e.xtagTrace = []
             return "<pre>" + "".join(traceback.format_exc()) + "\n".join(e.xtagTrace) + "</pre>"
             #raise
      
         
      def wrap(request, *args, **kwargs):
         tree = [];
         cProfile.runctx("tree.append(ajaxed(request, *args, **kwargs))", {}, t(ajaxed=ajaxed, request=request, args=args, kwargs=kwargs, tree=tree), "profile.txt")
         return tree[0]
      # import pstats; pstats.Stats('profile.txt').strip_dirs().sort_stats('time').print_stats(10)
      return ajaxed
      
   @staticmethod
   def recurse(newNode, oldNode, delta, indicies):
      
      oldNode = t(**oldNode)
      
      newNode = t(**newNode)
      
      if oldNode.partHash == newNode.partHash:
         newChildren = [child for child in newNode.children if type(child) is t]
         for i in xrange(len(newChildren)):
            new, old = newChildren[i], oldNode.children[i]
            Ajax.recurse(new, old, delta, indicies + "-" + str(i))
      else:
         
         
         delta.append(t(markers=t(start='s' + newNode.id, end='e' + newNode.id), html=newNode.html[0]))
         
         
   @staticmethod
   def fill(node, plain=False, id=""):
      s = []
      i = 0
      for child in node.children:
         if type(child) is str:
            s += [child]
         else:
            Ajax.fill(child, id=id+"-"+str(i))
            s += [child.html[0]]
            i += 1
      if node.ajax: s = ["<script class='s"+id+"'></script>"] + s + ["<script class='e"+id+"'></script>"]
      node.id = id
      s = "".join(s)
      node.html[0] = s
   
   
   @staticmethod
   def strip2(node):
      return node(html = None, 
                  children = [Ajax.strip2(child) 
                  for child in node.children])
      
   
   @staticmethod
   def partHash(node):
      if "partHash" in node:
         return node.partHash
      else:
         part = [  token 
                     if type(token) is str else 
                        Ajax.partHash(token) 
                     if type(token) is t and not token.ajax else
                        None
                     for token in node.children]
         
         node.partHash = hash(str(part))
                           
         return node.partHash                                    
                                 
   @staticmethod
   def strip(node):
      children = [token 
                  for child in node.children 
                  if type(child) is t
                  for token in Ajax.strip(child)]
      partHash = Ajax.partHash(node)
      if node.ajax:
         return ([t(name = node.name,
                  argHash = node.argHash,
                  html = node.html,
                  id = node.id,
                  children = children,
                  ajax=node.ajax,
                  partHash = partHash)]
                )
      else:
         return children

class Controller(object):
   def __init__(self, func, pure=0, ajax=0, name=None, args=None, type='jump', extra={}):
      self.func = func
      
      self.pure = pure
      self.ajax = ajax
      self.type = type
      self.name = name if name != None else func.__name__ 
      self.args = args if args else inspect.getargspec(func).args
      self.extra = extra
      self.sourceClass = None
      
   def prepare(self, *args, **kwargs):
         
      enclosedStack = kwargs['enclosed'] if 'enclosed' in kwargs else self.owner.enclosedStack()
      if 'enclosed' in kwargs: del kwargs['enclosed']
      
      argHash = XUtils.hash((self.owner.__class__, self.name, kwargs, dict(enclosedStack)))
      
      return t(cls=self.owner.__class__, 
               sourceClass=self.sourceClass,
               result=None,
               name=self.name,
               type=self.type, 
               args=kwargs,
               enclosedStack=enclosedStack,
               argHash=argHash,
               data=self.owner.data,
               pure=self.pure,
               ajax=self.ajax,
               html=[""],
               children=None,
               cached=None)
   
   @staticmethod
   def consolidate(stub):
      output = [""]
      for i, part in enumerate(stub.children):
         if type(part) is t:
            output.append(part)
            output.append("")
         elif type(part) is str:
            output[-1] += (part)
      stub.children = output
      #output.append("".join(input[start:-1]))
      return stub
            
            
   @staticmethod
   def pureRecurse(stub):
      if stub.result:
         return stub
      else:
 
         stub.result = [(Controller.pureRecurse(child) if type(child) is t and child.pure else 
                        (child(children=None, result=None) if type(child) is t and not child.pure else child)) 
                        for child in stub.children] 
                   
         
         return stub
      
   @staticmethod
   def run(stub):
      try:
         newPage = stub.cls()
         newPage.data, newPage.enclosedStack = stub.data, stub.enclosedStack
         cacheID = str((stub.cls, stub.argHash)) if stub.pure else 0;
         result = XLoad.load(cacheID) if stub.pure else None
         if not result:
            children = getattr(newPage, stub.name).func(newPage, **stub.args)
            stub = Controller.consolidate(stub(children = children))
            if stub.pure:
               Controller.pureRecurse(stub)
               XLoad.save(cacheID, stub.result)
         else:
            stub = Controller.descend(stub(result=result), newPage)
            
         
         return [stub]
      except BaseException, e:
         if not hasattr(e, "xtagTrace"): e.xtagTrace = []
         e.xtagTrace += [str(stub.sourceClass.__name__) + ": " + str(stub.name) + " " + 
                        ((stub.enclosedStack.origin.source + " " + str(stub.enclosedStack.origin.lines)) 
                        if stub.enclosedStack.origin else "")]
         raise
       
   
   @staticmethod
   def descend(part, newPage):
      if type(part) is t:
         if part.result != None:
            return part(children = [Controller.descend(child, newPage) for child in part.result])
         else:
            return Controller.run(part(data=newPage.data, cls=newPage.__class__))[0] 
      else:
         return part

   def __call__(self, *args, **kwargs):   
      return Controller.run(self.prepare(self, *args, **kwargs))
   
   def __get__(self, owner, objtype):
      self.owner = owner
      return self
      
def controller(*args, **kwargs):
   def converter(func):
      return Controller(func, *args, **kwargs)
   return converter
   
# Base class for all controllers to inherit from. Includes the permanent,
# non over-rideable property "template", which when used as in Base.template.main()
# calls the template definition <def main~> and retrieves its output.

class Object(object):
   def __get__(self, owner, objtype):
      return Object(owner, self.get)
      
   def __init__(self, owner=None, get=None):
      object.__setattr__(self, "owner", owner)
      object.__setattr__(self, "get", get)
      
   def __getattr__(self, name):
      try:   
         return self.get(object.__getattribute__(self, "owner"), name)
      except:
         raise Exception("Access Failed, no such item: " + str(name))
   
   def __setattr__(self, name, value):
      
      owner = object.__getattribute__(self, "owner")
      data[owner][name] = value
      
class XPage(object):
   
   template = Object(get=lambda owner, name: getattr(owner, "template def: " + name))
   
   def __init__(self, request=None, parent=None):
      self.request = request
      if parent:
         self.data = parent.data()
         self.enclosedStack = parent.enclosedStack()
      else:
         self.data = t()
         self.enclosedStack = t(origin=t(), attrs={}, classes=[])
   
   def handle(post):
      for key, value in post.items():
         pass
   
   def __call__(self, **kwargs):
      for key, value in kwargs.items():
         self.data[key] = value
      return self
         
   @controller(type='render', pure=1)
   def render(self, source, **varContext):
      template = XCompiler.loadXTag(source)
      
      return template.toHTML(self, varContext)

   def enclosedData(self):
      
      return self.enclosedStack.origin
      
   @controller(type='enclosed', ajax=0, pure=1, args=[])
   def enclosed(self, source, index, lines, context):
      enclosed = XLoad.load("enclosedDict" + source)[index].printChildren(self, context)
      if not enclosed:
         XCompiler.loadXTag(source)
         enclosed = XLoad.load("enclosedDict" + source)[index].printChildren(self, context)
      return enclosed
      
      
   def set(self, **kwargs):
      for key, value in kwargs.items():
         data[self][key] = value
      return self

   # Decorator for all controllers to use; shorthand for linking template
   # files to the controller
   @staticmethod
   def xinclude(*sources):

      def wrap(cls):
         
         
         for source in sources:
            if type(source) is not str:
               cls.__bases__ = (source,) + cls.__bases__
               continue
            else:
               cls.include(source)
               
         for i in dir(cls):
            if type(getattr(cls, i)) is Controller and getattr(cls, i).sourceClass == None:
               getattr(cls, i).sourceClass = cls
               
         return cls
         
      return wrap
      
   
      
   @staticmethod
   def makeCallback(defTag):
      # callback to run each def 
      #return [t(cls=cls, getFunc=getFunc(), name=name, args=args, enclosed=enclosed)]
      @controller(name="template def: " + defTag.name, pure=1, ajax=defTag.ajax, args=defTag.attrs)
      def callback(self, **varContext): 
         varContext = varContext.copy() ;
         
         for name, attr in defTag.attrs.items():
            if name in varContext:
               pass 
            elif attr != None:
               varContext[name] = eval(attr, varContext.copy()) 
            else:
               raise StandardError("Missing Non-Optional Argument: definition of <" + defTag.name + "~> missing argument: "+name)

         return defTag.toHTML(self, varContext)
      
      return callback

   # performs the heavy lifting of loading a template file, parsing it's DOM tree
   # and adding the defined tags from the template into the controller's namespace
   # as callable methods, together with argument-checking and error-catching
   @classmethod
   def include(cls, source):
      template = XCompiler.loadXTag(source)

      # picks out all the <def> tags in the base namespace of the template
      # and creates a function that calls each one, sticking that function
      # into the controller's name space
      for child in template.children:
         if type(child) is DefTag:
            setattr(cls, "template def: " + child.name, XPage.makeCallback(child))
      
      
      #sourcefunc = lambda cls: getattr(cls, 'controller: enclosedStack')[-1][0].source + str(getattr(cls, 'controller: enclosedStack')[-1][0].line)
      #return [t(enclosedTag=True)]

      setattr(cls, "template def: " + "classes", 
         lambda s: s.enclosedStack.classes[:])
      
      setattr(cls, "template def: " + "attrs", 
         lambda s: s.enclosedStack.attrs)
      

# XCompileriler that performs much of the heavy duty parsing and houses
# utility functions used throughout the code
class XCompiler:
  # tags which are not converted into classes
   nativeTags = [ 'a', 'div', 'span', 'img', 'p', 'br',
                  'ol', 'ul', 'li', 'dl', 'dt', 'dd', 
                  'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
                  'table', 'tr', 'th', 'td', 
                  'link', 'script', 'pre', 'code', 
                  'form', 'input', 'option', 'textarea',
                  'html', 'head', 'title', 'body',
                  'fb:login-button', 'iframe']
                  
   def __init__(self):
      self.lines = 0, 0
   
   # Keeps self.line up to date by seeing how many newlines are in the
   # currently processing token
   def updateLines(self, token):
      self.lines = self.lines[1], self.lines[1] + token.count("\n")
      
   
   def doTag(self, text, current, source):
      shortMatch = re.search("<[a-z:/].*? ", text, re.DOTALL)
      contFlow = shortMatch == '<for' or shortMatch == '<if'
      tagRegex = "<[a-z:/].*?>" 
      
      match = re.search(tagRegex, text, re.DOTALL)
      self.updateLines(text[:match.end()])
      token = match.group()
      # cut off triangle brackets
      tokenContents = token[1:-1]
      self.updateLines(tokenContents)

      # self-closing combo tag; removes the self-closing
      # marker and marks the tag to be closed after it is
      # processed
      selfClosing = False
      if tokenContents[-1] == "/":
         tokenContents = tokenContents[:-1]
         selfClosing = True
      
      # close-open combo tag
      # processed before other tags. Closes the current
      # tag and continues processsing the new tag defined
      # by the string after the colon
      if tokenContents[0] == ':': 
         current = current.parent
         tokenContents = tokenContents[1:]
         
      tag, remainder = (tokenContents + " ").split(" ", 1)
        
      # consider tag type
      if tag[0] == '/': # closing tag
         if tag[1:] != current.nominalTag: raise StandardError("Unclosed Tag: <" + tag + "> cannot close <" + current.nominalTag + ">")
         current = current.parent
      elif tag == 'for':      current = ForTag(current, tag, remainder)
      elif tag == 'if':       current = IfTag(current, tag, remainder)
      elif tag == 'elif':     current = ElifTag(current, tag, remainder)
      elif tag == 'elfor':    current = ElforTag(current, tag, remainder)
      elif tag == 'else':     current = ElseTag(current, tag)
      elif tag == 'def':      current = DefTag(current, tag, remainder)
      elif tag == "enclosed~":current = EnclosedTag(current, tag, remainder)
      elif tag == 'render':   current = RenderTag(current, tag, remainder)
      elif tag[-1] == "~":    current = TemplateTag(current, tag, remainder)
      elif tag[-1] == "*":    current = ControllerTag(current, tag, remainder)
      else:                   current = HTMLTag(current, tag, remainder)
      
      current.lines = self.lines
      current.source = source
      # back out of any self-closing tags
      if selfClosing:
         current = current.parent
      
      return current, match.end()
      
   def findMatch(self, index, text):
      totalBrackets = 0
      for i in xrange(index, len(text)):
         char = text[i]
         if char == '{':
            totalBrackets += 1
         if char == '}':
            totalBrackets -= 1
         if totalBrackets == 0:  
            return i

            
   def doRaw(self, text, current, source):
      index = text.index('{')
      endIndex = self.findMatch(index, text)
      
      rawText = text[index+1:endIndex]  
      
      self.updateLines(text[:endIndex])
      stringNode = StringTag(current, rawText, True, self.lines, source)  
      return current, endIndex+1
   
   def doText(self, text, current, source):
      match = re.search(r"`.*?`", text, re.DOTALL)
      forcedText = match.group()[1:-1]
      self.updateLines(match.group())
      stringNode = StringTag(current, forcedText, False, self.lines, source)
      return current, match.end()
      
   def parse(self, text, source):
      try:
         self.lines =  1, 1

         tagStart = "<[a-z:/]"
         textStart = '`'
         rawStart = '{'
         
         # create and start from base
         base = BaseTag()
         current = base

         while True:
         #   textMatch = re.search(textStart, text)
        #    textMatch = textMatch.start() if textMatch else 1000000
            matches = [ (re.search(rawStart, text), self.doRaw),
                        (re.search(tagStart, text), self.doTag),
                        (re.search(textStart, text), self.doText) ] 
            
            matches.sort(key=lambda a: a[0].start() if a[0] else 10000000)
            match = matches[0]
            if not match[0]:
               break
            
            StringTag(current, text[:match[0].start()], False, self.lines, source)
            current, index = match[1](text, current, source)
           
            text = text[index:]
         return base   
      except StandardError, e:  
         # Error occured while compiling Template; append template
         # line numbers onto exception and re-raise
         e.args = (e.args[0], "Parsing " + str(source) + " Lines " +  str(self.lines))
         raise 
         
 
   enclosedDict = {}
   @staticmethod
   @cache(watchFile)
   def loadXTag(source):
      value = XLoad.loadRaw(source)
      value = XCompiler().parse(value, source)
      if not XLoad.load("enclosedDict" + source):
         XLoad.save("enclosedDict" + source, XCompiler.enclosedRecurse(value))
      
      return value
      
   @staticmethod
   def enclosedRecurse(node, list=[]):
      if type(node) is str: return
      if type(node) in [JumpTag, TemplateTag, ControllerTag, RenderTag]:
         node.enclosedIndex = len(list)
         list += [node]
      for child in node.children:
         XCompiler.enclosedRecurse(child, list)
      return list
      
      
# class used to keep track of a tag's attributes. stores
# the name and value of the attribute, and whether or not
# the value is raw or a variable. spits out the value itself
# if raw or grabs the value of the variable from context 
# otherwise
class Attr(object):
   # __slots__ = ("name", "value", "string")
   styleAttrs={
      't' : 'top',    'b' : 'bottom',
      'l' : 'left',   'r' : 'right',
      'h' : 'height', 'w' : 'width',
      'ml': 'margin-left', 'mr': 'margin-right',
      'mt': 'margin-top',  'mb': 'margin-bottom',
      'c' : 'background-color',
      'p' : 'position'
   }
   
   def __init__(self, name, value, string=True):
      self.name = name
      self.value = value
      self.string = string
      
   # reads the blah="blahh" string and takes the appropiate response,
   # either adding the attribute normally or (in the case of styleAttrs)
   # appending onto an existing one
   @staticmethod
   def make(token):
      token = token.split("=", 1)
      name = token[0].strip()
      value = token[1].strip()
      if value[0] == value[-1] == "'" or value[0] == value[-1] == '"':
         value = XString(value[1:-1], raw=True)
         string = True
      elif value[0] == value[-1] == "~":
         value = value[1:-1]
         string = False
      else:
         raise Exception("malformed attribute: must be either quoted or tildad")
      return Attr(name, value, string)
    
   # evaluates the contents of this Attr and converts 
   # it into a string
   def fullEval(self, varContext):
      return XString.escapeHTML(str(self.partEval(varContext)))

   # evaluates the contents of this Attr and leaves it
   # as a python variable; used to pass variables into
   # TemplateTags
   def partEval(self, varContext):
      
      if(self.string):
         # evaluates into a String, with python variables inserted
         return self.value.toString(varContext.copy())
      else:
         # evaluates into a Python variable
         return eval(self.value, varContext.copy())
         
   def __repr__(self):
      return "Attr(name: " + self.name + ", value=" + self.value + ", raw="+str(self.raw)+")" 
   # grabs the attributes out of the token; checking for double quotes,
   # single quotes and tildas. Processes the found strings into a list of Attr
   # objects to return
   @staticmethod
   def matchAttr(token):

      token = " " + token
      attrRegex1 = " +?[^ ]+? *= *~.*?~"
      attrRegex2 = " +?[^ ]+? *= *\".*?\""
      attrRegex3 = " +?[^ ]+? *= *'.*?'"
      attrTokens = re.findall(attrRegex1, token, re.DOTALL)

      remainder = re.sub(attrRegex1, "", token)
      attrTokens += re.findall(attrRegex2, remainder, re.DOTALL)

      remainder = re.sub(attrRegex2, "", remainder)
      attrTokens += re.findall(attrRegex3, remainder, re.DOTALL)
      remainder = re.sub(attrRegex3, "", remainder)

      attrs = {}
      for attrToken in attrTokens:
         attr = Attr.make(attrToken)
         attrs[attr.name] = attr
         
      return attrs, remainder
      

# base class for all Nodes in the "DOM" tree, including
# control flow statements, def/calls and raw strings. 
class XTag(object):
   # __slots__ = ("parent", "children", "nominalTag", "line", "prev", "next", "source")
   def __init__(self, parent, tag):
      #print "Init " + tag
      self.parent = parent
      self.children = []
      self.nominalTag = tag    
      self.lines = None
      
      # add this to parents child-list and sibling-linked-list
      if parent != None:
        if len(parent.children) > 0:
           parent.children[-1].next = self
           self.prev = parent.children[-1]
        parent.children.append(self)

   # goes on top of the toHTML() function of all sub classes. does 
   # basic preprocessing and can print debug statements
   def toHTMLHeader(self, controller, varContext):
      pass
   
   # prints out all this nodes children; used in all the sub classes'
   # toHTML() functions
   def printChildren(self, controller, varContext):
      s = []
      for child in self.children: 
         s += child.toHTML(controller, varContext)
      return s
   
   # recursively creates the HTML from the DOM tree
   def toHTML(self, controller, varContext):
      raise Exception("Function Not Defined: toHTML()") 
      
      
# Node representing a single HTML DOM object.L
class HTMLTag(XTag):
   # __slots__ = ("attrs", "classes", "includeClasses", "includeAttrs", "tag")
   def __init__(self, parent, tag, remainder):
      XTag.__init__(self, parent, tag) 
      # get attrs
      self.attrs, remainder = Attr.matchAttr(remainder)
      
      # get everything else as classes, including starting tag
      classes = remainder.split(" ") + [tag]
      classes = [c for c in classes if c.strip() != ""]
      # default to using div
      self.tag = 'div'
      
      # setup for including classes from enclosedStack
      self.includeClasses = False
      self.includeAttrs = False
      
      self.classes = []
      for c in classes:
         # but choose new tag if found in classes; use nativeTags
         # to set the Tag rather than the Classes
         if c in XCompiler.nativeTags:
            self.tag = c
         elif c == 'classes': # if class "classes" found, include classes from enclosedStack
            self.includeClasses = True
         elif c == 'attrs': # if class "classes" found, include classes from enclosedStack
            self.includeAttrs = True
         else:
            self.classes += [c]

   def toHTML(self, controller, varContext):
      self.toHTMLHeader(controller, varContext)
      # starts opening\ tag
      prefix = "<" + self.tag 

      # add all attributes  
      prefix += self.printAttrs(controller, varContext) + ">"
          
      # prepare content
      s = self.printChildren(controller, varContext)
      # prepare closing tag
      suffix = "</"+self.tag+">"

      return [prefix] + s + [suffix]
   
   # Takes all the attributes of a HTMLTag and converts it into
   # a string that can be added to the opening tag; performs 
   # and reshuffling within the attributes (i.e. for styles)
   def printAttrs(self, controller, varContext):
              
      finalAttrs = defaultdict(str)
      
      if self.includeClasses:
         finalAttrs['class'] += " ".join(controller.template.classes())
         
      finalAttrs['class'] += "".join(" " +  x for x in self.classes)
      
      if finalAttrs['class'] == "": del finalAttrs['class']
      
      if self.includeAttrs:
         for key, value in controller.template.attrs().items():
            if key in Attr.styleAttrs.keys():
               finalAttrs['style'] += Attr.styleAttrs[key] + ": " + value + "; "
            else:
               finalAttrs[key] += value
               
      for name, attr in self.attrs.items():
         if attr.name in Attr.styleAttrs.keys():
            finalAttrs['style'] += Attr.styleAttrs[attr.name] + ": "+attr.fullEval(varContext)+"; "
         else:
            finalValue = attr.fullEval(varContext)
            if finalValue != "" :
               finalAttrs[attr.name] += finalValue 
      return "".join(" " + name + "=\"" + attrString + "\"" for name, attrString in finalAttrs.items())    
 

class XString(object):
   subs = {
         '\\~':'~',
         '\\`':'`',
         '\\\\':'\\'
      }
   regex = r'(\\~)|(\\")|(\\\\)'
   # __slots__ = ("raw", "nodes")
   def __init__(self, text, raw):
      
      self.raw = raw
      self.nodes = re.split(r"(?<![\\])~", text)
      for i, node in enumerate(self.nodes):
         self.nodes[i] = re.sub(XString.regex, lambda m: XString.subs[m.group()], self.nodes[i])
         if i % 2 == 0 and not self.raw:
            self.nodes[i] = XString.escapeHTML(self.nodes[i])
      
      if not self.raw and len(self.nodes) == 1 and self.nodes[0].strip() == "":
         self.nodes[0] = ""
   def toString(self, varContext):
      if len(self.nodes) == 1:
         return self.nodes[0]
         
      string = []
      i = 0
      for i, node in enumerate(self.nodes):
         if i % 2 == 0:
            string.append(node)
         else:
            s = str(eval(node, varContext.copy()))
            if not self.raw: s = XString.escapeHTML(s)
            string.append(s)
      return "".join(string)
   
   
      
   @staticmethod
   def escapeHTML(text, raw=False):
      subs = {'&': '&amp;',
                     '"': '&quot;',
                     "'": '&apos;',
                     '>': '&gt;',
                     '<': '&lt;'}
      pattern = "(&)|(\")|(')|(>)|(<)"
      
      if raw:
         return text
      else:
         return re.sub(pattern, lambda c: subs[c.group()], text)
# node just meant to keep track of naked Strings
class StringTag(XTag):
   # __slots__ = ("value", "raw")
   def __init__(self, parent, value, raw, lines, source):
      XTag.__init__(self, parent, 'str')
      self.value = XString(value, raw)
      self.raw = raw
      self.lines = lines
      self.source = source
   
   def toHTML(self, controller, varContext): #HTML of a raw string is just that string
      self.toHTMLHeader(controller, varContext)
      return [self.value.toString(varContext)]

# Root node of the DOM tree; prevents having to maintain a forest
# and is generally a lightweight container which outputs no HTML
class BaseTag(XTag): 
   def __init__(self):
      XTag.__init__(self, None, 'base')
      self.name = 'base'
      
   def toHTML(self, controller, varContext):
      self.toHTMLHeader(controller, varContext)
      s = self.printChildren(controller, varContext)
      return s


# superclass of for, if, else, elif, etc. tags, with common
# functionality
class ContFlowTag(XTag):
   # Prints the child nodes once for each context returned by 
   # results(). 
   def toHTML(self, controller, varContext):
      self.toHTMLHeader(controller, varContext)
      
      if not self.elseFires(varContext): return []
      
      results = self.results(varContext)
      if results == None: return []
      
      
      s = []
      for context in results:
         s = s + self.printChildren(controller, context)
      return s
               
   # Returns a set of contexts to execute the child nodes in.
   # If the if/for/elif/elfor is executed and fails, it returns
   # an empty list []. If an elif/elfor is not executed in the
   # first place, it returns None, so subsequent elif/elfors 
   # know not to run. Otherwise it returns a non-empty list
   # of contexts
   def results(self, varContext):
      raise Exception("Function Not Defined: results()") 
      
   def elseFires(self, varContext):
      return True

      
# Node representing a foreach loop. for example:
# <for x, y, z in EXPRESSION>
# </for>
class ForTag(ContFlowTag):
   # __slots__ = ("variables", "expression")
   def __init__(self, parent, tag, remainder):
      ContFlowTag.__init__(self, parent, 'for')

      pieces = remainder.split(" in ", 1)
      if len(pieces) != 2:   
         raise StandardError("<"+self.nominalTag+"> tag needs ' in ' keyword")
      if pieces[0].strip() == "":
         raise StandardError("<"+self.nominalTag+"> tag: iterator variables before 'in' cannot be blank")
      if pieces[1].strip() == "":
         raise StandardError("<"+self.nominalTag+"> tag: expression after 'in' cannot be blank")   
      self.variables = [v.strip() for v in pieces[0].split(",")]
      self.expression = pieces[1]
      
   # Returns a list of contexts, one for each time the for loop
   # runs with the loop-variables included. If the loop does not
   # run, returns []
   def results(self, varContext):
      forlist = eval(self.expression, varContext.copy())
      contexts = []
      for item in forlist:
         newContext = varContext.copy()
         for i in xrange(len(self.variables)):
            newContext[self.variables[i]] = item[i] if len(self.variables) > 1 else item
         contexts += [newContext]
      return contexts
      

# node representing an if statement. Prints its children if 
# EXPRESSION evaluates to true, otherwise prints nothing
# <if EXPRESSION>
# </if>
class IfTag(ContFlowTag):
   # __slots__ = ()
   def __init__(self, parent, tag, remainder):
      ContFlowTag.__init__(self, parent, 'if')
      self.expression = remainder
      if remainder.strip() == "": 
         raise StandardError("<if> tag cannot be empty!")

   # returns a list with only the parent context if the expression
   # is true, otherwise returns []
   def results(self, varContext):
      return [varContext.copy()] if eval(self.expression, varContext.copy()) else []


# else tag; has to follow a if/for/elif/elfor, and prints
# its children if the previous tag is executed but produces
# no output
# <if>
# <:else>
# </else>
class ElseTag(ContFlowTag):
   # __slots__ = ()
   # Returns the parent context if the previous statement fails,
   # otherwise returns []
   def results(self, varContext):
      return [varContext] if self.elseFires(varContext) else []

   # Returns whether this else statement should fire: It should
   # fire if the previous statement was executed and it failed
   def elseFires(self, varContext):
      if not issubclass(type(self.prev), ContFlowTag):
         raise StandardError("<" + self.nominalTag + "> tag must follow for/if/elif/elfor, not " + self.prev.nominalTag)
      prevResults = self.prev.results(varContext)
      return prevResults != None  and len(prevResults) == 0


# elif node; to be placed after a for loop or if statement,
# and triggers if the previous statement is not executed
# (for loop is empty or the if statement is false)
class ElifTag(IfTag, ElseTag):
   # __slots__ = ()
   pass


# elfor node; also to be placed after a for loop or if statement,
# but runs a loop if the previous statement is not executed
class ElforTag(ForTag, ElseTag):  
   # __slots__ = ()
   pass


# tag that defines a new tag type that can be called later. This
# can only be used in the global scope, and causes the definition
# to be added to the attached Controller. The definitions are 
# then global
class DefTag(XTag):
   # __slots__ = ("attrs", "name", "ajax")
   def __init__(self, parent, tag, remainder):
      XTag.__init__(self, parent, 'def')
      
      # first two tokens are the "def" and "tag~"; remaining
      # tags are all attributes.  
      attrRegex = "~.*?~"
      attrTokens = re.findall(attrRegex, remainder, re.DOTALL) 
      remainder = re.sub(attrRegex, "", remainder)
      self.attrs = {}
      for attrToken in attrTokens:
         attrToken = attrToken[1:-1].split("=")
         self.attrs[attrToken[0]] = attrToken[1] if len(attrToken) > 1 else None
         
      parts = remainder.split(" ");
      self.name = parts[0]
      
      self.ajax = 1 if 'ajax' in parts else 0
      self.enclosed = 1 if 'enclosed' in parts else 0
      
   def toHTML(self, controller, varContext):
      self.toHTMLHeader(controller, varContext)
      return self.printChildren(controller, varContext)
   

# Abstract superclass of Template, enclosedStack  and Controller
# tags. Provides shared functionality.
class JumpTag(XTag):
   # __slots__ = ("attrs", "classes", "includeClasses", "includeAttrs", "enclosedIndex")
   def __init__(self, parent, tag, remainder):  
      # remove * or ~ from end of tag
      XTag.__init__(self, parent, tag[:-1])

      self.attrs, remainder = Attr.matchAttr(remainder)
      self.classes = [cls for cls in remainder.split(" ") if cls.strip() != ""]
       
      self.includeClasses = "classes" in self.classes
      self.includeAttrs = "attrs" in self.classes
         
   def toHTML(self, controller, varContext):  
      self.toHTMLHeader(controller, varContext)

      # this grabs the explicitly passed variables out of the external
      # context and places them in the context the JumpTag can use
      newContext = {}
      for name, attr in self.attrs.items():    
         newContext[name] = attr.partEval(varContext)

      return self.prepCall(controller, varContext, newContext)
  
   # adds/removes the JumpTag from the enclosedStack, so inner <def>s
   # can utilize the <enclosed~/> tag. Also initiaizes the stack if 
   # it does not exist
   def prepCall(self, controller, extContext, varContext):
      
      newClasses = self.classes[:] 
      
      newClasses += controller.template.classes() if self.includeClasses else []
      
      newAttrs = controller.template.attrs() if self.includeAttrs else {}
      
      args = self.getArgs(controller, varContext)

      if args != None: 
         # split up the given attributes into explicit attributes, which 
         # can be used in logic, and undeclared attributes, which can be 
         # passed on to any children via the "attrs" class
         newContext = {}
         for key, value in varContext.items():   
            if key in args:
               newContext[key] = value
            else:
               newAttrs[key] = value
      else:  
         # if the tag is a <render> tag, all arguments are passed to the 
         # rendered file as explicit attributes to be used
         newContext = varContext
      
      enclosed = t(origin=t(source=self.source, 
                    index=self.enclosedIndex, context=extContext if len(self.children) > 0 else {}, lines=self.lines), 
                    classes=newClasses, attrs=newAttrs)
         
      s = self.callForward(controller, newContext, enclosed)
      
      return s 
      
   def getArgs(self, controller, varContext):
      return getattr(controller, self.getFunc()).args

   def callForward(self, controller, varContext, enclosed):
      
      return getattr(controller, self.getFunc())(enclosed=enclosed, **varContext)
      
# tag that calls on a predefined tag type. This causes it to
# output the HTML of the DefTag's children in place of the call 
# tag. 
class TemplateTag(JumpTag):
   # __slots__ = ()
   def getFunc(self):
      return "template def: " + self.nominalTag


# tag that calls a predefined function in the Controller
# passes its attributes to the controller as keyword arguments
class ControllerTag(JumpTag): 
   # __slots__ = ()
   def getFunc(self):
      return self.nominalTag

# tag that refers to the area enclosed by the JumpTag after making a 
# jump. EnclosedTags cannot contain children, and for the sake of
# simplicity do not add themselves to the 
class EnclosedTag(ControllerTag):
   # __slots__ = ()
   def __init__(self, parent, tag, remainder):
      ControllerTag.__init__(self, parent, tag, remainder)
      if len(self.attrs) > 0: raise StandardError("<enclosed~/> tag cannot take arguments: " + str(self.attrs.keys()))

   # Do not add self to stack, since <enclosed> cannot have any children
   # and thus cannot be referred to through the enclosedStack
   def prepCall(self, controller, varContext, newContext):
      if len(self.children) > 0: raise StandardError("<enclosed~/> tag cannot contain anything")
      return self.callForward(controller, varContext, None)
   def callForward(self, controller, varContext, enclosed):
      return controller.enclosed(**controller.enclosedData())

class RenderTag(ControllerTag):
   # __slots__ = ()
   def __init__(self, parent, tag, remainder):
      remainder = "omgsource=" + remainder
      ControllerTag.__init__(self, parent, tag, remainder)
      
   def getArgs(self, controller, varContext):
      return None

   def callForward(self, controller, varContext, enclosed):
      return controller.render(source=str(varContext['omgsource']), **varContext)
      