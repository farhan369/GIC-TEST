from rest_framework import serializers


class AgeField(serializers.IntegerField):
    """
    Custom serializer field for age validation.
    Ensures age is between min_age and max_age years.
    
    Args:
        min_age (int): Minimum allowed age (default: 0)
        max_age (int): Maximum allowed age (default: 120)
    """
    def __init__(self, min_age=0, max_age=120, **kwargs):
        kwargs['min_value'] = min_age
        kwargs['max_value'] = max_age
        kwargs['required'] = False
        kwargs['allow_null'] = True
        self.min_age = min_age
        self.max_age = max_age
        super().__init__(**kwargs)

    def to_internal_value(self, value):
        if value is None:
            return value
        try:
            value = super().to_internal_value(value)
            return value
        except serializers.ValidationError as e:
            if 'min_value' in str(e) or 'max_value' in str(e):
                raise serializers.ValidationError(f"Age must be between {self.min_age} and {self.max_age}.")
            raise 