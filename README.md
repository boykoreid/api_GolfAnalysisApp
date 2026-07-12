# Golf Performance Analyzer API
*Status: Version 1 complete. Statistical analytics and predictive modeling currently under development.*

A FastAPI backend application for tracking and analyzing golf performance data.

This project was built to practice backend development concepts including REST APIs (through FastAPI), authentication, database design, testing, and data analytics. The application allows users to record and manage golf rounds while laying the foundation for future statistical analysis and predictive modeling.

## Features
- JWT-based authentication
- User registration and login
- Protected endpoints using FastAPI dependencies
- Admin permission system

## Round Tracking
Create, edit, retrieve, and delete golf rounds

Record individual hole statistics including:
- Par
- Score
- Putts
- Greens in Regulation (GIR)

Support for front-nine and back-nine rounds

## Database Design
The application uses foreign keys to link database tables. Database tables include:
- Users
- Rounds
- Holes

Each round consists of individual hole records, allowing for flexible analytics and future statistical modeling.

## Testing
The project includes a comprehensive pytest test suite covering:

- Authentication
- User endpoints
- Round endpoints
- Admin functionality
- Database interactions and edge cases

## Current Limitations
At this stage, the application supports 9-hole rounds only.

This decision was intentional. Most of my personal golf data consists of 9-hole rounds, and limiting the application to this format currently provides more representative statistics for future analysis. Support for 18-hole rounds may be added in a future version.

## Planned Features
The statistics module is currently under development and will eventually include:

- Linear algebra-based predictive models for score estimation and performance analysis
- Round summaries
- User performance analytics
- Greens in Regulation trends
- Putting trends
- Scoring breakdowns by hole type (Par 3, Par 4, Par 5)

The long-term goal is to use historical golf data to build personalized predictive insights rather than simple descriptive statistics.

# Technologies Used
- Python
- FastAPI
- SQLAlchemy
- Pydantic
- SQLite
- JWT Authentication
- Pytest

## Installation

1. Clone the repository:
```bash
 git clone <api_GolfAnalysisApp>
 cd <api_GolfAnalysisApp>
```

2. Create a virtual environment:
  ```bash
  python -m venv venv
  ```

3. Activate the virtual environment (for Windows):

  ```bash
  venv\Scripts\activate
  ```

4. Install dependencies:

  ```bash
  pip install -r requirements.txt
  ```

5. Running the Application

  ```bash
  python run.py
  ```

Once running, interactive API documentation is available through Swagger UI:

http://localhost:8001/docs
