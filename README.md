# Persona Insights - AI-Powered Personality Assessment

An AI-powered personality assessment system using Big Five personality traits, semantic web technologies (RDF/OWL), and Groq AI for intelligent analysis and career role recommendations.

## 🎯 Overview

Persona Insights is a Knowledge Representation and Reasoning (KRR) project that combines:
- **Big Five Personality Assessment** - 50-question IPIP-based questionnaire
- **Semantic Web Technologies** - RDF/OWL ontology for data storage and reasoning
- **AI-Powered Analysis** - Groq LLM for personalized insights and explanations
- **Career Role Fit Prediction** - Match personality traits to Software Engineer, Manager, and Researcher roles

## ✨ Features

- 📊 **Personality Trait Scoring** - Measures Openness, Conscientiousness, Extraversion, Agreeableness, and Neuroticism
- 💼 **Performance Prediction** - Estimates job and academic performance based on trait patterns
- 🎯 **Career Role Matching** - Calculates fit scores for different career paths
- 🧠 **AI Narratives** - Generates personalized insights using Groq AI
- 📝 **Explainable Results** - Provides justifications for all predictions
- 💾 **Semantic Storage** - Persists all data in RDF/OWL format for future analysis

## 🏗️ Architecture

```
┌─────────────────┐      ┌─────────────────┐     ┌─────────────────┐
│   React + Vite  │────▶│   Flask API     │────▶│   RDF/OWL       │
│   Frontend      │      │   Backend       │     │   Ontology      │
└─────────────────┘      └────────┬────────┘     └─────────────────┘
                                  │
                                  ▼
                         ┌─────────────────┐
                         │   Groq AI API   │
                         │   (LLaMA 3.3)   │
                         └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Node.js 18+
- Groq API Key (optional, for AI features)

### Backend Setup

```bash
cd backend
pip install -r requirements.txt

# Create .env file with your Groq API key (optional)
echo "GROQ_API_KEY=your_key_here" > .env

# Run the server
python app.py
```

The backend will start at `http://localhost:5000`

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The frontend will start at `http://localhost:5173`

## 📖 Usage

1. **Start Assessment** - Navigate to `/assessment` and enter your name and ID
2. **Answer Questions** - Respond to 50 statements on a 1-5 scale
3. **View Results** - See your personality scores, performance predictions, and AI analysis
4. **Explore Career Fit** - Click on career roles to see detailed fit breakdowns

## 🔬 Technical Details

### Ontology Structure

The RDF/OWL ontology includes:
- **Participant** - User information and assessment results
- **Assessment** - Links participants to their trait scores
- **PersonalityTrait** - Big Five traits (Openness, Conscientiousness, etc.)
- **TraitScore** - Calculated scores for each trait
- **CareerRole** - Role definitions with required traits and skills
- **AssessmentQuestion** - 50 IPIP marker questions with trait mappings

### Scoring Algorithm

1. Questions are answered on a 1-5 Likert scale
2. Reverse-coded items are flipped (6 - score)
3. Trait scores are averaged and converted to percentages
4. Performance predictions use weighted trait combinations
5. Career fit scores use proximity to ideal trait profiles

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/get_questions` | GET | Retrieve all assessment questions |
| `/validate_user` | POST | Validate user ID and name |
| `/submit_assessment` | POST | Submit answers and get results |
| `/get_previous_result` | GET | Retrieve previous assessment results |
| `/api/justification/{id}` | GET | Get AI-generated justification |
| `/api/career-fit/{id}` | GET | Get career role fit analysis |

## 👥 Team

- **Talha Rusman** - Team Member
- **Raghib Rizwan** - Team Member
- **Muhammad Umar** - Team Member
- **Muhammad Rafi** - Project Supervisor

## 📄 License

This project was developed as part of the Knowledge Representation and Reasoning (KRR) course.

## 🔗 Technologies Used

- **Frontend**: React 18, Vite
- **Backend**: Flask, Python
- **Ontology**: OWLReady2, RDF/OWL
- **AI**: Groq API (LLaMA 3.3 70B)
