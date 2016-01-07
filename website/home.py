from .imports import *
from .base import *
from .article import *
from www import facebook

@Ajax.ajaxify
def index(request): 
   return Home(request).main()


@XPage.xinclude("website/home.xtag")     
class Home (Base):       
   @controller(ajax=1)
   def content(self):  
      
      posts = [meta(text=firstPara(meta))
               for directory in ("design", "hardware", "software", "photos")
               for meta in getAllArticles("/"+directory)][0:5]
      
      posts.sort(key=lambda x: x.latest)
      posts.reverse()
      return self.template.content(posts=posts)
   
   @controller()
   def banner(self):
      
      posts = [meta(text=firstPara(meta))
               for directory in ("design", "hardware", "software", "photos")
               for meta in getAllArticles("/"+directory)[0:5]]
               
      posts.sort(key=lambda x: x.latest)
      posts.reverse()
   
      return self.template.banner(posts=posts)
   
   @controller(ajax=1)
   def comments(self):
      comments = []  
      for comment in Comment.objects.order_by('-date')[0:8]:   
         meta = loadArticle(comment.article)
         comments += [t(text=comment.text, 
                        userdata=t(**cache()(facebook.GraphAPI().get_object)(comment.userID)), 
                        date=comment.date, 
                        article=meta.name, 
                        url=meta.url)]
         log(comments[-1].userdata)
                    
      return self.template.comments(comments=comments)
      
      
      
@cache() #this automatically invalidates because ~meta~ contains ~meta.latest~, which changes if modified 
def firstPara(meta):
   
   tree = Article()(meta=meta).render(source=meta.filepath + "/Article.xtag", date=meta.latest, fullname=meta.fullname)
   Ajax.fill(tree[0])
   text = tree[0].html[0]
   paragraphs = re.findall('<p.*?>.*?</p>', text, re.DOTALL)
   paragraphs[0] = re.sub('<p.*?>|</p>', "", paragraphs[0])
   return paragraphs[0]