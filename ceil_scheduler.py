# =============================================================================
# CEIL S3 2025-2026 — Multi-Criteria Automated Scheduling Optimizer
# Engine: Google OR-Tools CP-SAT
# Version: 5.0 — Hard Constraint: SI groups strictly exactly 4 days a week
# =============================================================================

import json
import collections
import logging
import os
from ortools.sat.python import cp_model

logger = logging.getLogger(__name__)

PREF_COST = {
    "preferred":   -10,
    "neutral":       0,
    "dislike":      50,
    "unavailable": None   
}

def load_data(json_path: str) -> dict:
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)

def build_index_maps(data: dict) -> dict:
    days  = data["metadata"]["days"]        
    slots = [s["id"] for s in data["metadata"]["slots"]]  

    timeslots = [(d, s) for d in range(len(days)) for s in slots]
    ts_to_idx = {ts: i for i, ts in enumerate(timeslots)}

    teachers = {t["id"]: t for t in data["teachers"]}
    groups   = {g["id"]: g for g in data["groups"]}
    rooms    = {r["id"]: r for r in data["rooms"]}

    teacher_list = list(teachers.keys())
    group_list   = list(groups.keys())
    room_list    = list(rooms.keys())

    special_room_ids = [r["id"] for r in data["rooms"] if r.get("is_special", False)]
    cefr_map = {g["id"]: g.get("cefr_numeric", 1) for g in data["groups"]}

    return {
        "days": days,
        "slots": slots,
        "timeslots": timeslots,
        "ts_to_idx": ts_to_idx,
        "teachers": teachers,
        "groups": groups,
        "rooms": rooms,
        "teacher_list": teacher_list,
        "group_list": group_list,
        "room_list": room_list,
        "special_room_ids": special_room_ids,
        "cefr_map": cefr_map,
        "num_days": len(days),
        "num_slots": len(slots),
        "num_ts": len(timeslots),
    }

def build_preference_matrix(data: dict, idx: dict) -> dict:
    days       = idx["days"]
    slots      = idx["slots"]
    day_to_idx = {d: i for i, d in enumerate(days)}

    pref_cost = {}
    for t in data["teachers"]:
        tid = t["id"]
        pref_cost[tid] = {}
        t_prefs = t.get("preferences", {})
        
        for day_str, day_i in day_to_idx.items():
            for s in slots:
                if day_str in t_prefs and isinstance(t_prefs[day_str], dict):
                    raw = t_prefs[day_str].get(str(s), "neutral")
                else:
                    raw = t_prefs.get(f"{day_str}_{s}", "neutral")
                
                raw = str(raw).strip().lower()
                pref_cost[tid][(day_i, s)] = PREF_COST.get(raw, 0)   
    return pref_cost

def get_allowed_timeslots(group: dict, idx: dict) -> list:
    """Calculates all possible open timeslot choices for a group. 
    
    Unconstrained by default across all active working days, bound 
    strictly by structural hours and individual teacher availability.
    """
    allowed = []
    # 🟢 Completely bypass group.get("allowed_days"). Open up all system days.
    for di in range(idx["num_days"]):
        # Maintain allowed_slots so track rules (like Evening Shifts) still bind properly
        for s in group.get("allowed_slots", idx["slots"]):
            allowed.append((di, s))
    return allowed

