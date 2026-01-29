# User Profile Module - Implementation Plan

## 📋 Overview

Implementation of User Profile persistence to save user fiscal preferences and auto-fill calculator form on subsequent visits.

**Feature:** User Profile (Persistence of preferences)  
**Status:** In Planning  
**Start Date:** January 24, 2026

---

## 🎯 Requirements & Decisions

### Functional Requirements

- ✅ Save user fiscal data (income, deductions, etc.)
- ✅ Auto-fill calculator form on login if profile exists
- ✅ Require explicit user consent (checkbox opt-in)
- ✅ Only save last profile (no historical records)
- ✅ One profile per user (no multi-profile support)
- ✅ Remove field "taxpayer_name" from form only for users with saved profile

### Technical Decisions

- **Database:** PostgreSQL (production), SQLite (tests)
- **Migrations:** Alembic + SQLAlchemy (new dependency)
- **Architecture:** New bounded context `user_profile/` with hexagonal layers
- **Authentication:** Integrate with existing OAuth (`get_current_user` dependency)
- **API Pattern:** REST endpoints following existing conventions

---

## 📐 Architecture

### Module Structure

```
src/user_profile/
├── domain/
│   ├── __init__.py
│   ├── entities/
│   │   ├── __init__.py
│   │   └── user_profile.py          # UserProfile entity with validation
│   ├── value_objects/
│   │   ├── __init__.py
│   │   └── fiscal_preferences.py    # FiscalPreferences value object
│   └── ports/
│       ├── __init__.py
│       └── user_profile_repository.py  # Repository interface (ABC)
├── application/
│   ├── __init__.py
│   ├── get_user_profile_use_case.py
│   ├── save_user_profile_use_case.py
│   └── delete_user_profile_use_case.py
└── infrastructure/
    ├── __init__.py
    ├── api/
    │   ├── __init__.py
    │   └── profile_router.py         # REST API endpoints
    └── persistence/
        ├── __init__.py
        └── postgres_profile_repository.py  # PostgreSQL implementation
```

### Alembic Migration Structure

```
alembic/
├── versions/
│   └── 001_create_user_profiles_table.py
├── env.py
├── script.py.mako
└── alembic.ini
```

---

## 🗃️ Database Schema

### Table: `user_profiles`

```sql
CREATE TABLE user_profiles (
    user_id TEXT PRIMARY KEY,              -- Google OAuth sub or email

    -- Fiscal preferences
    fiscal_year INTEGER NOT NULL,
    monthly_gross_income NUMERIC(10,2),
    monthly_net_income NUMERIC(10,2),
    bonus_days INTEGER,
    vacation_days INTEGER,
    vacation_premium_cap NUMERIC(10,2),

    -- Deductions
    general_deductions NUMERIC(10,2),
    ppr_deductions NUMERIC(10,2),
    education_deductions NUMERIC(10,2),
    education_level TEXT,                   -- 'preescolar', 'primaria', etc.

    -- Metadata
    last_calculation_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_user_profiles_user_id ON user_profiles(user_id);
CREATE INDEX idx_user_profiles_updated_at ON user_profiles(updated_at);
```

---

## 🔌 API Endpoints

### `GET /api/profile`

**Auth:** Required (`get_current_user`)  
**Purpose:** Retrieve user profile to pre-fill calculator form  
**Response:**

```json
{
  "user_id": "google_sub_id",
  "fiscal_year": 2026,
  "monthly_gross_income": 12600.0,
  "monthly_net_income": 9500.0,
  "bonus_days": 15,
  "vacation_days": 12,
  "vacation_premium_cap": 5000.0,
  "general_deductions": 10000.0,
  "ppr_deductions": 20000.0,
  "education_deductions": 5000.0,
  "education_level": "primaria",
  "last_calculation_date": "2026-01-24T10:30:00Z",
  "created_at": "2026-01-20T08:00:00Z",
  "updated_at": "2026-01-24T10:30:00Z"
}
```

