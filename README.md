

GiftLedger is a production-grade, full-stack financial monitoring and guest ledger application designed for weddings, receptions, ceremonies, family functions, and community events. It provides tamper-evident financial accounting, physical gift cataloging, cash drawer reconciliation, collector shift tracking, and executive analytics with role-based access control (RBAC).

---

## Architecture & Technology Stack

### Backend
- **Framework**: Python 3.12+ / FastAPI
- **Database**: MongoDB 7.0+ (PyMongo Async engine)
- **Monetary Safety**: Authoritative money stored strictly as `bson.Decimal128` and manipulated via Python `decimal.Decimal` (zero floating-point precision hazards)
- **Security & Cryptography**: Argon2id password hashing, HTTP-only SameSite cookies, CSRF tokens, cryptographic QR verification tokens, request-id tracing, and memory-safe rate limiting
- **Auditability**: Append-only audit trail logging every administrative and financial state transition

### Frontend
- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript (strict type-checking)
- **Styling**: Tailwind CSS
- **Design System**: Inspired by [reactbits.dev](https://reactbits.dev) featuring:
  - **Spotlight Cards**: Cursor-following radial gradient glow
  - **Shiny Text & Buttons**: Shimmering metallic gradients and specular ray animations
  - **Glassmorphism**: Subtle translucent blur with border illumination
  - **Mobile Collector Mode**: Ergonomic mobile interface with quick guest search, fast QR badge lookup, preset quick-amount buttons, and instant voucher receipt generation
  - **Fintech Analytics**: Interactive charts using Recharts for hourly cash inflows and payment mode distributions

---

## Directory Structure

```text
guest-app/
├── docker-compose.yml              # Multi-container orchestration (MongoDB + Backend + Frontend)
├── README.md
│
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI application factory & middleware stack
│   │   ├── api/                    # REST API endpoints (auth, events, guests, transactions,
│   │   │                           # collectors, gifts, reconciliation, reports, audit, users, health)
│   │   ├── core/                   # Security, permissions, database manager, and error handlers
│   │   ├── models/                 # User roles and internal models
│   │   ├── repositories/           # MongoDB atomic repositories & aggregation pipelines
│   │   ├── schemas/                # Strict Pydantic v2 validation models
│   │   └── services/               # Business logic services
│   ├── scripts/
│   │   ├── seed.py                 # Comprehensive development seed script
│   │   ├── create_indexes.py       # MongoDB compound and unique index creation
│   │   └── provision_admin.py      # Bootstrap root administrator
│   ├── tests/                      # Pytest automated test suites
│   ├── Dockerfile
│   └── requirements.txt
│
└── frontend/
    ├── app/
    │   ├── login/                  # High-tech login with quick dev role fill
    │   ├── dashboard/              # Executive KPI metrics & charts
    │   ├── events/                 # Event creation and status management
    │   ├── guests/                 # Guest directory and QR code badge generator
    │   ├── transactions/           # Transaction ledger with verify, reject & lock workflows
    │   ├── collectors/
    │   │   └── mobile/             # High-speed mobile collector terminal
    │   ├── gifts/                  # Physical gift registry and valuation
    │   ├── reconciliation/         # Cash drawer shift count & variance resolution
    │   ├── reports/                # Audited document exports (CSV, XLSX, PDF)
    │   ├── audit-logs/             # Immutable audit trail inspector
    │   └── settings/               # Password rotation and admin user provisioning
    ├── components/
    │   ├── ui/                     # SpotlightCard, ShinyText, ShinyButton, Modal, Badge, QRCodeView
    │   └── layout/                 # Sidebar, Navbar, AppShell
    ├── hooks/                      # useAuth, useToast
    ├── lib/                        # api client, formatters, and utilities
    ├── types/                      # TypeScript definitions matching backend schemas
    └── Dockerfile
```

---

## Quick Start with Docker Compose

To launch the full stack (MongoDB, FastAPI Backend, and Next.js Frontend):

```bash
docker-compose up --build
```

- **Frontend Application**: [http://localhost:3000](http://localhost:3000)
- **FastAPI Backend API**: [http://localhost:8000](http://localhost:8000)
- **API Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **MongoDB**: `localhost:27017`

---

## Local Development Setup

### 1. Backend Setup

```bash
cd backend
python -m venv venv
.\venv\Scripts\activate          # Windows (or source venv/bin/activate on Unix)
pip install -r requirements.txt

# Run MongoDB locally or in Docker
docker run -d -p 27017:27017 --name mongo-dev mongo:7.0

# Initialize indexes & seed development data
python -m scripts.create_indexes
python -m scripts.seed

# Run tests
pytest

# Start FastAPI server
uvicorn app.main:app --reload --port 8000
```

### 2. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

---

## Development Credentials (Generated by `seed.py`)

| Role | Username | Email | Password | Allowed Access |
| :--- | :--- | :--- | :--- | :--- |
| **Admin** | `admin` | `admin@giftledger.dev` | `Admin@GiftLedger123!` | Full system control, verify/lock txns, user management, audit logs, reports |
| **Collector 1** | `collector1` | `collector1@giftledger.dev` | `Collector1@123!` | Mobile terminal, guest scanning, record cash/UPI gifts, submit reconciliation |
| **Collector 2** | `collector2` | `collector2@giftledger.dev` | `Collector2@123!` | Mobile terminal, guest scanning, record cash/UPI gifts, submit reconciliation |
| **Viewer** | `viewer` | `viewer@giftledger.dev` | `Viewer@123!` | Read-only ledger summaries, event statistics, guest contribution history |

---

## Security Safeguards

1. **NoSQL Injection Prevention**: All inputs pass through Pydantic v2 schemas; queries are assembled from sanitized scalar fields without allowing raw operator injection (`$where`, `$regex`, `$gt`).
2. **Broken Object-Level Authorization (BOLA)**: Server-side validation guarantees collectors only access and record contributions for events where they have an active assignment record.
3. **Idempotency Protection**: Transactions require an `Idempotency-Key` header to safely handle mobile network retries without double-charging or double-crediting.
4. **Privacy-Preserving QR Badges**: Guest badges carry an unguessable UUID token (`qr_token`), ensuring no sensitive PII (phone number, address, notes) is exposed in plain text within the QR code.
5. **Locked Financial Records**: Once an administrator locks a transaction, direct modifications are blocked at the repository level; any adjustment requires an audited reversal workflow.

---

## License
MIT License. Built with ❤️ for secure event ledger accounting.
