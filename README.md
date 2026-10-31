# White Leaf — Django project

Your static HTML pages and admin pages converted to Django (server-rendered, no REST API).

## First run (Windows)

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
copy .env.example .env
python manage.py migrate
python manage.py seed_whiteleaf        # loads starter content (safe to re-run)
python manage.py createsuperuser       # your admin login
python manage.py runserver
```

- Website: http://127.0.0.1:8000/
- Your dashboard: http://127.0.0.1:8000/manage/
- Django's built-in admin (backup): http://127.0.0.1:8000/backstage-x7k2/  <- change this in `config/urls.py`

## URLs

| URL | Page |
|---|---|
| `/` | Home |
| `/accommodations/` (`?category=room|suite|apartment`, `?page=2`) | Room list |
| `/accommodations/<slug>/` | Room details |
| `/tariffs/` | Tariffs |
| `/about/` | About |
| `/contact/` | Contact + review form |
| `/reviews/submit/` | Review form POST (JSON) |
| `/manage/` | Dashboard (staff only) |

## Already in your existing project?

Copy the apps (`core rooms tariffs reviews cms`), `templates/`, `static/`, then merge `config/settings.py`
(INSTALLED_APPS, MIDDLEWARE, the `core.context_processors.site` context processor, axes, media/static)
and `config/urls.py`.

## Notes

- Placeholder room photos are Unsplash links so the site looks complete. Upload real photos in
  Dashboard > Rooms, then delete the link rows.
- The 3 seeded reviews are your sample text. Delete them in Dashboard > Reviews.
- Suites (Orchid, Cinta, Marina, Palm) are not seeded because their prices aren't in your files.
  Add them in Dashboard > Rooms with category "Suites".
- Tailwind still loads from the CDN. Before launch, move to `django-tailwind-cli`.
- Uploaded files go to `media/`. If your host wipes the disk on deploy, use cloud storage.
