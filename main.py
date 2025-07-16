from fastapi import FastAPI\n\napp = FastAPI()\n\n@app.get("/")\nasync def read_root():\n    return {"message": "Hello from FastAPI backend!"}\n
