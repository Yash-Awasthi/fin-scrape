"""
Agent Type Definitions
Core data structures for AutoGen agent system
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Optional, Any


class AgentRole(Enum):
    """Agent role enumeration"""
    DATA_COLLECTOR = "data_collector"
    DATA_CLEANER = "data_cleaner"
    FINANCIAL_ANALYST = "financial_analyst"
    RISK_ANALYST = "risk_analyst"
    QUANTITATIVE_ANALYST = "quantitative_analyst"
    REPORT_GENERATOR = "report_generator"
    VALIDATOR = "validator"


@dataclass
class AgentConfig:
    """Agent configuration data class"""
    name: str
    role: AgentRole
    system_message: str
    llm_config: Dict[str, Any]
    max_consecutive_auto_reply: int = 10
    human_input_mode: str = "NEVER"
    code_execution_config: Optional[Dict[str, Any]] = None
    temperature: float = 0.1
    max_tokens: int = 8000
    top_p: float = 0.9
    frequency_penalty: float = 0.1
    presence_penalty: float = 0.1

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for AutoGen"""
        return {
            "name": self.name,
            "system_message": self.system_message,
            "llm_config": self.llm_config,
            "max_consecutive_auto_reply": self.max_consecutive_auto_reply,
            "human_input_mode": self.human_input_mode,
            "code_execution_config": self.code_execution_config
        }


@dataclass
class AgentPerformance:
    """Agent performance metrics"""
    agent_name: str
    tasks_completed: int = 0
    average_response_time: float = 0.0
    success_rate: float = 0.0
    error_count: int = 0
    last_activity: Optional[str] = None

    def update_performance(self, response_time: float, success: bool):
        """Update performance metrics"""
        self.tasks_completed += 1
        self.average_response_time = (
            (self.average_response_time * (self.tasks_completed - 1) + response_time)
            / self.tasks_completed
        )
        if success:
            self.success_rate = ((self.success_rate * (self.tasks_completed - 1)) + 1) / self.tasks_completed
        else:
            self.success_rate = (self.success_rate * (self.tasks_completed - 1)) / self.tasks_completed
            self.error_count += 1


@dataclass
class WorkflowResult:
    """Workflow execution result"""
    status: str
    data: Dict[str, Any] = field(default_factory=dict)
    execution_time: float = 0.0
    agents_involved: list = field(default_factory=list)
    errors: list = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_error(self, error: str):
        """Add error to result"""
        self.errors.append(error)
        if self.status == "success":
            self.status = "partial_failure"

    def merge_results(self, other: 'WorkflowResult'):
        """Merge another workflow result"""
        self.data.update(other.data)
        self.agents_involved.extend(other.agents_involved)
        self.errors.extend(other.errors)
        self.metadata.update(other.metadata)
        if other.status == "error" or (self.status == "success" and other.status == "partial_failure"):
            self.status = other.status