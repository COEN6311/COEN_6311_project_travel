
# Django Project Setup and Management Guide

This guide provides instructions for setting up your Django development environment, managing dependencies, configuring the database, running the development server, and handling migrations.

## Environment Setup

### Creating a Virtual Environment 

Create a virtual environment to isolate project dependencies:  
 
- For Linux/macOS:
  ```bash
  /usr/local/bin/python3.12 -m venv venv
  source venv/bin/activate
  
- For Windows:
  ```cmd
  /usr/local/bin/python3.12 -m venv .venv
  ```
    ```bash
      .\.venv\Scripts\activate
    ```
### Deactivating the Virtual Environment

To deactivate the virtual environment, simply run:

```bash
deactivate
```

## Dependency Management

### Installing Dependencies

Install required packages from `requirements.txt`:

```bash
pip install -r requirements.txt
```

### Updating Dependencies

If you've added or changed project dependencies, update `requirements.txt`:

```bash
pip freeze > requirements.txt
```

## Database Configuration

### MySQL Database Connection

The MySQL database on the cloud server is ready for use. Configure the database settings (account and password) in `settings.py` and connect using a MySQL client.

## Server Management

### Running the Development Server

Start the Django development server with:

```bash
python manage.py runserver
```

### Freeing Up Port 8000

If needed, free up port 8000 using:

```bash
sudo fuser -k 8000/tcp
```

## Model and Migration Management

### After Modifying Models

If you've modified models, generate and apply migrations:

- Generate migration files:
  ```bash
  python manage.py makemigrations
  ```
- Apply migrations to the database:
  ```bash
  python manage.py migrate
  ```

This guide should help you manage your Django project effectively. For more detailed instructions, refer to the Django documentation.
```
ps aux | grep 'start_order_consumer' | awk '{print $2}' | xargs kill -9