def build_model(data: dict, idx: dict, pref_cost: dict, weights: dict) -> tuple:
    model = cp_model.CpModel()

    # Extract dynamic weights locally (SI Spread is removed entirely)
    w_gap = weights.get("W_GAP", 30)
    w_pref = weights.get("W_PREFERENCE", 1)
    w_load = weights.get("W_LOAD_BALANCE", 20)
    w_fairness = weights.get("W_FAIRNESS", 15)
    w_room_change = weights.get("W_ROOM_CHANGE", 10)
    w_cognitive = weights.get("W_COGNITIVE", 5)

    days, slots = idx["days"], idx["slots"]
    num_days, num_slots = idx["num_days"], idx["num_slots"]
    groups = idx["groups"]
    room_list = idx["room_list"]
    special_rooms = set(idx["special_room_ids"])
    normal_rooms = [r for r in room_list if r not in special_rooms]
    group_list, teacher_list = idx["group_list"], idx["teacher_list"]

    # 1. Base Variables
    x = {}
    for gid in group_list:
        x[gid] = {}
        grp = groups[gid]
        allowed_ts = get_allowed_timeslots(grp, idx)
        eligible_rooms = list(special_rooms) if grp.get("is_ielts", False) else normal_rooms
        
        for rid in eligible_rooms:
            x[gid][rid] = {}
            for (d, s) in allowed_ts:
                x[gid][rid][(d, s)] = model.NewBoolVar(f"x__{gid}__{rid}__d{d}s{s}")

    # 2. Structural Requirements
    for gid in group_list:
        grp = groups[gid]
        all_x_for_group = [x[gid][rid][(d, s)] for rid in x[gid] for (d, s) in x[gid][rid]]
        if all_x_for_group:
            model.Add(sum(all_x_for_group) == grp.get("sessions_per_week", 2))

    for rid in room_list:
        for d in range(num_days):
            for s in slots:
                occupants = [x[gid][rid][(d, s)] for gid in group_list if rid in x[gid] and (d, s) in x[gid][rid]]
                if occupants:
                    model.Add(sum(occupants) <= 1)

    teacher_groups = collections.defaultdict(list)
    for gid in group_list:
        tid = groups[gid].get("teacher_id", "T_1")
        teacher_groups[tid].append(gid)

    for tid in teacher_list:
        for d in range(num_days):
            for s in slots:
                teacher_slot_vars = [x[gid][rid][(d, s)] for gid in teacher_groups[tid] for rid in x[gid] if (d, s) in x[gid][rid]]
                if not teacher_slot_vars:
                    continue
                if pref_cost[tid].get((d, s)) is None:
                    model.Add(sum(teacher_slot_vars) == 0)
                else:
                    model.Add(sum(teacher_slot_vars) <= 1)

    # 3. Evening Track Restraint
    for gid in group_list:
        if groups[gid].get("is_evening", False):
            for rid in x[gid]:
                for (d, s) in list(x[gid][rid].keys()):
                    if s != slots[-1]: # Strictly binding to the final possible shift
                        model.Add(x[gid][rid][(d, s)] == 0)

    # 4. Strict Boolean Arrays for Teacher States
    active = {}
    for tid in teacher_list:
        active[tid] = {}
        for d in range(num_days):
            for s in slots:
                # Guaranteed BoolVar (Critical for .Not() operator later)
                v = model.NewBoolVar(f"active__{tid}__d{d}s{s}")
                teacher_slot_vars = [x[gid][rid][(d, s)] for gid in teacher_groups[tid] for rid in x[gid] if (d, s) in x[gid][rid]]
                if teacher_slot_vars:
                    model.AddMaxEquality(v, teacher_slot_vars)
                else:
                    model.Add(v == 0)
                active[tid][(d, s)] = v

    # 5. Gap Penalty
    gap_vars = {}
    gap_penalty_terms = []
    for tid in teacher_list:
        gap_vars[tid] = {}
        for d in range(num_days):
            for si in range(num_slots):
                s = slots[si]
                act = active[tid][(d, s)]
                g_var = model.NewBoolVar(f"gap__{tid}__d{d}s{si}")
                gap_vars[tid][(d, si)] = g_var
                
                # Algebraic Constraint: No logical implication contradiction.
                for si_b in range(si):
                    for si_a in range(si + 1, num_slots):
                        model.Add(g_var >= active[tid][(d, slots[si_b])] + active[tid][(d, slots[si_a])] - act - 1)
                
                gap_penalty_terms.append(w_gap * g_var)

    # 6. Preferences Penalty
    pref_penalty_terms = []
    for tid in teacher_list:
        for d in range(num_days):
            for s in slots:
                cost = pref_cost[tid].get((d, s), 0)
                if cost is None or cost == 0:
                    continue
                pref_penalty_terms.append(w_pref * cost * active[tid][(d, s)])

    # 7. Distribution Penalties
    total_sessions = sum(g.get("sessions_per_week", 2) for g in data["groups"])
    daily_count = {}
    dev = {}
    load_penalty_terms = []

    for d in range(num_days):
        day_vars = [x[gid][rid][(dd, s)] for gid in group_list for rid in x[gid] for (dd, s) in x[gid][rid] if dd == d]
        dc = model.NewIntVar(0, len(group_list) * num_slots, f"daily_count__d{d}")
        model.Add(dc == sum(day_vars))
        daily_count[d] = dc

        dev_var = model.NewIntVar(0, len(group_list) * num_slots * num_days, f"dev__d{d}")
        model.Add(dev_var * num_days >= dc * num_days - total_sessions)
        model.Add(dev_var * num_days >= total_sessions - dc * num_days)
        dev[d] = dev_var
        load_penalty_terms.append(w_load * dev_var)

    teacher_penalty = {}
    pen_lower, pen_upper = -999999, 999999
    for tid in teacher_list:
        t_gap = sum(w_gap * gap_vars[tid][(d, si)] for d in range(num_days) for si in range(num_slots) if (d, si) in gap_vars.get(tid, {})) if gap_vars.get(tid) else 0
        t_pref = sum(w_pref * pref_cost[tid].get((d, s), 0) * active[tid][(d, s)] for d in range(num_days) for s in slots if pref_cost[tid].get((d, s)) not in (None, 0))

        t_pen = model.NewIntVar(pen_lower, pen_upper, f"teacher_penalty__{tid}")
        model.Add(t_pen == t_gap + t_pref)
        teacher_penalty[tid] = t_pen

    max_teacher_penalty = model.NewIntVar(pen_lower, pen_upper, "max_teacher_penalty")
    if teacher_penalty:
        model.AddMaxEquality(max_teacher_penalty, list(teacher_penalty.values()))
    else:
        model.Add(max_teacher_penalty == 0)

    # 8. Room Continuity
    room_change_vars = []
    room_change_terms = []
    teacher_room_vars = {}
    for tid in teacher_list:
        teacher_room_vars[tid] = {}
        for rid in room_list:
            teacher_room_vars[tid][rid] = {}
            for d in range(num_days):
                for s in slots:
                    matching_vars = [x[gid][rid][(d, s)] for gid in teacher_groups[tid] if rid in x[gid] and (d, s) in x[gid][rid]]
                    tr_var = model.NewBoolVar(f"tr__{tid}__{rid}__d{d}s{s}")
                    if matching_vars:
                        model.Add(tr_var == sum(matching_vars))
                    else:
                        model.Add(tr_var == 0)
                    teacher_room_vars[tid][rid][(d, s)] = tr_var

    for tid in teacher_list:
        for d in range(num_days):
            for si in range(1, num_slots):
                s_prev = slots[si - 1]
                s_curr = slots[si]
                rc = model.NewBoolVar(f"rchg__{tid}__d{d}s{si}")
                for rid in room_list:
                    prev_room = teacher_room_vars[tid][rid][(d, s_prev)]
                    curr_room = teacher_room_vars[tid][rid][(d, s_curr)]
                    model.Add(rc >= prev_room + active[tid][(d, s_curr)] - curr_room - 1)
                room_change_vars.append(rc)
                room_change_terms.append(w_room_change * rc)

    # 9. Cognitive Difficulty Jump
    cogn_penalty_terms = []
    for tid in teacher_list:
        t_groups = teacher_groups[tid]
        if len(t_groups) < 2: continue
        for d in range(num_days):
            for si in range(num_slots - 1):
                s_curr, s_next = slots[si], slots[si + 1]
                current_expr, next_expr = [], []
                for gid in t_groups:
                    c_lvl = idx["cefr_map"].get(gid, 1)
                    for rid in x[gid]:
                        if (d, s_curr) in x[gid][rid]: current_expr.append(c_lvl * x[gid][rid][(d, s_curr)])
                        if (d, s_next) in x[gid][rid]: next_expr.append(c_lvl * x[gid][rid][(d, s_next)])

                if not current_expr or not next_expr: continue

                t_cefr_curr = model.NewIntVar(0, 6, f"t_cefr_curr__{tid}__d{d}s{si}")
                t_cefr_next = model.NewIntVar(0, 6, f"t_cefr_next__{tid}__d{d}s{si}")
                model.Add(t_cefr_curr == sum(current_expr))
                model.Add(t_cefr_next == sum(next_expr))

                raw_diff = model.NewIntVar(-6, 6, f"raw_diff__{tid}__d{d}s{si}")
                model.Add(raw_diff == t_cefr_next - t_cefr_curr)
                abs_diff = model.NewIntVar(0, 6, f"abs_diff__{tid}__d{d}s{si}")
                model.AddAbsEquality(abs_diff, raw_diff)

                is_trans = model.NewBoolVar(f"is_trans__{tid}__d{d}s{si}")
                model.AddBoolAnd([active[tid][(d, s_curr)], active[tid][(d, s_next)]]).OnlyEnforceIf(is_trans)
                model.AddBoolOr([active[tid][(d, s_curr)].Not(), active[tid][(d, s_next)].Not()]).OnlyEnforceIf(is_trans.Not())

                final_diff = model.NewIntVar(0, 6, f"final_diff__{tid}__d{d}s{si}")
                model.Add(final_diff == abs_diff).OnlyEnforceIf(is_trans)
                model.Add(final_diff == 0).OnlyEnforceIf(is_trans.Not())

                cogn_penalty_terms.append(w_cognitive * final_diff)

    # 10. Semi-Intensive Structure (HARD CONSTRAINT: Strictly 4 days)
    for gid in group_list:
        if not groups[gid].get("is_si", False): continue
        day_used = {}
        for d in range(num_days):
            d_vars = [x[gid][rid][(dd, s)] for rid in x[gid] for (dd, s) in x[gid][rid] if dd == d]
            dv = model.NewBoolVar(f"si_day_used__{gid}__d{d}")
            if not d_vars:
                model.Add(dv == 0)
            else:
                model.AddMaxEquality(dv, d_vars)
            day_used[d] = dv

        num_days_used = model.NewIntVar(0, num_days, f"si_ndays__{gid}")
        model.Add(num_days_used == sum(day_used.values()))

        # Hard Constraint: SI groups must be scheduled on exactly 4 days
        # (Bounded dynamically in case you accidentally configure a group with less than 4 sessions)
        req_sessions = groups[gid].get("sessions_per_week", 4)
        target_days = 4 if req_sessions >= 4 else req_sessions
        model.Add(num_days_used == target_days)

    # 11. Day Clustering (HARD CONSTRAINT)
    for gid in group_list:
        for d in range(num_days):
            day_session_vars = [x[gid][rid][(dd, s)] for rid in x[gid] for (dd, s) in x[gid][rid] if dd == d]
            if day_session_vars:
                model.Add(sum(day_session_vars) <= 1)

    all_penalty_terms = (
        gap_penalty_terms + pref_penalty_terms + load_penalty_terms +
        [w_fairness * max_teacher_penalty] + room_change_terms +
        cogn_penalty_terms
    )

    model.Minimize(cp_model.LinearExpr.Sum(all_penalty_terms))

    return model, {"x": x}

