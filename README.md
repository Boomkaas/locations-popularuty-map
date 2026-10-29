# Locations Popularity Map

REST API for a service where users add interesting places, leave reviews and see the most popular locations on a map.

## Stack

Python 3.12, Django 5.2, Django REST Framework, django-filter, PostgreSQL 16, Redis 7, Celery, pandas, drf-spectacular, pytest, Docker Compose.

## Architecture

The project has five Django apps in `apps/`:

| App | What it does |
|---|---|
| `users` | registration, login, logout, password reset |
| `categories` | categories CRUD |
| `locations` | locations CRUD, soft delete, rating and popularity, views, cache, export |
| `reviews` | reviews and Like/Dislike |
| `subscriptions` | subscriptions to locations and email notifications |

Views stay thin. Business logic lives in `services.py`, complex queries live in the custom QuerySet (`Location.objects.with_stats()`).

Docker Compose runs five services:

| Service | Purpose |
|---|---|
| `web` | Django API on Gunicorn, port 8000 |
| `db` | PostgreSQL |
| `redis` | cache, view keys and Celery broker |
| `worker` | Celery worker that sends emails |
| `mailpit` | catches all emails in development, web UI on port 8025 |

## Quick start

```bash
cp .env.example .env
docker compose up --build
```

Migrations run automatically when the `web` container starts. In another terminal:

```bash
docker compose exec web python manage.py seed_data
docker compose exec web python manage.py createsuperuser
```

Change `SECRET_KEY` in `.env` before using the project anywhere except your machine.

## Links

| What | URL |
|---|---|
| Swagger | http://localhost:8000/api/docs/ |
| OpenAPI schema | http://localhost:8000/api/schema/ |
| Admin | http://localhost:8000/admin/ |
| Mailpit | http://localhost:8025/ |

## Demo data

`python manage.py seed_data` creates 5 users, 5 categories, 30 locations in 6 Ukrainian cities, reviews and views for the last 10 days. Running it again does not create duplicates.

Demo users: `olena`, `taras`, `maria`, `andrii`, `iryna`. Password for all of them: `DemoPass123!`

## Authentication

The API uses Django sessions and cookies, without JWT. The client works like this:

1. `GET /api/v1/auth/csrf/` sets the `csrftoken` cookie.
2. `POST /api/v1/auth/login/` with the `X-CSRFToken` header sets the `sessionid` cookie.
3. Every `POST`, `PUT`, `PATCH` and `DELETE` sends the cookies and the `X-CSRFToken` header.

Django changes the CSRF token after login, so read it from the cookie again.

```bash
curl -c cookies.txt http://localhost:8000/api/v1/auth/csrf/

CSRF=$(grep csrftoken cookies.txt | awk '{print $7}')
curl -b cookies.txt -c cookies.txt -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" -H "X-CSRFToken: $CSRF" \
  -d '{"username": "olena", "password": "DemoPass123!"}'

CSRF=$(grep csrftoken cookies.txt | awk '{print $7}')
curl -b cookies.txt -X POST http://localhost:8000/api/v1/locations/ \
  -H "Content-Type: application/json" -H "X-CSRFToken: $CSRF" \
  -d '{"title": "Shevchenko Park", "description": "Central park", "category": 1, "address": "Kyiv", "latitude": "50.4419", "longitude": "30.5133"}'
```

With `SessionAuthentication` an unauthorized request gets `403`, not `401`.

Password reset: `POST /api/v1/auth/password-reset/` always returns `200`, so nobody can find out which emails are registered. The email (see Mailpit) contains `uid` and `token`. Send them with the new password to `POST /api/v1/auth/password-reset/confirm/`. There is no frontend, so the email does not contain a link.

## Endpoints

