from fastapi import FastAPI

app = FastAPI(title="Human Memory Experiment API")


@app.get("/api/health")
def health_check():
    return {"status": "ok"}
