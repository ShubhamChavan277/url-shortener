# URL Shortener API

A backend URL shortener built with FastAPI, PostgreSQL, and Redis. It supports user authentication, short URL creation, redirects, URL expiration, click analytics, rate limiting, and caching.

## Features

- **User authentication:** Register and log in using email and password.
- **URL shortening:** Create short URLs from original URLs.
- **URL management:** View and delete your own short URLs.
- **URL redirects:** Redirect visitors to the original URL using a short code.
- **URL expiration:** Set an expiration date and time for a short URL.
- **Click analytics:** View the click count for your short URLs.
- **JWT authentication:** Protect endpoints that require a logged-in user.
- **Redis caching:** Cache eligible short URL data to reduce database lookups.
- **Rate limiting:** Limit requests by IP address and, for URL creation, by authenticated user.
- **Logging:** Record application events and errors.
- **Database migrations:** Manage database schema changes using Alembic.
- **Automated tests:** Test application features using pytest.
- **Docker Compose:** Run the application, PostgreSQL, and Redis as separate services.

## Technology Stack

- Python 3.13
- FastAPI
- PostgreSQL
- SQLAlchemy
- Alembic
- Redis
- JWT authentication
- Docker and Docker Compose
- pytest

## Database Schema

The application uses the following main database tables:

| Table | Important columns |
|---|---|
| `users` | `id` (primary key), `email` (required and unique), `password_hash` (required), `created_at` (required, defaults to the current time) |
| `urls` | `id` (primary key), `original_url` (required), `short_code` (required and unique), `user_id` (required foreign key to `users.id`), `created_at` (required, defaults to the current time), `expires_at` (optional) |
| `url_clicks` | `id` (primary key), `url_id` (required foreign key to `urls.id`), `clicked_at` (required, defaults to the current time) |

A user can own multiple short URLs. Each short URL belongs to a user, and its click records are associated with that URL to support click analytics. Foreign keys maintain these relationships, while indexes support uniqueness and lookups.

Alembic manages database schema changes through migration files. These migrations create or update the database structure as the project changes.

## Requirements

Choose one of the following setup options.

**Option 1 — Docker Compose**

- Docker Desktop with Docker Compose
- Git, if cloning the project repository

**Option 2 — Local Python Environment with Redis in Docker**

- Python 3.13
- PostgreSQL installed and running locally
- Docker Desktop with Docker Compose, to run Redis in a dedicated container
- Git, if cloning the project repository

## Setup Option 1: Docker Compose (Recommended)

Docker Compose runs the API, PostgreSQL, and Redis in separate containers. This is the recommended option for setting up the project on a new machine.

### 1. Open the project

Clone the repository using its Git URL, then open PowerShell in the project root. If the project is already on your machine, open PowerShell in its existing root directory.

Make sure Docker Desktop is running.

### 2. Create the `.env` file

Create a file named `.env` in the project root, next to `docker-compose.yml`.

Add the following variables:

```dotenv
DATABASE_URL=postgresql+psycopg://url_shortener:url_shortener_password@db:5432/url_shortener
JWT_SECRET_KEY=<generated-secret>
REDIS_URL=redis://redis:6379/0
```

Generate a secure, random JWT secret by running this command in PowerShell:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Copy the generated output and replace `<generated-secret>` with that value in your `.env` file. Use a new, unique secret for each deployment.

**Note:** The `DATABASE_URL` and `REDIS_URL` values use the Docker Compose service names `db` and `redis`. Keep these URLs as shown when using the supplied Compose configuration. The `JWT_SECRET_KEY` value is read from `.env`.

Do not commit your actual `.env` file to Git or share your JWT secret.

The database credentials in the supplied Compose configuration are intended for local development and demonstration. They should be changed before any real production deployment.

### 3. Build and start the services

Run:

```powershell
docker compose up --build -d
```

This builds the API image and starts the application, PostgreSQL, and Redis containers.

### 4. Apply database migrations

Run:

```powershell
docker compose exec app alembic upgrade head
```

This applies the available database migrations. Migrations are not automatically applied when the container starts, so run this command during the initial setup and whenever new migrations need to be applied.

