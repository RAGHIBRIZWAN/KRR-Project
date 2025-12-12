from flask import Flask, render_template, request, jsonify
from owlready2 import *
import os
from groq import Groq

app = Flask(__name__)

ONTOLOGY_PATH = "project.rdf"
GROQ_API_KEY = "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"

client = Groq(api_key=GROQ_API_KEY)

onto = get_ontology(ONTOLOGY_PATH).load()

base_iri = "http://www.semanticweb.org/personality#"

def get_trait_name(trait_class_list):
    """Helper to extract the string name of the trait from the ontology list"""
    if not trait_class_list:
        return "Unknown"
    # owlready2 returns a list of entities. We grab the first one's name.
    return trait_class_list[0].name

def get_groq_suggestions(scores, name):
    """Sends trait scores to Groq API for analysis."""
    prompt = f"""
    Analyze the personality of {name} based on these Big Five scores (Range 1-5):
    {scores}
    
    Provide a brief, supportive summary of their personality type and 3 actionable 
    suggestions for personal or professional growth based on their unique profile.
    """
    
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are an expert personality psychologist."},
                {"role": "user", "content": prompt}
            ],
            model="llama-3.3-70b-versatile",
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        return f"Error fetching suggestions from Groq: {str(e)}"

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    user_id = data.get('id')
    user_name = data.get('name')
    
    # Search for existing participant
    participant = onto.search_one(iri=f"*{user_id}")
    
    if participant:
        # User exists: Fetch their data
        # We assume the ontology links scores to the participant. 
        # Since the provided snippet doesn't explicitly show 'hasScore' linking directly 
        # from Participant in a simple way, we will search for TraitScore objects 
        # that might be associated or just return a message saying they exist.
        
        # NOTE: Logic here depends on how you linked scores to participants in previous runs.
        # For this example, we will just return a "Found" status and mock the retrieval 
        # or regenerate suggestions if the scores aren't easily traversing back in this specific ontology version.
        
        return jsonify({
            "status": "found",
            "message": f"Welcome back, {participant.name[0] if participant.name else user_name}!",
            "data": "User data retrieval would go here based on your specific object property links."
        })
    else:
        return jsonify({"status": "new", "message": "User not found. Starting assessment."})

@app.route('/get_questions', methods=['GET'])
def get_questions():
    questions_data = []
    
    # Query all individuals of class AssessmentQuestion
    # Note: Depending on owlready2 version, accessing instances might vary.
    questions = onto.search(type=onto.AssessmentQuestion)
    
    for q in questions:
        # Safely get properties. Owlready returns lists for properties.
        q_text = q.questionText[0] if q.questionText else "No text"
        q_id = q.questionID[0] if q.questionID else "NoID"
        is_reverse = q.isReverseCoded[0] if q.isReverseCoded else False
        
        # Get the trait it measures
        trait_measures = q.measures
        trait_name = get_trait_name(trait_measures)

        questions_data.append({
            "id": q_id,
            "text": q_text,
            "trait": trait_name,
            "reverse": is_reverse
        })
    
    # Sort by ID or Question Order usually desirable, here we send as is
    return jsonify(questions_data)

@app.route('/submit_assessment', methods=['POST'])
def submit_assessment():
    data = request.json
    user_id = data.get('id')
    user_name = data.get('name')
    answers = data.get('answers') # Dict of {question_id: score}
    questions_meta = data.get('meta') # We pass meta back to avoid re-querying
    
    # 1. Calculate Scores
    scores = {
        "Openness": [], "Conscientiousness": [], "Extraversion": [],
        "Agreeableness": [], "Neuroticism": []
    }
    
    for q_meta in questions_meta:
        q_id = q_meta['id']
        raw_val = int(answers.get(q_id, 3)) # Default to Neutral if missing
        
        # Reverse Scoring Logic
        final_val = (6 - raw_val) if q_meta['reverse'] else raw_val
        
        trait = q_meta['trait']
        if trait in scores:
            scores[trait].append(final_val)
            
    # Calculate Means
    final_scores = {k: round(sum(v)/len(v), 2) if v else 0 for k, v in scores.items()}

    # 2. Update Ontology
    with onto:
        # Create Participant
        # We use a unique IRI based on ID
        participant = onto.Participant(f"Participant_{user_id}")
        participant.participantID = [user_id]
        participant.name = [user_name]
        
        # Create Trait Scores and Link (Simplified for demonstration)
        for trait, value in final_scores.items():
            score_ind = onto.TraitScore(f"Score_{user_id}_{trait}")
            score_ind.meanScore = [value]
            # Ideally you would link score_ind to participant here using an ObjectProperty
            # e.g., participant.hasScore.append(score_ind) if that property exists in your schema
    
    # Save ontology (Optional: Be careful saving in production environments)
    onto.save(file=ONTOLOGY_PATH)

    # 3. Get Groq Suggestions
    suggestions = get_groq_suggestions(final_scores, user_name)
    
    return jsonify({
        "scores": final_scores,
        "analysis": suggestions
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)
