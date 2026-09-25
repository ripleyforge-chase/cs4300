# Homework 1

Python exercises and pytest tests for Tasks 1-7. Task 7 trains a small
English-to-Italian PyTorch model on authored practice sentences.

## Setup and run

Run these commands from the outer `cs4300` folder:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r homework1/requirements.txt
python -m pytest homework1/tests -q
python homework1/src/task7.py
```

Validated using Python 3.14.6. Dependencies are recorded in requirements.txt.
Task 6 expects the current working directory to be the outer cs4300 folder.
The translation test checks a known training example, not general translation accuracy.

The submission copy uses homework1/homework2 as specified in the assignment.
Imports and the Task 6 input path were adjusted from the local hw1 directory name.
