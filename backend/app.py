from flask import Flask, render_template, request, jsonify, send_from_directory
from owlready2 import *
import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# --- CONFIGURATION ---
ONTOLOGY_PATH = os.path.join(app.root_path, "project.rdf")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
FRONTEND_DIR = os.path.join(app.root_path, '../frontend')
ALLOWED_FRONTEND_ORIGIN = "http://localhost:5173"

client = Groq(api_key=GROQ_API_KEY)

# Load ontology once at startup (absolute path) and provide a helper for reloads
onto_world = None

# Default career-role blueprint used for scoring and ontology seeding
ROLE_BLUEPRINTS = {
    "Software Engineer": {
        "trait_targets": {
            "Openness": {"target": 82, "weight": 0.22},
            "Conscientiousness": {"target": 88, "weight": 0.30},
            "Neuroticism": {"target": 28, "weight": 0.20},
            "Agreeableness": {"target": 58, "weight": 0.14},
            "Extraversion": {"target": 48, "weight": 0.14},
        },
        "skills": ["System Design", "Code Quality", "Problem Decomposition", "Stakeholder Communication"],
    },
    "Manager": {
        "trait_targets": {
            "Extraversion": {"target": 80, "weight": 0.28},
            "Agreeableness": {"target": 78, "weight": 0.24},
            "Conscientiousness": {"target": 84, "weight": 0.26},
            "Openness": {"target": 70, "weight": 0.12},
            "Neuroticism": {"target": 36, "weight": 0.10},
        },
        "skills": ["Coaching", "Decision Making", "Conflict Resolution", "Stakeholder Alignment"],
    },
    "Researcher": {
        "trait_targets": {
            "Openness": {"target": 90, "weight": 0.32},
            "Conscientiousness": {"target": 76, "weight": 0.26},
            "Extraversion": {"target": 38, "weight": 0.12},
            "Agreeableness": {"target": 64, "weight": 0.14},
            "Neuroticism": {"target": 34, "weight": 0.16},
        },
        "skills": ["Experimental Design", "Data Analysis", "Technical Writing", "Cross-team Collaboration"],
    },
}


def ensure_custom_properties(o):
    """Ensure custom data properties exist on the ontology even after reloads."""
    created_new = False
    with o:
        jp = getattr(o, "jobPerformance", None) or o.search_one(iri=f"{o.base_iri}jobPerformance") or o.search_one(iri=f"{o.base_iri}#jobPerformance")
        if not jp:
            class jobPerformance(DataProperty):  # type: ignore
                domain = [o.Participant]
                range = [float]
                label = ["jobPerformance"]
                comment = ["Calculated predicted score for Job Performance"]
            created_new = True

        ap = getattr(o, "academicPerformance", None) or o.search_one(iri=f"{o.base_iri}academicPerformance") or o.search_one(iri=f"{o.base_iri}#academicPerformance")
        if not ap:
            class academicPerformance(DataProperty):  # type: ignore
                domain = [o.Participant]
                range = [float]
                label = ["academicPerformance"]
                comment = ["Calculated predicted score for Academic Performance"]
            created_new = True

        hj = getattr(o, "hasJustificationReport", None) or o.search_one(iri=f"{o.base_iri}hasJustificationReport") or o.search_one(iri=f"{o.base_iri}#hasJustificationReport")
        if not hj:
            class hasJustificationReport(DataProperty):  # type: ignore
                """Stores the generated justification narrative for a participant."""
                domain = [o.Participant]
                range = [str]
                label = ["hasJustificationReport"]
                comment = ["Explainability report for the participant's scores"]
            created_new = True

        # Career role fit extensions
        cr = getattr(o, "CareerRole", None) or o.search_one(iri=f"{o.base_iri}CareerRole") or o.search_one(iri=f"{o.base_iri}#CareerRole")
        if not cr:
            class CareerRole(Thing):  # type: ignore
                label = ["CareerRole"]
            created_new = True

        sk = getattr(o, "Skill", None) or o.search_one(iri=f"{o.base_iri}Skill") or o.search_one(iri=f"{o.base_iri}#Skill")
        if not sk:
            class Skill(Thing):  # type: ignore
                label = ["Skill"]
            created_new = True

        trait_cls = getattr(o, "Trait", None) or o.search_one(iri=f"{o.base_iri}Trait") or o.search_one(name="Trait")
        rt = getattr(o, "requiresTrait", None) or o.search_one(iri=f"{o.base_iri}requiresTrait") or o.search_one(iri=f"{o.base_iri}#requiresTrait")
        if not rt and trait_cls:
            class requiresTrait(ObjectProperty):  # type: ignore
                domain = [o.CareerRole] if getattr(o, "CareerRole", None) else [Thing]
                range = [trait_cls]
                label = ["requiresTrait"]
            created_new = True

        rs = getattr(o, "requiresSkill", None) or o.search_one(iri=f"{o.base_iri}requiresSkill") or o.search_one(iri=f"{o.base_iri}#requiresSkill")
        if not rs and getattr(o, "Skill", None):
            class requiresSkill(ObjectProperty):  # type: ignore
                domain = [o.CareerRole] if getattr(o, "CareerRole", None) else [Thing]
                range = [o.Skill]
                label = ["requiresSkill"]
            created_new = True

        tw = getattr(o, "traitWeight", None) or o.search_one(iri=f"{o.base_iri}traitWeight") or o.search_one(iri=f"{o.base_iri}#traitWeight")
        if not tw:
            class traitWeight(DataProperty):  # type: ignore
                domain = [o.CareerRole]
                range = [float]
                label = ["traitWeight"]
                comment = ["Relative importance (0-1) of traits required for a career role"]
            created_new = True

        rfs = getattr(o, "roleFitScore", None) or o.search_one(iri=f"{o.base_iri}roleFitScore") or o.search_one(iri=f"{o.base_iri}#roleFitScore")
        if not rfs:
            class roleFitScore(DataProperty):  # type: ignore
                domain = [o.Participant]
                range = [float, str]
                label = ["roleFitScore"]
                comment = ["Stores role-specific fit scores for a participant"]
            created_new = True

    if created_new:
        try:
            o.save(file=ONTOLOGY_PATH, format="rdfxml")
            print("💾 Added missing custom properties to ontology file")
        except Exception as save_err:
            print(f"⚠️ Could not persist custom properties: {save_err}")


