# Database Setup Guide

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Initialize Database

The database is automatically initialized when you start the API:

```bash
python src/api.py
```

Or use the initialization script:

```bash
python scripts/init_database.py
```

### 3. Verify Database

Check that the database file was created:

```bash
ls -lh data/mental_health.db
```

## Database Schema

The system uses SQLite by default with the following tables:

### Core Tables

1. **users** - User profiles (anonymized)
   - `user_id`: Anonymous hash ID
   - `consent_given`: Data storage consent
   - `total_conversations`, `total_messages`, `crisis_count`: Statistics

2. **user_metadata** - User preferences and settings
   - `preferred_name`: Display name
   - `age_range`: Age bracket
   - `main_concerns`: List of concerns
   - `conversation_style`: formal/casual

3. **conversations** - Chat history
   - `session_id`: Session identifier
   - `persona_id`: Counselor used
   - `message_role`: user/assistant
   - `message_content`: Message text
   - `emotion_detected`, `crisis_detected`: Analysis results

4. **assessments** - Psychological assessments
   - `assessment_type`: PHQ-9, GAD-7, K-10
   - `score`: Total score
   - `severity`: Severity level
   - `recommendations`: List of recommendations

### Feedback Tables

5. **persona_feedback** - User feedback on counselors
6. **persona_performance** - Aggregated counselor performance
7. **user_persona_preference** - User counselor preferences

## Configuration

### Environment Variables

```bash
# .env file
DATABASE_URL=sqlite:///data/mental_health.db  # Or PostgreSQL in production
ENABLE_LONG_TERM_MEMORY=true
```

### Production (PostgreSQL)

For production, use PostgreSQL:

```bash
# Install PostgreSQL adapter
pip install psycopg2-binary

# Update .env
DATABASE_URL=postgresql://user:password@localhost/mental_health_db
```

## Database Migrations

### Create Migration

```bash
# After modifying models in src/database.py
alembic revision --autogenerate -m "Description of changes"
```

### Apply Migrations

```bash
alembic upgrade head
```

### Rollback Migration

```bash
alembic downgrade -1  # Go back one migration
```

### View Migration History

```bash
alembic history
```

## Data Management

### Backup Database

```bash
# SQLite
cp data/mental_health.db data/backup_$(date +%Y%m%d).db

# PostgreSQL
pg_dump mental_health_db > backup_$(date +%Y%m%d).sql
```

### Restore Database

```bash
# SQLite
cp data/backup_20251118.db data/mental_health.db

# PostgreSQL
psql mental_health_db < backup_20251118.sql
```

### Clear Database (Development Only)

```bash
rm data/mental_health.db
python scripts/init_database.py
```

## Privacy & PIPA Compliance

### Data Retention

User data is automatically deleted after the retention period (default: 90 days).

### Manual Data Deletion

```python
from src.database import get_session, User

session = get_session()
user = session.query(User).filter_by(user_id="user_to_delete").first()
if user:
    session.delete(user)  # Cascade deletes all related data
    session.commit()
```

### Export User Data

```python
from src.database import get_session, User, Conversation

session = get_session()
user = session.query(User).filter_by(user_id="user_id").first()

# Get all conversations
conversations = session.query(Conversation).filter_by(user_id=user.id).all()

# Export to JSON
import json
data = {
    "user_id": user.user_id,
    "conversations": [
        {
            "role": c.message_role,
            "content": c.message_content,
            "timestamp": c.timestamp.isoformat()
        }
        for c in conversations
    ]
}

with open(f"user_data_{user.user_id}.json", "w") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
```

## Monitoring Database

### Check Database Size

```bash
# SQLite
du -h data/mental_health.db

# PostgreSQL
psql -c "SELECT pg_size_pretty(pg_database_size('mental_health_db'));"
```

### View Table Statistics

```python
from src.database import get_session, User, Conversation, Assessment

session = get_session()

print(f"Users: {session.query(User).count()}")
print(f"Conversations: {session.query(Conversation).count()}")
print(f"Assessments: {session.query(Assessment).count()}")
```

## Troubleshooting

### Database Locked Error

```bash
# Check for open connections
lsof data/mental_health.db

# Kill stuck processes if needed
kill -9 <PID>
```

### Migration Conflicts

```bash
# Stamp current state without running migrations
alembic stamp head

# Or reset migrations (CAUTION: loses migration history)
rm alembic/versions/*.py
alembic revision --autogenerate -m "Reset schema"
```

### Database Corruption

```bash
# SQLite integrity check
sqlite3 data/mental_health.db "PRAGMA integrity_check;"

# If corrupted, restore from backup
cp data/backup_latest.db data/mental_health.db
```

## Testing

### Run Database Tests

```bash
pytest tests/test_database_integration.py -v
```

### Test Database Performance

```bash
pytest tests/test_database_integration.py::TestDatabaseQueries -v
```

## Security Best Practices

1. **Never commit `.db` files** - Add to `.gitignore`
2. **Use strong passwords** for PostgreSQL
3. **Encrypt sensitive fields** in production
4. **Regular backups** - Automate daily backups
5. **Monitor access logs** - Track who accesses what
6. **Implement rate limiting** - Prevent abuse
7. **Use SSL/TLS** for database connections in production
