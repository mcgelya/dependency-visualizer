## Usage

Clone this repository using:
```bash
git clone https://github.com/mcgelya/dependency-visualizer
```

Activate `venv`:
```bash
python -m venv .venv
source .venv/bin/activate
```

Then install `fastapi`:
```bash
pip install "fastapi[standard]"
```

Then all other requirements:
```bash
pip install -r requirements.txt
```

Then run with:

```bash
fastapi dev app/main.py 
```
