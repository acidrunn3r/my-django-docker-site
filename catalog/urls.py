from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.index, name='index'),
    path('racing/', views.racing, name='racing'),
    path('media/', views.media, name='media'),
    path('register/', views.register, name='register'),
     path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('profile/', views.profile, name='profile'),
    path('check_username/', views.check_username, name='check_username'),
    path('admin/users/', views.user_management, name='user_management'),
    path('admin/users/delete/<int:user_id>/', views.delete_user, name='delete_user'),
    path('toggle_like/<int:image_id>/', views.toggle_like, name='toggle_like'),
    path('get_likes/', views.get_likes, name='get_likes'),
]  