**Status Codes:**

- `200 OK` - Profile found
- `404 Not Found` - No profile exists
- `401 Unauthorized` - Not authenticated

### `POST /api/profile`

**Auth:** Required (`get_current_user`)  
**Purpose:** Create or update user profile  
**Request Body:**

```json
{
  "fiscal_year": 2026,
  "monthly_gross_income": 12600.0,
  "monthly_net_income": 9500.0,
  "bonus_days": 15,
  "vacation_days": 12,
  "vacation_premium_cap": 5000.0,
  "general_deductions": 10000.0,
  "ppr_deductions": 20000.0,
  "education_deductions": 5000.0,
  "education_level": "primaria"
}
```

**Response:**

```json
{
  "message": "Profile saved successfully",
  "user_id": "google_sub_id"
}
```

**Status Codes:**

- `200 OK` - Profile updated
- `201 Created` - Profile created
- `400 Bad Request` - Validation error
- `401 Unauthorized` - Not authenticated

### `DELETE /api/profile`

**Auth:** Required (`get_current_user`)  
**Purpose:** Delete user profile (GDPR compliance)  
**Response:**

```json
{
  "message": "Profile deleted successfully"
}
```

**Status Codes:**

- `200 OK` - Profile deleted
- `404 Not Found` - No profile to delete
- `401 Unauthorized` - Not authenticated

---

## 🚀 Implementation Phases

### Phase 1: Setup & Infrastructure (Dependencies)

**Duration:** ~1 hour  
**Tasks:**

- [ ] Add Alembic + SQLAlchemy to `pyproject.toml`
- [ ] Initialize Alembic (`alembic init alembic`)
- [ ] Configure `alembic.ini` with DATABASE_URL
- [ ] Configure `alembic/env.py` to use async PostgreSQL
- [ ] Create base SQLAlchemy models setup
- [ ] Test migration system with dummy migration

**Deliverables:**

- `pyproject.toml` updated
- `alembic/` directory configured
- Alembic working with PostgreSQL connection

---

### Phase 2: Domain Layer

**Duration:** ~2 hours  
**Tasks:**

- [ ] Create `src/user_profile/domain/value_objects/fiscal_preferences.py`
  - FiscalPreferences dataclass with validation
  - Fields: fiscal_year, incomes, deductions, education_level
- [ ] Create `src/user_profile/domain/entities/user_profile.py`
  - UserProfile entity
  - Validation rules (positive values, year range, etc.)
  - Helper methods (to_dict, from_dict)
- [ ] Create `src/user_profile/domain/ports/user_profile_repository.py`
  - Abstract repository interface
  - Methods: get, save, delete, exists
- [ ] Write unit tests for domain logic
  - `tests/unit/user_profile/test_user_profile_entity.py`
  - `tests/unit/user_profile/test_fiscal_preferences.py`

**Deliverables:**

- Domain entities with full validation
- Repository interface (ABC)
- 20+ unit tests passing

---

### Phase 3: Database Migration

**Duration:** ~1 hour  
**Tasks:**

- [ ] Create migration: `001_create_user_profiles_table.py`
  - Define SQLAlchemy UserProfile model
  - Create table with all columns + indexes
- [ ] Run migration on local PostgreSQL
- [ ] Verify table creation
- [ ] Create rollback migration (downgrade)
- [ ] Document migration process in README

**Deliverables:**

- `alembic/versions/001_create_user_profiles_table.py`
- `user_profiles` table in PostgreSQL
- Migration docs

---

### Phase 4: Infrastructure Layer (Persistence)

**Duration:** ~3 hours  
**Tasks:**

- [ ] Create `src/user_profile/infrastructure/persistence/postgres_profile_repository.py`
  - Implement UserProfileRepository interface
  - Use psycopg (not SQLAlchemy ORM) for consistency
  - Methods: get, save, delete, exists
  - Handle connection pooling
  - Error handling (unique constraint, foreign keys)
