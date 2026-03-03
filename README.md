# Films and actors

## Setup
The project is using `uv` as the package manager. To install the dependencies, run the following command
in the terminal:

```bash
uv sync
```

## Usagge
### Obtaining data
To obtain the data, you need to run the command for getting data from the CSFD page. The command is invoked
from the repository root via

```bash
python manage.py scrape
```

The data is stored in the SQLite database. Once the `scrape` command is run for the first time,
every subsequent run will only add new data, not delete or update data for existing films and/or actors.

### Running the application
To run the application, you need to run the command for starting the server

```bash
python manage.py runserver 8000
```

This starts the *development* server on port `80000`.

> [!NOTE]
> The development server is not suitable for production use.


### Running tests
To run the tests, you need to run the following command from the repository root:

```bash
pytest
```
