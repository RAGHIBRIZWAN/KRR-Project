from flask import Flask, render_template, request, jsonify, send_from_directory
from owlready2 import *
import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# --- CONFIGURATION ---
ONTOLOGY_PATH = os.path.join(app.root_path, "project.rdf")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
FRONTEND_DIR = os.path.join(app.root_path, 'frontend')
ALLOWED_FRONTEND_ORIGIN = "http://localhost:5173"

client = Groq(api_key=GROQ_API_KEY)

# Load ontology once at startup (absolute path) and provide a helper for reloads
onto_world = None


def load_ontology(force_reload=False):
    """Load ontology from disk. For force_reload, build a fresh World to avoid stale in-memory duplicates."""
    global onto_world
    try:
        if force_reload or onto_world is None:
            onto_world = World()
        onto_obj = onto_world.get_ontology(ONTOLOGY_PATH)
        onto_loaded = onto_obj.load(reload=force_reload)
        print(f"✅ Ontology loaded from {ONTOLOGY_PATH}")
        return onto_loaded
    except Exception as e:
        print(f"❌ CRITICAL ERROR: Could not load ontology. {e}")
        raise


onto = load_ontology()

# --- ADD THIS BLOCK: DEFINE MISSING PROPERTIES ---
with onto:
    # Property for Job Performance Score
    class jobPerformance(DataProperty):
        domain = [onto.Participant]
        range = [float]
        label = ["jobPerformance"]
        comment = ["Calculated predicted score for Job Performance"]

    # Property for Academic Performance Score
    class academicPerformance(DataProperty):
        domain = [onto.Participant]
        range = [float]
        label = ["academicPerformance"]
        comment = ["Calculated predicted score for Academic Performance"]
# -------------------------------------------------

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
        
        # 1. Search by participantID property (Most reliable)
        if hasattr(onto, "Participant"):
            for p in onto.Participant.instances():
                # Check participantID property
                if hasattr(p, "participantID") and p.participantID and str(p.participantID[0]) == user_id:
                    participant = p
                    break
        
        # 2. Fallback to IRI search
        if not participant:
            participant = find_entity_by_id(onto.Participant, f"Participant_{user_id}")
        
        if not participant:
            print(f"❌ Participant_{user_id} not found in ontology.")
            return jsonify({"found": False, "message": "not found"}), 200

        # Performance scores (stored on participant)
        job_perf = float(participant.jobPerformance[0]) if hasattr(participant, 'jobPerformance') and participant.jobPerformance else 0.0
        acad_perf = float(participant.academicPerformance[0]) if hasattr(participant, 'academicPerformance') and participant.academicPerformance else 0.0

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

@app.route('/submit_assessment', methods=['POST'])
def submit_assessment():
    global onto
    # Reload ontology to ensure we see existing individuals before creating any
    onto = load_ontology(force_reload=True)

    data = request.json
    user_id = normalize_user_id(data.get('id', 'Unknown'))
    user_name = data.get('name', 'Anonymous')
    answers = data.get('answers', {})
    
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
                participant.jobPerformance = [float(perf_scores["JobPerformance"])]
            if "AcademicPerformance" in perf_scores:
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

        # Save and reload to make sure state is consistent
        onto.save(file=ONTOLOGY_PATH, format="rdfxml")
        onto = load_ontology(force_reload=True)
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