def diagnose_infeasibility(data: dict, idx: dict, pref_cost: dict) -> str:
    reasons = []
    total_evening_sessions = sum(g.get("sessions_per_week", 2) for g in data["groups"] if g.get("is_evening", False))
    max_evening_slots = len(idx["days"]) * len(data["rooms"])
    if total_evening_sessions > max_evening_slots:
        reasons.append(f"❌ Evening Slot Starvation: Evening groups require {total_evening_sessions} slots. Only {max_evening_slots} available.")

    total_ielts_sessions = sum(g.get("sessions_per_week", 2) for g in data["groups"] if g.get("is_ielts", False))
    num_special_rooms = len(idx["special_room_ids"])
    max_ielts_slots = len(idx["days"]) * len(idx["slots"]) * num_special_rooms
    if total_ielts_sessions > max_ielts_slots:
        reasons.append(f"❌ IELTS Location Shortage: IELTS tracks require {total_ielts_sessions} slots. Teacher's Room slots total {max_ielts_slots}.")

    teacher_groups = collections.defaultdict(list)
    for gid in idx["group_list"]:
        tid = idx["groups"][gid].get("teacher_id", "T_1")
        teacher_groups[tid].append(gid)

    for tid in idx["teacher_list"]:
        tname = idx["teachers"].get(tid, {}).get("name", tid)  
        required_sessions = sum(idx["groups"][gid].get("sessions_per_week", 2) for gid in teacher_groups[tid])
        open_slots = sum(1 for (d, s) in pref_cost[tid] if pref_cost[tid][(d, s)] is not None)
        
        if required_sessions > open_slots:
            reasons.append(f"❌ Teacher Starvation: '{tname}' ({tid}) has {required_sessions} sessions assigned, but only {open_slots} open slot(s).")
            
        # New Diagnostics: Catch if a teacher assigned to an SI class doesn't even work 4 days
        si_groups_for_teacher = [g for g in teacher_groups[tid] if idx["groups"][g].get("is_si", False)]
        if si_groups_for_teacher:
            working_days = len(set(d for (d, s) in pref_cost[tid] if pref_cost[tid][(d, s)] is not None))
            if working_days < 4:
                reasons.append(f"❌ SI Unavailability: '{tname}' is assigned an SI class requiring 4 days, but their availability matrix only allows them to work on {working_days} days.")

    if not reasons:
        return "• Schedule Matrix Congestion: Overlapping slot restrictions prevent a clear distribution path. Verify if day metrics are over-constrained."
    return "\n\n".join(reasons)

