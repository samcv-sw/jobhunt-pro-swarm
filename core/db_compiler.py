from sqlalchemy.ext.compiler import compiles
from sqlalchemy.types import String, JSON, TypeDecorator
from sqlalchemy.dialects.postgresql import UUID, JSONB


# 1. Custom UUID Type
class StringUUID(TypeDecorator):
    """
    Platform-independent UUID type.
    Uses PostgreSQL's UUID type if available, otherwise uses CHAR(32) in SQLite.
    """

    impl = String
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(UUID())
        else:
            return dialect.type_descriptor(String(32))


@compiles(StringUUID, "postgresql")
def compile_uuid_pg(type_, compiler, **kw):
    return "UUID"


@compiles(StringUUID, "sqlite")
def compile_uuid_sqlite(type_, compiler, **kw):
    return "CHAR(32)"


# 2. Custom JSON Type
class CompatibleJSON(TypeDecorator):
    """
    Platform-independent JSON type.
    Uses PostgreSQL's JSONB type if available, otherwise uses TEXT in SQLite.
    """

    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(JSONB())
        else:
            return dialect.type_descriptor(String())


@compiles(CompatibleJSON, "postgresql")
def compile_json_pg(type_, compiler, **kw):
    return "JSONB"


@compiles(CompatibleJSON, "sqlite")
def compile_json_sqlite(type_, compiler, **kw):
    return "TEXT"
