## Running the Project with Docker

This project is containerized for easy development and deployment using Docker and Docker Compose. Below are the instructions and details specific to this setup.

### Project-Specific Docker Requirements
- **Python Version:** 3.9 (as specified in the Dockerfile: `FROM python:3.9-slim`)
- **System Dependencies:** Installs `gcc`, `python3-dev`, and `libpq-dev` for building and running Python dependencies.
- **Entrypoint:** Uses Daphne ASGI server to run the Django project (`web_project.asgi:application`).

### Environment Variables
- No required environment variables are specified in the Dockerfile or docker-compose.yml by default.
- If you need to use environment variables, you can create a `.env` file and uncomment the `env_file: .env` line in `docker-compose.yml`.

### Build and Run Instructions
1. **Build and start the services:**
   ```sh
   docker-compose up --build
   ```
   This will build the Docker image and start the `python-web_project` service.

2. **Access the application:**
   - The Daphne server will be available at [http://localhost:8000](http://localhost:8000)

### Ports
- **8000:** Exposed by the `python-web_project` service for the Daphne/ASGI server.

### Special Configuration
- **User:** The container runs as a non-root user (`appuser`) for improved security.
- **Static/Media Files:**
  - By default, static and media files are not persisted outside the container.
  - To persist these files, uncomment and configure the `volumes` section in `docker-compose.yml`:
    ```yaml
    volumes:
      - ./media:/app/media
      - ./staticfiles:/app/staticfiles
    ```
- **Networks:** Uses a custom bridge network `webnet` for service isolation.

### Additional Notes
- If you add a database or other services, update the `depends_on` and `volumes` sections in `docker-compose.yml` as needed.
- The default command can be overridden in `docker-compose.yml` if you need to run migrations or other management commands.
