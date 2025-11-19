# Database Migrations

BACOWR uses Alembic for database schema migrations.

## Quick Start

### Create a new migration

After modifying models in `app/models/`:

```bash
cd api
alembic revision --autogenerate -m "Description of changes"
```

### Apply migrations

```bash
cd api
alembic upgrade head
```

### Rollback migrations

```bash
cd api
alembic downgrade -1  # Rollback one migration
alembic downgrade base  # Rollback all migrations
```

## Migration Workflow

1. **Modify database models** in `app/models/database.py` or `app/models/audit.py`

2. **Generate migration**:
   ```bash
   alembic revision --autogenerate -m "Add new field to User model"
   ```

3. **Review the migration** in `alembic/versions/` - always check auto-generated code!

4. **Test the migration** on development database:
   ```bash
   alembic upgrade head
   ```

5. **Test rollback**:
   ```bash
   alembic downgrade -1
   alembic upgrade head
   ```

6. **Commit migration file** to git

7. **Apply in production** during deployment

## Common Commands

```bash
# Check current migration version
alembic current

# Show migration history
alembic history --verbose

# Show SQL that would be executed (without running)
alembic upgrade head --sql

# Upgrade to specific version
alembic upgrade abc123

# Create empty migration (for data migrations)
alembic revision -m "Data migration description"
```

## Production Deployment

Always run migrations as part of deployment:

```bash
# In your deployment script
cd api
alembic upgrade head
```

For Railway/Heroku, add to `Procfile` or start command:
```
release: cd api && alembic upgrade head
web: cd api && uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

## Troubleshooting

### "Can't locate revision identified by 'xyz'"

The database has a migration that doesn't exist in code. Either:
- Pull latest code with migrations
- Or stamp the database to a known good version:
  ```bash
  alembic stamp head
  ```

### "Target database is not up to date"

Someone committed a migration you don't have:
```bash
git pull
alembic upgrade head
```

### SQLite limitations

SQLite doesn't support all ALTER TABLE operations. For complex schema changes:
1. Create new table with desired schema
2. Copy data from old table
3. Drop old table
4. Rename new table

Or manually edit the migration file.

## Migration File Structure

```python
def upgrade() -> None:
    """Apply the migration."""
    op.create_table('new_table',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade() -> None:
    """Rollback the migration."""
    op.drop_table('new_table')
```

## Best Practices

1. **Always review auto-generated migrations** - they're not always perfect
2. **Test both upgrade and downgrade** before committing
3. **Use descriptive migration messages**
4. **One logical change per migration** - makes rollbacks easier
5. **Include data migrations separately** - don't mix schema and data changes
6. **Backup production database** before running migrations
7. **Run migrations in maintenance window** for critical changes

## Current Schema

Run this to see current database schema:
```bash
alembic upgrade head
sqlite3 bacowr.db ".schema"  # For SQLite
# Or connect with psql for PostgreSQL
```
