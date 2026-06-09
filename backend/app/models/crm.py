from datetime import datetime, time
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, Integer, JSON, Numeric, String, Text, Time
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str | None] = mapped_column(String(255))
    assigned_user_id: Mapped[str | None] = mapped_column(String(36))
    customer_type: Mapped[str | None] = mapped_column(String(255))
    account_status: Mapped[str | None] = mapped_column(String(255))
    industry: Mapped[str | None] = mapped_column(String(255))
    rating: Mapped[str | None] = mapped_column(String(255))
    how_old_days: Mapped[int | None] = mapped_column(Integer)
    untouched_since_days: Mapped[int | None] = mapped_column(Integer)
    latest_comment: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime | None] = mapped_column(DateTime)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime)


class AccountContact(Base):
    __tablename__ = "account_contact"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    account_id: Mapped[str] = mapped_column(String(36))
    contact_id: Mapped[str] = mapped_column(String(36))
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime | None] = mapped_column(DateTime)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime)


class AccountOpportunity(Base):
    __tablename__ = "account_opportunity"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    account_id: Mapped[str] = mapped_column(String(36))
    opportunity_id: Mapped[str] = mapped_column(String(36))
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime | None] = mapped_column(DateTime)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime)


class AccountTicket(Base):
    __tablename__ = "account_ticket"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    account_id: Mapped[str] = mapped_column(String(36))
    ticket_id: Mapped[str] = mapped_column(String(36))
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime | None] = mapped_column(DateTime)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime)


class ActivityRel(Base):
    __tablename__ = "activities_rel"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    parent_module: Mapped[str] = mapped_column(String(255))
    parent_id: Mapped[str] = mapped_column(String(36))
    initial_module: Mapped[str] = mapped_column(String(255))
    initial_id: Mapped[str] = mapped_column(String(36))
    activity_module: Mapped[str] = mapped_column(String(255))
    activity_id: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime | None] = mapped_column(DateTime)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime)


class CallCampaign(Base):
    __tablename__ = "call_campaigns"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str | None] = mapped_column(String(255))
    call_campaign_status: Mapped[str | None] = mapped_column(String(30))
    module_name: Mapped[str | None] = mapped_column(String(255))
    assigned_user_id: Mapped[str | None] = mapped_column(String(36))
    created_at: Mapped[datetime | None] = mapped_column(DateTime)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime)


class CallCheckList(Base):
    __tablename__ = "call_check_lists"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    check_list_unique: Mapped[str] = mapped_column(String(36))
    name: Mapped[str | None] = mapped_column(String(200))
    module_id: Mapped[str | None] = mapped_column(String(36))
    module_name: Mapped[str | None] = mapped_column(String(100))
    assigned_user_id: Mapped[str | None] = mapped_column(String(36))
    call_campaign_id: Mapped[str | None] = mapped_column(String(36))
    duration: Mapped[time | None] = mapped_column(Time)
    call_status: Mapped[str | None] = mapped_column(String(255))
    execution_completed: Mapped[bool | None] = mapped_column(Boolean)
    number_of_try: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime | None] = mapped_column(DateTime)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime)


class Call(Base):
    __tablename__ = "calls"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str | None] = mapped_column(String(255))
    assigned_user_id: Mapped[str | None] = mapped_column(String(36))
    direction: Mapped[str | None] = mapped_column(String(100))
    start_date: Mapped[datetime | None] = mapped_column(DateTime)
    end_date: Mapped[datetime | None] = mapped_column(DateTime)
    duration: Mapped[time | None] = mapped_column(Time)
    total_duration_minute: Mapped[Decimal | None] = mapped_column(Numeric(16, 2))
    call_status: Mapped[str | None] = mapped_column(String(100))
    logged_by: Mapped[str | None] = mapped_column(String(100))
    call_type: Mapped[str | None] = mapped_column(String(100))
    latest_comment: Mapped[str | None] = mapped_column(Text)
    overall_call_rating: Mapped[int] = mapped_column(Integer, default=0)
    call_quality_metrics: Mapped[dict | None] = mapped_column(JSON)
    sentiment_analysis: Mapped[dict | None] = mapped_column(JSON)
    next_step: Mapped[str | None] = mapped_column(String(255))
    call_outcome: Mapped[str | None] = mapped_column(String(255))
    mom: Mapped[str | None] = mapped_column(Text)
    summary: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime | None] = mapped_column(DateTime)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime)


class AccountsAudit(Base):
    __tablename__ = "accounts_audit"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    parent_id: Mapped[str] = mapped_column(String(36))
    field_name: Mapped[str] = mapped_column(String(255))
    old_value: Mapped[str | None] = mapped_column(Text)
    new_value: Mapped[str | None] = mapped_column(Text)
    updated_by: Mapped[str | None] = mapped_column(String(36))
    updated_at: Mapped[datetime] = mapped_column(DateTime)
