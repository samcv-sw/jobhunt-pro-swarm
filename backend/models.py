from sqlalchemy import Column, Integer, String, Enum, DateTime, ForeignKey, Float, JSON
from sqlalchemy.orm import relationship
import enum
from datetime import datetime, timezone
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
    tenant_id = Column(String, index=True, nullable=False) # e.g. user_id or system account id
    currency = Column(String, default="CREDITS")
    balance_cents = Column(Integer, default=0) # Total available balance
    locked_cents = Column(Integer, default=0)  # Locked balance for active agents
    status = Column(String, default="ACTIVE")

class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    reference_id = Column(String, unique=True, index=True, nullable=False) # For idempotency
    state = Column(Enum(TransactionState), default=TransactionState.PENDING)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class LedgerEntry(Base):
    __tablename__ = "ledger_entries"
    
    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=False)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    amount_cents = Column(Integer, nullable=False)
    entry_type = Column(Enum(EntryType), nullable=False)
    
    transaction = relationship("Transaction")
    account = relationship("Account")

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    auditable_type = Column(String, nullable=False) # e.g., 'Account', 'Transaction'
    record_id = Column(Integer, nullable=False)
    old_values = Column(JSON, nullable=True)
    new_values = Column(JSON, nullable=True)
    user_agent = Column(String, nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
