from django.db import models
# Create your models here.
class Comment(models.Model):
   text = models.CharField(max_length=400)
   userID = models.CharField(max_length=100)
   date = models.DateTimeField(auto_now = True)
   article = models.CharField(max_length=100)
   def __str__(self):
      return self.text[:20] + (self.text[20:] and "..")