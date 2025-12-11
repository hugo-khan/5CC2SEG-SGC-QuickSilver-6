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
from django.urls import include, path

from recipes.views.admin_login_view import AdminLoginView
from recipes.views.author_recipes_view import author_recipes
from recipes.views.comment_view import AddCommentView
from recipes.views.comment_delete_view import CommentDeleteView
from recipes.views.dashboard_view import dashboard
from recipes.views.delete_account_view import DeleteAccountView
from recipes.views.edit_profile_view import ProfileUpdateView  # Edit profile
from recipes.views.like_view import ToggleLikeView
from recipes.views.log_in_view import LogInView
from recipes.views.log_out_view import log_out
from recipes.views.password_view import PasswordView
from recipes.views.profile_view import profile  # Display profile
from recipes.views.recipe_search_view import recipe_search
from recipes.views.sign_up_view import SignUpView


urlpatterns = [
    # Core pages
    path("admin/", admin.site.urls),
    path("", LogInView.as_view(), name="home"),
    path("dashboard/", dashboard, name="dashboard"),

    # Auth & profile
    path("log_in/", LogInView.as_view(), name="log_in"),
    path("admin/login/", AdminLoginView.as_view(), name="admin_login"),
    path("log_out/", log_out, name="log_out"),
    path("password/", PasswordView.as_view(), name="password"),
    path("profile/", profile, name="profile"),  # Display profile
    path(
        "profile/edit/",
        ProfileUpdateView.as_view(),
        name="profile_edit",
    ),  # Edit profile
    path("sign_up/", SignUpView.as_view(), name="sign_up"),
    path("account/delete/", DeleteAccountView.as_view(), name="delete_account"),

    # Google OAuth via allauth
    path("accounts/", include("allauth.urls")),

    # Recipe-related features (search, author listing, comments, likes)
    path("recipes/search/", recipe_search, name="recipe_search"),
    path("author/<int:author_id>/recipes/", author_recipes, name="author_recipes"),
    path(
        "recipe/<int:recipe_id>/comment/",
        AddCommentView.as_view(),
        name="add_comment",
    ),
    path(
        "comments/<int:pk>/delete/",
        CommentDeleteView.as_view(),
        name="comment_delete",
    ),
    path(
        "recipe/<int:recipe_id>/like/",
        ToggleLikeView.as_view(),
        name="toggle_like",
    ),

    # Include app URLs
    path("", include("recipes.urls")),
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
