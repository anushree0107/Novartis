"""Action Executor - LLM-powered agentic workflow execution."""
import os
import re
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import networkx as nx


class ActionType(Enum):
    ESCALATE = "escalate"
    GENERATE_REPORT = "generate_report"
    CREATE_ALERT = "create_alert"
    SCHEDULE_FOLLOWUP = "schedule_followup"
    SEND_NOTIFICATION = "send_notification"
    UPDATE_STATUS = "update_status"
    QUERY_DATA = "query_data"


class ActionStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ActionResult:
    """Result of an action execution."""
    action_id: str
    action_type: ActionType
    status: ActionStatus
    
    message: str = ""
    output: Optional[Any] = None
    
    executed_at: datetime = field(default_factory=datetime.now)
    execution_time_ms: int = 0
    
    steps_executed: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "action_id": self.action_id,
            "action_type": self.action_type.value,
            "status": self.status.value,
            "message": self.message,
            "output": self.output if not callable(self.output) else str(self.output),
            "executed_at": self.executed_at.isoformat(),
            "execution_time_ms": self.execution_time_ms,
            "steps_executed": self.steps_executed
        }


@dataclass
class ParsedAction:
    """LLM-parsed action from natural language."""
    action_type: ActionType
    entity_type: str
    entity_id: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    raw_input: str = ""


