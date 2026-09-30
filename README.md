# CBSS — Core Banking Security System

A production-grade banking management system with ML-powered fraud detection, customer segmentation, and loan evaluation.

## Architecture

```
CBSS/
├── apps/                          # Flask applications (5 services)
│   ├── admin.py                   # Port 5000 — Admin Dashboard
│   ├── client.py                  # Port 5001 — Client Portal (with fraud detection)
│   ├── hacker.py                  # Port 5002 — Hacker Attack Simulator
│   ├── fraud_detector.py          # Port 5003 — Fraud Detection Service
│   └── simple_transaction.py      # Port 5004 — Simple Transaction Portal
│
├── shared/                        # Shared infrastructure
│   ├── config.py                  # Environment-based configuration (.env)
│   ├── database.py                # Connection pooling + context managers
│   ├── logging_config.py          # Structured logging with service prefixes
│   ├── exceptions.py              # Exception hierarchy (12 subclasses)
│   └── security.py                # Flask app factory + session decorator
│
├── services/                      # ML model services (lazy-loaded)
│   ├── loan_model.py              # Loan approval (Decision Tree)
│   ├── segmentation_model.py      # Customer clustering (KMeans)
│   ├── fraud_model.py             # Fraud detection (Decision Tree)
│   └── attack_model.py            # Attack simulation (Decision Tree)
│
├── templates/                     # Jinja2 templates (organized by domain)
│   ├── admin/                     # Admin pages
│   │   ├── dashboard.html         # Main admin dashboard
│   │   ├── root.html              # Customer management root
│   │   ├── customers.html         # Customer CRUD
│   │   ├── employees.html         # Employee CRUD
│   │   ├── loan.html              # Loan evaluation
│   │   ├── segmentation.html      # Customer segmentation
│   │   └── transactions.html      # Admin transaction history
│   ├── client/                    # Client pages
│   │   ├── dashboard.html         # Client dashboard with charts
│   │   ├── login.html             # Client login
│   │   ├── make_transaction.html  # Create transaction
│   │   ├── transactions.html      # Client transaction history
│   │   └── fraud.html             # Fraud review
│   └── shared/                    # Shared pages
│       └── hacker.html            # Hacker attack simulator
│
├── static/                        # Static assets
│   └── js/
│       └── api.js                 # Centralized API layer
│
├── scripts/                       # Process management
│   ├── start_all.py               # Start all 5 services
│   ├── stop_all.py                # Stop all services
│   ├── health_check.py            # Verify all services running
│   └── seed_data.py               # Insert sample data
│
├── tests/                         # Test suite
│   ├── unit/                      # Unit tests (config, exceptions, security)
│   └── integration/               # Integration tests (all 5 apps)
│
├── data/                          # Data files
│   ├── schema.sql                 # MySQL database schema
│   └── demo_transactions.csv      # ML training data (1000 records)
│
├── legacy/                        # Original files (preserved, not used)
│   ├── app.py                     # Original admin app
│   ├── trans.py                   # Original client app
│   ├── model.py                   # Original hacker simulator
│   ├── FRUAD.py                   # Original fraud detector
│   ├── MAKETRANSCLIENT.py         # Original simple transaction
│   └── ...                        # Other legacy files
│
├── .env                           # Environment configuration
├── .env.example                   # Configuration template
├── .gitignore                     # Git ignore rules
├── requirements.txt               # Python dependencies
└── README.md                      # This file
```

## Quick Start

### Prerequisites
- Python 3.12+
- MySQL running with `cbss` database

### Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Create database schema
mysql -u root -p < data/schema.sql

# 3. Configure environment
cp .env.example .env
# Edit .env with your MySQL password

# 4. Seed sample data
python scripts/seed_data.py

# 5. Start all services
python scripts/start_all.py
```

### Service Ports

| Port | Service | URL |
|------|---------|-----|
| 5000 | Admin Dashboard | http://localhost:5000/admin |
| 5000 | Admin Root | http://localhost:5000/ |
| 5001 | Client Portal | http://localhost:5001/login |
| 5002 | Hacker Simulator | http://localhost:5002/ |
| 5003 | Fraud Detector | http://localhost:5003/hacker |
| 5004 | Simple Transaction | http://localhost:5004/login |

### Login Credentials

| Portal | Username | Password |
|--------|----------|----------|
| Client (port 5001) | Customer ID `1`–`5` | `password123` |
| Admin (port 5000) | No login required | — |

## ML Models

| Model | Training Data | Algorithm | Trigger |
|-------|--------------|-----------|---------|
| Loan Approval | `customers` table | Decision Tree | First prediction |
| Customer Segmentation | `customers` table | KMeans (4 clusters) | First prediction |
| Fraud Detection | `data/demo_transactions.csv` | Decision Tree (balanced) | First prediction |
| Attack Simulation | `data/demo_transactions.csv` | Decision Tree (balanced) | First prediction |

## Management Scripts

```bash
python scripts/start_all.py          # Start all 5 services
python scripts/stop_all.py           # Stop all services
python scripts/health_check.py       # Check service health
python scripts/seed_data.py          # Insert sample data
```

## Testing

```bash
PYTHONPATH=. python -m pytest tests/ -v
```

## Configuration

All configuration is managed via environment variables (`.env` file):

```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=cbss
SECRET_KEY=your-secret-key
DEBUG=false
LOG_LEVEL=INFO
ADMIN_PORT=5000
CLIENT_PORT=5001
HACKER_PORT=5002
FRAUD_DETECTOR_PORT=5003
SIMPLE_TRANSACTION_PORT=5004
```

## API Endpoints

### Admin (Port 5000)

| Method | URL | Description |
|--------|-----|-------------|
| GET | `/admin` | Dashboard |
| GET | `/api/stats` | Dashboard statistics |
| GET | `/api/customers` | List all customers |
| GET | `/api/customers/<id>` | Get customer |
| POST | `/api/customers/add` | Add customer |
| POST | `/api/customers/edit` | Edit customer |
| POST | `/api/customers/delete` | Delete customer |
| POST | `/api/customers/search` | Search customer |
| GET | `/api/employees` | List all employees |
| POST | `/api/employees/add` | Add employee |
| POST | `/api/employees/edit` | Edit employee |
| POST | `/api/employees/delete` | Delete employee |
| POST | `/api/employees/search` | Search employee |
| GET | `/api/transactions` | List all transactions |
| POST | `/api/loan/evaluate` | ML loan prediction |
| POST | `/api/segmentation/predict` | ML segmentation |
| GET | `/api/fraud/pending` | Pending fraud transactions |
| POST | `/api/fraud/decide` | Approve/reject fraud |
| GET | `/health` | Health check |

### Client (Port 5001)

| Method | URL | Description |
|--------|-----|-------------|
| GET/POST | `/login` | Login |
| GET | `/client` | Dashboard |
| GET/POST | `/add` | Make transaction |
| GET | `/show` | Transaction history |
| GET | `/api/transactions` | User transactions (JSON) |
| GET | `/api/customer/info` | Customer info (JSON) |
| GET | `/health` | Health check |