def ensure_career_roles_seed(o):
    """Seed core career roles, skills, and trait links so downstream scoring can attach data."""
    try:
        if not hasattr(o, "CareerRole") or not hasattr(o, "Skill"):
            return

        def safe_name(label):
            return "_".join(label.split()).replace("/", "_").replace("-", "_")

        with o:
            for role_label, cfg in ROLE_BLUEPRINTS.items():
                role_name = f"Role_{safe_name(role_label)}"
                role = find_entity_by_id(o.CareerRole, role_name) or o.CareerRole(role_name)
                try:
                    role.label = [role_label]
                except Exception:
                    pass

                trait_entities = []
                weight_values = []
                for trait_label, meta in cfg.get("trait_targets", {}).items():
                    trait_entity = o.search_one(name=trait_label)
                    if trait_entity is None:
                        continue
                    trait_entities.append(trait_entity)
                    weight_values.append(meta.get("weight", 0.0))

                if trait_entities:
                    try:
                        role.requiresTrait = list(trait_entities)
                    except Exception:
                        pass
                if weight_values and hasattr(role, "traitWeight"):
                    try:
                        role.traitWeight = list(weight_values)
                    except Exception:
                        pass

                skills = []
                for skill_label in cfg.get("skills", [])[:4]:
                    skill_name = f"Skill_{safe_name(skill_label)}"
                    skill = find_entity_by_id(o.Skill, skill_name) or o.Skill(skill_name)
                    try:
                        skill.label = [skill_label]
                    except Exception:
                        pass
                    skills.append(skill)

                if skills:
                    try:
                        role.requiresSkill = skills
                    except Exception:
                        pass

        try:
            o.save(file=ONTOLOGY_PATH, format="rdfxml")
            print("💾 Career roles and skills seeded into ontology")
        except Exception as save_err:
            print(f"⚠️ Could not persist career roles: {save_err}")
    except Exception as seed_err:
        print(f"⚠️ Could not seed career roles: {seed_err}")


def load_ontology(force_reload=False):
    """Load ontology from disk. For force_reload, build a fresh World to avoid stale in-memory duplicates."""
    global onto_world
    try:
        if force_reload or onto_world is None:
            onto_world = World()
        onto_obj = onto_world.get_ontology(ONTOLOGY_PATH)
        onto_loaded = onto_obj.load(reload=force_reload)
        print(f"✅ Ontology loaded from {ONTOLOGY_PATH}")
        ensure_custom_properties(onto_loaded)
        ensure_career_roles_seed(onto_loaded)
        return onto_loaded
    except Exception as e:
        print(f"❌ CRITICAL ERROR: Could not load ontology. {e}")
        raise


onto = load_ontology()
ensure_custom_properties(onto)
ensure_career_roles_seed(onto)

# --- HELPER FUNCTIONS ---

def get_question_details(q):
    """ Extract question info based on your ontology structure. """
    text = "Question text missing"
    if hasattr(q, "questionText") and q.questionText:
        text = q.questionText[0]
    elif hasattr(q, "hasText") and q.hasText:
        text = q.hasText[0]
    
    q_id = q.name
    if hasattr(q, "questionID") and q.questionID:
        q_id = q.questionID[0]

    trait_name = "Unknown"
    if hasattr(q, "measures") and q.measures:
        measured_entity = q.measures[0]
        trait_name = measured_entity.name 

    is_reverse = False
    if hasattr(onto, "NegativelyKeyedQuestion") and isinstance(q, onto.NegativelyKeyedQuestion):
        is_reverse = True
    if not is_reverse and hasattr(q, "isReverseCoded") and q.isReverseCoded:
        val = q.isReverseCoded[0]
        if str(val).lower() == "true" or val is True:
            is_reverse = True

    return { "id": q_id, "text": text, "trait": trait_name, "is_reverse": is_reverse }


