from flask import Flask, render_template, request, jsonify
from owlready2 import *
import os
from groq import Groq

app = Flask(__name__)

# --- CONFIGURATION ---
ONTOLOGY_PATH = "project.rdf" 
GROQ_API_KEY = "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" 

client = Groq(api_key=GROQ_API_KEY)

# Load ontology
try:
    onto = get_ontology(ONTOLOGY_PATH).load()
    print(f"✅ Ontology loaded from {ONTOLOGY_PATH}")
except Exception as e:
    print(f"❌ CRITICAL ERROR: Could not load ontology. {e}")

# ... existing code loading ontology ...
try:
    onto = get_ontology(ONTOLOGY_PATH).load()
    print(f"✅ Ontology loaded from {ONTOLOGY_PATH}")
except Exception as e:
    print(f"❌ CRITICAL ERROR: Could not load ontology. {e}")

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
        "AcademicPerformance": round(max(20, min(100, (acad_perf/5))*100), 2)
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
def index():
    return render_template('index.html')

@app.route('/get_questions', methods=['GET'])
def get_questions():
    questions_data = []
    if not hasattr(onto, "AssessmentQuestion"): return jsonify([])

    for q in onto.AssessmentQuestion.instances():
        try:
            questions_data.append(get_question_details(q))
        except: pass

    # Sort
    def sort_key(q):
        try: return int(''.join(filter(str.isdigit, q['id'])))
        except: return q['id']
    questions_data.sort(key=sort_key)
    
    return jsonify(questions_data)

@app.route('/submit_assessment', methods=['POST'])
def submit_assessment():
    data = request.json
    user_id = data.get('id', 'Unknown')
    user_name = data.get('name', 'Anonymous')
    answers = data.get('answers', {})

    # 1. Calc Scores
    trait_totals = {}
    for q in onto.AssessmentQuestion.instances():
        details = get_question_details(q)
        q_id = details['id']
        trait = details['trait'].lower()
        if trait == "unknown": continue
        if trait not in trait_totals: trait_totals[trait] = []
        if q_id in answers:
            raw_val = int(answers[q_id])
            final_val = (6 - raw_val) if details['is_reverse'] else raw_val
            trait_totals[trait].append(final_val)

    # Dictionaries for different purposes
    raw_scores = {}             # 1-5 Scale (For math/performance logic)
    numeric_percentages = {}    # 0-100 Float (For Ontology storage)
    formatted_scores = {}       # Strings with % (For Display/JSON)

    for t, values in trait_totals.items():
        trait_key = t.capitalize()
        if values:
            # Calculate raw mean (1-5)
            mean_val = sum(values)/len(values)
            raw_scores[trait_key] = mean_val
            
            # Calculate percentage (0-100)
            pct_val = round((mean_val / 5) * 100, 2)
            
            numeric_percentages[trait_key] = pct_val
            formatted_scores[trait_key] = f"{pct_val}%" 
        else:
            raw_scores[trait_key] = 0
            numeric_percentages[trait_key] = 0.0
            formatted_scores[trait_key] = "0%"

    # IMPORTANT: Use raw_scores (1-5) for performance calculation
    # This keeps your deviation logic (score - 3.0) mathematically correct
    perf_scores = calculate_performance_scores(raw_scores)
    
    # Use numeric percentages for the AI analysis
    suggestions = get_groq_suggestions(numeric_percentages, user_name)

    # 2. SAVE TO ONTOLOGY
    print(f"💾 Attempting to save data for user: {user_name}...")
    try:
        with onto:
            # Create Participant
            participant = onto.search_one(iri=f"*Participant_{user_id}")
            if not participant:
                participant = onto.Participant(f"Participant_{user_id}")
            
            participant.participantID = [user_id]
            participant.name = [user_name]
            
            # Create Assessment
            assessment = onto.Assessment(f"Assessment_{user_id}")
            assessment.completedBy = [participant]

            # Save Performance Scores (Float values)
            if "JobPerformance" in perf_scores:
                participant.jobPerformance = [float(perf_scores["JobPerformance"])]
            if "AcademicPerformance" in perf_scores:
                participant.academicPerformance = [float(perf_scores["AcademicPerformance"])]

            # Save Trait Scores (Saving 0-100 Numbers, not strings)
            # We save the number (e.g. 80.0) because the ontology expects 'decimal'
            for trait, value in numeric_percentages.items():
                ts = onto.TraitScore(f"Score_{user_id}_{trait}")
                ts.meanScore = [value]
                
                # Link to Trait
                trait_obj = onto.search_one(iri=f"*{trait}")
                if trait_obj:
                    ts.scoresOnTrait = [trait_obj]
                
                # Link to Assessment
                assessment.hasScore.append(ts)

        # FORCE SAVE
        onto.save(file=ONTOLOGY_PATH)
        print("✅ Data successfully saved to project.rdf")

    except Exception as e:
        print(f"❌ ERROR SAVING ONTOLOGY: {str(e)}")

    # Return the FORMATTED strings (with %) to the user
    return jsonify({
        "scores": formatted_scores,  # Shows "84.0%", "66.0%", etc.
        "performance": perf_scores,
        "analysis": suggestions
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)