def solve(model: cp_model.CpModel, time_limit_s: int = 300, log_cb=None) -> tuple:
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds  = time_limit_s

    # --- REFACTORED: Dynamic Hardware-Aware Thread Allocation ---
    available_cores = os.cpu_count() or 2
    safe_workers = max(1, available_cores - 1) if available_cores > 2 else 1
    solver.parameters.num_search_workers = safe_workers
    # ------------------------------------------------------------

    solver.parameters.log_search_progress  = True
    solver.parameters.cp_model_presolve    = True
    if log_cb:
        solver.log_callback = log_cb
    else:
        solver.log_callback = lambda msg: logger.info(f"[OR-Tools Engine] {msg}")

    status = solver.Solve(model)
    return solver, solver.StatusName(status)

def extract_schedule(solver, solver_vars: dict, idx: dict, data: dict) -> list:
    x = solver_vars["x"]
    days = idx["days"]
    slot_labels = {s["id"]: s["label"] for s in data["metadata"]["slots"]}

    schedule = []
    for gid in idx["group_list"]:
        grp = idx["groups"][gid]
        teacher_id = grp.get("teacher_id", "T_Unknown")
        
        # Format human readable output labels instead of pure IDs
        teacher_name = idx["teachers"].get(teacher_id, {}).get("name", teacher_id)
        group_name = grp.get("name", gid)

        for rid in x[gid]:
            room_name = idx["rooms"].get(rid, {}).get("name", rid)
            for (d, s), var in x[gid][rid].items():
                if solver.Value(var) == 1:
                    schedule.append({
                        "group":    group_name,
                        "language": grp.get("language", "English"),
                        "level":    grp.get("level", "A1"),
                        "teacher":  teacher_name,
                        "day":      days[d],
                        "slot":     slot_labels[s],
                        "room":     room_name,
                    })

    day_order = {d: i for i, d in enumerate(days)}
    schedule.sort(key=lambda r: (day_order.get(r["day"], 0), r["slot"], r["room"]))
    print(f"🔬 PROBE SOLVER: First record output: {schedule[0]}")
    return schedule

def run_solver(input_data: dict, penalty_weights: dict, log_cb=None) -> dict:
    try:
        idx = build_index_maps(input_data)
        pref_cost = build_preference_matrix(input_data, idx)
        
        model, solver_vars = build_model(input_data, idx, pref_cost, penalty_weights)
        
        # --- Fetch the timeout limit dynamically from metadata ---
        time_limit = input_data.get("metadata", {}).get("solver_timeout", 60)
        solver, status = solve(model, time_limit_s=time_limit, log_cb=log_cb)
        
        if status in ("OPTIMAL", "FEASIBLE"):
            return {
                "status": "SUCCESS",
                "objective_value": solver.ObjectiveValue(),
                "schedule": extract_schedule(solver, solver_vars, idx, input_data)
            }
        return {"status": "INFEASIBLE", "schedule": [], "objective_value": -1, "reason": diagnose_infeasibility(input_data, idx, pref_cost)}
    except Exception as e:
        logger.exception(f"Solver pipeline crashed: {str(e)}")
        return {"status": "CRASHED", "schedule": [], "objective_value": -1, "reason": str(e)}