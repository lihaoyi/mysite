   
from .imports import *
from .utils import *
import StringIO 
import urllib2
@XPage.xinclude("website/article.xtag")   
class Article (Utils):   


      
   @controller()
   def image(self, source, link=None, width=None, height=None,  highTitle=False):
      return Utils(parent=self).image(  source=self.data.meta.imagePath() + source, 
                                 width=width, 
                                 height=height, 
                                 link=link, 
                                 highTitle=highTitle);
      
   @controller()
   def loadRaw(self, source): 
      return Utils(parent=self).loadRaw(source=self.data.meta.filepath + "/" + source);
      
   @controller()
   def a(self, href):
      return self.template.a(href=href if href.startswith("http") or href.startswith("/") else "/" + self.data.meta.filepath + "/" + href)