# TravelGo

Django (site + admin pages, TravelGo design) + FastAPI (`api.py`, JSON for home data) + MySQL.

## Setup
1. `pip install -r requirements.txt`
2. Create DB: `CREATE DATABASE dream_travel CHARACTER SET utf8mb4;`
3. Set env vars (optional): `DB_NAME DB_USER DB_PASSWORD DB_HOST DB_PORT`. For a quick trial use `DB_ENGINE=sqlite`.
4. `python manage.py makemigrations core && python manage.py migrate`
5. `python manage.py createsuperuser` (this is the Admin ID/password) then `python manage.py runserver`
6. Admin panel: http://127.0.0.1:8000/admin/ (add packages, vehicles, hotels; view bookings and payments)
7. FastAPI: `uvicorn api:app --port 8001` -> http://127.0.0.1:8001/docs

## Notes
- Login accepts email or phone. Forgot password prints the reset link to the console (set SMTP in settings for real email).
- Payment is simulated. Replace the marked TODO in `core/views.py::pay` with the real PhonePe / Google Pay gateway.
- Total = amount x members (packages) or amount x days (vehicles, hotels).

## Admin pages (in the site UI)
Log in with the superuser (or any user with `is_staff`) on the normal login page; you land on `/manage/`.
From there: add/edit/delete tour packages, vehicles and hotels (with photo upload), view/filter bookings and change status,
see payments, email customers, and edit your admin profile. Django's `/admin/` still works as a backup.

## Pages (matches the 16-page design)
Login/Register, Home (search), Destination gallery (category filter), Tour packages (filters + search), Package details,
Vehicle preference, Hotel + room types, Booking (date, adults/children, vehicle, hotel, nights), Payment, Confirmation (PDF ticket),
Feedback, User dashboard (sidebar), Admin dashboard, Manage destinations, plus architecture and DB model as in the design.
Not wired: Google/Facebook sign-in buttons (placeholders; needs django-allauth), real payment gateway.
Re-run `makemigrations core` and `migrate` after updating (new models and fields). Delete old migrations/db first if you already migrated.