- [ ] Create SQLite repository for tests
  - `src/user_profile/infrastructure/persistence/sqlite_profile_repository.py`
  - Same interface, in-memory SQLite
- [ ] Write integration tests
  - `tests/integration/test_postgres_profile_repository.py`
  - Test CRUD operations
  - Test concurrent access

**Deliverables:**

- PostgreSQL repository implementation
- SQLite test repository
- 15+ integration tests passing

---

### Phase 5: Application Layer (Use Cases)

**Duration:** ~2 hours  
**Tasks:**

- [ ] Create `src/user_profile/application/get_user_profile_use_case.py`
  - Input: user_id
  - Output: UserProfile or None
  - Handle not found gracefully
- [ ] Create `src/user_profile/application/save_user_profile_use_case.py`
  - Input: user_id + FiscalPreferences
  - Output: Success/Error
  - Validate before saving
  - Update timestamp
- [ ] Create `src/user_profile/application/delete_user_profile_use_case.py`
  - Input: user_id
  - Output: Success/Error
  - GDPR compliance
- [ ] Register use cases in `DependencyContainer`
  - Singleton pattern for use cases
  - Inject repository
- [ ] Write use case tests
  - `tests/unit/user_profile/test_get_user_profile_use_case.py`
  - `tests/unit/user_profile/test_save_user_profile_use_case.py`
  - Mock repository

**Deliverables:**

- 3 use cases implemented
- DependencyContainer updated
- 12+ use case tests passing

---

### Phase 6: Infrastructure Layer (API)

**Duration:** ~3 hours  
**Tasks:**

- [ ] Create schemas in `src/shared/infrastructure/api/schemas/profile_schemas.py`
  - UserProfileRequest (Pydantic)
  - UserProfileResponse (Pydantic)
  - Validation examples
- [ ] Create `src/user_profile/infrastructure/api/profile_router.py`
  - GET /api/profile endpoint
  - POST /api/profile endpoint
  - DELETE /api/profile endpoint
  - Use `get_current_user` dependency
  - Error handling (404, 401, 400)
- [ ] Register router in `src/main.py`
  - Add to FastAPI app
  - Update API docs
- [ ] Write API tests
  - `tests/integration/test_profile_router.py`
  - Test authenticated access
  - Test unauthorized access
  - Test CRUD flow

**Deliverables:**

- API schemas
- Profile router with 3 endpoints
- Router registered in main app
- 18+ API tests passing

---

### Phase 7: Frontend Integration

**Duration:** ~4 hours  
**Tasks:**

- [ ] Add "Save preferences" checkbox to calculator form
  - `templates/calculator.html` modification
  - Styled checkbox with label
  - Default unchecked (opt-in)
- [ ] Load profile on page load (if authenticated)
  - Fetch GET /api/profile on DOM ready
  - Pre-fill all form inputs if 200 OK
  - Handle 404 gracefully (no profile yet)
