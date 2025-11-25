<!-- Add this fil to README.md -->
# Testing Setup for Quizly Backend

## Installation

Install the testing dependencies:

```powershell
pip install -r requirements.txt
```

## Running Tests

### Run all tests
```powershell
pytest
```

### Run tests with coverage
```powershell
pytest --cov=auth_app --cov-report=html
```

### Run specific test file
```powershell
pytest auth_app/tests/test_register.py
```

### Run specific test
```powershell
pytest auth_app/tests/test_register.py::TestRegisterView::test_register_user_success
```

### Run tests in verbose mode
```powershell
pytest -v
```

## Coverage Reports

After running tests with coverage, view the HTML report:
```powershell
start htmlcov/index.html
```

## Test Structure

- `auth_app/tests/test_register.py` - Tests for user registration endpoint
- Test fixtures provide reusable test data
- Tests are organized by scenario (success, validation errors, edge cases)
