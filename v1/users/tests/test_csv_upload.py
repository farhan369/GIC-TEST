from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock import patch, Mock
from v1.users.models import CustomUser
from celery.result import AsyncResult
from django.core.cache import cache
from v1.users.tasks.csv_upload import process_csv_upload


class CSVUploadViewTests(TestCase):
    def setUp(self):
        """Set up test environment before each test method."""
        self.client = APIClient()
        self.url = reverse('csv_upload')
        self.valid_csv_content = b'name,email,age\nJohn Doe,john@example.com,30'
        self.invalid_csv_content = b'name,email,age\nInvalid Data'
        cache.clear()  # Clear cache before each test

    def tearDown(self):
        """Clean up after each test method."""
        cache.clear()  # Clear cache after each test

    def test_no_file_provided(self):
        """Test API response when no file is provided."""
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['error'], 'No file provided.')

    def test_invalid_file_type(self):
        """Test API response when non-CSV file is uploaded."""
        file = SimpleUploadedFile(
            "test.txt",
            b"test content",
            content_type="text/plain"
        )
        response = self.client.post(self.url, {'file': file})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['error'], 'Invalid file type. Only CSV files are allowed.')

    @patch('v1.users.tasks.csv_upload.process_csv_upload')
    def test_successful_csv_upload(self, mock_task):
        """Test successful CSV file upload and task creation."""
        # Mock the delay method
        mock_task.delay = Mock(return_value=Mock(id='test-task-id'))

        file = SimpleUploadedFile(
            "test.csv",
            self.valid_csv_content,
            content_type="text/csv"
        )
        response = self.client.post(self.url, {'file': file})
        
        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.data['message'], 'CSV processing started.')
        self.assertEqual(response.data['task_id'], 'test-task-id')
        mock_task.delay.assert_called_once()

    @patch('v1.users.tasks.csv_upload.process_csv_upload')
    def test_rate_limiting(self, mock_task):
        """Test rate limiting functionality."""
        # Mock the delay method
        mock_task.delay = Mock(return_value=Mock(id='test-task-id'))
        
        file = SimpleUploadedFile(
            "test.csv",
            self.valid_csv_content,
            content_type="text/csv"
        )

        for _ in range(100): 
            response = self.client.post(self.url, {'file': file})
            self.assertEqual(response.status_code, 202)

        response = self.client.post(self.url, {'file': file})
        self.assertEqual(response.status_code, 429)
        self.assertEqual(response.content.decode(), 'Too Many Requests')
        self.tearDown()

    def test_csv_processing_result(self):
        """Test the actual CSV processing functionality."""
        CustomUser.objects.create(
            email='john@example.com',
            first_name='John',
            last_name='Doe',
            age=30
        )

        csv_content = (
            b'name,email,age\n'
            b'Jane Smith,jane@example.com,25\n' 
            b'John Doe,john@example.com,30\n'    
            b'Invalid User,invalid-email,150\n' 
        )

        file = SimpleUploadedFile(
            "test.csv",
            csv_content,
            content_type="text/csv"
        )

        # Upload the file
        with patch('v1.users.tasks.csv_upload.process_csv_upload') as mock_task:
            mock_task.delay = Mock(return_value=Mock(id='test-task-id'))
            response = self.client.post(self.url, {'file': file})
            self.assertEqual(response.status_code, 202)
            task_id = response.data['task_id']

        # Mock AsyncResult for task status check
        task_result = {
            'saved_records': 1,
            'rejected_records': 2,
            'errors': [
                {'row': 2, 'errors': {'email': ['Email address already exists.']}},
                {'row': 3, 'errors': {'age': ['Age must be between 0 and 120.']}}
            ]
        }

        with patch('common.views.AsyncResult') as mock_async_result:
            instance = mock_async_result.return_value
            instance.state = 'SUCCESS'
            instance.result = task_result

            # Check task status
            status_url = reverse('task_status', kwargs={'task_id': task_id})
            response = self.client.get(status_url)
            self.assertEqual(response.status_code, 200)
            
            # Verify the results
            self.assertEqual(response.data['status'], 'SUCCESS')
            result = response.data['result']
            self.assertEqual(result['saved_records'], 1)
            self.assertEqual(result['rejected_records'], 2)
            self.assertEqual(len(result['errors']), 2) 