def normalize_user_id(user_id):
    return str(user_id).strip() if user_id is not None else ""


def find_entity_by_id(cls, name):
    """Robustly find an entity by name using multiple IRI strategies."""
    base = onto.base_iri
    candidates = []
    
    # Strategy 1: Construct IRI with #
    if base.endswith('#'):
        candidates.append(f"{base}{name}")
    else:
        candidates.append(f"{base}#{name}")
    
    # Strategy 2: Construct IRI with /
    if base.endswith('/'):
        candidates.append(f"{base}{name}")
    else:
        candidates.append(f"{base}/{name}")

    # Strategy 3: Just the name (if base is empty or weird)
    candidates.append(name)

    for iri in candidates:
        found = onto.search_one(iri=iri)
        if found:
            return found
            
    # Strategy 4: Search by name property (slower but fallback)
    if hasattr(cls, "instances"):
        for inst in cls.instances():
            if inst.name == name:
                return inst

    # Strategy 5: Wildcard search (desperate fallback)
    try:
        results = onto.search(iri=f"*{name}")
        for r in results:
            if hasattr(r, 'name') and r.name == name:
                return r
    except Exception:
        pass
                
    return None

def get_or_create_singleton(cls, name):
    """Return a single individual by name; if multiple exist, keep one and destroy extras; if none, create."""
    print(f"🔍 Looking for singleton: {name} of type {cls.name} (Base IRI: {onto.base_iri})")
    
    keeper = find_entity_by_id(cls, name)
    
    if keeper:
        print(f"   ✅ Found existing: {keeper.iri}")
        # Check for duplicates in instances list just in case
        if hasattr(cls, "instances"):
            matches = [m for m in cls.instances() if m.name == name and m != keeper]
            for dup in matches:
                print(f"   🗑️ Removing duplicate: {dup.iri}")
                destroy_entity(dup)
    else:
        print(f"   ✨ Creating new: {name}")
        try:
            keeper = cls(name)
        except Exception as e:
            print(f"   ⚠️ Creation failed ({e}). Retrying fetch...")
            # Retry fetch in case of race condition or DB sync issue
            keeper = find_entity_by_id(cls, name)
            if not keeper:
                print(f"   ❌ CRITICAL: Could not create or find {name}")
                raise e
            else:
                print(f"   ✅ Recovered existing after error: {keeper.iri}")
                
    return keeper


def dedup_user_entities(user_id):
    """Clean duplicates for this user: participant, assessment, and trait scores with the user prefix."""
    print(f"🧹 Deduplicating entities for user: {user_id}")
    # Participant
    get_or_create_singleton(onto.Participant, f"Participant_{user_id}")

    # Assessment and its hasScore list
    assessment = get_or_create_singleton(onto.Assessment, f"Assessment_{user_id}")
    try:
        if hasattr(assessment, "hasScore") and assessment.hasScore:
            # detach any scores that are not for this user
            assessment.hasScore = [ts for ts in assessment.hasScore if ts.name.startswith(f"Score_{user_id}_")]
    except Exception:
        pass

    # Trait scores: keep one per trait suffix, drop extras
    by_trait = {}
    for ts in list(onto.TraitScore.instances()):
        if ts.name.startswith(f"Score_{user_id}_"):
            trait_suffix = ts.name.split(f"Score_{user_id}_", 1)[-1]
            if trait_suffix not in by_trait:
                by_trait[trait_suffix] = ts
            else:
                try:
                    destroy_entity(ts)
                except Exception:
                    pass

    # Reattach cleaned trait scores to assessment
    try:
        assessment.hasScore = list(by_trait.values())
    except Exception:
        pass


def get_participant_display_name(participant):
    """Resolve the participant's display name safely across ontology variants."""
    try:
        if hasattr(onto, "name") and isinstance(onto.name, DataPropertyClass) and participant.name:
            return str(participant.name[0])
    except Exception:
        pass

    try:
        if participant.label:
            return str(participant.label[0])
    except Exception:
        pass

    return getattr(participant, "name", "Participant")


def extract_trait_percentages_for_participant(user_id):
    """Return Big Five trait percentages for the participant, reading the latest ontology state."""
    scores = {}
    assessment = find_entity_by_id(onto.Assessment, f"Assessment_{user_id}") if hasattr(onto, "Assessment") else None
    trait_scores = []

    if assessment and hasattr(assessment, "hasScore"):
        trait_scores = list(assessment.hasScore or [])
    else:
        try:
            trait_scores = [ts for ts in onto.TraitScore.instances() if ts.name.startswith(f"Score_{user_id}_")]
        except Exception:
            trait_scores = []

    for ts in trait_scores:
        try:
            val = 0.0
            if hasattr(ts, "meanScore") and ts.meanScore:
                val = float(ts.meanScore[0])
            trait_name = ts.name.split('_')[-1] if '_' in ts.name else (
                ts.scoresOnTrait[0].name if hasattr(ts, "scoresOnTrait") and ts.scoresOnTrait else "Trait"
            )
            scores[trait_name] = val
        except Exception:
            continue

    return scores


