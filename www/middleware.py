from django.http import HttpResponse
from models import *
from datetime import datetime
import facebook

class t(dict):
   def __getattr__(self, v):
      try: return self[v]
      except KeyError: raise AttributeError("Key " + str(v) + " does not exist.")
      
   def __init__(self, *args, **kwargs):
      for source in args:
         for i, j in source.items():
            self[i] = j
         
      for i, j in kwargs.items():
         self[i] = j

         
class ActionMiddleware(object):

   def __init__(self):
      pass
   def process_request(self, request):
      user = None
      try: user = t(facebook.get_user_from_cookie(request.COOKIES, "165907186817169", "01b396117cc378372ee05c33470b4fff"))
      except Exception, e: pass
      
      POST = t(request.POST)
      try:
         
         userdata = t(facebook.GraphAPI(user.access_token).request("me"))
         newComment = Comment(text = POST.text,
                              userID = userdata.id,
                              date = datetime.now(),
                              article = request.POST['article'])
         newComment.save();
      except Exception, e:  pass
         
   def process_view(self, request, view_func, view_args, view_kwargs):
      pass
   def process_template_response(self, request, response):
      return response
   def process_response(self, request, response):
      return HttpResponse(response)
   def process_exception(self, request, exception):
      pass
