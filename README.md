1.create a venv environment and ensure that the project runs under the venv environment.
.\.venv\Scripts\activate or source venv/bin/activate(linux)

2.pip install -r requirements.txt  

3.If you've added or changed the project dependencies, 
you need to update the dependencies
pip freeze > requirements.txt

4.sql 
The MySQL database on the cloud server is ready, 
with the account and password already provided in settings.py. 
You can directly connect using a MySQL client.

5.python manage.py runserver 

6.after modify model
python manage.py makemigrations
python manage.py migrate