### 5. Check the services

Run:

```powershell
docker compose ps
```

Check the API health endpoint in PowerShell:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

A successful health check displays output similar to:

```text
status
------
ok
```

When you open `http://127.0.0.1:8000/health` directly in a browser, the response appears as JSON:

```json
{
  "status": "ok"
}
```

The health endpoint confirms that the API process is responding. It does not verify that PostgreSQL and Redis are fully operational.

### 6. Open the API documentation

Open the following URL in your browser:

[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

Swagger UI lets you explore the API and send requests to its endpoints.

### Useful Docker Compose commands

View application logs:

```powershell
docker compose logs -f app
```

Stop the services:

```powershell
docker compose down
```

The PostgreSQL data is stored in a Docker volume. The normal `docker compose down` command preserves that volume. Avoid using `docker compose down -v` unless you intentionally want to remove the Compose volumes and their stored database data.

## Setup Option 2: Local Python Environment

Use this option if you want to run FastAPI and PostgreSQL directly on your machine while running Redis in a dedicated Docker container.

### 1. Prepare PostgreSQL and Redis

Install and start PostgreSQL locally.

Create a PostgreSQL database and user for the project. Make sure the database name, username, password, host, and port match your `DATABASE_URL`.

For a typical local setup, PostgreSQL uses port `5432` and Redis uses port `6379`.

You do not need to install Redis directly on Windows. Instead, start the dedicated Redis container using Docker Compose:

```powershell
docker compose up -d redis
```

This starts the Redis service defined in `docker-compose.yml` without starting the API or PostgreSQL Compose services.

Verify that Redis is responding:

```powershell
docker compose exec redis redis-cli ping
```

The expected output is:

```text
PONG
```

Because the supplied Compose configuration exposes Redis on `127.0.0.1:6379`, the locally running FastAPI application can connect to it through `localhost`.

### 2. Create and activate a virtual environment

From the project root, run:

```powershell
py -3.13 -m venv .venv
```

Activate the environment:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 3. Install the dependencies

Upgrade pip:

```powershell
python -m pip install --upgrade pip
```

Install the project dependencies:

```powershell
python -m pip install -r requirements.txt
```

### 4. Create the `.env` file

Create a `.env` file in the project root with the following variables:

```dotenv
DATABASE_URL=postgresql+psycopg://<user>:<password>@localhost:5432/<database>
JWT_SECRET_KEY=<generated-secret>
REDIS_URL=redis://localhost:6379/0
```

Replace `<user>`, `<password>`, and `<database>` with the credentials and database name for your local PostgreSQL setup.

Generate the JWT secret using the same PowerShell command shown in the Docker Compose setup:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Copy the generated output and replace `<generated-secret>` with that value. Keep the `.env` file private and do not commit it to Git.

**Note:** The local `DATABASE_URL` uses `localhost` because PostgreSQL runs on your machine. The `REDIS_URL` also uses `localhost` because Redis runs in Docker with its port published to your machine. These URLs differ from the Docker Compose URLs, which use the service names `db` and `redis`.

Other settings, such as the environment, JWT configuration, rate limits, logging level, and cache TTL, have default values in the application configuration and can be overridden through environment variables when needed.

### 5. Apply database migrations

Run:

```powershell
python -m alembic upgrade head
```

This creates or updates the database schema using the project's Alembic migrations.

### 6. Start the application

Run:

```powershell
python -m uvicorn app.main:app --reload
```

The API will be available at:

- API documentation: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- Health check: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

The `--reload` option automatically restarts the development server when application code changes.

## API Endpoints

The following table lists the main API endpoints.

| Method | Endpoint | Purpose | Authentication |
|---|---|---|---|
| POST | `/api/v1/auth/register` | Register a new user | No |
| POST | `/api/v1/auth/login` | Log in and obtain an access token | No |
| POST | `/api/v1/urls` | Create a short URL | Yes |
| GET | `/api/v1/urls` | List your short URLs | Yes |
| DELETE | `/api/v1/urls/{short_code}` | Delete your short URL | Yes |
| GET | `/api/v1/urls/{short_code}/stats` | View click statistics | Yes |
| GET | `/{short_code}` | Redirect to the original URL | No |
| GET | `/health` | Check API health | No |

The API documentation at `/docs` provides request schemas, response details, and interactive endpoint testing.

## Authentication

Registration creates a user account. Login uses an email address and password and returns an access token.

To test protected endpoints in Swagger UI:

1. Open `/docs`.
2. Register a user using `/api/v1/auth/register`.
3. If you want to test login separately, submit the credentials to `/api/v1/auth/login`.
4. Click **Authorize** in Swagger UI and enter the login credentials when prompted. Enter the email address in the `username` field and the password in the `password` field.
5. Use the protected endpoints.

The separate login request in step 3 is optional when using Swagger's **Authorize** dialog. The dialog can submit the credentials to the configured login endpoint and obtain the access token itself.

Swagger UI manages the bearer token for authorized requests. You do not need to copy and manually enter the access token for every request.

The access token expires after the configured period, which defaults to 30 minutes. After expiration, click **Logout** in the authorization dialog, then click **Authorize** and enter your credentials again to obtain a new token.

### Example: User Ownership and Access Control

You can verify that users can access only their own short URLs using two different accounts.

1. Register two users, Alice and Bob, using different email addresses.
2. Authorize Alice in Swagger UI and create a short URL.
3. Call `GET /api/v1/urls` as Alice. Her short URL should appear in the response.
4. Click **Logout** in Swagger's authorization dialog, then authorize Bob.
5. Call `GET /api/v1/urls` as Bob. Alice's short URL should not appear.
6. While authorized as Bob, try to delete Alice's short URL or view its statistics. The API should return `404 Not Found`.

This demonstrates that URL listing, deletion, and statistics are restricted to the authenticated owner's resources.

## URL Expiration

When creating a short URL, you can provide an optional `expires_at` timestamp. It must represent a future date and time.

Example request body:

```json
{
  "original_url": "https://example.com/",
  "expires_at": "2026-10-20T18:30:00+05:30"
}
```

The `expires_at` value uses an ISO 8601 timestamp with a timezone offset. In this example, `+05:30` represents the offset from UTC used in India.

If the expiration time is omitted or set to `null`, the URL has no configured expiration time.

An expired short URL returns `410 Gone`. A short code that does not exist returns `404 Not Found`.

## Redirect Behavior

The public redirect endpoint is:

```http
GET /{short_code}
```

For a valid short URL, the API returns an HTTP `307 Temporary Redirect` response with a `Location` header pointing to the original URL.

### How to test a redirect in your browser

1. Create a short URL using `POST /api/v1/urls` in Swagger UI and note the short code returned by the API.
2. Open your browser and enter the following address, replacing `<short_code>` with the actual code returned by the API:

   ```text
   http://localhost:8000/<short_code>
   ```

3. For example, if the returned short code is `abc123`, open:

   ```text
   http://localhost:8000/abc123
   ```

4. The browser requests the short URL, receives the HTTP `307 Temporary Redirect` response, reads the original URL from the `Location` header, and navigates to that original URL.

**Note:** Swagger UI may display `Failed to fetch` or a CORS-related message when testing the public redirect endpoint (`GET /{short_code}`). This does not necessarily mean the redirect failed. Verify the HTTP `307` response, the `Location` header, or the application logs to confirm the redirect.

## Redis Caching

Redis is used for short URL caching and rate limiting.

The redirect flow uses a cache-aside approach:

1. A request arrives for a short code.
2. The API checks the rate limit.
3. The API checks Redis for cached short URL data.
4. On a cache hit, it uses the cached data.
5. On a cache miss, it looks up the short URL in PostgreSQL and caches eligible results.
6. The API records the click and returns the redirect response.

The default cache TTL is 3,600 seconds (one hour). URLs with an expiration time are not cached. Deleting a short URL invalidates its cached entry.

The cache layer handles certain Redis read and write failures by falling back to database lookup or continuing without caching. However, Redis is also used for rate limiting. If Redis is unavailable, rate-limited requests return `503 Service Unavailable`, including redirect requests. Therefore, cache fallback alone does not guarantee that redirects remain available during a Redis outage.

## Rate Limiting

The application uses Redis to track request counts within fixed time windows. Each endpoint scope has its own counter for each IP address; requests to one endpoint do not consume the IP-based allowance for another endpoint.

| Endpoint or scope | Limit | Window |
|---|---|---|
| Registration: `POST /api/v1/auth/register` | 60 requests per IP | 60 seconds |
| Login: `POST /api/v1/auth/login` | 60 requests per IP | 60 seconds |
| Public redirect: `GET /{short_code}` | 60 requests per IP | 60 seconds |
| URL creation: `POST /api/v1/urls` — IP limit | 50 requests per IP | 60 seconds |
| URL creation: `POST /api/v1/urls` — user limit | 10 requests per authenticated user | 60 seconds |

The registration, login, and redirect limits are separate. For example, login requests do not consume the registration or redirect allowance for the same IP address.

For URL creation, **both limits are checked**. A request is rejected with `429 Too Many Requests` if either limit is exceeded.

- The IP limit is shared by users sending requests from the same IP address within the URL-creation scope.
- The user limit is tracked independently for each authenticated user.
- The redirect rate limit is checked before the cache lookup.
- Requests that reach the rate-limit check count toward the limit even if they subsequently fail validation or authentication. For example, unsuccessful login attempts also count toward the login limit.
- A rejected request includes a `Retry-After` header indicating the number of seconds remaining in the rate-limit window. The value is calculated from Redis's remaining key lifetime and is never negative.
- If Redis is unavailable while the application checks rate limits, the request returns `503 Service Unavailable`.

The `429` response and `Retry-After` header have been verified manually in Swagger UI. During testing, a temporary limit of two registration requests per IP was configured. The first two registration requests succeeded, and the third returned `429` with `Retry-After: 17`. The temporary setting was subsequently removed and the normal configuration was restored. Under the default configuration, registration, login, and redirects each have a limit of 60 requests per IP per 60 seconds, while URL creation retains its separate limits of 50 requests per IP and 10 requests per authenticated user per 60 seconds. The observed value of `17` is an example; the value can vary depending on when a request is made.

These limits are configurable through the application settings and can be overridden using environment variables.

## Running the Tests

Activate the local virtual environment if it is not already active, then run:

```powershell
python -m pytest -q
```

The last verified test run completed with **40 passed tests** and two dependency deprecation warnings. Results may differ after code or dependency changes.

## Database Migrations

Alembic manages database schema changes.

For local Python execution:

```powershell
python -m alembic upgrade head
```

For Docker Compose execution:

```powershell
docker compose exec app alembic upgrade head
```

Run the appropriate migration command after setting up the database and whenever the project introduces new migrations.

## Project Structure

```text
url-shortener/
├── alembic/                # Database migration files
├── app/
│   ├── api/                # API endpoints
│   ├── core/               # Configuration, security, logging, rate limiting
│   ├── db/                 # Database setup and base model
│   ├── models/             # Database models
│   ├── schemas/             # Request and response schemas
│   ├── services/            # Business logic, URL operations, caching
│   └── main.py             # FastAPI application entry point
├── tests/                  # Automated tests
├── .dockerignore
├── .gitignore
├── alembic.ini
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── README.md
```

## Security Notes

- Never commit `.env` or expose your JWT secret.
- Use a strong, unique JWT secret for each deployment.
- The database credentials in the supplied Docker Compose configuration are for local development and demonstration, not public production use.
- Before deploying publicly, review database credentials, secret management, network exposure, and other production security settings.

## Current Limitations and Future Work

- **AWS deployment and cloud infrastructure:** Deploy the API and supporting services to AWS.
- **CI/CD automation:** Automate code checks, tests, and deployments.
- **Monitoring, metrics, and alerting:** Track application health and detect failures.
- **Improved graceful handling of database and Redis outages:** Improve application behavior when dependencies are unavailable.
- **Additional security hardening and production deployment checks:** Review and strengthen settings before a real-world deployment.
- **Frontend for URL management:** Build a user interface for creating, viewing, and deleting short URLs.
