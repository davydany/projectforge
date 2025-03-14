from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import date, datetime
import uuid

class TeamMember(BaseModel):
    """Model for team members"""
    id: Optional[int] = None
    first_name: str
    last_name: str
    email: Optional[str] = None
    team_id: Optional[int] = None
    
    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary for database storage"""
        return {
            "id": self.id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": self.email,
            "team_id": self.team_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TeamMember':
        """Create model from dictionary"""
        return cls(**data)

class Team(BaseModel):
    """Model for teams"""
    id: Optional[int] = None
    name: str
    description: Optional[str] = None
    location: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary for database storage"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "location": self.location
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Team':
        """Create model from dictionary"""
        return cls(**data)

class Task(BaseModel):
    """Model for tasks"""
    id: Optional[int] = None
    project_id: Optional[int] = None
    sub_project_id: Optional[int] = None
    name: str
    description: Optional[str] = None
    jira_ticket: Optional[str] = None
    status: str = "not started"
    assigned_to: Optional[int] = None
    
    @validator('status')
    def validate_status(cls, v):
        valid_statuses = ["not started", "started", "in progress", "blocked", "waiting", "completed"]
        if v not in valid_statuses:
            raise ValueError(f"Status must be one of {valid_statuses}")
        return v
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary for database storage"""
        return {
            "id": self.id,
            "project_id": self.project_id,
            "sub_project_id": self.sub_project_id,
            "name": self.name,
            "description": self.description,
            "jira_ticket": self.jira_ticket,
            "status": self.status,
            "assigned_to": self.assigned_to
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Task':
        """Create model from dictionary"""
        return cls(**data)

class SubProject(BaseModel):
    """Model for sub-projects"""
    id: Optional[int] = None
    project_id: int
    name: str
    description: Optional[str] = None
    start_date: date
    end_date: date
    deviation: int = 0
    assigned_to: Optional[int] = None
    
    @validator('end_date')
    def end_date_after_start_date(cls, v, values):
        if 'start_date' in values and v < values['start_date']:
            raise ValueError('End date must be after start date')
        return v
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary for database storage"""
        return {
            "id": self.id,
            "project_id": self.project_id,
            "name": self.name,
            "description": self.description,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "deviation": self.deviation,
            "assigned_to": self.assigned_to
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SubProject':
        """Create model from dictionary"""
        # Convert string dates to date objects if needed
        if isinstance(data.get('start_date'), str):
            data['start_date'] = datetime.fromisoformat(data['start_date'].split('T')[0]).date()
        if isinstance(data.get('end_date'), str):
            data['end_date'] = datetime.fromisoformat(data['end_date'].split('T')[0]).date()
        return cls(**data)

class Project(BaseModel):
    """Model for projects"""
    id: Optional[int] = None
    name: str
    description: Optional[str] = None
    start_date: date
    end_date: date
    deviation: int = 0
    assigned_to: Optional[int] = None
    
    @validator('end_date')
    def end_date_after_start_date(cls, v, values):
        if 'start_date' in values and v < values['start_date']:
            raise ValueError('End date must be after start date')
        return v
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary for database storage"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "deviation": self.deviation,
            "assigned_to": self.assigned_to
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Project':
        """Create model from dictionary"""
        # Convert string dates to date objects if needed
        if isinstance(data.get('start_date'), str):
            data['start_date'] = datetime.fromisoformat(data['start_date'].split('T')[0]).date()
        if isinstance(data.get('end_date'), str):
            data['end_date'] = datetime.fromisoformat(data['end_date'].split('T')[0]).date()
        return cls(**data)

class Note(BaseModel):
    """Model for notes"""
    id: Optional[int] = None
    task_id: int
    note: str
    created_at: datetime = Field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary for database storage"""
        return {
            "id": self.id,
            "task_id": self.task_id,
            "note": self.note,
            "created_at": self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Note':
        """Create model from dictionary"""
        # Convert string datetime to datetime object if needed
        if isinstance(data.get('created_at'), str):
            data['created_at'] = datetime.fromisoformat(data['created_at'].replace('Z', '+00:00'))
        return cls(**data)

class Reminder(BaseModel):
    """Model for reminders"""
    id: Optional[int] = None
    task_id: int
    reminder_date: date
    note: str
    followed_up: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary for database storage"""
        return {
            "id": self.id,
            "task_id": self.task_id,
            "reminder_date": self.reminder_date.isoformat(),
            "note": self.note,
            "followed_up": 1 if self.followed_up else 0
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Reminder':
        """Create model from dictionary"""
        # Convert string date to date object if needed
        if isinstance(data.get('reminder_date'), str):
            data['reminder_date'] = datetime.fromisoformat(data['reminder_date'].split('T')[0]).date()
        # Convert integer to boolean for followed_up
        if 'followed_up' in data and isinstance(data['followed_up'], int):
            data['followed_up'] = bool(data['followed_up'])
        return cls(**data) 