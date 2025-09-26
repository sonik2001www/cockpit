# Cockpit API

## Overview
Django REST API project running in Docker. Provides ready-to-use setup with PostgreSQL and Django Admin.

## Key Features
- Django REST Framework for APIs
- PostgreSQL as the database
- Docker for deployment
- Automatic creation of superuser
- Code style checks with Black and Flake8

## Setup Instructions

1. Install [Docker Desktop](https://www.docker.com/products/docker-desktop/).
2. Create a `.env` file in the root folder:



`.env`
~~~
POSTGRES_DB=cockpit
POSTGRES_USER=cockpituser
POSTGRES_PASSWORD=1234
POSTGRES_PORT=5432
POSTGRES_HOST=db

DB_HOST=localhost

DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_PASSWORD=admin
DJANGO_SUPERUSER_EMAIL=adminsubachka@gmail.com
~~~

3. Build and run the project:

~~~
docker-compose up
~~~
4. Open the app in your browser:  
[http://localhost:8000](http://localhost:8000)

