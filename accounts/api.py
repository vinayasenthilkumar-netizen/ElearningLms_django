# import the user model 
from django.contrib.auth import get_user_model
# import a helper that returns an object or gives a 404 if not found
from django.shortcuts import get_object_or_404
# import rest framework tools for permissions and http status codes
from rest_framework import permissions, status
# import the response class 
from rest_framework.response import Response

# import for building api views
from rest_framework.views import APIView
# import the database models 
from .models import Profile, StatusUpdate, Notification

# import the serializers
from .serializers import (
    UserMeSerializer,
    UserPublicSerializer,
    StatusUpdateSerializer,
    NotificationSerializer,
)

# get the active user model used by the project
User = get_user_model()


# api view for getting and updating the logged in users own details
class MeAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request):
        # make sure the user has a profile, and default the role to student if new
        Profile.objects.get_or_create(
            user=request.user,
            defaults={"role": Profile.Role.STUDENT},
        )
        serializer = UserMeSerializer(request.user)
        # return the serialized data
        return Response(serializer.data)

    def put(self, request):
        # make sure the user has a profile and default the role to student if new
        Profile.objects.get_or_create(
            user=request.user,
            defaults={"role": Profile.Role.STUDENT},
        )
        # load the request data into the serializer 
        serializer = UserMeSerializer(request.user, data=request.data, partial=False)
        # check the data and raise an error if anything is invalid
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


# api view for viewing someone else's public profile by username
class UserProfileAPIView(APIView):
    # require the user to be logged in for this endpoint
    permission_classes = [permissions.IsAuthenticated]

    # handle get requests
    def get(self, request, username):
        # find the user by username or return 404
        user = get_object_or_404(User, username=username)
        Profile.objects.get_or_create(
            user=user,
            defaults={"role": Profile.Role.STUDENT},
        )
        serializer = UserPublicSerializer(user)
        return Response(serializer.data)


# api view for listing and creating status updates
class StatusListCreateAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request):
        # get all status updates linked to the logged-in user
        queryset = request.user.status_updates.all()

        serializer = StatusUpdateSerializer(queryset, many=True)
        return Response(serializer.data)

    # handle post requests to create a new status update
    def post(self, request):
        # try to get the user's profile (it may not exist yet)
        profile = getattr(request.user, "profile", None)
        # read the role from the profile if available
        role = getattr(profile, "role", None)

        # only students are allowed to post status updates
        if role != "STUDENT":
            return Response(
                {"detail": "Only students can post status updates."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = StatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # save the status update and attach it to the current user
        serializer.save(user=request.user)
        # return the created status update with a 201 created status
        return Response(serializer.data, status=status.HTTP_201_CREATED)


# api view for listing notifications for the current user
class NotificationListAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    # handle get requests to return the latest notifications
    def get(self, request):
        # get up to 20 notifications
        queryset = request.user.notifications.all()[:20]
        # serialize the notifications list
        serializer = NotificationSerializer(queryset, many=True)
        return Response(serializer.data)


# api view for marking a notification as read
class NotificationReadAPIView(APIView):
    # require the user to be logged in for this endpoint
    permission_classes = [permissions.IsAuthenticated]

    # handle post requests to mark one notification as read
    def post(self, request, notification_id):
        # find the notification that belongs to this user or return 404
        notification = get_object_or_404(
            Notification,
            id=notification_id,
            user=request.user,
        )
        notification.is_read = True
        notification.save()
        return Response({"success": True, "id": notification.id})