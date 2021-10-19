# new-york-city

## Getting Started

### Virtual Environment
Create a virtual environment.

```bash
python3 -m venv venv
```
Activate the virtual environment.
```bash
source venv/bin/activate
```

### Dependency Requirements

Install local packages.
```bash
python -m pip install packages/*
```
Install remote packages.
```bash
python -m pip install -r requirements.txt
```

## Testing
### Running unit-tests

```bash
cd tests
python -m unittest discover -v
```

