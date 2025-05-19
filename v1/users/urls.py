
from django.urls import path

from v1.users.views import csv_upload as csv_upload_views


urlpatterns = [
    path("csv-upload/", csv_upload_views.CSVUploadView.as_view(), name="csv_upload"),
]