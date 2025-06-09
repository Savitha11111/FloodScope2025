# Tests for FloodScope AI

This directory contains unit tests for the FloodScope AI project.

## Setting up the environment

Before running the tests, it is recommended to create and activate a Python virtual environment.

### Create and activate virtual environment

On Mac/Linux:
```bash
python3 -m venv venv
source venv/bin/activate
```

On Windows:
```bash
python -m venv venv
venv\Scripts\activate.bat
```

### Install dependencies

Install the required dependencies using pip:

```bash
pip install -r requirements-local.txt
```

## Running the tests

The tests use the built-in `unittest` framework.

To run all tests in this directory, execute:

```bash
python -m unittest discover -s tests
```

## Notes

- The tests mock external API calls, so you do **not** need to run the API server separately to run the tests.
- Ensure your virtual environment is activated before running the tests to use the correct dependencies.
