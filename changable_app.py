from flask import Flask, render_template, request, jsonify
from owlready2 import *
import os
from groq import Groq

app = Flask(__name__)

# --- CONFIGURATION ---
ONTOLOGY_PATH = "project.rdf" 
GROQ_API_KEY = "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" 

client = Groq(api_key=GROQ_API_KEY)
onto = get_ontology(ONTOLOGY_PATH).load()

# --- HELPER FUNCTIONS ---
def get_trait_name(trait_class_list):
    if not trait_class_list: return "Unknown"
    name = trait_class_list[0].name
    return "Extraversion" if name == "ExtraversionTrait" else name

def calculate_performance_scores(final_scores):
    # (Same logic as your previous code)
    job_perf = 3.0
    acad_perf = 3.0
    weights = {
        "JobPerformance": {"Conscientiousness": 0.22, "Neuroticism": -0.15, "Extraversion": 0.10, "Agreeableness": 0.08, "Openness": 0.05},
        "AcademicPerformance": {"Conscientiousness": 0.28, "Agreeableness": 0.07, "Openness": 0.15, "Neuroticism": -0.10, "Extraversion": 0.05}
    }
    for trait, score in final_scores.items():
        deviation = score - 3.0
        if trait in weights["JobPerformance"]: job_perf += deviation * weights["JobPerformance"][trait]
        if trait in weights["AcademicPerformance"]: acad_perf += deviation * weights["AcademicPerformance"][trait]
    return {"JobPerformance": round(max(1.0, min(5.0, job_perf)), 2), "AcademicPerformance": round(max(1.0, min(5.0, acad_perf)), 2)}

def get_groq_suggestions(scores, name):
    prompt = f"Analyze personality for {name}. Scores: {scores}. Provide summary and 3 growth tips."
    try:
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama3-8b-8192",
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        return f"Error: {str(e)}"

# --- ROUTES ---

@app.route('/')
def index():
    return render_template('index.html')

# REPLACE THE PREVIOUS 'get_questions' FUNCTION IN app.py WITH THIS:

@app.route('/get_questions', methods=['GET'])
def get_questions():
    questions_data = []
    try:
        # Check if class exists
        if not hasattr(onto, "AssessmentQuestion"):
            print("ERROR: Class 'AssessmentQuestion' not found in ontology.")
            return jsonify([])

        # Debug: Print how many questions were found
        questions_list = list(onto.AssessmentQuestion.instances())
        print(f"Found {len(questions_list)} questions in ontology.")

        for q in questions_list:
            # Safe checks to prevent crashing if a field is missing in RDF
            q_text = q.hasText[0] if hasattr(q, "hasText") and q.hasText else "Error: Text missing in Ontology"
            
            # Use 'name' as fallback if questionID is missing
            q_id = q.questionID[0] if hasattr(q, "questionID") and q.questionID else q.name
            
            measures = q.measures if hasattr(q, "measures") else []
            is_reverse = q.isReverseCoded[0] if hasattr(q, "isReverseCoded") and q.isReverseCoded else False

            questions_data.append({
                "id": q_id,
                "text": q_text,
                "trait": get_trait_name(measures),
                "is_reverse": is_reverse
            })
            
    except Exception as e:
        # This will print the exact error to your terminal so you can fix it
        print(f"SERVER ERROR in /get_questions: {str(e)}")
        return jsonify({"error": str(e)}), 500
        
    return jsonify(questions_data)

# 2. UPDATED ROUTE: Matches your HTML's "/submit_assessment"
@app.route('/submit_assessment', methods=['POST'])
def submit_assessment():
    data = request.json
    user_id = data.get('id', 'Unknown')
    user_name = data.get('name', 'Anonymous')
    answers = data.get('answers', {})
    
    # Calculate scores based on the answers received
    scores = {t: [] for t in ["Extraversion", "Agreeableness", "Conscientiousness", "Neuroticism", "Openness"]}
    
    # We map the answers back to the traits using the ontology
    for q in onto.AssessmentQuestion.instances():
        q_id = q.questionID[0]
        trait = get_trait_name(q.measures)
        
        if trait in scores and q_id in answers:
            raw_val = int(answers[q_id])
            is_reverse = q.isReverseCoded[0]
            final_val = (6 - raw_val) if is_reverse else raw_val
            scores[trait].append(final_val)

    final_scores = {k: round(sum(v)/len(v), 2) if v else 0 for k, v in scores.items()}
    perf_scores = calculate_performance_scores(final_scores)
    suggestions = get_groq_suggestions(final_scores, user_name)

    # (Ontology saving logic omitted for brevity, but you can keep it here if needed)

    return jsonify({
        "scores": final_scores,
        "performance": perf_scores,
        "analysis": suggestions
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)
