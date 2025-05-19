install requirements.txt in a virtualenv i have used python 3.11.11
i am not using any .env or secrect file as it is a sample project 
task 1 
1. run python manage.py migrate as i have excluded db file in git
2. run python manage.py runserver 
3. upload a valid csv file to the endpoint - http://127.0.0.1:8000/v1/users/csv-upload/ as file 
4. it will be response like  - {
  "message": "CSV processing started.",
  "task_id": "06f4cec3-e990-4bd4-9b63-6ecffc264bdd"
}
5. copy the task_id and paste in this endpoint - http://127.0.0.1:8000/tasks/06f4cec3-e990-4bd4-9b63-6ecffc264bdd/status/
  like this 
you will be able to see the output as desired

task 2 
1. run python manage.py runserver
2. run the api end point - http://127.0.0.1:8000/rate-limiter/test/200/ where 200 is the number of requests you want to test
3. if you want to clear cache run the api end point - http://127.0.0.1:8000/rate-limiter/clear/

