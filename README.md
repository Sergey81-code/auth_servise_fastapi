# my-fastapi

To set up migrations, if the file "alembic.ini" does not yet exist, run the following command in the terminal:

...
alembic init db/migrations
...
This will create a folder named migrations and a configuration file for Alembic

- In the alembic.ini file, set the database URL for the database you want to manage migrations for.
- Then, navigate to the migrations folder and open env.py. In that file, make the necessary changes in the section where you add the following import:

...
from myapp import mymodel
...

- Also, add the following function:

```python
def include_object(object, name, type_, reflected, compare_to):
    if type_ == "table":
        return name in target_metadata.tables
    return True
```

- Then replace

```python
with connectable.connect() as connection:
    context.configure(connection=connection, target_metadata=target_metadata)
```

- At the bottom of the file, replace it with:

```python
with connectable.connect() as connection:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        version_table="alembic_version_name_of_your_service",
        compare_type=True,
        include_object=include_object,
    )
```



- Next, run the following command to create a new migration: ```alembic revision --autogenerate -m "comment"``` - also doing if you want to change any models
- This will generate a migration file
- Finaly, apply the migration useing: ```alembic upgrade heads```
