# Library Reservations App

A Django-based library reservation system that manages book reservations with automatic queue management and expiration handling.

## Features

- **Member Management**: Add and manage library members
- **Book Catalog**: Maintain book inventory with availability tracking
- **Reservation System**: Queue-based reservations with automatic promotion
- **Admin Interface**: Comprehensive admin panel with inline reservations
- **Background Jobs**: Management command for handling expired reservations
- **REST API**: Simple API endpoints for listing available books

## Models

- **Member**: Library members with contact information
- **Book**: Book catalog with availability status
- **Reservation**: Reservation tracking with status (queued/ready/cancelled)

## Business Rules

- Only one active "ready" reservation per book
- When a book is returned, the oldest queued reservation becomes ready
- Expired reservations auto-cancel and free the book
- Reservations expire after 7 days by default

## Setup

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd library_reservations
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run migrations**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

5. **Create superuser**
   ```bash
   python manage.py createsuperuser
   ```

6. **Run the development server**
   ```bash
   python manage.py runserver
   ```

## Usage

### Admin Interface
- Access at `http://localhost:8000/admin/`
- Manage members, books, and reservations
- Use "Mark book as returned" action to return books
- View inline reservations under each member

### Management Command
Run the expiration management command:
```bash
python manage.py expire_reservations
```

**Options:**
- `--dry-run`: Show what would be done without making changes

**Example:**
```bash
# Run normally
python manage.py expire_reservations

# Preview changes
python manage.py expire_reservations --dry-run
```

### API Endpoints
- `GET /api/books/` - List all books
- `GET /api/books/available/` - List only available books
- `GET /api/reservations/` - List all reservations

## Testing

Run the test suite:
```bash
python manage.py test
```

## Project Structure

```
db.sqlite3
Dockerfile
docker-compose.yml
Improvements.txt
manage.py
README.md
requirements.txt
library_reservations/
    __init__.py
    asgi.py
    settings.py
    urls.py
    wsgi.py
    __pycache__/
reservations/
    __init__.py
    admin.py
    apps.py
    models.py
    serializers.py
    tests.py
    urls.py
    views.py
    management/
        __init__.py
        commands/
            expire_reservations.py
            __init__.py
    migrations/
        __init__.py
        0001_initial.py
```
