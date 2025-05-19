import csv
from pathlib import Path

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from v1.users.tasks import csv_upload as csv_upload_tasks


class CSVUploadView(APIView):
    """
    API View to handle CSV file uploads for user data.
    Triggers a Celery task to process the file asynchronously.
    """

    def post(self, request):
        """
        Handles POST requests for CSV file uploads.
        Validates file extension and sends the file content to a Celery task.
        """
        file = request.FILES.get('file', None)
        if not file:
            return Response(
                {"error": "No file provided."},
                status=status.HTTP_400_BAD_REQUEST
            )
        if not Path(file.name).suffix.lower() == '.csv':
            return Response(
                {"error": "Invalid file type. Only CSV files are allowed."},
                status=status.HTTP_400_BAD_REQUEST
            )
        file_obj = request.data['file']
        csv_content = file_obj.read().decode('utf-8')

        task = csv_upload_tasks.process_csv_upload.delay(csv_content)
        return Response(
            {"message": "CSV processing started.", "task_id": task.id},
            status=status.HTTP_202_ACCEPTED
        )