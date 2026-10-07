# Homework 2: Frame Cinema

CS4300 - Introduction to Django. A movie theater booking application built with
Django 5.2, Django REST Framework, Bootstrap 5.3, and Behave.

Repository: https://github.com/ripleyforge-chase/cs4300

**Live Render app: https://chase-cs4300-cinema.onrender.com/**

Deployed and verified on October 6, 2026 using a free Render web service and
PostgreSQL database. Nothing has been submitted to Canvas.

## What the application does

- Browse and search three fictional movies with descriptions, release years,
  durations, and live seat counts.
- Create an account, sign in, choose an available seat, and view personal tickets.
- Cancel a booking and immediately return its seat to availability.
- Use the same movies, seats, reservations, and booking rules through the API.
- Manage movies through staff-only API CRUD and the Django admin.
- Reject duplicate reservations, invalid movie/seat pairs, anonymous booking
  requests, and attempts to access another user's tickets.

Each movie represents **one screening**, with its own A1-D8 seat inventory.
The assignment does not define showtimes, so this implementation does not invent
schedules. Each `Seat` belongs to a movie; `Booking` records movie, seat, user,
and booking date. `booking_status` is a read-only property derived from the
booking relationship, so it cannot disagree with the reservation. A database
one-to-one constraint prevents two bookings for the same seat. Both the HTML
views and API call `reserve_seat()` in `bookings/services.py`.

## Local setup (replaces DevEDU)

Python 3.13 is recommended; this project was verified with Python 3.13.13.
Run these commands from the repository root (the folder containing `homework2`):

```sh
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install -r homework2/requirements.txt
cd homework2/movie_theater_booking
python manage.py migrate
python manage.py seed_demo
python manage.py collectstatic --noinput
python manage.py runserver 127.0.0.1:8000
```

Open http://127.0.0.1:8000/ and choose **Create account**. No email, payment,
DevEDU account, Docker, or cloud service is needed. Choose any username and a
password that passes Django's validation. No shared user/admin credentials are
included. `seed_demo` creates sample movies and seats, not users, and can be
rerun without resetting reservations.

For staff-only movie editing, create a local administrator:

```sh
python manage.py createsuperuser
```

Sign in at http://127.0.0.1:8000/admin/ or `/api-auth/login/`. The admin also lets
you add seats for a new movie. Regular users cannot edit the movie catalog.
SQLite stores local data in `db.sqlite3`; this file is intentionally not committed
or packaged. Bootstrap CSS, custom styles, JavaScript, and authored SVG posters
are all local static assets. Once dependencies are installed, the local app
works without an internet connection.

## Pages and API

| URL | Purpose |
| --- | --- |
| `/` | Movie listings and `?q=` title/description search |
| `/movies/<id>/book/` | Authenticated seat picker and booking form |
| `/bookings/` | Signed-in user's ticket history |
| `/accounts/signup/`, `/accounts/login/` | Account creation and sign-in |
| `/admin/` | Staff administration |
| `/api/` | Browsable API index |
| `/health/` | Readiness response after a database query |

| API endpoint | Methods | Access / behavior |
| --- | --- | --- |
| `/api/movies/` | GET, POST | Public read; staff create |
| `/api/movies/<id>/` | GET, PUT, PATCH, DELETE | Public read; staff changes |
| `/api/seats/` | GET | Public availability; filter with `?movie=<id>` |
| `/api/seats/<id>/` | GET | One seat and its booking status |
| `/api/seats/<id>/book/` | POST | Signed-in user reserves that seat |
| `/api/bookings/` | GET, POST | Personal history or create a reservation |
| `/api/bookings/<id>/` | GET, DELETE | Retrieve or cancel one's own booking |

Create a booking with JSON such as `{"movie": 1, "seat": 12}`. The server derives
`user` from authentication; clients cannot book as someone else. Success returns
HTTP 201 with `id`, `movie`, `movie_title`, `seat`, `seat_number`, `user`, and
`booking_date`. Duplicate/invalid seats return HTTP 400, unauthenticated access
returns HTTP 403 with session authentication, and another user's ticket returns
HTTP 404. Cancellation returns HTTP 204. Updating/reassigning an existing
booking is deliberately unsupported; cancel and book again instead.

The browsable API uses the same session as the website. HTML and authenticated
session API writes require CSRF tokens. For a terminal demo, DRF also supports
HTTP Basic authentication; use it only on localhost or HTTPS. The following
command prompts for your password instead of placing it in shell history:

```sh
curl http://127.0.0.1:8000/api/movies/
curl 'http://127.0.0.1:8000/api/seats/?movie=1'
curl -u YOUR_USERNAME -H 'Content-Type: application/json' \
  -d '{"movie":1,"seat":12}' http://127.0.0.1:8000/api/bookings/
curl -u YOUR_USERNAME http://127.0.0.1:8000/api/bookings/
```

## Tests and coverage

With the virtual environment active, run from `homework2/movie_theater_booking`:

```sh
python manage.py collectstatic --noinput
python manage.py test
coverage run manage.py test
coverage report
behave
python manage.py makemigrations --check --dry-run
python manage.py check
```

The unit/integration suite covers model validation and database constraints,
movie CRUD permissions, API status codes/JSON, booking ownership, invalid inputs,
duplicate reservations, cancellation, signup/login/logout, CSRF, HTML errors,
shared API/HTML state, and repeatable sample-data setup. Behave has six scenarios
for movie discovery, HTML booking/API history, duplicate prevention, private
history, cancellation, and anonymous booking rejection. It uses Django's test
clients and a disposable test database, not a browser driver or the local demo DB.

Verified on October 6, 2026:

