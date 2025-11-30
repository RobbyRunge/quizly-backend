# Quizly Backend

A Django REST API backend for generating and managing quizzes from YouTube videos using AI-powered content analysis.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Installation](#installation)
  - [Prerequisites](#prerequisites)
  - [Setup](#setup)
- [Configuration](#configuration)
- [Running the Application](#running-the-application)
- [API Documentation](#api-documentation)
  - [Authentication Endpoints](#authentication-endpoints)
  - [Quiz Management Endpoints](#quiz-management-endpoints)
- [Database Models](#database-models)
- [Testing](#testing)
- [Security](#security)
- [Contributing](#contributing)
- [License](#license)

## Overview

Quizly Backend is a RESTful API service that enables users to automatically generate educational quizzes from YouTube video content. The system uses AI to transcribe videos, analyze content, and create relevant multiple-choice questions.

## Features

- 🔐 **User Authentication**: JWT-based authentication with registration, login, and logout
- 📹 **YouTube Integration**: Generate quizzes from YouTube videos
- 🤖 **AI-Powered**: Uses Google's Gemini AI for content analysis and question generation
- 📝 **Quiz Management**: Create, read, update, and delete quizzes
- 👥 **User-Specific Content**: Users can only manage their own quizzes
- 🔒 **Permission System**: Role-based access control with custom permissions
- 🧪 **Comprehensive Testing**: Full test coverage with pytest
- 📊 **Admin Interface**: Django admin panel for content management

## Tech Stack

- **Framework**: Django 5.2.8
- **REST API**: Django REST Framework 3.16.1
- **Authentication**: Django REST Framework SimpleJWT 5.3.1
- **Database**: SQLite (default, configurable for PostgreSQL/MySQL)
- **AI Integration**: Google Generative AI (Gemini)
- **Video Processing**: OpenAI Whisper for transcription
- **Testing**: pytest, pytest-django, pytest-cov
- **CORS**: django-cors-headers

## Project Structure

```
quizly-backend/
├── auth_app/                   # Authentication application
│   ├── api/                    # API-specific code
│   │   ├── authentication.py   # Custom authentication
│   │   ├── serializers.py      # Data serialization
│   │   ├── urls.py             # URL routing
│   │   └── views.py            # API views
│   ├── migrations/             # Database migrations
│   └── tests/                  # Test files
│       ├── test_login.py
│       ├── test_logout.py
│       └── test_register.py
├── quiz_management_app/        # Quiz management application
│   ├── api/                    # API-specific code
│   │   ├── serializers.py      # Data serialization
│   │   ├── urls.py             # URL routing
│   │   └── views.py            # API views
│   ├── migrations/             # Database migrations
│   ├── models.py               # Database models
│   └── tests/                  # Test files
│       ├── conftest.py
│       ├── test_create_quiz.py
│       ├── test_delete_quiz.py
│       ├── test_external_apis.py
│       ├── test_get_quizzes.py
│       ├── test_list_quizzes.py
│       └── test_models.py
├── core/                       # Project configuration
│   ├── settings.py             # Django settings
│   ├── urls.py                 # Main URL configuration
│   └── wsgi.py                 # WSGI configuration
├── db.sqlite3                  # SQLite database
├── manage.py                   # Django management script
├── requirements.txt            # Python dependencies
├── pytest.ini                  # Pytest configuration
├── TESTING.md                  # Testing documentation
└── README.md                   # This file
```

## Installation

### Prerequisites

- Python 3.10 or higher
- pip (Python package manager)
- Git
- Virtual environment tool (venv)

### Setup

1. **Clone the repository**
   ```powershell
   git clone https://github.com/RobbyRunge/quizly-backend.git
   cd quizly-backend
   ```

2. **Create a virtual environment**
   ```powershell
   python -m venv .venv
   ```

3. **Activate the virtual environment**
   ```powershell
   # Terminal
   .venv/Scripts/activate

   # Windows PowerShell
   .\.venv\Scripts\Activate.ps1
   
   # Windows Command Prompt
   .venv\Scripts\activate.bat
   ```

4. **Install dependencies**
   ```powershell
   pip install -r requirements.txt
   ```

5. **Create a `.env` file** in the project root with the following variables:
   ```env
   SECRET_KEY=your-secret-key-here
   DEBUG=True
   ALLOWED_HOSTS=localhost,127.0.0.1
   GEMINI_API_KEY=your-gemini-api-key-here
   ```

6. **Run database migrations**
   ```powershell
   python manage.py migrate
   ```

7. **Create a superuser** (optional, for admin access)
   ```powershell
   python manage.py createsuperuser
   ```

8. **Run server**
   ```powershell
   python manage.py runserver
   ```

## Configuration

The project uses environment variables for configuration. Key settings include:

- `SECRET_KEY`: Django secret key for cryptographic signing
- `DEBUG`: Enable/disable debug mode (True for development, False for production)
- `ALLOWED_HOSTS`: Comma-separated list of allowed hostnames
- `GEMINI_API_KEY`: Google Gemini API key for AI-powered quiz generation

### JWT Configuration

JWT tokens are configured in `core/settings.py`:
- Access token lifetime: 15 minutes
- Refresh token lifetime: 1 days
- Token stored in cookies with HTTP-only flag

## Running the Application

Start the development server:

```powershell
python manage.py runserver
```

The API will be available at `http://localhost:8000/`

Access the admin panel at `http://localhost:8000/admin/`

## API Documentation

### Authentication Endpoints

#### Register User
- **URL**: `/api/register/`
- **Method**: `POST`
- **Body**:
  ```json
  {
    "username": "string",
    "password": "string",
    "confirmed_password": "string",
    "email": "string",
  }
  ```
- **Response**: `201 Created`
  ```json
  {
    "message": "User registered successfully."
  }
  ```

#### Login
- **URL**: `/api/login/`
- **Method**: `POST`
- **Body**:
  ```json
    {
        "username": "your_username",
        "password": "your_password"
    }
  ```
- **Response**: `200 OK` (Sets JWT tokens in HTTP-only cookies)
  ```json
    {
        "detail": "Login successfully!",
        "user": {
            "id": 1,
            "username": "your_username",
            "email": "your_email@example.com"
        }
    }
  ```

#### Logout
- **URL**: `/api/logout/`
- **Method**: `POST`
- **Authentication**: Required
- **Response**: `200 OK`
  ```json
    {
        "detail": "Log-Out successfully! All Tokens will be deleted. Refresh token is now invalid."
    }
  ```

### Quiz Management Endpoints

#### List User's Quizzes
- **URL**: `/api/quizzes/`
- **Method**: `GET`
- **Authentication**: Required
- **Response**: `200 OK`
  ```json
    [
        {
            "id": 1,
            "title": "Quiz Title",
            "description": "Quiz Description",
            "created_at": "2023-07-29T12:34:56.789Z",
            "updated_at": "2023-07-29T12:34:56.789Z",
            "video_url": "https://www.youtube.com/watch?v=example",
            "questions": [
                {
                    "id": 1,
                    "question_title": "Question 1",
                    "question_options": [
                    "Option A",
                    "Option B",
                    "Option C",
                    "Option D"
                    ],
                    "answer": "Option A"
                }
            ]
        }
    ]
  ```

#### Create Quiz from YouTube Video
- **URL**: `/api/createQuiz/`
- **Method**: `POST`
- **Authentication**: Required
- **Body**:
  ```json
    {
        "url": "https://www.youtube.com/watch?v=example"
    }
  ```
- **Response**: `201 Created`
  ```json
    {
        "id": 1,
        "title": "Quiz Title",
        "description": "Quiz Description",
        "created_at": "2023-07-29T12:34:56.789Z",
        "updated_at": "2023-07-29T12:34:56.789Z",
        "video_url": "https://www.youtube.com/watch?v=example",
        "questions": [
            {
                "id": 1,
                "question_title": "Question 1",
                "question_options": [
                    "Option A",
                    "Option B",
                    "Option C",
                    "Option D"
                ],
                "answer": "Option A",
                "created_at": "2023-07-29T12:34:56.789Z",
                "updated_at": "2023-07-29T12:34:56.789Z"
            }
        ]
    }
  ```

#### Get Quiz Details
- **URL**: `/api/quizzes/<id>/`
- **Method**: `GET`
- **Authentication**: Required
- **Response**: `200 OK`
  ```json
    {
        "id": 1,
        "title": "Quiz Title",
        "description": "Quiz Description",
        "created_at": "2023-07-29T12:34:56.789Z",
        "updated_at": "2023-07-29T14:45:12.345Z",
        "video_url": "https://www.youtube.com/watch?v=example",
        "questions": [
            {
                "id": 1,
                "question_title": "Question 1",
                "question_options": [
                    "Option A",
                    "Option B",
                    "Option C",
                    "Option D"
                ],
                "answer": "Option A"
            }
        ]
    }
  ```

#### Patch Quiz Details
- **URL**: `/api/quizzes/<id>/`
- **Method**: `PATCH`
- **Authentication**: Required
- **Response**: `200 OK`
- **Body**:
  ```json
    {
        "title": "Partially Updated Title"
    }
  ```
- **Response**: `200 OK`
  ```json
    {
        "id": 1,
        "title": "Partially Updated Title",
        "description": "Quiz Description",
        "created_at": "2023-07-29T12:34:56.789Z",
        "updated_at": "2023-07-29T14:45:12.345Z",
        "video_url": "https://www.youtube.com/watch?v=example",
        "questions": [
            {
                "id": 1,
                "question_title": "Question 1",
                "question_options": [
                    "Option A",
                    "Option B",
                    "Option C",
                    "Option D"
                ],
                "answer": "Option A"
            }
        ]
    }
  ```

#### Delete Quiz
- **URL**: `/api/quizzes/<id>/`
- **Method**: `DELETE`
- **Authentication**: Required is 
- **Response**: `204 No Content`

## Database Models

### User Model
Uses Django's built-in `User` model from `django.contrib.auth.models`.

### Quiz Model
- `title`: CharField (max_length=255)
- `description`: TextField (max_length=150)
- `video_url`: URLField
- `created_by`: ForeignKey to User
- `created_at`: DateTimeField (auto_now_add)
- `updated_at`: DateTimeField (auto_now)

### Question Model
- `quiz`: ForeignKey to Quiz
- `question_title`: CharField (max_length=500)
- `question_options`: JSONField (array of options)
- `answer`: CharField (max_length=255)
- `created_at`: DateTimeField (auto_now_add)
- `updated_at`: DateTimeField (auto_now)

## Testing

For comprehensive testing documentation, please refer to [TESTING.md](TESTING.md).

### Quick Start

Run all tests:
```powershell
pytest
```

Run tests with coverage report:
```powershell
pytest --cov=auth_app --cov=quiz_management_app --cov-report=html
```

View coverage report:
```powershell
start htmlcov/index.html
```

Run specific test file:
```powershell
pytest auth_app/tests/test_register.py
```

Run tests in verbose mode:
```powershell
pytest -v
```

### Test Coverage

The project includes comprehensive test coverage for:
- User registration, login, and logout
- Quiz creation from YouTube videos
- Quiz retrieval and listing
- Quiz deletion
- Permission and authentication checks
- External API integrations (YouTube, Whisper, Gemini)
- Model validations

## Security

### Authentication
- JWT-based authentication with HTTP-only cookies
- CSRF protection enabled
- Password hashing using Django's PBKDF2 algorithm

### Permissions
- Custom permission classes ensure users can only access their own quizzes
- Admin users have full access to all resources
- Token-based authentication for API endpoints

### CORS
- Configured for cross-origin requests
- Credentials allowed for cookie-based authentication
- Configurable allowed origins

### Environment Variables
- Sensitive data stored in environment variables
- `.env` file excluded from version control
- Secret key rotation recommended for production

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

Please ensure:
- All tests pass (`pytest`)
- Code follows PEP 8 style guidelines
- New features include appropriate tests
- Documentation is updated

## License

This project is part of the Developer Academy curriculum. All rights reserved.

---

**Project**: Quizly Backend  
**Author**: Robby Runge  
**Repository**: [github.com/RobbyRunge/quizly-backend](https://github.com/RobbyRunge/quizly-backend)
