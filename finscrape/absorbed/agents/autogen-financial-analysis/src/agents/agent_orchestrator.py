"""
Agent Orchestrator
Manages coordination and workflow execution between multiple agents
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from .agent_types import WorkflowResult, AgentPerformance
from .agent_factory import FinancialAgentFactory


class AgentOrchestrator:
    """Orchestrates agent workflows and coordination"""

    def __init__(self, agents: Dict[str, Any]):
        self.agents = agents
        self.conversation_history: List[Dict] = []
        self.workflow_results: List[WorkflowResult] = []
        self.logger = logging.getLogger(__name__)
        self.active_workflows: Dict[str, asyncio.Task] = {}

    async def execute_analysis_workflow(self,
                                      task: str,
                                      workflow_type: str = "comprehensive",
                                      context: Optional[Dict] = None) -> WorkflowResult:
        """Execute a complete analysis workflow"""
        start_time = time.time()
        workflow_id = f"workflow_{int(time.time() * 1000)}"

        try:
            self.logger.info(f"Starting workflow {workflow_id}: {task}")

            # Initialize workflow result
            result = WorkflowResult(
                status="running",
                execution_time=0.0,
                agents_involved=list(self.agents.keys()),
                metadata={
                    "workflow_id": workflow_id,
                    "task": task,
                    "workflow_type": workflow_type,
                    "start_time": datetime.now().isoformat(),
                    "context": context or {}
                }
            )

            # Execute workflow based on type
            if workflow_type == "comprehensive":
                result = await self._execute_comprehensive_workflow(task, result, context)
            elif workflow_type == "quick_analysis":
                result = await self._execute_quick_analysis_workflow(task, result, context)
            elif workflow_type == "risk_assessment":
                result = await self._execute_risk_assessment_workflow(task, result, context)
            elif workflow_type == "portfolio_analysis":
                result = await self._execute_portfolio_analysis_workflow(task, result, context)
            else:
                raise ValueError(f"Unknown workflow type: {workflow_type}")

            # Calculate execution time
            result.execution_time = time.time() - start_time
            result.metadata["end_time"] = datetime.now().isoformat()

            # Store workflow result
            self.workflow_results.append(result)

            self.logger.info(f"Workflow {workflow_id} completed in {result.execution_time:.2f}s")
            return result

        except Exception as e:
            error_time = time.time() - start_time
            error_result = WorkflowResult(
                status="error",
                execution_time=error_time,
                agents_involved=list(self.agents.keys()),
                errors=[str(e)],
                metadata={
                    "workflow_id": workflow_id,
                    "task": task,
                    "workflow_type": workflow_type,
                    "start_time": datetime.now().isoformat(),
                    "end_time": datetime.now().isoformat(),
                    "error": str(e)
                }
            )

            self.workflow_results.append(error_result)
            self.logger.error(f"Workflow {workflow_id} failed: {str(e)}")
            return error_result

    async def _execute_comprehensive_workflow(self, task: str, result: WorkflowResult, context: Optional[Dict]) -> WorkflowResult:
        """Execute comprehensive financial analysis workflow"""

        # Phase 1: Data Collection
        self.logger.info("Phase 1: Data Collection")
        try:
            data_result = await self._execute_phase("data_collection", task, context)
            result.data["data_collection"] = data_result
        except Exception as e:
            result.add_error(f"Data collection failed: {str(e)}")

        # Phase 2: Financial Analysis
        self.logger.info("Phase 2: Financial Analysis")
        try:
            analysis_result = await self._execute_phase("financial_analysis", task, {
                "data": result.data.get("data_collection", {}),
                "context": context
            })
            result.data["financial_analysis"] = analysis_result
        except Exception as e:
            result.add_error(f"Financial analysis failed: {str(e)}")

        # Phase 3: Risk Assessment
        self.logger.info("Phase 3: Risk Assessment")
        try:
            risk_result = await self._execute_phase("risk_assessment", task, {
                "data": result.data.get("data_collection", {}),
                "analysis": result.data.get("financial_analysis", {}),
                "context": context
            })
            result.data["risk_assessment"] = risk_result
        except Exception as e:
            result.add_error(f"Risk assessment failed: {str(e)}")

        # Phase 4: Quantitative Analysis
        self.logger.info("Phase 4: Quantitative Analysis")
        try:
            quant_result = await self._execute_phase("quantitative_analysis", task, {
                "data": result.data.get("data_collection", {}),
                "analysis": result.data.get("financial_analysis", {}),
                "context": context
            })
            result.data["quantitative_analysis"] = quant_result
        except Exception as e:
            result.add_error(f"Quantitative analysis failed: {str(e)}")

        # Phase 5: Validation
        self.logger.info("Phase 5: Validation")
        try:
            validation_result = await self._execute_phase("validation", task, {
                "all_results": result.data,
                "context": context
            })
            result.data["validation"] = validation_result
        except Exception as e:
            result.add_error(f"Validation failed: {str(e)}")

        # Phase 6: Report Generation
        self.logger.info("Phase 6: Report Generation")
        try:
            report_result = await self._execute_phase("report_generation", task, {
                "all_results": result.data,
                "validation": result.data.get("validation", {}),
                "context": context
            })
            result.data["report"] = report_result
        except Exception as e:
            result.add_error(f"Report generation failed: {str(e)}")

        return result

    async def _execute_quick_analysis_workflow(self, task: str, result: WorkflowResult, context: Optional[Dict]) -> WorkflowResult:
        """Execute quick analysis workflow"""

        # Simplified workflow for quick analysis
        phases = [
            ("data_collection", "Data Collection"),
            ("financial_analysis", "Financial Analysis"),
            ("report_generation", "Report Generation")
        ]

        for phase_name, phase_display in phases:
            self.logger.info(f"Quick Analysis Phase: {phase_display}")
            try:
                phase_result = await self._execute_phase(phase_name, task, {
                    "quick_mode": True,
                    "context": context,
                    "previous_results": result.data
                })
                result.data[phase_name] = phase_result
            except Exception as e:
                result.add_error(f"{phase_display} failed: {str(e)}")

        return result

    async def _execute_risk_assessment_workflow(self, task: str, result: WorkflowResult, context: Optional[Dict]) -> WorkflowResult:
        """Execute risk assessment workflow"""

        phases = [
            ("data_collection", "Market Data Collection"),
            ("risk_analysis", "Risk Analysis"),
            ("stress_testing", "Stress Testing"),
            ("validation", "Risk Validation")
        ]

        for phase_name, phase_display in phases:
            self.logger.info(f"Risk Assessment Phase: {phase_display}")
            try:
                phase_result = await self._execute_phase(phase_name, task, {
                    "risk_focus": True,
                    "context": context,
                    "previous_results": result.data
                })
                result.data[phase_name] = phase_result
            except Exception as e:
                result.add_error(f"{phase_display} failed: {str(e)}")

        return result

    async def _execute_portfolio_analysis_workflow(self, task: str, result: WorkflowResult, context: Optional[Dict]) -> WorkflowResult:
        """Execute portfolio analysis workflow"""

        phases = [
            ("data_collection", "Portfolio Data Collection"),
            ("quantitative_analysis", "Portfolio Analysis"),
            ("risk_assessment", "Portfolio Risk Assessment"),
            ("optimization", "Portfolio Optimization")
        ]

        for phase_name, phase_display in phases:
            self.logger.info(f"Portfolio Analysis Phase: {phase_display}")
            try:
                phase_result = await self._execute_phase(phase_name, task, {
                    "portfolio_focus": True,
                    "context": context,
                    "previous_results": result.data
                })
                result.data[phase_name] = phase_result
            except Exception as e:
                result.add_error(f"{phase_display} failed: {str(e)}")

        return result

    async def _execute_phase(self, phase_name: str, task: str, phase_context: Dict) -> Dict[str, Any]:
        """Execute a specific workflow phase"""

        # Map phases to agent types
        phase_agent_mapping = {
            "data_collection": "data_collector",
            "financial_analysis": "financial_analyst",
            "risk_analysis": "risk_analyst",
            "risk_assessment": "risk_analyst",
            "quantitative_analysis": "quantitative_analyst",
            "validation": "validator",
            "report_generation": "report_generator",
            "stress_testing": "risk_analyst",
            "optimization": "quantitative_analyst"
        }

        agent_name = phase_agent_mapping.get(phase_name)
        if not agent_name or agent_name not in self.agents:
            raise ValueError(f"No agent available for phase: {phase_name}")

        agent = self.agents[agent_name]

        # Prepare task context for the agent
        agent_task = self._prepare_agent_task(phase_name, task, phase_context)

        # Execute agent task
        try:
            # In a real implementation, this would use AutoGen's conversation system
            # For now, we'll simulate the execution
            result = await self._simulate_agent_execution(agent, agent_task, phase_context)

            # Log the conversation
            self.conversation_history.append({
                "timestamp": datetime.now().isoformat(),
                "phase": phase_name,
                "agent": agent_name,
                "task": agent_task,
                "result": result
            })

            return result

        except Exception as e:
            self.logger.error(f"Phase {phase_name} execution failed: {str(e)}")
            raise

    def _prepare_agent_task(self, phase_name: str, task: str, context: Dict) -> str:
        """Prepare task description for agent"""

        task_templates = {
            "data_collection": f"Collect comprehensive financial data for: {task}",
            "financial_analysis": f"Perform detailed financial analysis for: {task}",
            "risk_analysis": f"Conduct risk assessment for: {task}",
            "risk_assessment": f"Execute comprehensive risk assessment for: {task}",
            "quantitative_analysis": f"Perform quantitative analysis for: {task}",
            "validation": f"Validate analysis results for: {task}",
            "report_generation": f"Generate comprehensive analysis report for: {task}",
            "stress_testing": f"Execute stress testing scenarios for: {task}",
            "optimization": f"Perform portfolio optimization for: {task}"
        }

        base_task = task_templates.get(phase_name, f"Execute {phase_name} for: {task}")

        # Add context information
        if context:
            context_str = "\n\nContext:\n"
            for key, value in context.items():
                context_str += f"- {key}: {value}\n"
            base_task += context_str

        return base_task

    async def _simulate_agent_execution(self, agent: Any, task: str, context: Dict) -> Dict[str, Any]:
        """Simulate agent execution (placeholder for actual AutoGen integration)"""

        # This is a placeholder for actual AutoGen agent execution
        # In a real implementation, this would use AutoGen's conversation system

        await asyncio.sleep(0.1)  # Simulate processing time

        # Return simulated result
        return {
            "status": "completed",
            "agent": getattr(agent, 'name', 'unknown'),
            "task": task,
            "timestamp": datetime.now().isoformat(),
            "result_summary": f"Simulated execution of: {task[:100]}...",
            "data_quality": 0.95
        }

    def get_workflow_results(self, limit: Optional[int] = None) -> List[WorkflowResult]:
        """Get workflow execution results"""
        if limit:
            return self.workflow_results[-limit:]
        return self.workflow_results.copy()

    def get_conversation_history(self, limit: Optional[int] = None) -> List[Dict]:
        """Get conversation history"""
        if limit:
            return self.conversation_history[-limit:]
        return self.conversation_history.copy()

    async def execute_parallel_workflows(self, tasks: List[Dict]) -> List[WorkflowResult]:
        """Execute multiple workflows in parallel"""

        workflows = []
        for task_config in tasks:
            workflow = self.execute_analysis_workflow(
                task=task_config["task"],
                workflow_type=task_config.get("workflow_type", "comprehensive"),
                context=task_config.get("context")
            )
            workflows.append(workflow)

        results = await asyncio.gather(*workflows, return_exceptions=True)

        # Process results and handle exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                error_result = WorkflowResult(
                    status="error",
                    execution_time=0.0,
                    agents_involved=list(self.agents.keys()),
                    errors=[str(result)],
                    metadata={
                        "task": tasks[i]["task"],
                        "error": str(result)
                    }
                )
                processed_results.append(error_result)
            else:
                processed_results.append(result)

        return processed_results

    def get_workflow_statistics(self) -> Dict[str, Any]:
        """Get workflow execution statistics"""
        if not self.workflow_results:
            return {"total_workflows": 0}

        total_workflows = len(self.workflow_results)
        successful_workflows = sum(1 for r in self.workflow_results if r.status == "success")
        failed_workflows = sum(1 for r in self.workflow_results if r.status == "error")
        partial_workflows = total_workflows - successful_workflows - failed_workflows

        avg_execution_time = sum(r.execution_time for r in self.workflow_results) / total_workflows

        return {
            "total_workflows": total_workflows,
            "successful_workflows": successful_workflows,
            "failed_workflows": failed_workflows,
            "partial_workflows": partial_workflows,
            "success_rate": successful_workflows / total_workflows,
            "average_execution_time": avg_execution_time,
            "most_active_agent": self._get_most_active_agent()
        }

    def _get_most_active_agent(self) -> str:
        """Get the most frequently used agent"""
        agent_usage = {}
        for result in self.workflow_results:
            for agent in result.agents_involved:
                agent_usage[agent] = agent_usage.get(agent, 0) + 1

        return max(agent_usage.items(), key=lambda x: x[1])[0] if agent_usage else "none"