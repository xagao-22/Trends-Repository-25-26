# EQUI-Track

A Django equipment checkout and inventory tracker for a school's athletics office. The app includes student registration, staff-managed student and equipment records, borrowing, returns, lost-item tracking, dashboard totals, and overdue indicators.

## Run locally

Python 3.10 or newer is recommended. SQLite is the default database, so a local MySQL server is not required to try the app.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

For a SQLite quick start, leave `DB_ENGINE` unset in `.env` (or remove that line). Then initialize the database, create the first staff login, and start Django:

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open <http://127.0.0.1:8000/>. Sign in with the superuser account. Use **Admin tools** to add the first equipment and student records, or create student accounts through the registration page. Registration creates a regular student account; it does not grant staff privileges.

To run the automated workflow tests and Django configuration checks:

```bash
python manage.py test
python manage.py check
```

## Use MySQL

Install the MySQL connector requirements:

```bash
python -m pip install -r requirements-mysql.txt
```

Create a database and a dedicated application user in MySQL (choose your own password):

```sql
CREATE DATABASE equi_track CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'equi_track_user'@'localhost' IDENTIFIED BY 'choose-a-strong-password';
GRANT ALL PRIVILEGES ON equi_track.* TO 'equi_track_user'@'localhost';
```

Set `DB_ENGINE=mysql` and the matching `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, and `DB_PORT` values in `.env`. Then run `python manage.py migrate` and `python manage.py createsuperuser` as above. Do not commit `.env` or production secrets.

## Production checklist

- Set a long, random `SECRET_KEY`, `DEBUG=False`, and `ALLOWED_HOSTS` to your actual domain names.
- Serve the site over HTTPS, configure secure cookies and Django's CSRF trusted origins, and use a production WSGI/ASGI server instead of `runserver`.
- Run `python manage.py collectstatic` and configure a static-file server; back up the database and test restores.
- Restrict staff accounts to trusted athletics office personnel. Student registration intentionally creates non-staff accounts only.