def score_role_fit(trait_scores):
    """Compute per-role fit scores using ROLE_BLUEPRINTS and return detailed breakdown."""
    role_results = {}
    for role_name, cfg in ROLE_BLUEPRINTS.items():
        total_weight = sum(meta.get("weight", 0.0) for meta in cfg.get("trait_targets", {}).values()) or 1.0
        contributions = []
        weighted_sum = 0.0

        for trait_label, meta in cfg.get("trait_targets", {}).items():
            target = meta.get("target", 70)
            weight = meta.get("weight", 0.1)
            actual = float(trait_scores.get(trait_label, 0.0))
            proximity = max(0.0, 1.0 - abs(actual - target) / 100.0)
            weighted = proximity * weight
            weighted_sum += weighted
            contributions.append({
                "trait": trait_label,
                "actual": round(actual, 2),
                "target": target,
                "weight": weight,
                "closeness": round(proximity * 100, 2),
            })

        overall = round(max(0.0, min(100.0, (weighted_sum / total_weight) * 100)), 2)
        role_results[role_name] = {
            "score": overall,
            "contributions": sorted(contributions, key=lambda c: c["closeness"], reverse=True),
        }

    ranking = sorted(role_results.keys(), key=lambda k: role_results[k]["score"], reverse=True)
    return role_results, ranking


ROLE_TRAIT_SKILL_GAPS = {
    "Software Engineer": {
        "Conscientiousness": ["Task Planning", "Test-Driven Development"],
        "Openness": ["System Design Patterns", "Technical Architecture"],
        "Neuroticism": ["Stress Management", "Incident Response Playbooks"],
        "Extraversion": ["Stakeholder Communication", "Team Demos"],
        "Agreeableness": ["Code Review Facilitation", "Pair Programming"],
    },
    "Manager": {
        "Extraversion": ["Executive Presence", "Facilitation"],
        "Agreeableness": ["Conflict Mediation", "Coaching"],
        "Conscientiousness": ["Operational Cadence", "Prioritization"],
        "Openness": ["Strategic Framing", "Innovation Workshops"],
        "Neuroticism": ["Emotional Regulation", "Resilience Training"],
    },
    "Researcher": {
        "Openness": ["Exploratory Research Methods", "Creative Prototyping"],
        "Conscientiousness": ["Study Planning", "Documentation Rigor"],
        "Extraversion": ["Conference Presentations", "Interviewing"],
        "Agreeableness": ["Cross-team Collaboration", "Stakeholder Alignment"],
        "Neuroticism": ["Experiment Recovery Plans", "Mindfulness"],
    },
}


def suggest_skill_gaps(role_name, contributions):
    """Pick two skills to develop based on the weakest contributing traits."""
    ordered = sorted(contributions, key=lambda c: c["closeness"])
    skills = []
    for item in ordered:
        trait = item.get("trait")
        trait_skills = ROLE_TRAIT_SKILL_GAPS.get(role_name, {}).get(trait, [])
        for skill in trait_skills:
            if skill not in skills:
                skills.append(skill)
            if len(skills) >= 2:
                return skills[:2]

    fallback = ROLE_BLUEPRINTS.get(role_name, {}).get("skills", [])
    for skill in fallback:
        if skill not in skills:
            skills.append(skill)
        if len(skills) >= 2:
            break

    return skills[:2]


def build_counterfactual_insight(contributions):
    """Summarize which trait lifts would raise the role score most."""
    weakest = sorted(contributions, key=lambda c: c["closeness"])[:2]
    parts = []
    for item in weakest:
        trait = item.get("trait")
        actual = item.get("actual", 0)
        target = item.get("target", 0)
        delta = max(0, target - actual) if target >= actual else max(0, actual - target)
        direction = "increase" if target > actual else "reduce"
        parts.append(f"{direction} {trait} by ~{round(abs(delta), 1)} points toward {target} to lift this role")
    return "; ".join(parts) if parts else "Maintain current balance to keep this fit strong."


def persist_role_fit_scores(participant, role_results):
    """Store role fit scores on the participant using the roleFitScore data property."""
    try:
        participant.roleFitScore = []
        for role, info in role_results.items():
            participant.roleFitScore.append(f"{role}:{info.get('score', 0)}")
    except Exception as exc:
        print(f"⚠️ Could not persist role fit scores: {exc}")


