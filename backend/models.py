import enum
from datetime import UTC, datetime

from sqlalchemy import JSON, Boolean, Column, DateTime, Enum, ForeignKey, Integer, String, Index
from sqlalchemy.orm import relationship

from .database import Base


class TransactionState(enum.Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    REVERSED = "REVERSED"

class EntryType(enum.Enum):
    CREDIT = "CREDIT"
    DEBIT = "DEBIT"

class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String, index=True, nullable=False)
    currency = Column(String, default="CREDITS")
    balance_cents = Column(Integer, default=0)
    locked_cents = Column(Integer, default=0)
    status = Column(String, default="ACTIVE")
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    def __repr__(self):
        return f"<Account(id={self.id}, tenant={self.tenant_id}, currency={self.currency}, balance={self.balance_cents})>"

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    reference_id = Column(String, unique=True, index=True, nullable=False)
    state = Column(Enum(TransactionState), default=TransactionState.PENDING)
    timestamp = Column(DateTime, default=lambda: datetime.now(UTC), index=True)

    def __repr__(self):
        return f"<Transaction(id={self.id}, ref={self.reference_id}, state={self.state})>"

class LedgerEntry(Base):
    __tablename__ = "ledger_entries"

    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=False, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False, index=True)
    amount_cents = Column(Integer, nullable=False)
    entry_type = Column(Enum(EntryType), nullable=False)

    transaction = relationship("Transaction", lazy="selectin")
    account = relationship("Account", lazy="selectin")
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))

    __table_args__ = (
        Index("ix_ledger_entry_account_type", "account_id", "entry_type"),
    )

    def __repr__(self):
        return f"<LedgerEntry(id={self.id}, tx={self.transaction_id}, account={self.account_id}, amount={self.amount_cents})>"

# --- NEW: Outbox Synchronization Pattern ---
class SyncOutbox(Base):
    """
    Records local state mutations to be streamed to the cloud PostgreSQL database.
    This enables the 'Local-First' zero-latency architecture.
    """
    __tablename__ = "ps_crud_outbox"

    id = Column(Integer, primary_key=True, autoincrement=True)
    table_name = Column(String, nullable=False, index=True)
    record_id = Column(String, nullable=False)
    operation = Column(String, nullable=False) # INSERT, UPDATE, DELETE
    payload = Column(JSON, nullable=True) # The changed data
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    synced = Column(Boolean, default=False, index=True)

    def __repr__(self):
        return f"<SyncOutbox(id={self.id}, table={self.table_name}, record={self.record_id}, op={self.operation})>"


# --- NEW: Subscription & Usage Models for Billing Integration ---
class Subscription(Base):
    """
    SaaS subscription details per tenant, synced to remote cloud PG.
    """
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String, index=True, nullable=False, unique=True)
    stripe_customer_id = Column(String, nullable=True, index=True)
    stripe_subscription_id = Column(String, nullable=True, index=True)
    tier = Column(String, default="Free")  # Free, Pro, Enterprise
    status = Column(String, default="active")  # active, trialing, past_due, canceled
    current_period_start = Column(DateTime, nullable=True)
    current_period_end = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    def __repr__(self):
        return f"<Subscription(id={self.id}, tenant={self.tenant_id}, tier={self.tier}, status={self.status})>"


class Usage(Base):
    """
    Tracks resource utilization (scraping, AI letter generation) per tenant per billing period.
    """
    __tablename__ = "usages"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String, index=True, nullable=False)
    feature = Column(String, nullable=False)  # "scraping", "cover_letter"
    count = Column(Integer, default=0)
    billing_period_start = Column(DateTime, nullable=False)
    billing_period_end = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    def __repr__(self):
        return f"<Usage(id={self.id}, tenant={self.tenant_id}, feature={self.feature}, count={self.count})>"


class User(Base):
    """
    User model for authentication and active status validation.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    def __repr__(self):
        return f"<User(id={self.id}, user_id={self.user_id}, email={self.email}, active={self.is_active})>"

