"""Data models for risk policies and approval lifecycles."""

from enum import Enum
from typing import Any, Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ApprovalStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    AUTO_APPROVED = "AUTO_APPROVED"


class PolicyRule(BaseModel):
    rule_id: str
    tool_name_pattern: str  # e.g. "delete_*", "transfer_funds", "execute_sql"
    risk_level: RiskLevel
    description: str
    condition_expression: Optional[str] = None  # e.g. "amount > 500" or "is_production == True"


class ApprovalRequest(BaseModel):
    request_id: str
    agent_id: str
    tool_name: str
    arguments: Dict[str, Any]
    risk_level: RiskLevel
    triggered_rules: List[str] = Field(default_factory=list)
    status: ApprovalStatus = ApprovalStatus.PENDING
    approver: Optional[str] = None
    rejection_reason: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
