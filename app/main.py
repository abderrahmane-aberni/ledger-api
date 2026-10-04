from fastapi import FastAPI

app = FastAPI(title="Ledger API")

@app.get("/")
def root():
    return {"message": "Ledger API is running"}