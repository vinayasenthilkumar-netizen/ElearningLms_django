# this file controls which urls connect to which views in the project
"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
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

# import redirect helper to send users to another page
from django.shortcuts import redirect
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from django.views.generic import TemplateView

# import drf spectacular views for schema and swagger docs
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

# import api views from the accounts app
from accounts.api import (
    MeAPIView,
    UserProfileAPIView,
    StatusListCreateAPIView,
    NotificationListAPIView,
    NotificationReadAPIView,
)

# import api views from the courses app
from courses.api import (
    CourseListAPIView,
    CourseDetailAPIView,
    EnrollCourseAPIView,
    CourseFeedbackAPIView,
)

# main url patterns list for the project
urlpatterns = [
    # landing page route (shows landing.html)
    path("", TemplateView.as_view(template_name="landing.html"), name="landing"),

    # admin site route
    path("admin/", admin.site.urls),

    # include routes for the courses app
    path("courses/", include("courses.urls")),

    # include our custom accounts routes first (signup/login/logout pages)
    path("accounts/", include("accounts.urls")),

    # include django’s built-in auth routes (password reset and more)
    path("accounts/", include("django.contrib.auth.urls")),

    # redirect root url to the courses list page
    path("", lambda request: redirect("courses:list")),

    # include routes for the chat app
    path("chat/", include("chat.urls")),

     # swagger  openapi routes
    path("api/schema/", SpectacularAPIView.as_view(), name="api-schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="api-schema"), name="api-docs"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="api-schema"), name="api-redoc"),

    # api endpoints for users
    path("api/users/me/", MeAPIView.as_view(), name="api-me"),
    path("api/users/<str:username>/", UserProfileAPIView.as_view(), name="api-user-profile"),

    # api endpoints for status updates and notifications
    path("api/status/", StatusListCreateAPIView.as_view(), name="api-status"),
    path("api/notifications/", NotificationListAPIView.as_view(), name="api-notifications"),
    path("api/notifications/<int:notification_id>/read/", NotificationReadAPIView.as_view(), name="api-notification-read"),

    # api endpoints for courses
    path("api/courses/", CourseListAPIView.as_view(), name="api-courses"),
    path("api/courses/<int:course_id>/", CourseDetailAPIView.as_view(), name="api-course-detail"),
    path("api/courses/<int:course_id>/enroll/", EnrollCourseAPIView.as_view(), name="api-course-enroll"),
    path("api/courses/<int:course_id>/feedback/", CourseFeedbackAPIView.as_view(), name="api-course-feedback"),
]

# during development, serve uploaded media files through django
if settings.DEBUG:
    # add media url patterns in debug mode only
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)