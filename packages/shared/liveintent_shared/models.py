from datetime import datetime
from sqlalchemy import (
    BigInteger, Boolean, DateTime, ForeignKey, Integer, String, Text,
    UniqueConstraint, Index, func
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from .enums import Vertical, VerticalSource

# BIGINT primary keys that still autoincrement under SQLite (used in tests).
BigIntPK = BigInteger().with_variant(Integer, "sqlite")
BigIntFK = BigInteger().with_variant(Integer, "sqlite")

class Base(DeclarativeBase):
    pass

class Publisher(Base):
    __tablename__ = "publishers"
    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True)
    # NOT unique — one publisher domain may have N persona inboxes, each is its own row.
    domain: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str | None] = mapped_column(String(255))
    seed_email_address: Mapped[str] = mapped_column(String(320), nullable=False, unique=True)
    subscribed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_email_received_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)

class EmailRaw(Base):
    __tablename__ = "emails_raw"
    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True)
    publisher_id: Mapped[int] = mapped_column(ForeignKey("publishers.id"), nullable=False)
    imap_uid: Mapped[int] = mapped_column(BigInteger, nullable=False)
    subject: Mapped[str | None] = mapped_column(Text)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    from_addr: Mapped[str | None] = mapped_column(String(320))
    raw_html_path: Mapped[str] = mapped_column(Text, nullable=False)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    processing_error: Mapped[str | None] = mapped_column(Text)
    __table_args__ = (
        Index("ix_emails_publisher_received", "publisher_id", "received_at"),
        UniqueConstraint("publisher_id", "imap_uid", name="uq_emails_publisher_uid"),
    )

class Advertiser(Base):
    __tablename__ = "advertisers"
    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True)
    domain: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(255))
    vertical: Mapped[str] = mapped_column(String(32), default=Vertical.UNCLASSIFIED.value, nullable=False)
    vertical_source: Mapped[str] = mapped_column(String(16), default=VerticalSource.AUTO.value, nullable=False)
    vertical_classified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    notes: Mapped[str | None] = mapped_column(Text)

class Creative(Base):
    __tablename__ = "creatives"
    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True)
    advertiser_id: Mapped[int] = mapped_column(ForeignKey("advertisers.id"), nullable=False)
    creative_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    headline: Mapped[str | None] = mapped_column(Text)
    screenshot_path: Mapped[str] = mapped_column(Text, nullable=False)
    click_tracker_url: Mapped[str] = mapped_column(Text, nullable=False)
    final_landing_url: Mapped[str | None] = mapped_column(Text)
    final_landing_url_resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class Impression(Base):
    __tablename__ = "impressions"
    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True)
    creative_id: Mapped[int] = mapped_column(ForeignKey("creatives.id"), nullable=False)
    publisher_id: Mapped[int] = mapped_column(ForeignKey("publishers.id"), nullable=False)
    email_id: Mapped[int] = mapped_column(ForeignKey("emails_raw.id"), nullable=False)
    seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (
        Index("ix_impressions_creative_seen", "creative_id", "seen_at"),
        Index("ix_impressions_publisher_seen", "publisher_id", "seen_at"),
    )

class DigestRun(Base):
    __tablename__ = "digest_runs"
    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True)
    ran_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    window_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    window_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    top_advertisers_json: Mapped[str] = mapped_column(Text, nullable=False)
    telegram_message_id: Mapped[str | None] = mapped_column(String(64))
