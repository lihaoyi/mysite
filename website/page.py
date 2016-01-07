from www import facebook
from .imports import *
from .home import *
from .article import *

@Ajax.ajaxify
def index(request, name): 
   log(name)
   HTML = Page(request).link(os.path.abspath("/"+name)).main()       
   return HTML

@XPage.xinclude("website/page.xtag")    
class Page (Home):

   def link(self, name):    
      self.data.meta = loadArticle(name)
      user = None
      try:
         user = t(**facebook.get_user_from_cookie(self.request.COOKIES, "165907186817169", "01b396117cc378372ee05c33470b4fff"))
      except Exception, e: 
         pass
         log("exception: " + str(e))
      self.data.user = user
      return self

   
   
   @controller(ajax=1)
   def content(self):
      return Article(parent=self).template.content( 
                                       source=self.data.meta.filepath + "/Article.xtag", 
                                       date=self.data.meta.latest, 
                                       fullname=self.data.meta.fullname,
                                       banner = self.data.meta.banner)

   @controller()
   def banner(self):
      return []
      
   @controller()
   def leaveComment(self):
      return self.template.leaveComment()

   @controller(ajax=1)
   def comments(self):
      
      comments = [t( text=comment.text, 
                     userdata=t(**cache()(facebook.GraphAPI(self.data.user.access_token).get_object)(comment.userID)), 
                     date=comment.date, 
                     article=None, 
                     url=None)
                  for comment in 
                  Comment.objects.filter(article=self.data.meta.path).order_by('-date')]
      
      return self.template.comments(comments=comments)
      
   @controller(ajax=1)
   def articleLabel(self):
      return self.template.articleLabel(article=self.data.meta.path)
      
   @controller(ajax=1)
   def fblogin(self):
      userdata = None   
      accessToken = None
      try:     
         
         accessToken = self.data.user.access_token
         userdata = t(**cache()(facebook.GraphAPI(accessToken).request)("me"))
      except Exception, e:  
         pass
         #log(traceback.format_exc())

      return self.template.fblogin(userdata=userdata, accessToken=accessToken)