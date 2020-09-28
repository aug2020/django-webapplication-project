"""yumaker URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path,include
from yumakerapp import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('',views.home,name='home'),
    path('generate/', views.generate, name='generate'),
    path('login/', views.login, name='login'),
    path('upload/',views.upload_video, name='upload'),
    path('oauth2callback/', views.authorize, name='oauth2callback'),
    path('aboutus/',views.aboutus,name='aboutus'),
    path('howitworks/',views.howitworks,name='howitworks')
]
if settings.DEBUG: #if we are in debug mode so on our own server we will use the static and media url on my local machine
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_URL)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
