from .imports import *
from .utils import *
from django.views.generic import View
@Ajax.ajaxify
def index(request):       
   tree = Base(request).main() 
   return tree
 

@XPage.xinclude("website/base.xtag", Utils) 
class Base (XPage, View): 
   @controller(ajax=1)
   def main(self):
      return self.template.main()

   @controller(pure=1, ajax=1)
   def menubar(self):   
      articleSet = [t(name=category, content=getAllArticles("/"+category))
                     for category in 
                     ("design", "hardware", "software", "photos")]

      return self.template.menubar(articles=articleSet)   

   @controller(pure=1, ajax=1)
   def sidebar(self):   
      return self.template.sidebar()  
      
   @controller(pure=1, ajax=1)
   def content(self):        
      return self.template.content()
   
   @controller(pure=1, ajax=1)
   def banner(self):        
      return self.template.banner()   
      
   @controller()
   def floatMenu(self):
      return self.template.floatMenu(text=XUtils.randB64ID())
      
   
class ArticleData(t):
   def imagePath(self):
      return self.filepath + "/images/"
   
articleBase = "media/projects"
def loadArticle(path):
   
   filepath = articleBase + path
   url = "/page" + path
   latest = datetime.fromtimestamp(os.stat(filepath).st_mtime)
   meta = eval(XLoad.loadRaw(filepath + "/meta.txt"))
   return ArticleData(url=url, 
                      path=path, 
                      filepath=filepath, 
                      content=None,
                      latest=latest,
                      **meta)
   
# gets the list of 
def getAllArticles(path):
   return   ([loadArticle(path)]
            if os.path.exists(articleBase + path + "/Article.xtag") else
            [  article
               for child in os.listdir(articleBase + path)
               for article in getAllArticles(path + "/" + child )])

      