class ActionExecutor:
    """
    LLM-Powered Action Executor for agentic workflows.
    
    Features:
    - Natural language action parsing
    - Multi-step workflow execution
    - Integration hooks for external systems
    - Audit logging
    """
    
    ACTION_PATTERNS = {
        ActionType.ESCALATE: [
            r"escalate\s+(site|patient|study)\s+(\S+)",
            r"raise\s+(?:an?\s+)?issue\s+(?:for|about)\s+(site|patient|study)\s+(\S+)",
            r"notify\s+manager\s+about\s+(site|patient|study)\s+(\S+)"
        ],
        ActionType.GENERATE_REPORT: [
            r"generate\s+(?:a\s+)?report\s+(?:for\s+)?(site|patient|study)\s+(\S+)",
            r"create\s+(?:a\s+)?(?:summary|report)\s+(?:for\s+)?(site|patient|study)\s+(\S+)",
            r"report\s+on\s+(site|patient|study)\s+(\S+)"
        ],
        ActionType.CREATE_ALERT: [
            r"create\s+(?:an?\s+)?alert\s+(?:for\s+)?(site|patient|study)\s+(\S+)",
            r"flag\s+(site|patient|study)\s+(\S+)",
            r"alert\s+(?:about\s+)?(site|patient|study)\s+(\S+)"
        ],
        ActionType.SCHEDULE_FOLLOWUP: [
            r"schedule\s+(?:a\s+)?follow\s*-?\s*up\s+(?:for\s+)?(site|patient|study)\s+(\S+)",
            r"set\s+(?:a\s+)?reminder\s+(?:for\s+)?(site|patient|study)\s+(\S+)"
        ],
        ActionType.SEND_NOTIFICATION: [
            r"send\s+(?:a\s+)?(?:notification|message|email)\s+(?:to\s+)?(\S+)\s+about\s+(site|patient|study)\s+(\S+)",
            r"notify\s+(\S+)\s+about\s+(site|patient|study)\s+(\S+)"
        ],
        ActionType.QUERY_DATA: [
            r"(?:get|fetch|retrieve|show)\s+(?:data|info|information)\s+(?:for|about)\s+(site|patient|study)\s+(\S+)",
            r"what\s+(?:is|are)\s+(?:the\s+)?(?:details|status)\s+(?:of|for)\s+(site|patient|study)\s+(\S+)"
        ]
    }
    
    def __init__(self, graph: nx.DiGraph, llm=None, report_generator=None, 
                 alert_engine=None, dqi_calculator=None):
        self.graph = graph
        self.llm = llm
        self.report_generator = report_generator
        self.alert_engine = alert_engine
        self.dqi_calculator = dqi_calculator
        self._action_counter = 0
        self._audit_log: List[Dict] = []
        self._init_llm()
    
    def _init_llm(self):
        if self.llm is None:
            try:
                from langchain_groq import ChatGroq
                self.llm = ChatGroq(
                    model="qwen/qwen3-32b",
                    temperature=0.1,
                    groq_api_key=os.getenv("GROQ_API_KEY")
                )
            except Exception:
                self.llm = None
    
    def _generate_action_id(self) -> str:
        self._action_counter += 1
        return f"ACT-{datetime.now().strftime('%Y%m%d%H%M')}-{self._action_counter:04d}"
    
    def execute(self, action_request: str) -> ActionResult:
        """Execute an action from natural language request."""
        start_time = datetime.now()
        action_id = self._generate_action_id()
        
        parsed = self.parse_action(action_request)
        
        if parsed.confidence < 0.5:
            return ActionResult(
                action_id=action_id,
                action_type=parsed.action_type or ActionType.QUERY_DATA,
                status=ActionStatus.FAILED,
                message=f"Could not understand action request: {action_request}"
            )
        
        result = self._execute_action(action_id, parsed)
        
        result.execution_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
        
        self._log_action(action_id, parsed, result)
        
        return result
    
    def parse_action(self, action_request: str) -> ParsedAction:
        """Parse natural language into structured action."""
        action_request_lower = action_request.lower().strip()
        
        for action_type, patterns in self.ACTION_PATTERNS.items():
            for pattern in patterns:
                match = re.search(pattern, action_request_lower)
                if match:
                    groups = match.groups()
                    
                    if action_type == ActionType.SEND_NOTIFICATION:
                        recipient = groups[0] if len(groups) > 0 else None
                        entity_type = groups[1] if len(groups) > 1 else "site"
                        entity_id = groups[2] if len(groups) > 2 else None
                        return ParsedAction(
                            action_type=action_type,
                            entity_type=entity_type,
                            entity_id=entity_id or "",
                            parameters={"recipient": recipient},
                            confidence=0.9,
                            raw_input=action_request
                        )
                    else:
                        entity_type = groups[0] if len(groups) > 0 else "site"
                        entity_id = groups[1] if len(groups) > 1 else None
                        return ParsedAction(
                            action_type=action_type,
                            entity_type=entity_type,
                            entity_id=entity_id or "",
                            confidence=0.9,
                            raw_input=action_request
                        )
        
        if self.llm:
            return self._llm_parse_action(action_request)
        
        return ParsedAction(
            action_type=ActionType.QUERY_DATA,
            entity_type="unknown",
            entity_id="",
            confidence=0.3,
            raw_input=action_request
        )
    
    def _llm_parse_action(self, action_request: str) -> ParsedAction:
        """Use LLM to parse complex action requests."""
        prompt = f"""Parse this action request and extract:
1. action_type: One of [escalate, generate_report, create_alert, schedule_followup, send_notification, update_status, query_data]
2. entity_type: One of [site, patient, study]
3. entity_id: The specific ID mentioned
4. confidence: How confident you are (0.0-1.0)

Request: "{action_request}"

Respond in this exact format:
action_type: [type]
entity_type: [type]
entity_id: [id]
confidence: [score]"""
        
        try:
            response = self.llm.invoke(prompt)
            content = response.content
            
            action_type = ActionType.QUERY_DATA
            entity_type = "unknown"
            entity_id = ""
            confidence = 0.5
            
            for line in content.split("\n"):
                if "action_type:" in line.lower():
                    type_str = line.split(":")[-1].strip().lower()
                    for at in ActionType:
                        if at.value in type_str:
                            action_type = at
                            break
                elif "entity_type:" in line.lower():
                    entity_type = line.split(":")[-1].strip().lower()
                elif "entity_id:" in line.lower():
                    entity_id = line.split(":")[-1].strip()
                elif "confidence:" in line.lower():
                    try:
                        confidence = float(line.split(":")[-1].strip())
                    except ValueError:
                        pass
            
            return ParsedAction(
                action_type=action_type,
                entity_type=entity_type,
                entity_id=entity_id,
                confidence=confidence,
                raw_input=action_request
            )
        except Exception:
            return ParsedAction(
                action_type=ActionType.QUERY_DATA,
                entity_type="unknown",
                entity_id="",
                confidence=0.3,
                raw_input=action_request
            )
    
    def _execute_action(self, action_id: str, parsed: ParsedAction) -> ActionResult:
        """Execute the parsed action."""
        steps = []
        
        if parsed.action_type == ActionType.ESCALATE:
            return self._execute_escalate(action_id, parsed, steps)
        
        elif parsed.action_type == ActionType.GENERATE_REPORT:
            return self._execute_generate_report(action_id, parsed, steps)
        
        elif parsed.action_type == ActionType.CREATE_ALERT:
            return self._execute_create_alert(action_id, parsed, steps)
        
        elif parsed.action_type == ActionType.SCHEDULE_FOLLOWUP:
            return self._execute_schedule_followup(action_id, parsed, steps)
        
        elif parsed.action_type == ActionType.SEND_NOTIFICATION:
            return self._execute_send_notification(action_id, parsed, steps)
        
        elif parsed.action_type == ActionType.QUERY_DATA:
            return self._execute_query_data(action_id, parsed, steps)
        
        else:
            return ActionResult(
                action_id=action_id,
                action_type=parsed.action_type,
                status=ActionStatus.FAILED,
                message=f"Unknown action type: {parsed.action_type}"
            )
    
    def _execute_escalate(self, action_id: str, parsed: ParsedAction, steps: List[str]) -> ActionResult:
        """Execute escalation workflow."""
        steps.append(f"Identified escalation for {parsed.entity_type} {parsed.entity_id}")
        
        entity_data = self._get_entity_data(parsed.entity_type, parsed.entity_id)
        steps.append("Retrieved entity data")
        
        escalation_record = {
            "action_id": action_id,
            "entity_type": parsed.entity_type,
            "entity_id": parsed.entity_id,
            "escalated_at": datetime.now().isoformat(),
            "data": entity_data,
            "status": "escalated"
        }
        steps.append("Created escalation record")
        
        steps.append("Notification queued for manager (simulation)")
        
        return ActionResult(
            action_id=action_id,
            action_type=ActionType.ESCALATE,
            status=ActionStatus.COMPLETED,
            message=f"Successfully escalated {parsed.entity_type} {parsed.entity_id}",
            output=escalation_record,
            steps_executed=steps
        )
    
    def _execute_generate_report(self, action_id: str, parsed: ParsedAction, steps: List[str]) -> ActionResult:
        """Execute report generation workflow."""
        steps.append(f"Generating report for {parsed.entity_type} {parsed.entity_id}")
        
        if self.report_generator:
            try:
                if parsed.entity_type == "site":
                    report = self.report_generator.generate_site_summary(parsed.entity_id)
                elif parsed.entity_type == "study":
                    report = self.report_generator.generate_study_overview(parsed.entity_id)
                else:
                    report = self.report_generator.generate_weekly_digest()
                
                steps.append("Report generated successfully")
                
                return ActionResult(
                    action_id=action_id,
                    action_type=ActionType.GENERATE_REPORT,
                    status=ActionStatus.COMPLETED,
                    message=f"Report generated for {parsed.entity_type} {parsed.entity_id}",
                    output=report.to_markdown(),
                    steps_executed=steps
                )
            except Exception as e:
                steps.append(f"Report generation failed: {str(e)}")
                return ActionResult(
                    action_id=action_id,
                    action_type=ActionType.GENERATE_REPORT,
                    status=ActionStatus.FAILED,
                    message=f"Failed to generate report: {str(e)}",
                    steps_executed=steps
                )
        else:
            entity_data = self._get_entity_data(parsed.entity_type, parsed.entity_id)
            simple_report = f"# Report: {parsed.entity_type.title()} {parsed.entity_id}\n\n"
            simple_report += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
            simple_report += f"Data: {entity_data}"
            
            steps.append("Simple report generated (no ReportGenerator available)")
            
            return ActionResult(
                action_id=action_id,
                action_type=ActionType.GENERATE_REPORT,
                status=ActionStatus.COMPLETED,
                message=f"Report generated for {parsed.entity_type} {parsed.entity_id}",
                output=simple_report,
                steps_executed=steps
            )
    
    def _execute_create_alert(self, action_id: str, parsed: ParsedAction, steps: List[str]) -> ActionResult:
        """Execute alert creation workflow."""
        steps.append(f"Creating alert for {parsed.entity_type} {parsed.entity_id}")
        
        alert_record = {
            "alert_id": f"ALT-{action_id}",
            "entity_type": parsed.entity_type,
            "entity_id": parsed.entity_id,
            "created_at": datetime.now().isoformat(),
            "severity": "medium",
            "status": "active"
        }
        steps.append("Alert record created")
        
        return ActionResult(
            action_id=action_id,
            action_type=ActionType.CREATE_ALERT,
            status=ActionStatus.COMPLETED,
            message=f"Alert created for {parsed.entity_type} {parsed.entity_id}",
            output=alert_record,
            steps_executed=steps
        )
    
    def _execute_schedule_followup(self, action_id: str, parsed: ParsedAction, steps: List[str]) -> ActionResult:
        """Execute follow-up scheduling workflow."""
        steps.append(f"Scheduling follow-up for {parsed.entity_type} {parsed.entity_id}")
        
        followup_date = datetime.now().replace(day=datetime.now().day + 7)
        
        followup_record = {
            "followup_id": f"FUP-{action_id}",
            "entity_type": parsed.entity_type,
            "entity_id": parsed.entity_id,
            "scheduled_for": followup_date.isoformat(),
            "created_at": datetime.now().isoformat(),
            "status": "scheduled"
        }
        steps.append(f"Follow-up scheduled for {followup_date.strftime('%Y-%m-%d')}")
        
        return ActionResult(
            action_id=action_id,
            action_type=ActionType.SCHEDULE_FOLLOWUP,
            status=ActionStatus.COMPLETED,
            message=f"Follow-up scheduled for {parsed.entity_type} {parsed.entity_id}",
            output=followup_record,
            steps_executed=steps
        )
    
    def _execute_send_notification(self, action_id: str, parsed: ParsedAction, steps: List[str]) -> ActionResult:
        """Execute notification sending workflow."""
        recipient = parsed.parameters.get("recipient", "manager")
        steps.append(f"Preparing notification for {recipient}")
        
        notification_record = {
            "notification_id": f"NTF-{action_id}",
            "recipient": recipient,
            "entity_type": parsed.entity_type,
            "entity_id": parsed.entity_id,
            "sent_at": datetime.now().isoformat(),
            "status": "sent"
        }
        steps.append(f"Notification sent to {recipient} (simulation)")
        
        return ActionResult(
            action_id=action_id,
            action_type=ActionType.SEND_NOTIFICATION,
            status=ActionStatus.COMPLETED,
            message=f"Notification sent to {recipient} about {parsed.entity_type} {parsed.entity_id}",
            output=notification_record,
            steps_executed=steps
        )
    
    def _execute_query_data(self, action_id: str, parsed: ParsedAction, steps: List[str]) -> ActionResult:
        """Execute data query workflow."""
        steps.append(f"Querying data for {parsed.entity_type} {parsed.entity_id}")
        
        data = self._get_entity_data(parsed.entity_type, parsed.entity_id)
        steps.append("Data retrieved from knowledge graph")
        
        if self.dqi_calculator and parsed.entity_type == "site":
            try:
                dqi = self.dqi_calculator.calculate_site(parsed.entity_id)
                data["dqi"] = dqi.to_dict()
                steps.append("DQI calculated")
            except Exception:
                pass
        
        return ActionResult(
            action_id=action_id,
            action_type=ActionType.QUERY_DATA,
            status=ActionStatus.COMPLETED,
            message=f"Data retrieved for {parsed.entity_type} {parsed.entity_id}",
            output=data,
            steps_executed=steps
        )
    
    def _get_entity_data(self, entity_type: str, entity_id: str) -> Dict[str, Any]:
        """Retrieve entity data from the graph."""
        node_prefixes = {
            "site": "SITE:",
            "patient": "SUBJECT:",
            "subject": "SUBJECT:",
            "study": "STUDY:"
        }
        
        prefix = node_prefixes.get(entity_type.lower(), "")
        node_key = f"{prefix}{entity_id}" if prefix and not entity_id.startswith(prefix) else entity_id
        
        if self.graph.has_node(node_key):
            return dict(self.graph.nodes[node_key])
        
        return {"entity_id": entity_id, "entity_type": entity_type, "error": "Not found"}
    
    def _log_action(self, action_id: str, parsed: ParsedAction, result: ActionResult):
        """Log action for audit trail."""
        self._audit_log.append({
            "action_id": action_id,
            "timestamp": datetime.now().isoformat(),
            "request": parsed.raw_input,
            "parsed": {
                "action_type": parsed.action_type.value,
                "entity_type": parsed.entity_type,
                "entity_id": parsed.entity_id,
                "confidence": parsed.confidence
            },
            "result": {
                "status": result.status.value,
                "message": result.message,
                "execution_time_ms": result.execution_time_ms
            }
        })
    
    def get_audit_log(self) -> List[Dict]:
        """Get the audit log of all actions."""
        return self._audit_log.copy()
    
    def get_available_actions(self) -> List[Dict[str, str]]:
        """Get list of available actions with examples."""
        return [
            {"action": "escalate", "example": "Escalate site 637 to manager"},
            {"action": "generate_report", "example": "Generate a report for site 637"},
            {"action": "create_alert", "example": "Create an alert for patient 12345"},
            {"action": "schedule_followup", "example": "Schedule a follow-up for site 637"},
            {"action": "send_notification", "example": "Send notification to CRA about site 637"},
            {"action": "query_data", "example": "Get data for site 637"}
        ]
