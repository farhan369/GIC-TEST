import csv
from io import StringIO
from celery import shared_task
from django.db import IntegrityError

from v1.users.serializers import users as user_serializers
from v1.users.models import CustomUser


@shared_task
def process_csv_upload(csv_data):
    """
    Celery task to process the uploaded CSV data.
    Parses, validates, and saves user records asynchronously.
    """
    print("Processing CSV data...")
    decoded_file = StringIO(csv_data)
    reader = csv.DictReader(decoded_file)

    saved_count = 0
    rejected_count = 0
    errors = []

    for row_num, row in enumerate(reader, start=1):
        serializer = user_serializers.UserSerializer(data=row)

        if serializer.is_valid():
            try:
                CustomUser.objects.create(**serializer.validated_data)
                saved_count += 1
            except IntegrityError:
                rejected_count += 1
                errors.append({
                    "row": row_num,
                    "data": row,
                    "errors": {"email": ["Email address already exists."]}
                })
            except Exception as e:
                rejected_count += 1
                errors.append({
                    "row": row_num,
                    "data": row,
                    "errors": {"database_error": [str(e)]}
                })
        else:
            rejected_count += 1
            errors.append({
                "row": row_num,
                "data": row,
                "errors": serializer.errors
            })

    return {
        "saved_records": saved_count,
        "rejected_records": rejected_count,
        "errors": errors
    }