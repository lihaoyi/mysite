   
from .imports import *

import StringIO 
import urllib2
@XPage.xinclude("website/utils.xtag")   
class Utils (XPage):   
   @controller()
   def image(self, source, link=None, textSource=None, width=None, height=None, highTitle=False):
      
      if link == None:
         link = source.split(os.extsep)
         link[0] += " Full"  
         link = link[0] + "." + link[1] if len(link) > 1 else link[0]
         if not os.path.exists(link):
            link = None
         else:
            link = "/" + link
      
      if link == None and (width or height):
         if not os.path.exists(source):
            link = None
         else:
            link = "/" + source
      
      
      source = XImage.prepSizedImage(source, width, height)
      
      return self.template.image(source="/"+source, link=link, textSource=textSource,  highTitle=highTitle);
      
   @controller()
   def loadRaw(self, source):
      text = XLoad.loadRaw(source)
      text = XString.escapeHTML(text)
      return [text]
   
   @controller(ajax=1)
   def timestamp(self, time):
      from datetime import timedelta
      delta = datetime.now() - time
      if delta < timedelta(seconds = 60):
         if delta.seconds < 2: text = "seconds ago"
         else: text = str(delta.seconds) + " seconds ago"
      elif delta < timedelta(minutes = 60):
         text = str(delta.seconds / 60) + " minute" + ("s" if delta.seconds/60 > 1 else "") + " ago"
      elif delta < timedelta(hours = 24):
         text = str(delta.seconds / 60 / 60) + " hour" + ("s" if delta.seconds/60/60 > 1 else "") + " ago"
      else:
         text = time.strftime("%d %B %y")
      return self.template.timestamp(time=text)
   
   @controller(ajax=1)
   def now(self):
      return self.template.timestamp(time=datetime.now().strftime("%M:%H %d %b %y"))
      
   @controller(pure=1)
   def script(self):
      return ["<script class=\"star\" style='display:none;'>(function(script){"] + self.enclosed(**self.enclosedData()) + ["})($(script ? script : $('script').last()));</script>"]
   
