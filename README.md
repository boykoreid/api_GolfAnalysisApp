# Golf Performance Analyzer API
*Status: Version 2 complete. Full backend implemented*

A FastAPI backend for tracking, analyzing, and modeling golf performance data.

This project was built to develop practical experience with backend development, including REST API design, authentication, relational database design, automated testing, and statistical analysis. Users can record golf rounds and individual hole statistics, then use the API's analytical tools to identify scoring trends and relationships between different aspects of their game.

## Features
- Linear algebra-based predictive models for score estimation and performance analysis
- Scoring trend analysis for:
  - Greens in Regulation (GIR)
  - Putts
  - Fairways hit
  - Penalty strokes
- Scoring breakdowns by hole type:
  - Par 3
  - Par 4
  - Par 5
- JWT-based authentication for user registration and login
- Protected endpoints using FastAPI dependencies
- Role-based admin permissions
- Create, retrieve, update, and delete golf rounds

### Statistical Analysis
Users can view: 
- Predictive models for estimating scoring outcomes
- Linear algebra-based pattern analysis of golf performance
- Scoring trends across rounds
- Average score and performance statistics
- Performance breakdowns by hole type
- Relationships between scoring and individual performance metrics

The analytical system is designed to help identify which aspects of a player's game have the greatest relationship with scoring performance.

## Database Design
The application uses a relational database with foreign-key relationships between the following tables:

- Users: authentication and user information
- Rounds: round-level information such as date and course
- Holes: individual hole statistics associated with a round

Users are required to provide a score, par, and number of putts for each hole. Fairways hit and penalty strokes are optional.

## Authentication & Authorization

The API uses JWT-based authentication to protect user-specific endpoints.

Users must authenticate before accessing protected resources, while administrative functionality is restricted to users with the appropriate permissions.

## Testing

The project includes a comprehensive pytest test suite covering:

- Authentication
- User endpoints
- Round endpoints
- Analytics endpoints
- Statistical summaries
- Admin functionality
- Database interactions
- Edge cases and validation

## Current Limitations

### 9-Hole Rounds

The application currently supports 9-hole rounds only.

This was an intentional design decision. Most of my personal golf data consists of 9-hole rounds, so limiting the application to this format provides more representative data for the statistical analysis currently being developed. Support for 18-hole rounds may be introduced in a future version.

### Available Statistics
The database currently tracks:

- Putts
- Greens in Regulation (GIR)
- Fairways hit
- Penalty strokes

This was also an intentional design decision. The application is designed around the statistics that an average golfer is realistically able to track without requiring specialized golf-tracking technology. 

## Planned Features

### Version 3 — Frontend
- Develop a frontend application for interacting with the API. This will help with accessibility for non-coders
- Provide visualizations for scoring and performance trends

### Version 4 — Public Release
- Deploy the application for public use
- Improve scalability

## Technologies Used
- Python
- FastAPI
- SQLAlchemy
- Pydantic
- SQLite
- JWT
- Pytest
- NumPy

## Installation

1. Clone the repository

    ```bash
    git clone https://github.com/boykoreid/api_GolfAnalysisApp.git

    cd api_GolfAnalysisApp
    ```

2. Create a virtual environment

    ```bash
    python -m venv venv
    ```

3. Activate the virtual environment

    **Windows:**

    ```bash
    venv\Scripts\activate
    ```

4. Install dependencies

    ```bash
    pip install -r requirements.txt
    ```

5. Start the application

    ```bash
    python run.py
    ```

6. Seed the database

    To create the initial administrative user:

    ```bash
    python seed.py
    ```

    The administrative credentials used by the seed script are defined in `seed.py`.

7. Open the API documentation

    Once running, interactive API documentation is available through Swagger UI:

    ```text
    http://localhost:8001/docs
    ```
