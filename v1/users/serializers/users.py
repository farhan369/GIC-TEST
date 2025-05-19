from rest_framework import serializers
from v1.users.models import CustomUser


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = [
            'username',
            'email',
            'first_name',
            'last_name',
            'age'
        ]

    def validate_age(self, value):
        if value is not None and not (0 <= value <= 120):
            raise serializers.ValidationError("Age must be between 0 and 120.")
        return value