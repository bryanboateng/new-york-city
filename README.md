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

Put the yakindu parser archive inside a folder named "packages" underneath the project folder. (new-york-city/packages/yakindu_parser-0.0.1.tar.gz).

Upgrade pip.
```bash
python -m pip install --upgrade pip
```
Install the packages.
```bash
python -m pip install -r requirements.txt --no-index --find-links packages/yakindu_parser-0.0.1.tar.gz
```

## Testing
### Running unit-tests

```bash
python -m unittest discover -v
```

