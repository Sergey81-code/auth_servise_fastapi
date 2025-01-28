# my-fastapi-test

## Setting up migrations for the test database

To set up migrations in the `tests/migrations` directory for the test database:

1. If the file `alembic.ini` does not yet exist in the `tests/migrations` folder, it will be moved from the main directory to `tests/migrations`.
2. After that, the database path in the `alembic.ini` file will be adjusted.
3. In the alembic.ini file, set the database URL for the database you want to manage migrations for.
4. Then run any test
5. Then, navigate to the migrations folder and open env.py. In that file, make the necessary changes in the section where you add the following import:

...
from myapp import mymodel
...

When running any test one more time, if migrations haven't been applied yet, they will be automatically executed.