def generate_role_explanations(name, trait_scores, role_results):
    """Use Groq to create concise explanations per role. Returns mapping role -> text payload."""
    role_payload = {r: {
        "score": data.get("score"),
        "top_traits": [c["trait"] for c in sorted(data.get("contributions", []), key=lambda c: c["closeness"], reverse=True)[:3]],
        "weak_traits": [c for c in sorted(data.get("contributions", []), key=lambda c: c["closeness"])[:2]],
    } for r, data in role_results.items()}

    prompt = f"""
You are a concise career coach. Summarize role fit for {name} using the provided scores.

Trait scores (0-100): {trait_scores}
Role fit scores: { {k: v['score'] for k, v in role_results.items()} }

For each role (Software Engineer, Manager, Researcher), produce JSON with keys:
- role: role name
- explanation: 2-3 sentences on why it fits or not (mention strengths and challenges)
- strengths: array of 2 short bullet phrases
- challenges: array of 2 short bullet phrases
- counterfactual: one sentence on which trait change would most increase fit
- skill_gaps: array of 2 skill recommendations to grow fit

Keep total output compact and strictly valid JSON array.
"""

    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "Return only JSON for career role fit."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.5,
        )
        raw = completion.choices[0].message.content
        data = json.loads(raw)
        mapped = {}
        for item in data:
            role = item.get("role")
            if not role:
                continue
            mapped[role] = {
                "explanation": item.get("explanation", ""),
                "strengths": item.get("strengths", []),
                "challenges": item.get("challenges", []),
                "counterfactual": item.get("counterfactual", ""),
                "skill_gaps": item.get("skill_gaps", []),
            }
        return mapped
    except Exception as exc:
        print(f"⚠️ Groq role explanation fallback: {exc}")
        # Fallback deterministic explanations
        mapped = {}
        for role, info in role_results.items():
            mapped[role] = {
                "explanation": f"Role fit at {info['score']}%. Strongest traits: {', '.join([c['trait'] for c in info['contributions'][:2]])}.",
                "strengths": [c["trait"] for c in info.get("contributions", [])[:2]],
                "challenges": [c["trait"] for c in info.get("contributions", [])[-2:]],
                "counterfactual": build_counterfactual_insight(info.get("contributions", [])),
                "skill_gaps": suggest_skill_gaps(role, info.get("contributions", [])),
            }
        return mapped

def calculate_performance_scores(final_scores):
    job_perf = 3.0
    acad_perf = 3.0
    scores_lower = {k.lower(): v for k, v in final_scores.items()}

    weights = {
        "JobPerformance": { "conscientiousness": 0.22, "neuroticism": -0.15, "extraversion": 0.10, "agreeableness": 0.08, "openness": 0.05 },
        "AcademicPerformance": { "conscientiousness": 0.28, "agreeableness": 0.07, "openness": 0.15, "neuroticism": -0.10, "extraversion": 0.05 }
    }

    for trait, score in scores_lower.items():
        deviation = score - 3.0
        for w_trait, weight in weights["JobPerformance"].items():
            if w_trait in trait: job_perf += deviation * weight
        for w_trait, weight in weights["AcademicPerformance"].items():
            if w_trait in trait: acad_perf += deviation * weight

    return {
        "JobPerformance": round(max(20, min(100, (job_perf/5)*100)), 2),
        "AcademicPerformance": round(max(20, min(100, (acad_perf/5)*100)), 2)
    }

def get_groq_suggestions(scores, name):
    prompt = f"""
        Act as an expert Industrial-Organizational Psychologist and Personality Profiler. 
        Analyze the personality of '{name}' based on the following Big Five trait scores (scale 0-100%):
        {scores}

        Your goal is to provide a deep, empathetic, and actionable analysis. 
        Do not just list the traits one by one; analyze how they interact with each other.

        Please structure your response in the following Markdown format:

        ### 🧠 The Executive Summary
        [A 2-3 sentence "elevator pitch" of their personality archetype. Give them a creative title, like "The Compassionate Architect" or "The Ambitious Driver".]

        ### ⚡ Key Strengths (Superpowers)
        * **[Strength 1]:** [Description based on high scoring traits]
        * **[Strength 2]:** [Description]
        * **[Strength 3]:** [Description]

        ### ⚠️ Potential Blind Spots
        [Discuss 2 specific challenges they might face, such as burnout, conflict avoidance, or disorganization, based on their specific score combinations.]

        ### 💼 Performance & Work Style
        * **Work Approach:** [How they handle tasks/deadlines]
        * **Team Dynamics:** [How they interact with others]

        ### 🚀 3 Tailored Growth Strategies
        1.  **[Strategy 1]:** [Actionable advice]
        2.  **[Strategy 2]:** [Actionable advice]
        3.  **[Strategy 3]:** [Actionable advice]
    """
    try:
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        return f"Error getting suggestions: {str(e)}"


