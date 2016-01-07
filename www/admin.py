import models
from django.contrib import admin
class CommentAdmin(admin.ModelAdmin):
   list_display = ('__str__', 'article','date', 'userID')
   list_filter = ('article', 'date', 'userID')
   search_fields = ('text', 'article', 'userID', 'date')
   
   
admin.site.register(models.Comment, CommentAdmin)
