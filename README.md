install dependencies
```bash
pip install -r requirements.txt
```

make an .env with `OPENAI_API_KEY`

```bash
cp .env.example .env
```

run the ui

```bash
gradio ui.py
```

## docker instructions:

build:

```bash
docker build -t finance-ui .

docker run -p 7860:7860 finance-ui
```