- 28 Django unit/integration tests passed.
- 6 Behave scenarios / 32 steps passed.
- 99% combined statement/branch coverage of `bookings` (224/225 statements and
  28/28 branches). Tests and generated migrations are excluded. The only
  uncovered statement is the admin's add-booking restriction.
- A fresh virtual environment installed the pinned requirements successfully.
- Render build/start scripts passed locally with `DEBUG=0`, Gunicorn, hashed
  static assets, and an isolated SQLite database.
- Hosted PostgreSQL migrations and sample-data setup passed on Render. The live
  health endpoint, movie API, signup, seat booking, ticket history, cancellation,
  and sign-out were verified. The seat API reflected both booking and cancellation.
- Chrome walkthrough passed: signup, choose B4, book, view history, cancel.
- Movie listings and seat selection fit a 390 CSS-pixel viewport without
  horizontal overflow.

## Render deployment and recreation

The repository-root `render.yaml` defines one free Python web service and one
free PostgreSQL database, both in Oregon. Automatic deployments are disabled.
No CI/CD workflow is included.

The deployed application source is commit `d5b6160` on
`homework2/movie-theater`. Subsequent README-only commits do not change the
running application. Render reported **Deploy succeeded / Live**; the service
uses `chase-cs4300-cinema-db` (PostgreSQL 18). A synthetic `deployment-check`
account was used for the live walkthrough; its test ticket was canceled and
the browser was signed out. No real personal data was used.

To recreate this deployment:

1. Sign in to Render and choose **New > Blueprint**. Select this repository and
   the `homework2/movie-theater` branch (or `main` after the homework PR is merged).
2. Use the repository-root `render.yaml`. Review that both plans are **Free**.
   The blueprint sets the root directory to `homework2`, build command to
   `bash build.sh`, and start command to `bash start.sh`.
3. Render generates `DJANGO_SECRET_KEY` and supplies `DATABASE_URL` from the
   database. `DJANGO_DEBUG=0` and `PYTHON_VERSION=3.13.13` are configured.
   The app reads `RENDER_EXTERNAL_HOSTNAME` for host and CSRF origin settings.
4. Deploy. The build installs the pinned dependencies and collects static files.
   Startup runs migrations, seeds the sample movies/seats, and starts Gunicorn.
5. Open the actual `.onrender.com` URL displayed by Render. Check `/health/`,
   the movie list, signup, booking, history, cancellation, and `/api/movies/`.
   If the new deployment has a different URL, update this README and regenerate
   the source ZIP.

PostgreSQL is necessary on Render because free web-service filesystem changes,
including SQLite databases, are lost on restarts. **Free Render PostgreSQL expires
30 days after creation**, and free web services sleep when idle, so schedule the
deployment to cover grading. See [Render's free-service documentation](https://render.com/docs/free).
The operator created the Render account. This task created the two free
resources from the Blueprint; no paid plan was selected. To stop the app without
deleting its database, suspend the web service in Render. Keep the database
expiration in mind when scheduling grading.

For a manual web-service setup, use the same commands and environment variables
above. If the custom hostname differs, set `DJANGO_ALLOWED_HOSTS` to its hostname
(no scheme). Never commit a secret key or database connection string.

## Project structure

```text
render.yaml                        # Optional Render blueprint, at repo root
homework2/
  README.md
  requirements.txt                 # Pinned runtime and test dependencies
  build.sh / start.sh              # Render build and startup
  movie_theater_booking/
    manage.py
    .coveragerc
    movie_theater_booking/         # Settings, root URLs, WSGI/ASGI
    bookings/
      models.py / migrations/      # Movie, Seat, Booking
      services.py                  # Shared reservation transaction
      api.py / serializers.py      # DRF viewsets and JSON
      views.py / forms.py / urls.py # Django MVT browser flow
      templates/                   # Bootstrap pages and account forms
      static/bookings/             # Local CSS, JS, and original SVG artwork
      management/commands/         # Repeatable seed_demo command
      tests.py                     # Unit and integration tests
    features/                      # Behave scenarios, hooks, and steps
```

## Source ZIP

From the repository root, after committing the current source:

```sh
git archive --format=zip --prefix=cs4300-homework2/ \
  -o cs4300-homework2.zip HEAD homework2 render.yaml AGENTS.md .gitignore
```

This includes source, migrations, tests, templates, static assets, requirements,
and deployment instructions with the verified live URL. It excludes virtual environments, databases, users,
passwords, caches, and generated static files. Rebuild after any later source or URL changes.
Upload to Canvas only when you choose to submit; this work does not submit it.

## AI assistance and references

OpenAI Codex was used to interpret the assignment, design the data model and
interface, generate the Django/DRF implementation, author the fictional movie
copy and SVG artwork, write tests and Behave scenarios, debug failures, prepare
Render configuration, deploy through the operator's Render session, verify the
hosted application, and draft this README. AI-generated code was incorporated
directly and iteratively exercised with automated tests and a Chrome walkthrough.
This disclosure does not imply that a separate human review has occurred.

References used:
- [Assignment PDF](https://tghastings.github.io/cs4300andcs5300/homework_2.pdf)
- [Django 5.2 documentation](https://docs.djangoproject.com/en/5.2/)
- [DRF viewsets](https://www.django-rest-framework.org/api-guide/viewsets/)
- [Bootstrap](https://getbootstrap.com/docs/5.3/getting-started/introduction/)
- [Behave tutorial](https://behave.readthedocs.io/en/stable/tutorial/)
- [Render Django deployment](https://render.com/docs/deploy-django)
- [Render Blueprint reference](https://render.com/docs/blueprint-spec)

Bootstrap remains under its upstream MIT license (included in the vendor folder).
The sample film descriptions and illustrations are fictional demonstration data.
