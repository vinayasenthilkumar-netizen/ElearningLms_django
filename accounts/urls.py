# these old imports and urlpatterns are commented out (kept for reference)
# from django.urls import path
# from . import views
# from .views import signup, CustomLoginView
# urlpatterns = [
#     path("signup/", views.signup, name="signup"),
#     path("login/", CustomLoginView.as_view(), name="login"),
# ]


# import path so we can define url routes
from django.urls import path

# import many views
from .views import signup, CustomLoginView, CustomLogoutView, dashboard, notification_read, notification_delete, teacher_search, profile_home, profile_edit, status_create,todo_create,todo_edit,todo_delete


# list of url patterns for the accounts app
urlpatterns = [
  
    # route for the dashboard/home page
    path("home/", dashboard, name="dashboard"),

    # route for the signup page
    path("signup/", signup, name="signup"),

    # route for the login page
    path("login/", CustomLoginView.as_view(), name="login"),

    # route for the logout page
    path("logout/", CustomLogoutView.as_view(), name="logout"),

    # route to mark a notification as read
    path("notifications/<int:notification_id>/read/", notification_read, name="notification_read"),

    # route for teacher search page
    path("search/", teacher_search, name="teacher_search"),

    # route to edit the logged-in user's profile
    path("profile/edit/", profile_edit, name="profile_edit"),

    # route to view a user's profile by username
    path("profile/<str:username>/", profile_home, name="user_profile"),

    # route to create a new status update
    path("status/create/", status_create, name="status_create"),

    # route to delete a notification
    path("notifications/<int:notification_id>/delete/", notification_delete, name="notification_delete"),

    # route to create a new todo item
    path("todo/create/", todo_create, name="todo_create"),

    # route to edit a todo item by id
    path("todo/<int:todo_id>/edit/", todo_edit, name="todo_edit"),

    # route to delete a todo item by id
    path("todo/<int:todo_id>/delete/", todo_delete, name="todo_delete"),
]