from website.imports import *
import traceback

def index(request):

   #if request.META['HTTP_HOST'] == 'localhost':
      from library import *
      import facebook
      
      from website import about
      

      startTime = datetime.now()
      schedlog("scheduled tasks: " + str(len(tasks.items())))
      for func, (minute, hour, day) in tasks.items():
         if ((minute == None or minute == startTime.minute) and
             (hour == None or hour == startTime.hour) and 
             (day == None or day == startTime.day)):
            try:
               func()
               schedlog(str(func) + " DONE")
            except BaseException, e:
               schedlog(traceback.format_exc())
      
      return HttpResponse("")

