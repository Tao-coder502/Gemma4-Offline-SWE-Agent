import json

with open("kaggle_submission_runner.ipynb", encoding="utf-8") as f:
    nb = json.load(f)

cell6_lines = nb["cells"][6]["source"]
print("Current Cell 6 lines 1-25:")
print("".join(cell6_lines[:25]))