| Method | URL | Access |
|---|---|---|
| GET | `/api/v1/auth/csrf/` | everyone |
| POST | `/api/v1/auth/register/`, `/api/v1/auth/login/` | everyone |
| POST | `/api/v1/auth/logout/` | logged in |
| GET | `/api/v1/auth/me/` | logged in |
| POST | `/api/v1/auth/password-reset/`, `/api/v1/auth/password-reset/confirm/` | everyone |
| GET | `/api/v1/categories/`, `/api/v1/categories/{id}/` | everyone |
| POST, PUT, PATCH, DELETE | `/api/v1/categories/...` | admin |
| GET | `/api/v1/locations/`, `/api/v1/locations/{id}/` | everyone |
| GET | `/api/v1/locations/map/`, `/api/v1/locations/popular/` | everyone |
| GET | `/api/v1/locations/export/?export_format=csv` or `json` | everyone |
| POST | `/api/v1/locations/` | logged in |
| PUT, PATCH, DELETE | `/api/v1/locations/{id}/` | author or admin |
| GET, POST | `/api/v1/locations/{id}/reviews/` | read: everyone, create: logged in |
| GET, PATCH, DELETE | `/api/v1/reviews/{id}/` | read: everyone, change: author or admin |
| POST, DELETE | `/api/v1/reviews/{id}/reaction/` | logged in |
| POST, DELETE | `/api/v1/locations/{id}/subscribe/` | logged in |
| GET | `/api/v1/subscriptions/` | logged in |

### Search, filters and ordering

The locations list, the map and the export accept the same parameters, and they can be combined:

| Parameter | Example | What it does |
|---|---|---|
| `search` | `?search=park` | search in title and description |
| `category` | `?category=3` | category id |
| `category_slug` | `?category_slug=parks` | category slug |
| `author` | `?author=7` | author id |
| `author_username` | `?author_username=olena` | author username, case does not matter |
| `min_rating`, `max_rating` | `?min_rating=4` | average rating range |
| `lat_min`, `lat_max`, `lng_min`, `lng_max` | `?lat_min=50&lat_max=51` | visible area of the map |
| `ordering` | `?ordering=-popularity` | `created_at`, `rating`, `popularity`, `reviews_count`, minus for descending |
| `page`, `page_size` | `?page=2&page_size=50` | pagination, 20 by default, 100 at most |

## Rating and popularity

Nothing is stored in the database. Rating, reviews count, views for the last 7 days and popularity are calculated by the ORM in one query (`with_stats()`), each value in its own subquery so the counts are not multiplied by joins.

```
popularity = 2.0 * rating + 1.5 * ln(1 + reviews_count) + 1.0 * ln(1 + views_last_7d)
```

`rating` is the average review score, or 0 when there are no reviews. The logarithm keeps big numbers in check: a thousand views do not beat good reviews, and one 5-star review does not beat dozens of good ones.

| Example | Rating | Reviews | Views for 7 days | Popularity |
|---|---|---|---|---|
| Popular park | 4.5 | 10 | 100 | 17.21 |
| New cafe with one review | 5.0 | 1 | 3 | 12.43 |

The weights are in `POPULARITY_WEIGHTS` in `config/settings/base.py`.

## Decisions

- **Categories** can be changed only by an admin. The task does not say who manages them.
- **Soft delete.** `DELETE` on a location only marks it as deleted. It disappears from the list, details, map, export and its reviews. The admin shows deleted locations and can restore them. A category that still has locations, even deleted ones, cannot be deleted (`409`).
- **Duplicates** return `409 Conflict`: a second review of the same location (`review_already_exists`) and a second vote on the same review (`reaction_already_exists`). A vote can be withdrawn with `DELETE` and given again.
- **Views** are counted when the location details are opened, once per hour for one viewer. A logged in user is recognized by id, an anonymous visitor by a hash of IP and User-Agent, so clearing cookies does not add views. Redis blocks repeats (`SET NX` with a 1 hour TTL), and every counted view is saved in the database with its date. `python manage.py cleanup_views --days 30` deletes old views. If Redis is down, the API keeps working and views are just not counted.
- **Cache.** The locations list is cached in Redis for 5 minutes. The key contains a version number and the sorted query parameters. Any change of a location, review or category bumps the version after the database commit. New views do not clear the cache, so `popularity` and `views_last_7d` in the list can be up to 5 minutes old. The details page is not cached.
- **Export** uses the `export_format` parameter, because DRF already uses `format`. CSV has a BOM so Excel shows Cyrillic correctly. One export returns at most 10 000 rows.
- **Emails** about new reviews are sent by the Celery worker after the database commit, so creating a review does not wait for SMTP. The location author and all subscribers get an email, the reviewer does not. Failed emails are retried up to 3 times.

## Tests

```bash
docker compose run --rm web pytest
docker compose run --rm web pytest --cov=apps
```

57 API tests cover authentication, categories, locations, soft delete, reviews, likes, rating and popularity, views, filters, cache, export and subscriptions. Coverage is 92%.
