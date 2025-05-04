# 🏷️ Auction API - Backend Assessment

This is a Django REST Framework (DRF) based RESTful API for a simple Auction System. It supports user registration, auction listing, bidding, and admin functionalities.

---

## 🚀 Features

- User Registration & Authentication (JWT)
- Create and manage Auctions
- Bid on live auctions
- Admin controls for managing auctions and bids
- Secure endpoints
- Unit tests and Swagger API documentation

---

## 🛠️ Tech Stack

- asgiref==3.8.1
- Django==5.2
- djangorestframework==3.16.0
- djangorestframework_simplejwt==5.5.0
- drf-yasg==1.21.10
- inflection==0.5.1
- packaging==25.0
- PyJWT==2.9.0
- pytz==2025.2
- PyYAML==6.0.2
- sqlparse==0.5.3
- uritemplate==4.1.1

---

## 📦 Project Setup Instructions

```bash
### 1. Clone the repository
git clone https://github.com/william-4/backend-engineer-assessment/tree/main/backend-assessment
cd backend-assessment

### 2. Create a virtual environment and activate it
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`

### 3. Install dependencies
pip install -r requirements.txt

### 4. Apply database migrations
python manage.py makemigrations
python manage.py migrate

### 5. Create a superuser for admin access
python manage.py createsuperuser

### 6. Run the development server
python manage.py runserver

### 7. Access the API
- Swagger UI: http://127.0.0.1:8000/swagger/

### 8. Run tests
python manage.py test
```

---

