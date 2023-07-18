import re


from django.core.exceptions import ValidationError


def validate_username(value):
    if value.lower() == 'me':
        raise ValidationError(
            f'{value} зарезервированно системой.'
        )
    if not re.match(r'^[\w.@+-]+$', value):
        raise ValidationError(
            f'{value} содержит неизвестные символы.'
        )
