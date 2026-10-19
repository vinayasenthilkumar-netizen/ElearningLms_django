from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import Profile, StatusUpdate, Notification
User = get_user_model()


class UserMeSerializer(serializers.ModelSerializer):
    role = serializers.CharField(source="profile.role", read_only=True)
    # allow updating the bio through the related profile
    bio = serializers.CharField(source="profile.bio", required=False, allow_blank=True)
    # expose the profile photo from the related profile
    photo = serializers.ImageField(source="profile.photo", read_only=True)


    class Meta:
        # connect this serializer to the user model
        model = User
        # list the fields 
        fields = ["username", "first_name", "last_name", "email", "role", "bio", "photo"]

        read_only_fields = ["username", "role", "photo"]

    def update(self, instance, validated_data):
        profile_data = validated_data.pop("profile", {})

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        # save the user changes
        instance.save()

        # make sure the user has a profile, and default role to student if new
        profile, _ = Profile.objects.get_or_create(
            user=instance,
            defaults={"role": Profile.Role.STUDENT},
        )

        if "bio" in profile_data:
            profile.bio = profile_data["bio"]
            profile.save()

        return instance


# serializer for showing public user profile info to other users
class UserPublicSerializer(serializers.ModelSerializer):
    role = serializers.CharField(source="profile.role", read_only=True)
    bio = serializers.CharField(source="profile.bio", read_only=True)
    photo = serializers.ImageField(source="profile.photo", read_only=True)

    class Meta:
        # connect this serializer to the user model
        model = User
        # list the fields that will be returned
        fields = ["username", "first_name", "last_name", "email", "role", "bio", "photo"]


# serializer for status updates
class StatusUpdateSerializer(serializers.ModelSerializer):

    class Meta:
     
        model = StatusUpdate
        # fields included in the api response
        fields = ["id", "content", "created_at"]


# serializer for notifications
class NotificationSerializer(serializers.ModelSerializer):

    class Meta:
      
        model = Notification
        # fields included in the api response
        fields = ["id", "title", "message", "link", "is_read", "created_at"]