from enum import Enum
from typing import Optional, Any
from app.models.entities import User, Case, Evidence, Finding, CaseAssignment
from app.models.enums import Role, Department

class Action(str, Enum):
    VIEW_CASE = "VIEW_CASE"
    UPDATE_CASE = "UPDATE_CASE"
    ASSIGN_CASE = "ASSIGN_CASE"
    SNAPSHOT_CASE = "SNAPSHOT_CASE"

    VIEW_EVIDENCE = "VIEW_EVIDENCE"
    UPLOAD_EVIDENCE = "UPLOAD_EVIDENCE"
    CLASSIFY_EVIDENCE = "CLASSIFY_EVIDENCE"
    DOWNLOAD_EVIDENCE = "DOWNLOAD_EVIDENCE"
    PROCESS_EVIDENCE = "PROCESS_EVIDENCE"

    VIEW_OBSERVATION = "VIEW_OBSERVATION"
    CREATE_OBSERVATION = "CREATE_OBSERVATION"
    VERIFY_OBSERVATION = "VERIFY_OBSERVATION"

    VIEW_FINDING = "VIEW_FINDING"
    CREATE_FINDING = "CREATE_FINDING"
    VERIFY_FINDING = "VERIFY_FINDING"

    VIEW_CLAIM = "VIEW_CLAIM"
    CREATE_CLAIM = "CREATE_CLAIM"
    VERIFY_CLAIM = "VERIFY_CLAIM"

    VIEW_TIMELINE = "VIEW_TIMELINE"
    MODIFY_TIMELINE = "MODIFY_TIMELINE"

    VIEW_ENTITY = "VIEW_ENTITY"
    CREATE_ENTITY = "CREATE_ENTITY"
    CONFIRM_ENTITY_LINK = "CONFIRM_ENTITY_LINK"

    VIEW_HYPOTHESIS = "VIEW_HYPOTHESIS"
    GENERATE_HYPOTHESIS = "GENERATE_HYPOTHESIS"
    CHALLENGE_HYPOTHESIS = "CHALLENGE_HYPOTHESIS"
    REVIEW_HYPOTHESIS = "REVIEW_HYPOTHESIS"

    VIEW_GAP_CONFLICT = "VIEW_GAP_CONFLICT"
    DETECT_GAP_CONFLICT = "DETECT_GAP_CONFLICT"
    RESOLVE_GAP_CONFLICT = "RESOLVE_GAP_CONFLICT"

    QUERY_COPILOT = "QUERY_COPILOT"
    GENERATE_REPORT = "GENERATE_REPORT"
    VIEW_REPORT = "VIEW_REPORT"

from sqlalchemy import inspect

def is_case_assigned(user: User, case: Case, assignments: Optional[list] = None) -> bool:
    if user.role == Role.ADMIN:
        return True
    if case.created_by == user.id:
        return True
    if assignments is not None:
        for a in assignments:
            if a.user_id == user.id and a.case_id == case.id and a.is_active:
                return True
    else:
        try:
            insp = inspect(case)
            if "assignments" in insp.dict:
                for a in insp.dict["assignments"]:
                    if a.user_id == user.id and a.is_active:
                        return True
        except Exception:
            pass
    return False

def check_access(
    user: User,
    action: Action,
    resource: Optional[Any] = None,
    case: Optional[Case] = None,
    assignments: Optional[list] = None
) -> bool:
    """
    Attribute-Based Access Control (ABAC) evaluation.
    Evaluates User (Role, Department), Action, Resource (Evidence department restrictions), and Case context.
    """
    # 1. Admin has access across system within organization
    if user.role == Role.ADMIN:
        return True

    # 2. Case assignment check (if case context is present)
    if case is not None:
        if not is_case_assigned(user, case, assignments):
            return False

    # 3. Evidence department authorization
    if action in (Action.VIEW_EVIDENCE, Action.DOWNLOAD_EVIDENCE, Action.PROCESS_EVIDENCE):
        if resource is not None and isinstance(resource, Evidence):
            authorized = resource.authorized_departments or []
            # If authorized_departments is defined, check if user's department is permitted
            if authorized:
                # String comparison or Enum comparison
                user_dept_str = user.department.value if hasattr(user.department, "value") else str(user.department)
                auth_dept_strs = [d.value if hasattr(d, "value") else str(d) for d in authorized]
                # Investigation lead/investigator has oversight, or user dept must match
                if user_dept_str not in auth_dept_strs and user.role not in (Role.LEAD_INVESTIGATOR, Role.ADMIN):
                    return False

    # 4. Role action capabilities
    verification_actions = (
        Action.VERIFY_OBSERVATION,
        Action.VERIFY_FINDING,
        Action.VERIFY_CLAIM,
        Action.REVIEW_HYPOTHESIS,
        Action.CONFIRM_ENTITY_LINK,
        Action.RESOLVE_GAP_CONFLICT,
    )
    if action in verification_actions:
        if user.role not in (Role.ADMIN, Role.LEAD_INVESTIGATOR, Role.INVESTIGATOR):
            return False

    # 5. Departmental boundaries on timelines
    if action == Action.MODIFY_TIMELINE:
        if user.department == Department.FINANCIAL:
            return False

    # 6. Case assignment mutation
    if action == Action.ASSIGN_CASE:
        if user.role not in (Role.ADMIN, Role.LEAD_INVESTIGATOR):
            return False

    return True
