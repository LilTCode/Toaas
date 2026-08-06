"""Project package.

Registers PyMySQL as the MySQLdb driver so the local MySQL setup works without
compiling mysqlclient. On Vercel the database is Postgres, so the shim is
skipped when PyMySQL is unavailable.
"""

try:
    import pymysql
except ImportError:  # pragma: no cover - Postgres/production path
    pass
else:
    pymysql.install_as_MySQLdb()
