## Requirements

### Requirement: Reproducible Environment
The system SHALL provide a `Dockerfile` that automates the installation of Python 3.12 and all dependencies listed in `requirements.txt`.

### Requirement: Lightweight Image
The final Docker image SHALL be optimized for size, preferably under 500MB.

### Requirement: Persistent Storage
The system SHALL use Docker Volumes to ensure that the SQLite database file (`vinbot.db`) remains persistent across container restarts and updates.

### Requirement: Orchestration
A `docker-compose.yml` file SHALL be provided to:
- Build the bot image.
- Map the necessary ports (8000).
- Load environment variables from a `.env` file.
- Mount the database volume.

### Requirement: Security
The container SHOULD NOT run as the `root` user for production deployments (optional but recommended).
The `.dockerignore` file SHALL exclude sensitive and temporary files.
