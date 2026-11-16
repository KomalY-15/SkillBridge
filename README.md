# SkillBridge — Skill Gap Analyzer & Career Roadmap Generator

A web-based career intelligence platform that helps users assess their technical skills, identify skill gaps, and generate personalized learning roadmaps based on their target career paths.

**Live Website:** https://skillbridge-2tu4.onrender.com

**GitHub Repository:** https://github.com/KomalY-15/SkillBridge

## About the Project

SkillBridge is a full-stack web application developed using Python, Flask, SQLite, HTML, CSS, Bootstrap, and JavaScript.

The platform allows users to select their target job role, evaluate their existing skills, and understand which additional skills they should develop.

It provides an interactive analysis dashboard, skill-match percentage, learning roadmap, and downloadable PDF report.

## Key Features

- **20 Career Paths:** Explore roles across Data Analytics, Software Development, AI, Cloud, DevOps, Cybersecurity, and more.
- **Skill Gap Analysis:** Compare selected skills with role-specific skill requirements.
- **Interactive Dashboard:** Visualize matched and missing skills using Chart.js.
- **Skill Match Percentage:** Calculate a transparent percentage based on predefined skill lists.
- **Personalized Learning Roadmap:** Generate learning steps for missing skills.
- **PDF Report Generation:** Download a detailed skill assessment report.
- **Analysis History:** Store and view previous assessments using SQLite.
- **Skill Search and Filters:** Search skills and filter by selected career path.
- **Responsive Interface:** Supports desktop and mobile devices.

## Technology Stack

| Category | Technologies |
|---|---|
| Frontend | HTML, CSS, JavaScript, Bootstrap |
| Backend | Python, Flask |
| Database | SQLite |
| Visualization | Chart.js |
| PDF Generation | ReportLab |
| Deployment | Render |
| Version Control | Git, GitHub |

## How It Works

1. Select a target career role.
2. Choose the skills you already know.
3. Click **Analyze My Skills**.
4. View your skill-match percentage.
5. Explore matched and missing skills.
6. Follow the generated learning roadmap.
7. Download the PDF analysis report.
8. View previous assessments in Analysis History.

## Project Structure

```text
SkillBridge/
├── app.py
├── skills.json
├── requirements.txt
├── README.md
├── .gitignore
├── templates/
│   ├── index.html
│   ├── dashboard.html
│   └── history.html
└── static/
    └── style.css
```

The SQLite database is created locally when the application starts.

## Installation and Setup

**1. Clone the repository**

```bash
git clone https://github.com/KomalY-15/SkillBridge.git
cd SkillBridge
```

**2. Create a virtual environment**

```bash
python3 -m venv venv
source venv/bin/activate
```

**3. Install dependencies**

```bash
pip install -r requirements.txt
```

**4. Run the application**

```bash
python app.py
```

**5. Open the application**

Visit http://127.0.0.1:5001 in your browser.

## Live Demo

Try SkillBridge here:

https://skillbridge-2tu4.onrender.com

*Note: The free hosting instance may take some time to start after inactivity. SQLite history may be reset after redeployment or service restart.*

## Future Enhancements

- User registration and authentication
- Persistent PostgreSQL database
- Alternative technology stack recommendations
- Skill proficiency levels
- Course and learning resource recommendations
- Career progress tracking
- AI-powered learning recommendations

## Author

**Komal Yadav**

GitHub: https://github.com/KomalY-15

---

*SkillBridge — Discover • Analyze • Improve*