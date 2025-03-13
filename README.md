# ProjectForge

A comprehensive project management application built with Streamlit.

## Running with Docker

### Prerequisites

- Docker
- Docker Compose

### Quick Start

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/projectforge.git
   cd projectforge
   ```

2. Build and start the Docker container:
   ```
   docker-compose up -d
   ```

3. Access the application in your browser:
   ```
   http://localhost:8501
   ```

### Data Persistence

The application data is stored in a SQLite database file in the `./data` directory, which is mounted as a volume in the Docker container. This ensures that your data persists even if the container is stopped or removed.

### Stopping the Application
