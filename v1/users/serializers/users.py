from rest_framework import serializers
from v1.users.models import CustomUser
from common.serializers.custom_fields import AgeField


class UserSerializer(serializers.ModelSerializer):
    age = AgeField(min_age=0, max_age=120)
    
    class Meta:
        model = CustomUser
        fields = [
            'username',
            'email',
            'first_name',
            'last_name',
            'age'
        ]