# Hospital Management System

A backend system built with **Django** and **Django REST Framework (DRF)** for managing hospital operations — patient records, appointments, doctors, and staff/admin administration. The API is secured with **JWT authentication** and documented via **Swagger**.

## Features

-  **Patient Management** — create, view, update, and manage patient records
-  **Appointment Scheduling** — book and manage appointments between patients and doctors
-  **Doctor Management** — manage doctor profiles, specializations, and availability
-  **Admin / Staff Management** — manage hospital staff and administrative roles
- **JWT Authentication** — secure, token-based authentication for all API endpoints
-  **Swagger API Documentation** — interactive API docs for exploring and testing endpoints
- **Docker Support** — containerized setup for consistent local and production environments

## Tech Stack

- **Backend Framework:** Django, Django REST Framework
- **Authentication:** JWT (JSON Web Tokens)
- **API Documentation:** Swagger / OpenAPI
- **Containerization:** Docker
- **Environment Management:** venv

## Prerequisites

- Python 3.14
- pip
- Docker & Docker Compose (optional, for containerized setup)

## Installation

### Option 1: Local Setup (venv)

1. **Clone the repository**

    \`\`\`bash
    git clone https://github.com/your-username/hospital-management-system.git
    cd hospital-management-system
    \`\`\`

2. **Create and activate a virtual environment**

    \`\`\`bash
    python -m venv venv

    # On Windows
    venv\Scripts\activate

    # On macOS/Linux
    source venv/bin/activate
    \`\`\`

3. **Install dependencies**

    \`\`\`bash
    pip install -r requirements.txt
    \`\`\`

4. **Set up environment variables**

    Create a `.env` file in the project root and add the required variables (e.g. `SECRET_KEY`, `DEBUG`, database credentials, JWT settings). See `.env.example` if available.

5. **Apply database migrations**

    \`\`\`bash
    python manage.py migrate
    \`\`\`

6. **Create a superuser** (for admin access)

    \`\`\`bash
    python manage.py createsuperuser
    \`\`\`

7. **Run the development server**

    \`\`\`bash
    python manage.py runserver
    \`\`\`

    The API will be available at `http://127.0.0.1:8000/`.

### Option 2: Docker Setup

1. **Build and start the containers**

    \`\`\`bash
    docker compose up --build
    \`\`\`

2. **Run migrations inside the container** (if not automated)

    \`\`\`bash
    docker compose exec web python manage.py migrate
    \`\`\`

3. **Create a superuser inside the container**

    \`\`\`bash
    docker compose exec web python manage.py createsuperuser
    \`\`\`

## API Documentation

Once the server is running, interactive API documentation is available via Swagger:

\`\`\`
http://127.0.0.1:8000/api/docs/
\`\`\`

Use this to explore available endpoints, view request/response schemas, and test the API directly.

## Authentication

This project uses **JWT authentication**. To access protected endpoints:

1. Obtain a token by authenticating via the login/token endpoint (see Swagger docs for exact path).
2. Include the token in the `Authorization` header of subsequent requests:

    \`\`\`
    Authorization: Bearer 
    \`\`\`

## Project Structure

\`\`\`
hospital-management-system/
├── manage.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env
├── Hospital-Management/          # Project settings
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
└── apps/                    # Django apps
    ├── patients/
    ├── doctors/
    ├── appointments/
    └── staff/
\`\`\`



## Running Tests

\`\`\`bash
python manage.py test
\`\`\`

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Commit your changes (`git commit -m 'Add some feature'`)
4. Push to the branch (`git push origin feature/your-feature`)
5. Open a Pull Request

## License

This project is licensed under the [MIT License](LICENSE) — update this section if a different license applies.

## Authors

1. Erika Gwiyo
2. Jaden Afrika
3. Fidelis Njoki
4. Favour Kendi
5. Gladwell Birika
