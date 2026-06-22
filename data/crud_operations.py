"""
crud_operations.py
I/O pipelines for data ingestion and OR-Tools matrix extraction.
"""
from typing import List, Dict, Tuple, Optional, Set
from sqlalchemy.orm import Session as DBSession
from sqlalchemy import select
from .models import Teacher, Language, TeacherPref, Session as DBSession_Model, Room, Timeslot, Group

def insert_teacher_with_preferences(
    db: DBSession, 
    teacher_name: str, 
    lang_ids: List[int], 
    preferences: List[Dict[str, float]]
) -> Teacher:
    """
    Atomic insertion of a Teacher, their language qualifications, and availability weights.
    
    :param preferences: List of dicts e.g. [{"slot_id": 1, "weight": 10.0, "group_id": None}]
    """
    # 1. Fetch requested Language objects
    languages = db.scalars(select(Language).where(Language.lang_id.in_(lang_ids))).all()
    
    # 2. Construct Teacher
    new_teacher = Teacher(name=teacher_name, languages=list(languages))
    
    # 3. Attach Preferences
    for pref in preferences:
        new_pref = TeacherPref(
            slot_id=pref["slot_id"],
            weight=pref["weight"],
            group_id=pref.get("group_id")
        )
        new_teacher.preferences.append(new_pref)
        
    db.add(new_teacher)
    db.commit()
    db.refresh(new_teacher)
    
    return new_teacher

def get_preference_matrix(db: DBSession) -> Dict[Tuple[int, int], float]:
    """
    Extracts the teacher-timeslot preference weights for the OR-Tools solver.
    Returns a dictionary keyed by (teacher_id, slot_id) mapping to the weight.
    This O(1) lookup dictionary is the exact format OR-Tools CP-SAT requires.
    """
    stmt = select(TeacherPref.teacher_id, TeacherPref.slot_id, TeacherPref.weight)
    results = db.execute(stmt).all()
    
    # Construct the optimization matrix lookup
    pref_matrix: Dict[Tuple[int, int], float] = {
        (row.teacher_id, row.slot_id): row.weight for row in results
    }
    
    return pref_matrix

def get_booked_slots(db: DBSession, calendar_date: Optional[str] = None) -> Set[Tuple[int, int, int]]:
    """
    Query existing sessions (especially Makeup sessions) for a specific date.
    Returns a set of (group_id, slot_id, room_id) tuples that are already booked.
    These are "hard locked" variables for OR-Tools pre-processing.
    
    :param calendar_date: ISO date string (YYYY-MM-DD). If None, returns all booked slots.
    :return: Set of (group_id, slot_id, room_id) tuples representing locked bookings
    """
    query = select(DBSession_Model.group_id, DBSession_Model.slot_id, DBSession_Model.room_id)
    
    if calendar_date:
        query = query.where(DBSession_Model.calendar_date == calendar_date)
    
    results = db.execute(query).all()
    
    booked_slots: Set[Tuple[int, int, int]] = {
        (row.group_id, row.slot_id, row.room_id) for row in results
    }
    
    return booked_slots

def get_booked_rooms_by_slot(db: DBSession, calendar_date: Optional[str] = None) -> Dict[int, Set[int]]:
    """
    Returns a dict mapping slot_id -> set of booked room_ids for a given date.
    Useful for room availability checks in the solver's constraint loop.
    
    :param calendar_date: ISO date string. If None, returns all bookings.
    :return: Dict[slot_id] -> Set[room_id]
    """
    query = select(DBSession_Model.slot_id, DBSession_Model.room_id)
    
    if calendar_date:
        query = query.where(DBSession_Model.calendar_date == calendar_date)
    
    results = db.execute(query).all()
    
    booked_by_slot: Dict[int, Set[int]] = {}
    for row in results:
        if row.slot_id not in booked_by_slot:
            booked_by_slot[row.slot_id] = set()
        booked_by_slot[row.slot_id].add(row.room_id)
    
    return booked_by_slot

def get_teacher_hard_constraints(db: DBSession, teacher_id: int) -> Dict[int, float]:
    """
    Fetch HARD CONSTRAINTS for a teacher (group_id IS NOT NULL).
    These are preferences tied to specific groups that the solver MUST enforce.
    
    :param teacher_id: Teacher's ID
    :return: Dict[slot_id] -> weight (for hard override logic in solver)
    """
    stmt = select(TeacherPref.slot_id, TeacherPref.weight).where(
        (TeacherPref.teacher_id == teacher_id) & 
        (TeacherPref.group_id.isnot(None))
    )
    results = db.execute(stmt).all()
    
    hard_constraints: Dict[int, float] = {
        row.slot_id: row.weight for row in results
    }
    
    return hard_constraints

def get_teacher_global_preferences(db: DBSession, teacher_id: int) -> Dict[int, float]:
    """
    Fetch GLOBAL PREFERENCES for a teacher (group_id IS NULL).
    These are optimization biases applied uniformly across the teacher's schedule.
    
    :param teacher_id: Teacher's ID
    :return: Dict[slot_id] -> weight (soft optimization preference)
    """
    stmt = select(TeacherPref.slot_id, TeacherPref.weight).where(
        (TeacherPref.teacher_id == teacher_id) & 
        (TeacherPref.group_id.is_(None))
    )
    results = db.execute(stmt).all()
    
    global_prefs: Dict[int, float] = {
        row.slot_id: row.weight for row in results
    }
    
    return global_prefs