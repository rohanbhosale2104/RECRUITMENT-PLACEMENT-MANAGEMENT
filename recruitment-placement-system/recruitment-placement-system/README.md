# Recruitment & Placement Management System

Kiran Academy project: UI prototype + MySQL database + connected Flask backend.

```
recruitment-placement-system/
├── app.py                  Flask routes (all 12 screens, validations, transactions)
├── db.py                   MySQL connectivity helpers (parameterized queries, tx())
├── config.py               DB host/user/password (or set DB_* environment variables)
├── requirements.txt
├── templates/ static/      12 pages built from the UI prototype (shared CSS + logo)
├── database/
│   ├── database_schema.sql 17 tables, PK/FK/UNIQUE/CHECK, indexes
│   ├── sample_data.sql     30 candidates, 46 applications, 43 interviews, 11 offers, 7 placements ...
│   ├── reports.sql         required reporting queries + transaction rollback demo
│   ├── data_dictionary.md  generated from the live schema
│   └── er_diagram.md       Mermaid ER diagram
└── ui-prototype/           original static HTML/CSS prototype (no backend)
```

## Run it
1. Install MySQL 8 (or MariaDB 10.5+) and Python 3.10+.
2. Create the database:
   `mysql -u root -p < database/database_schema.sql`
   `mysql -u root -p < database/sample_data.sql`
3. Install packages: `pip install -r requirements.txt`
4. Set credentials (or edit `config.py`):
   - Linux/Mac: `export DB_USER=root DB_PASSWORD=yourpassword`
   - Windows (PowerShell): `$env:DB_USER="root"; $env:DB_PASSWORD="yourpassword"`
5. Start: `python app.py` and open http://127.0.0.1:5000

## Demo logins (password `Demo@123`)
| Username / Email | Role |
|---|---|
| admin / admin@demo.com | Admin |
| priya.d / recruiter@demo.com | Recruiter |
| sanjay.p, meena.k | Recruiter |
| officer / officer@demo.com | Placement Officer |

The role selected on the login screen must match the user's role.

## How the workflow maps to transactions
- Application status change -> update application -> insert application_history
- Interview feedback -> insert feedback -> complete interview -> update application -> history
- Selected -> create offer -> application OFFERED -> history
- Joining -> create/update placement -> candidate PLACED -> application JOINED -> history

Each runs inside `with tx():` in `db.py` (START TRANSACTION / COMMIT, ROLLBACK on error).
Passwords are stored as hashes; all SQL is parameterized; records are never hard-deleted.

## Notes
- `jobs.required_technology` is one column added to the spec's `jobs` table because the UI has a Required Technology field and filter.
- Reports (`/reports`) and the dashboard run live queries; filters on the Reports page apply to the KPI, funnel, company, technology and recruiter blocks.
- Run `database/reports.sql` in MySQL Workbench to execute the required reports directly.