- [ ] Auto-save after calculation (if checkbox enabled)
  - POST /api/profile after successful tax calculation
  - Background request (don't block UI)
  - Show success/error toast notification
- [ ] Add "Delete my data" button (optional)
  - Confirmation modal
  - DELETE /api/profile request
  - Clear form after deletion
- [ ] Update loading states
  - Show spinner while loading profile
  - Disable form during save
- [ ] Error handling UI
  - Toast for save errors
  - Retry mechanism

**Deliverables:**

- Checkbox UI component
- Auto-load functionality
- Auto-save functionality
- Delete functionality
- Full UX flow working

---

### Phase 8: Testing & Documentation

**Duration:** ~2 hours  
**Tasks:**

- [ ] Run full test suite (`uv run pytest tests/ -v`)
- [ ] Fix any failing tests
- [ ] Update `.github/copilot-instructions.md`
  - Document new user_profile module
  - Add architecture diagram
  - Explain Alembic integration
- [ ] Update README.md
  - Mention user profile feature
  - Add migration instructions
- [ ] Create user documentation
  - How to save preferences
  - How to delete data (GDPR)
  - Privacy policy notes
- [ ] Manual QA testing
  - Test full flow: login → fill form → save → logout → login → auto-fill
  - Test checkbox opt-in/opt-out
  - Test delete functionality

**Deliverables:**

- All tests passing (280+ tests)
- Updated documentation
- QA checklist completed

---

### Phase 9: Deployment

**Duration:** ~1 hour  
**Tasks:**

- [ ] Run Alembic migrations on Railway PostgreSQL
  - `alembic upgrade head`
- [ ] Verify table creation in production
- [ ] Deploy new code to Railway
- [ ] Monitor logs for errors
- [ ] Test production flow
- [ ] Update environment variables if needed

**Deliverables:**

- Production database migrated
- Feature live in production
- Monitoring enabled

---

## 🔐 Security & Privacy Considerations

### Data Sensitivity

- **User fiscal data is HIGHLY sensitive**
- Must comply with GDPR/privacy regulations
- Encryption in transit (HTTPS enforced)
- Encryption at rest (PostgreSQL encrypted storage)

### GDPR Compliance

- ✅ Explicit consent required (checkbox opt-in)
- ✅ Right to deletion (DELETE /api/profile endpoint)
- ✅ Data minimization (only essential fields)
- ✅ Purpose limitation (only for calculator pre-fill)
- ✅ Transparency (user knows what is saved)

### Authentication & Authorization

- All endpoints require authentication
- User can only access own profile (enforced by `user_id`)
- No admin access to user profiles (privacy by design)

---

## 📊 Success Metrics

### Technical Metrics

- [ ] All tests passing (target: 280+ tests)
- [ ] API response time < 200ms (p95)
- [ ] Database query time < 50ms
- [ ] Zero data loss incidents
- [ ] Zero unauthorized access attempts

### User Metrics

- [ ] % of users who enable "Save preferences"
- [ ] % reduction in form completion time (target: 80%)
- [ ] User satisfaction survey (target: 4.5/5)
- [ ] Feature adoption rate (target: 60% within 1 month)

---

## 🚧 Risks & Mitigations

| Risk                          | Impact   | Probability | Mitigation                                     |
| ----------------------------- | -------- | ----------- | ---------------------------------------------- |
| SQLAlchemy adds complexity    | High     | Medium      | Use only for migrations, not ORM queries       |
| Migration fails in production | Critical | Low         | Test thoroughly in staging, have rollback plan |
| User data privacy breach      | Critical | Low         | Encryption, auditing, minimal data collection  |
| Performance degradation       | Medium   | Low         | Index optimization, connection pooling         |
| Users don't enable checkbox   | Low      | High        | Good UX, clear value proposition               |

---

## 📝 Notes

- **Why Alembic?** Professional migration tool, version control for schema changes, team collaboration
- **Why not use SQLAlchemy ORM everywhere?** Keep consistency with existing codebase (raw SQL + psycopg)
- **Why opt-in checkbox?** Privacy-first approach, user control, GDPR compliance
- **Why single profile?** Simplicity first, can add multi-profile later if needed

---

## 🔄 Future Enhancements (Post-MVP)

- [ ] **Profile history:** Track changes over time, compare year-over-year
- [ ] **Multiple profiles:** Support freelancer + employee scenarios
- [ ] **Export data:** Allow user to download their data (CSV/JSON)
- [ ] **Profile templates:** Pre-configured profiles for common scenarios
- [ ] **Notifications:** Remind user to update profile annually
- [ ] **Analytics:** Aggregate insights (anonymized) for tax optimization trends

---

## ✅ Definition of Done

- [ ] All 9 phases completed
- [ ] All tests passing (unit + integration + E2E)
- [ ] Documentation updated
- [ ] Code reviewed
- [ ] Production deployment successful
- [ ] Feature announced to users
- [ ] Monitoring dashboards created
- [ ] User feedback collected

---

**Last Updated:** January 24, 2026  
**Next Review:** After Phase 3 completion
