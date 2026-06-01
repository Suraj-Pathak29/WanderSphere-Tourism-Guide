# 🌍 WanderSphere — AI-Powered Tourism Guide System

> BCA Final Year Project | KCC Institute of Legal & Higher Education (GGSIPU)

A full-stack web application that delivers personalised travel destination 
recommendations using a Hybrid Machine Learning Recommendation Engine.

---

## 🧠 ML Architecture

| Component | Technique | Weight |
|---|---|---|
| Content-Based Filtering | TF-IDF + Cosine Similarity (9-dim feature vectors) | 60% |
| Collaborative Filtering | Truncated SVD (scipy, k=20) | 40% |
| **Hybrid Score** | `0.6 × content + 0.4 × collaborative` | — |

---

## ✨ Key Features

- **Hybrid Recommendation Dashboard** — Top-10 personalised picks with match %
- **Interactive Leaflet.js Map** — 560 destinations with ATM/washroom/hospital overlays
- **Season-aware Safety Guide** — Auto Safe/Risky classification from temperature data
- **AJAX 5-Star Rating System** — Background SVD rebuild after every rating
- **One-command Dataset Pipeline** — Full CSV import + matrix build in ~15 seconds

---

## 🛠️ Tech Stack
Backend   : Python 3.11, Django 4.2
Database  : SQLite3 (Django ORM)
ML        : scikit-learn (TF-IDF, cosine_similarity), scipy (svds), pandas, numpy
Frontend  : Bootstrap 5, Leaflet.js, Chart.js
Auth      : Django AbstractUser with 9-dimension preference profiling

---

## 🚀 Quick Start


# 1. Clone the repository
git clone https://github.com/Suraj-Pathak29/WanderSphere-Tourism-Guide.git
cd wandersphere

# 2. Create and activate virtual environment
python -m venv venv
source venv/bin/activate        # Mac/Linux
venv\Scripts\activate           # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run migrations
python manage.py makemigrations accounts destinations ratings safety
python manage.py migrate

# 5. Import dataset and build ML matrices
python scripts/preprocess_dataset.py --csv path/to/destinations_.csv

# 6. Create admin account
python manage.py createsuperuser

# 7. Start the server
python manage.py runserver


Visit http://127.0.0.1:8000

---

## 📁 Project Structure
tourism_guide/
-├── accounts/          ← Custom user model with 9 interest dimensions
-├── destinations/      ← Destination & Utility models, map view
-├── recommendations/   ← Hybrid ML engine (engine.py)
-├── ratings/           ← AJAX rating system + background SVD rebuild
-├── safety/            ← Season-aware safety classification
-├── scripts/           ← Dataset preprocessing pipeline
-├── templates/         ← Bootstrap 5 HTML templates
-└── static/            ← CSS & JS

---

## 👤 Author

**Suraj Pathak** — BCA, KCC Institute (GGSIPU)  
[LinkedIn](linkedin.com/in/suraj-pathak-1b6575351) · [GitHub](https://github.com/Suraj-Pathak29)