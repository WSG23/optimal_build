"""AI Agent models for Singapore Property Development Platform."""

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Enum as SQLEnum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.models.base import UUID, BaseModel


class AIAgentType(str, Enum):
    """Types of AI agents in the system."""

    FEASIBILITY_ANALYST = "feasibility_analyst"
    REGULATORY_COMPLIANCE = "regulatory_compliance"
    COST_ESTIMATOR = "cost_estimator"
    DESIGN_OPTIMIZER = "design_optimizer"
    RISK_ASSESSOR = "risk_assessor"
    MARKET_ANALYST = "market_analyst"
    DOCUMENTATION_GENERATOR = "documentation_generator"
    BCA_COMPLIANCE = "bca_compliance"  # Building and Construction Authority
    URA_COMPLIANCE = "ura_compliance"  # Urban Redevelopment Authority
    SCDF_COMPLIANCE = "scdf_compliance"  # Singapore Civil Defence Force


class AIAgentStatus(str, Enum):
    """Status of AI agents."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"
    DEPRECATED = "deprecated"


class AIAgent(BaseModel):
    """AI Agent configuration and metadata."""

    __tablename__ = "ai_agents"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, unique=True)
    agent_type = Column(SQLEnum(AIAgentType), nullable=False)
    description = Column(Text)
    version = Column(String(50), nullable=False, default="1.0.0")

    status = Column(
        SQLEnum(AIAgentStatus), default=AIAgentStatus.ACTIVE, nullable=False
    )
    is_enabled = Column(Boolean, default=True, nullable=False)

    # Model configuration
    model_provider = Column(String(100), default="openai")
    model_name = Column(String(100), default="gpt-4")
    temperature = Column(Float, default=0.7)
    max_tokens = Column(Integer, default=2000)

    # Singapore regulatory knowledge base
    singapore_regulations = Column(JSON)  # Store relevant regulations
    compliance_frameworks = Column(JSON)  # BCA, URA, SCDF requirements

    # System prompt and instructions
    system_prompt = Column(Text)
    instruction_template = Column(Text)

    # Capabilities and limitations
    capabilities = Column(JSON)  # List of agent capabilities
    limitations = Column(JSON)  # Known limitations

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    sessions = relationship(
        "AIAgentSession", back_populates="agent", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<AIAgent {self.name} ({self.agent_type})>"


class AIAgentSession(BaseModel):
    """AI Agent interaction sessions."""

    __tablename__ = "ai_agent_sessions"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)

    # Foreign keys
    agent_id = Column(UUID(), ForeignKey("ai_agents.id"), nullable=False)
    user_id = Column(UUID(), ForeignKey("users.id"), nullable=False)
    project_id = Column(UUID(), ForeignKey("projects.id"))
    property_id = Column(UUID(), ForeignKey("singapore_properties.id"))

    # Session data
    session_type = Column(String(100))  # analysis, compliance_check, report_generation
    status = Column(String(50), default="active")  # active, completed, failed

    # Context and memory
    context = Column(JSON)  # Session context data
    memory = Column(JSON)  # Conversation memory

    # Input/Output
    input_data = Column(JSON)  # Initial input for the session
    output_data = Column(JSON)  # Final output/results

    # Conversation history
    messages = Column(JSON)  # Full conversation history
    total_messages = Column(Integer, default=0)

    # Usage metrics
    tokens_used = Column(Integer, default=0)
    cost_estimate = Column(Float, default=0.0)
    processing_time = Column(Float)  # in seconds

    # Singapore specific analysis
    singapore_compliance_score = Column(Float)  # 0-100 score
    regulatory_issues = Column(JSON)  # List of compliance issues
    recommendations = Column(JSON)  # Agent recommendations

    # Timestamps
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime)
    last_activity = Column(DateTime, default=datetime.utcnow)

    # Relationships
    agent = relationship("AIAgent", back_populates="sessions")
    user = relationship("User", back_populates="ai_agent_sessions")
    project = relationship("Project", back_populates="ai_sessions")
    # property = relationship("SingaporeProperty", back_populates="ai_sessions")  # Disabled - circular dependency issue

    def __repr__(self):
        return (
            f"<AIAgentSession {self.id} (Agent: {self.agent_id}, User: {self.user_id})>"
        )