def generate_justification_report(big_five_scores, performance_predictions, answered_questions):
    """Generate an explainable justification report via Groq."""
    if not GROQ_API_KEY:
        return "Groq API key not configured; justification unavailable."

    # Build question evidence block
    question_lines = []
    for idx, q in enumerate(answered_questions, start=1):
        q_text = q.get("question_text", "Unknown question")
        trait = q.get("trait", "Unknown")
        ans = q.get("answer", "?")
        reverse_note = " (reverse-coded)" if q.get("is_reverse_coded") else ""
        effective = q.get("effective_score")
        effective_note = f" -> effective score {effective}" if effective is not None else ""
        question_lines.append(f"{idx}. \"{q_text}\" | Trait: {trait} | Answer: {ans}{reverse_note}{effective_note}")

    system_prompt = "You are an Industrial-Organizational Psychologist providing explainable personality assessments."

    user_instructions = f"""
USER TASK:
- Explain trait-by-trait why the user received each Big Five score.
- Reference patterns in the user's answers and cite example questions in natural language.
- Explain how traits influenced Academic and Job performance predictions.
- Avoid generic descriptions and do not invent data.

DATA CONTEXT:
- Big Five Scores (0-100): {big_five_scores}
- Performance Predictions: {performance_predictions}
- Answered Questions:
{os.linesep.join(question_lines) if question_lines else 'No responses provided'}

RESPONSE STRUCTURE (keep this order):
1. Trait-by-Trait Justification
2. Academic Performance Justification
3. Job Performance Justification
4. Plain-English Summary
"""

    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_instructions},
            ],
            temperature=0.4,
        )
        return completion.choices[0].message.content
    except Exception as exc:
        print(f"❌ ERROR generating justification: {exc}")
        return "Justification could not be generated at this time."

# --- ROUTES ---

@app.route('/')
def landing():
    return jsonify({"status": "ok", "message": "API server is running. Frontend served by Vite on port 5173."})


@app.before_request
def handle_preflight():
    if request.method == 'OPTIONS':
        resp = app.make_response(('', 204))
        resp.headers['Access-Control-Allow-Origin'] = ALLOWED_FRONTEND_ORIGIN
        resp.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        resp.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        return resp


@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = ALLOWED_FRONTEND_ORIGIN
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    return response

@app.route('/get_previous_result', methods=['GET'])
def get_previous_result():
    global onto
    user_id = normalize_user_id(request.args.get('id'))
    if not user_id:
        return jsonify({"found": False, "message": "id is required"}), 400

    try:
        # Ensure we read latest ontology state
        onto = load_ontology(force_reload=True)
        
        participant = None
        
        # 1. Priority: Search by canonical IRI (Participant_{user_id})
        # This is the one we write to in submit_assessment
        participant = find_entity_by_id(onto.Participant, f"Participant_{user_id}")
        
        # 2. Fallback: Search by participantID property
        if not participant and hasattr(onto, "Participant"):
            print(f"⚠️ Canonical Participant_{user_id} not found. Searching by ID property...")
            for p in onto.Participant.instances():
                if hasattr(p, "participantID") and p.participantID and str(p.participantID[0]) == user_id:
                    participant = p
                    break
        
        if not participant:
            print(f"❌ Participant_{user_id} not found in ontology.")
            return jsonify({"found": False, "message": "not found"}), 200

        print(f"✅ Found participant: {participant.name} (IRI: {participant.iri})")

        # Performance scores (stored on participant)
        # Use the last value in the list if multiple exist, but we expect only one after cleanup
        job_perf = 0.0
        if hasattr(participant, 'jobPerformance') and participant.jobPerformance:
            job_perf = float(participant.jobPerformance[-1]) # Take last added
            print(f"   JobPerformance: {participant.jobPerformance}")

        acad_perf = 0.0
        if hasattr(participant, 'academicPerformance') and participant.academicPerformance:
            acad_perf = float(participant.academicPerformance[-1]) # Take last added
            print(f"   AcademicPerformance: {participant.academicPerformance}")

        # Try to find assessment and trait scores
        assessment = find_entity_by_id(onto.Assessment, f"Assessment_{user_id}")
        scores = {}
        trait_scores = []
        if assessment and hasattr(assessment, 'hasScore'):
            trait_scores = list(assessment.hasScore)
        else:
            # fallback: search trait scores by naming pattern
            trait_scores = [ts for ts in onto.TraitScore.instances() if ts.name.startswith(f"Score_{user_id}_")]

        for ts in trait_scores:
            val = 0.0
            if hasattr(ts, 'meanScore') and ts.meanScore:
                val = float(ts.meanScore[0])
            trait_name = ts.name.split('_')[-1] if '_' in ts.name else (ts.scoresOnTrait[0].name if hasattr(ts, 'scoresOnTrait') and ts.scoresOnTrait else 'Trait')
            scores[trait_name] = f"{round(val, 2)}%"

        return jsonify({
            "found": True,
            "scores": scores,
            "performance": {
                "JobPerformance": round(job_perf, 2),
                "AcademicPerformance": round(acad_perf, 2)
            },
            "analysis": ""  # analysis is not stored; left blank
        })
    except Exception as e:
        print(f"❌ ERROR reading previous result: {e}")
        return jsonify({"found": False, "message": "internal error"}), 500


