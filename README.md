# my-fastapi

To set up migrations, if the file "alembic.ini" does not yet exist, run the following command in the terminal:

...
alembic init migrations
...
This will create a folder named migrations and a configuration file for Alembic

- In the alembic.ini file, set the database URL for the database you want to manage migrations for.
- Then, navigate to the migrations folder and open env.py. In that file, make the necessary changes in the section where you add the following import:

...
from myapp import mymodel
...

- Next, run the following command to create a new migration: ```alembic revision --autogenerate -m "comment"```
- This will generate a migration file
- Finaly, apply the migration useing: ```alembic upgrade heads```