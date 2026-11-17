# EqualPlay AI

EqualPlay AI is an AI-powered football match intelligence platform designed to make match information more accessible and easier to understand.

The platform processes structured football match events and statistics, generates AI-powered summaries and commentary, and presents the match through multiple accessibility-focused viewing modes.

## Features

- AI-generated match summaries using Azure AI
- Expressive and simplified AI commentary
- Event-by-event match replay
- Match timeline with playback controls
- First-half and second-half navigation
- Key match moments and event feed
- Live-style match statistics
- Persistent commentary caching to reduce repeated AI requests
- Accessibility-focused interface with three viewing modes:
  - Visual
  - Audio-first
  - Simplified
- Adjustable narration speed
- Screen-reader-friendly match updates
- Keyboard-accessible controls
- Responsive dark-themed frontend

## Tech Stack

### Backend

- Python
- FastAPI
- Azure AI
- REST APIs
- JSON-based synthetic football event data

### Frontend

- HTML
- CSS
- JavaScript

### Deployment

- Azure App Service — Backend API
- GitHub Pages — Frontend

## Project Architecture

```text
           Football Match Data
                    |
                    v
        Data Validation & Processing
                    |
                    v
      Match Statistics / Event Processing
                    |
        +----------------------+
        |                      |
        v                      v
    FastAPI API             Azure AI
        |                      |
        |                  Summaries &
        |                  Commentary
        |                      |
        +----------+-----------+
                   |
                   v
             Web Interface
                   |
        +----------+----------+
        |          |          |
      Visual   Audio-first  Simplified
```

## Project Structure

```text
equalplay-ai/
|
├── data/
│   └── synthetic/
│       ├── match_001.json
│       ├── match_001_metadata.json
│       └── match_001_commentary_cache.json
|
├── src/
│   ├── api/
│   │   └── main.py
│   |
│   ├── ai/
│   │   ├── azure_client.py
│   │   ├── match_summary.py
│   │   └── commentary_cache.py
│   |
│   └── processing/
│       └── match_stats.py
|
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── script.js
|
├── requirements.txt
└── README.md
```

> The exact folder structure may vary slightly depending on the current repository version.

## API Endpoints

### Match Data

```http
GET /api/events
```

Returns match events in chronological order.

```http
GET /api/stats
```

Returns calculated match statistics.

```http
GET /api/replay
```

Returns data used for match replay and timeline playback.

```http
GET /api/key-moments
```

Returns important events from the match.

### AI Features

```http
GET /api/ai/summary
```

Generates a natural-language summary of the match using Azure AI.

```http
GET /api/ai/commentary
```

Returns AI-generated football commentary.

Commentary can be provided in different styles, including:

- Expressive
- Simplified

## Running the Project Locally

### 1. Clone the Repository

```bash
git clone https://github.com/pranavng/equalplay-ai.git
cd equalplay-ai
```

### 2. Create a Virtual Environment

#### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
```

#### Windows

```bash
python -m venv .venv
.venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file and add the required Azure AI configuration.

Example:

```env
AZURE_AI_ENDPOINT=your_endpoint
AZURE_AI_API_KEY=your_api_key
AZURE_AI_DEPLOYMENT=your_deployment_name
```

Do not commit API keys or secrets to GitHub.

### 5. Run the FastAPI Backend

From the project root:

```bash
uvicorn src.api.main:app --reload
```

The API will normally be available at:

```text
http://127.0.0.1:8000
```

FastAPI documentation:

```text
http://127.0.0.1:8000/docs
```

### 6. Run the Frontend

If the frontend is inside the `frontend` directory:

```bash
python -m http.server 5500 --directory frontend
```

Then open:

```text
http://localhost:5500
```

## Accessibility Modes

### Visual

Designed for users who prefer a traditional match interface with statistics, match events, timeline controls, and AI-generated insights.

### Audio-first

Focuses on spoken match narration so users can follow match events with minimal visual interaction.

### Simplified

Reduces information density and presents important match events and commentary in a clearer, easier-to-follow format.

## AI Commentary Caching

EqualPlay AI stores generated commentary in a persistent JSON cache.

This helps:

- Reduce repeated Azure AI requests
- Reduce token usage
- Improve response speed
- Keep commentary consistent during repeated match replays

Cached commentary can be regenerated when the commentary version changes.

## Data Processing

The backend processes event-level football data to calculate match statistics such as:

- Goals
- Shots
- Shots on target
- Expected goals (xG)
- Possession
- Pass accuracy
- Corners
- Fouls
- Yellow cards
- Tackles
- Interceptions

The processed data is then exposed through FastAPI endpoints and used by the frontend and AI components.

## Example Match

The current demo uses a curated synthetic match between Chelsea and Manchester City.

Final score:

```text
Chelsea 2 - 3 Manchester City
```

The synthetic dataset allows the complete system to be demonstrated without relying on a paid or restricted live football data provider.

## Deployment

The application is deployed using:

- GitHub Pages for the frontend
- Azure App Service for the FastAPI backend
- Azure AI for AI-generated summaries and commentary

The deployed frontend communicates with the backend through REST API requests.

## Project Goals

EqualPlay AI was built to explore how generative AI can improve the accessibility and presentation of football data.

The project focuses on:

- Accessible sports experiences
- AI-generated football narratives
- Backend API development
- Event-driven data processing
- Generative AI integration
- Cloud deployment

## Future Improvements

Possible future extensions include:

- Support for multiple matches
- Integration with live football data
- Additional commentary styles
- User-customisable accessibility preferences
- Improved narration controls
- Player-level match insights
- Historical match comparison
- Additional languages

## Authors

Developed collaboratively by **Pranav Ghatigar** and **Dhruv Ghatigar**.

## License

This project is intended for educational and portfolio purposes.
