from django.urls import path
from . import views
app_name = 'posts'
urlpatterns =[
    path('create/',views.create_post,name = 'create_post'),
    path('like/<int:post_id>/',views.like_post,name = 'like_post'),
    path('comment/<int:post_id>/',views.comment_post,name = 'comment_post'),
    path('delete/<int:post_id>/',views.delete_post,name= 'delete_post'),
]