@app.route('/api/justification/<participant_id>', methods=['GET'])
def get_justification(participant_id):
    global onto
    user_id = normalize_user_id(participant_id)
    if not user_id:
        return jsonify({"found": False, "message": "id is required"}), 400

    try:
        onto = load_ontology(force_reload=True)
        ensure_custom_properties(onto)
        participant = find_entity_by_id(onto.Participant, f"Participant_{user_id}")

        if not participant:
            return jsonify({"found": False, "message": "not found"}), 200

        justification_text = ""
        if hasattr(participant, 'hasJustificationReport') and participant.hasJustificationReport:
            justification_text = str(participant.hasJustificationReport[-1])
            print(f"📤 Returning justification for {participant.name if hasattr(participant,'name') else participant}: {justification_text[:120]}...")

        if not justification_text:
            justification_text = "Justification not available for this participant. Please re-run the assessment."

        return jsonify({"found": True, "justification": justification_text}), 200
    except Exception as e:
        print(f"❌ ERROR fetching justification: {e}")
        return jsonify({"found": False, "message": "internal error"}), 500


@app.route('/api/career-fit/<participant_id>', methods=['GET'])
def get_career_fit(participant_id):
    """Return career role fit scores, explanations, skill gaps, and counterfactual insights."""
    global onto
    user_id = normalize_user_id(participant_id)
    if not user_id:
        return jsonify({"found": False, "message": "id is required"}), 400

    try:
        onto = load_ontology(force_reload=True)
        ensure_custom_properties(onto)
        ensure_career_roles_seed(onto)

        participant = find_entity_by_id(onto.Participant, f"Participant_{user_id}") if hasattr(onto, "Participant") else None
        if not participant:
            return jsonify({"found": False, "message": "not found"}), 200

        trait_scores = extract_trait_percentages_for_participant(user_id)
        if not trait_scores:
            return jsonify({"found": False, "message": "Trait scores unavailable for this participant"}), 200

        role_results, ranking = score_role_fit(trait_scores)
        explanations = generate_role_explanations(get_participant_display_name(participant), trait_scores, role_results)

        # Shape response per role
        response_roles = {}
        for role, info in role_results.items():
            role_expl = explanations.get(role, {})
            raw_skill_gaps = role_expl.get("skill_gaps")
            skill_gaps = raw_skill_gaps if isinstance(raw_skill_gaps, list) else suggest_skill_gaps(role, info.get("contributions", []))
            raw_strengths = role_expl.get("strengths")
            strengths = raw_strengths if isinstance(raw_strengths, list) else ([raw_strengths] if raw_strengths else [])
            raw_challenges = role_expl.get("challenges")
            challenges = raw_challenges if isinstance(raw_challenges, list) else ([raw_challenges] if raw_challenges else [])
            counterfactual = role_expl.get("counterfactual") or build_counterfactual_insight(info.get("contributions", []))
            response_roles[role] = {
                "score": info.get("score", 0),
                "explanation": role_expl.get("explanation", ""),
                "strengths": strengths,
                "challenges": challenges,
                "skill_gaps": skill_gaps,
                "counterfactual": counterfactual,
                "traits": info.get("contributions", []),
            }

        # Persist role fit scores back to ontology
        try:
            with onto:
                persist_role_fit_scores(participant, role_results)
            onto.save(file=ONTOLOGY_PATH, format="rdfxml")
        except Exception as save_err:
            print(f"⚠️ Could not save role fit scores: {save_err}")

        ranking_payload = [
            {"role": r, "score": role_results[r]["score"], "position": idx + 1}
            for idx, r in enumerate(ranking)
        ]

        return jsonify({
            "found": True,
            "roles": response_roles,
            "ranking": ranking_payload,
            "top_recommendation": ranking[0] if ranking else None,
        }), 200
    except Exception as e:
        print(f"❌ ERROR computing career fit: {e}")
        return jsonify({"found": False, "message": "internal error"}), 500


@app.route('/get_questions', methods=['GET'])
def get_questions():
    questions_data = []
    if not hasattr(onto, "AssessmentQuestion"):
        return jsonify([])

    for q in onto.AssessmentQuestion.instances():
        try:
            questions_data.append(get_question_details(q))
        except Exception:
            pass

    def sort_key(q):
        try:
            return int(''.join(filter(str.isdigit, q['id'])))
        except Exception:
            return q['id']

    questions_data.sort(key=sort_key)
    return jsonify(questions_data)

@app.route('/validate_user', methods=['POST'])
def validate_user():
    global onto
    data = request.json
    user_id = normalize_user_id(data.get('id'))
    user_name = data.get('name', '').strip()

    if not user_id:
        return jsonify({"valid": False, "message": "User ID is required"}), 400

    try:
        # Ensure we read latest ontology state
        onto = load_ontology(force_reload=True)
        
        participant = find_entity_by_id(onto.Participant, f"Participant_{user_id}")
        
        if participant:
            # Check name
            stored_name = ""
            
            # Determine where the name is stored - logic matches submit_assessment
            if hasattr(onto, "name") and isinstance(onto.name, DataPropertyClass):
                if participant.name:
                    stored_name = str(participant.name[0])
            elif participant.label:
                stored_name = str(participant.label[0])
            
            # Only validate if we actually found a stored name
            if stored_name and stored_name.lower() != user_name.lower():
                 return jsonify({"valid": False, "message": f"ID '{user_id}' is already registered with a different name."}), 200
        
        return jsonify({"valid": True}), 200

    except Exception as e:
        print(f"❌ ERROR validating user: {e}")
        return jsonify({"valid": False, "message": "Internal server error"}), 500

