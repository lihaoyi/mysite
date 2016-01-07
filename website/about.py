from .imports import *
from .home import *
import urllib2

@Ajax.ajaxify
def index(request):
   return About(request).main()
   

         
@XPage.xinclude("website/about.xtag") 
class About (Base):     
   @controller(ajax=1, pure=1)
   def content(self):  
      return self.template.content()
   
   @controller(ajax=1)
   def aboutMe(self):
      
      
      images = open("media/about/imageList.txt").readlines()
      random.shuffle(images)      
      images = [t(pic=link.strip(), url=link.strip(), tooltip="") for link in images[0:5]]

      return self.template.aboutMe(images=images);
      
   @controller(ajax=1)
   def aboutTechcreation(self):
      articles = [meta
                  for directory in ("design", "hardware", "software", "photos")
                  for meta in getAllArticles("/" + directory)]
      random.shuffle(articles) 
      articles= articles[:5]
      images = [t(pic=article.imagePath() + article.displayPic, url=article.url, tooltip=article.name) 
                  for article in articles]
      return self.template.aboutTechcreations(images=images);
      
      
@scheduled(minute=0)
def preparePhotos():
   log("preparing photos")
   log("NEW")
   access_token = "AAACW5EbvmJEBAJ62Ino5Hny6IJS2JrxZCGKxDRuPDnx8cZC7ZBZBakm4HB6jJBTzLZALbRMxk6IJlnQ0QdToGBERBXwiK5VYZD"
   photoData = facebook.request("li.haoyi/photos", access_token, {"limit":"0"})["data"]
   photoData = list(enumerate(photoData))
   photoData.sort(key=lambda photo: photo[0] + random.gauss(0, len(photoData)))
   images = [image['images'][0]['source'] for index, image in photoData[0:50]]
   
   imageList = ""
   for source in images:
      XImage.prepSizedImage(source, 120, 90)
      imageList += source + "\n"
      open("media/about/imageList.txt", 'w').write(imageList)