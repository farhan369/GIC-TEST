from celery.result import AsyncResult

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status


class TaskStatusView(APIView):
    """
    API View to check the status and retrieve the result of a Celery task.
    """
    def get(self, request, task_id):
        """
        Handles GET requests to check task status.
        Retrieves task status and result using the task ID.
        """
        task_result = AsyncResult(task_id)
        state = task_result.state

        response_data = {
            "task_id": task_id,
            "status": state,
        }

        if state == 'SUCCESS':
            response_data["result"] = task_result.result
            return Response(response_data, status=status.HTTP_200_OK)
        elif state == 'FAILURE':
            response_data["error"] = str(task_result.result)
            return Response(response_data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response(response_data, status=status.HTTP_200_OK)