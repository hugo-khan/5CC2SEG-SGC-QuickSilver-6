"""
URL configuration for recipify project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
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
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path
from recipes.views.home_view import home
from recipes.views.dashboard_view import dashboard
from recipes.views.log_in_view import LogInView
from recipes.views.log_out_view import log_out
from recipes.views.password_view import PasswordView
from recipes.views.profile_view import profile  # Display profile
from recipes.views.edit_profile_view import ProfileUpdateView  # Edit profile
from recipes.views.sign_up_view import SignUpView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='home'),
    path('dashboard/', dashboard, name='dashboard'),
    path('log_in/', LogInView.as_view(), name='log_in'),
    path('log_out/', log_out, name='log_out'),
    path('password/', PasswordView.as_view(), name='password'),
    path('profile/', profile, name='profile'),  # Display profile
    path('profile/edit/', ProfileUpdateView.as_view(), name='profile_edit'),  # Edit profile
    path('sign_up/', SignUpView.as_view(), name='sign_up'),
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
