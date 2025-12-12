from flask import Flask, render_template, request, jsonify
from owlready2 import *
import os
from groq import Groq

app = Flask(__name__)

# --- CONFIGURATION ---
ONTOLOGY_PATH = "project.rdf"
# Ideally, keep API keys in environment variables for security
GROQ_API_KEY = "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"

client = Groq(api_key=GROQ_API_KEY)

# Load ontology once when app starts
onto = get_ontology(ONTOLOGY_PATH).load()

# --- HELPER FUNCTIONS ---

def get_trait_name(trait_class_list):
    """Helper to extract the string name of the trait from the ontology list."""
    if not trait_class_list:
        return "Unknown"
    
    # owlready2 returns a list of entities. We grab the first one's name.
    name = trait_class_list[0].name
    
    # --- FIX: Map Ontology Individual names to Standard Trait names ---
    # The ontology uses 'ExtraversionTrait' (individual) for some questions
    # but the logic expects 'Extraversion'.
    if name == "ExtraversionTrait":
        return "Extraversion"
    
    return name

def calculate_performance_scores(final_scores):
    """
    Calculates performance scores based on weighted trait correlations.
    """
    job_perf = 3.0
    acad_perf = 3.0
    
    # Weights based on meta-analytic research (simplified)
    weights = {
        "JobPerformance": {
            "Conscientiousness": 0.22,
            "Neuroticism": -0.15,
            "Extraversion": 0.10,
            "Agreeableness": 0.08,
            "Openness": 0.05
        },
        "AcademicPerformance": {
            "Conscientiousness": 0.28,
            "Agreeableness": 0.07,
            "Openness": 0.15,
            "Neuroticism": -0.10,
            "Extraversion": 0.05
        }
    }

    for trait, score in final_scores.items():
        deviation = score - 3.0 # Deviation from neutral
        
        if trait in weights["JobPerformance"]:
            job_perf += deviation * weights["JobPerformance"][trait]
            
        if trait in weights["AcademicPerformance"]:
            acad_perf += deviation * weights["AcademicPerformance"][trait]

    # Return clamped values (1.0 - 5.0)
    return {
        "JobPerformance": round(max(1.0, min(5.0, job_perf)), 2),
        "AcademicPerformance": round(max(1.0, min(5.0, acad_perf)), 2)
    }

def get_groq_suggestions(scores, name):
    """Sends trait scores to Groq API for analysis."""
    prompt = f"""
    Analyze the personality of {name} based on these Big Five scores (Range 1-5):
    {scores}
    
    Provide a brief, supportive summary of their personality type and 3 actionable 
    suggestions for personal or professional growth.
    """
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are an expert personality psychologist."},
                {"role": "user", "content": prompt}
            ],
            model="llama3-8b-8192",
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        return f"Error getting suggestions: {str(e)}"

# --- ROUTES ---

@app.route('/')
def index():
    """Serves the main HTML page."""
    # Ensure you have an 'index.html' file in a 'templates' folder
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit_assessment():
    """Handles the form submission, score calculation, and ontology update."""
    data = request.json
    user_id = data.get('userId', 'Unknown')
    user_name = data.get('userName', 'Anonymous')
    answers = data.get('answers', {})

    # 1. Calculate Scores
    scores = {t: [] for t in ["Extraversion", "Agreeableness", "Conscientiousness", "Neuroticism", "Openness"]}
    
    for q in onto.AssessmentQuestion.instances():
        q_id = q.questionID[0]
        trait = get_trait_name(q.measures)
        
        if trait in scores and q_id in answers:
            raw_val = int(answers[q_id])
            # Handle Reverse Coding
            is_reverse = q.isReverseCoded[0]
            final_val = (6 - raw_val) if is_reverse else raw_val
            scores[trait].append(final_val)

    # Compute Means
    final_scores = {k: round(sum(v)/len(v), 2) if v else 0 for k, v in scores.items()}

    # 2. Calculate Performance
    perf_scores = calculate_performance_scores(final_scores)

    # 3. Update Ontology
    with onto:
        # Define properties dynamically if they don't exist
        if not hasattr(onto, "jobPerformanceScore"):
            class jobPerformanceScore(DataProperty):
                domain = [onto.Participant]
                range = [float]
        
        if not hasattr(onto, "academicPerformanceScore"):
            class academicPerformanceScore(DataProperty):
                domain = [onto.Participant]
                range = [float]

        # Create/Update Participant
        participant = onto.Participant(f"Participant_{user_id}")
        participant.participantID = [user_id]
        participant.name = [user_name]
        
        # Add Performance Scores (Float)
        participant.jobPerformanceScore = [perf_scores["JobPerformance"]]
        participant.academicPerformanceScore = [perf_scores["AcademicPerformance"]]
        
        # Add Trait Scores
        for trait, value in final_scores.items():
            score_ind = onto.TraitScore(f"Score_{user_id}_{trait}")
            score_ind.meanScore = [value]
    
    # Save ontology (be careful with concurrency in production)
    onto.save(file=ONTOLOGY_PATH)

    # 4. Get AI Analysis
    suggestions = get_groq_suggestions(final_scores, user_name)
    
    return jsonify({
        "scores": final_scores,
        "performance": perf_scores,
        "analysis": suggestions
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)