@app.route('/submit_assessment', methods=['POST'])
def submit_assessment():
    global onto
    # Reload ontology to ensure we see existing individuals before creating any
    onto = load_ontology(force_reload=True)
    ensure_custom_properties(onto)

    data = request.json
    user_id = normalize_user_id(data.get('id', 'Unknown'))
    user_name = data.get('name', 'Anonymous')
    answers = data.get('answers', {})
    answered_questions_data = []
    
    # 1. Calculate trait totals
    trait_totals = {}
    for q in onto.AssessmentQuestion.instances():
        details = get_question_details(q)
        q_id = details['id']
        trait = details['trait'].lower()
        if trait == "unknown":
            continue
        if trait not in trait_totals:
            trait_totals[trait] = []
        if q_id in answers:
            raw_val = int(answers[q_id])
            final_val = (6 - raw_val) if details['is_reverse'] else raw_val
            trait_totals[trait].append(final_val)
            answered_questions_data.append({
                "question_text": details['text'],
                "trait": details['trait'],
                "answer": raw_val,
                "is_reverse_coded": details['is_reverse'],
                "effective_score": final_val
            })

    # Aggregate scores
    raw_scores = {}
    numeric_percentages = {}
    formatted_scores = {}

    for t, values in trait_totals.items():
        trait_key = t.capitalize()
        if values:
            mean_val = sum(values) / len(values)
            raw_scores[trait_key] = mean_val
            pct_val = round((mean_val / 5) * 100, 2)
            numeric_percentages[trait_key] = pct_val
            formatted_scores[trait_key] = f"{pct_val}%"
        else:
            raw_scores[trait_key] = 0
            numeric_percentages[trait_key] = 0.0
            formatted_scores[trait_key] = "0%"

    # Performance and AI suggestions
    perf_scores = calculate_performance_scores(raw_scores)
    suggestions = get_groq_suggestions(numeric_percentages, user_name)
    justification_report = generate_justification_report(numeric_percentages, perf_scores, answered_questions_data) or "Justification not available."
    print(f"💾 Attempting to save data for user: {user_name}...")
    try:
        with onto:
            # Find or create participant by name (no wildcard), consolidating duplicates
            participant = get_or_create_singleton(onto.Participant, f"Participant_{user_id}")
            participant.participantID = [user_id]
            
            # Use label or a specific property for the display name to avoid renaming the entity
            # If 'name' is a DataProperty in your ontology, this is fine. 
            # But if it conflicts with owlready2's .name (IRI suffix), it causes issues.
            # Safest is to use label or ensure we are setting the DataProperty.
            if hasattr(onto, "name") and isinstance(onto.name, DataPropertyClass):
                 participant.name = [user_name]
            else:
                 participant.label = [user_name]

            # Find or create assessment by name (no wildcard), consolidating duplicates
            assessment = get_or_create_singleton(onto.Assessment, f"Assessment_{user_id}")
            assessment.completedBy = [participant]

            # Update performance scores
            if "JobPerformance" in perf_scores:
                print(f"   🔄 Updating JobPerformance to: {perf_scores['JobPerformance']}")
                participant.jobPerformance = [] # Clear previous values to ensure update
                participant.jobPerformance = [float(perf_scores["JobPerformance"])]
            
            if "AcademicPerformance" in perf_scores:
                print(f"   🔄 Updating AcademicPerformance to: {perf_scores['AcademicPerformance']}")
                participant.academicPerformance = [] # Clear previous values to ensure update
                participant.academicPerformance = [float(perf_scores["AcademicPerformance"])]

            # Ensure hasScore is a list
            if not hasattr(assessment, 'hasScore') or assessment.hasScore is None:
                assessment.hasScore = []

            # Build expected set of trait score individuals, reusing by name
            expected_scores = []
            for trait, value in numeric_percentages.items():
                name = f"Score_{user_id}_{trait}"
                ts = get_or_create_singleton(onto.TraitScore, name)
                ts.meanScore = [value]

                trait_obj = onto.search_one(name=trait)
                if trait_obj:
                    ts.scoresOnTrait = [trait_obj]

                expected_scores.append(ts)

            # Replace assessment.hasScore with expected set (no destroys) and persist
            assessment.hasScore = expected_scores

            # Attach justification report
            participant.hasJustificationReport = []
            participant.hasJustificationReport = [justification_report]
            print(f"   📝 Justification attached (len={len(participant.hasJustificationReport)}): {participant.hasJustificationReport[-1][:120]}...")

        # Save and reload to make sure state is consistent
        onto.save(file=ONTOLOGY_PATH, format="rdfxml")
        print("💾 Ontology saved with justification report")
        onto = load_ontology(force_reload=True)
        ensure_custom_properties(onto)
        print("✅ Data successfully saved to project.rdf")

    except Exception as e:
        print(f"❌ ERROR SAVING ONTOLOGY: {str(e)}")

    return jsonify({
        "scores": formatted_scores,
        "performance": perf_scores,
        "analysis": suggestions
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)
