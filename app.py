from __future__ import annotations
import json, os, re, shutil, subprocess, time, uuid
from pathlib import Path
from typing import Literal
import litellm
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

load_dotenv()
ROOT = Path(__file__).resolve().parent
DATA = Path(os.getenv("TEAMGRIT_DATA_DIR", ROOT / "data")).resolve()
PROJECTS, RENDERS = DATA / "projects", DATA / "renders"
PROJECTS.mkdir(parents=True, exist_ok=True)
RENDERS.mkdir(parents=True, exist_ok=True)
app = FastAPI(title="Team-Grit Studio API", version="0.1.0")
app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")

class GenerateRequest(BaseModel):
    prompt: str = Field(min_length=8, max_length=4000)
    mode: Literal["auto","quality","fast","local","custom"] = "auto"
    provider: Literal["openai","anthropic","gemini","openai-compatible","local"] | None = None
    model: str | None = Field(default=None, max_length=160)
    base_url: str | None = Field(default=None, max_length=500)
    api_key: str | None = Field(default=None, max_length=1000, repr=False)
    audience: Literal["beginner","intermediate","advanced"] = "beginner"
    duration_seconds: int = Field(default=60, ge=15, le=300)
    aspect_ratio: Literal["16:9","9:16","1:1"] = "16:9"
    style: Literal["minimal","cinematic","chalkboard","editorial","technical"] = "minimal"
    narration: bool = True

class RenderRequest(BaseModel):
    quality: Literal["preview","production"] = "preview"

def resolve_provider(req):
    provider = "local" if req.mode == "local" else "openai-compatible" if req.mode == "custom" else req.provider or os.getenv("TEAMGRIT_DEFAULT_PROVIDER","openai")
    model = req.model
    if not model and req.mode == "fast": model = os.getenv("TEAMGRIT_FAST_MODEL","gpt-4o-mini")
    if not model and req.mode == "quality": model = os.getenv("TEAMGRIT_QUALITY_MODEL","gpt-4o")
    key, base = req.api_key, req.base_url
    if provider == "openai":
        model, key = model or os.getenv("OPENAI_MODEL","gpt-4o-mini"), key or os.getenv("OPENAI_API_KEY")
    elif provider == "anthropic":
        model, key = model or os.getenv("ANTHROPIC_MODEL","anthropic/claude-3-5-sonnet-latest"), key or os.getenv("ANTHROPIC_API_KEY")
    elif provider == "gemini":
        model, key = model or os.getenv("GEMINI_MODEL","gemini/gemini-2.5-flash"), key or os.getenv("GEMINI_API_KEY")
    elif provider == "openai-compatible":
        model, base, key = model or os.getenv("CUSTOM_MODEL","openai-compatible/model"), base or os.getenv("OPENAI_BASE_URL"), key or os.getenv("OPENAI_COMPATIBLE_API_KEY")
    elif provider == "local":
        model, base, key = model or os.getenv("LOCAL_MODEL","openai/local-model"), base or os.getenv("LOCAL_BASE_URL","http://localhost:11434/v1"), key or os.getenv("LOCAL_API_KEY","local")
    else: raise HTTPException(400,"Unsupported provider.")
    if not key and provider != "local": raise HTTPException(400,"No API key configured for " + provider + ". Set it in server environment or for this request.")
    if provider in ("openai-compatible","local") and not base: raise HTTPException(400,"This provider requires a base URL.")
    return model,key,base,provider

def ask_model(model,key,base,system,user):
    args={"model":model,"messages":[{"role":"system","content":system},{"role":"user","content":user}],"temperature":0.4}
    if key: args["api_key"]=key
    if base: args["api_base"]=base
    try:
        response=litellm.completion(**args)
        result=response.choices[0].message.content
        if not isinstance(result,str) or not result.strip(): raise ValueError("Empty response")
        return result.strip()
    except Exception as exc:
        raise HTTPException(502,"Model request failed ("+type(exc).__name__+"). Check provider, model, endpoint, and credentials.") from exc

def json_from_model(value):
    fence=chr(96)*3
    value=re.sub(r"^\s*"+re.escape(fence)+r"(?:json)?\s*|\s*"+re.escape(fence)+r"\s*$","",value,flags=re.I)
    try: data=json.loads(value)
    except json.JSONDecodeError:
        start,end=value.find("{"),value.rfind("}")
        try: data=json.loads(value[start:end+1])
        except Exception as exc: raise HTTPException(502,"Model returned invalid storyboard JSON. Try again.") from exc
    if not isinstance(data,dict): raise HTTPException(502,"Model returned an invalid storyboard.")
    return data

def new_id(): return uuid.uuid4().hex[:12]
def project_path(pid):
    if not re.fullmatch(r"[a-f0-9]{12}",pid): raise HTTPException(400,"Invalid project ID.")
    path=PROJECTS/(pid+".json")
    if not path.exists(): raise HTTPException(404,"Project not found.")
    return path
def load_project(pid): return json.loads(project_path(pid).read_text(encoding="utf-8"))

@app.get("/")
def home(): return FileResponse(ROOT/"static"/"index.html")

@app.get("/api/v1/health")
def health(): return {"status":"ok","service":"team-grit-studio","version":app.version}

@app.get("/api/v1/providers")
def provider_options():
    return {"modes":[{"id":"auto","label":"Auto"},{"id":"quality","label":"Quality"},{"id":"fast","label":"Fast"},{"id":"local","label":"Local model"},{"id":"custom","label":"Custom API"}],
    "providers":[{"id":"openai","configured":bool(os.getenv("OPENAI_API_KEY"))},{"id":"anthropic","configured":bool(os.getenv("ANTHROPIC_API_KEY"))},{"id":"gemini","configured":bool(os.getenv("GEMINI_API_KEY"))},{"id":"openai-compatible","configured":bool(os.getenv("OPENAI_BASE_URL"))},{"id":"local","configured":bool(os.getenv("LOCAL_BASE_URL"))}],
    "note":"Request keys are used transiently and are never saved in project data."}

@app.post("/api/v1/projects")
def create_project(req: GenerateRequest):
    model,key,base,provider=resolve_provider(req)
    system="""You are an exceptional educator and Manim animation director. Return ONLY valid JSON with keys title, learning_objective, visual_direction, narration_style, scenes. scenes is an array of 3-8 objects with title, objective, visual_description, animation_beats (array), on_screen_text (array), narration, duration_seconds. Build a progressive explanation, not a list of facts. Use elegant visual metaphors, readable text, smooth transitions, correct mathematics, and no filler."""
    storyboard=json_from_model(ask_model(model,key,base,system,json.dumps({"prompt":req.prompt,"audience":req.audience,"duration_seconds":req.duration_seconds,"aspect_ratio":req.aspect_ratio,"style":req.style,"narration":req.narration})))
    scenes=storyboard.get("scenes")
    if not isinstance(scenes,list) or not 2<=len(scenes)<=10: raise HTTPException(502,"Storyboard must contain 2–10 scenes.")
    code_system="""You are a senior Manim Community Edition animator. Return ONLY Python source code, no markdown. Write a self-contained class named GeneratedScene using from manim import *. Make polished educational motion design: clear hierarchy, deliberate spacing, consistent palette, smooth transitions, readable equations, one main idea at a time. Use standard Manim CE APIs only. Do not use network, filesystem, subprocess, eval, exec, dynamic imports, or external assets. Keep all objects in frame. Narration is rendered separately."""
    code=ask_model(model,key,base,code_system,json.dumps({"prompt":req.prompt,"storyboard":storyboard,"aspect_ratio":req.aspect_ratio,"style":req.style,"duration_seconds":req.duration_seconds,"requirements":["Class must be GeneratedScene.","Only import manim and optionally math/random.","Do not access files, network, shell, or dynamic imports.","Make a coherent visual story, not a title and bullet list."]}))
    fence=chr(96)*3
    code=re.sub(r"^\s*"+re.escape(fence)+r"(?:python)?\s*|\s*"+re.escape(fence)+r"\s*$","",code,flags=re.I)
    if "class GeneratedScene" not in code or "from manim import" not in code: raise HTTPException(502,"Model did not return a valid Manim scene. Try again.")
    pid=new_id()
    project={"id":pid,"created_at":int(time.time()),"prompt":req.prompt,"settings":{"mode":req.mode,"provider":provider,"model":model,"audience":req.audience,"duration_seconds":req.duration_seconds,"aspect_ratio":req.aspect_ratio,"style":req.style,"narration":req.narration},"storyboard":storyboard,"code":code,"status":"draft"}
    (PROJECTS/(pid+".json")).write_text(json.dumps(project,indent=2),encoding="utf-8")
    return {"project":project}

@app.get("/api/v1/projects")
def list_projects():
    result=[]
    for path in sorted(PROJECTS.glob("*.json"),key=lambda p:p.stat().st_mtime,reverse=True)[:50]:
        try:
            p=json.loads(path.read_text(encoding="utf-8"))
            result.append({"id":p["id"],"title":p.get("storyboard",{}).get("title","Untitled story"),"prompt":p.get("prompt",""),"created_at":p.get("created_at"),"status":p.get("status","draft")})
        except Exception: continue
    return {"projects":result}

@app.get("/api/v1/projects/{project_id}")
def get_project(project_id:str): return {"project":load_project(project_id)}

@app.get("/api/v1/projects/{project_id}/code")
def get_code(project_id:str): 
    p=load_project(project_id)
    return {"project_id":project_id,"code":p["code"]}

@app.get("/api/v1/projects/{project_id}/narration")
def get_narration(project_id:str):
    p=load_project(project_id)
    return {"project_id":project_id,"style":p["storyboard"].get("narration_style","clear and conversational"),"transcript":[{"scene":s.get("title"),"text":s.get("narration",""),"duration_seconds":s.get("duration_seconds",0)} for s in p["storyboard"].get("scenes",[])]}

@app.get("/api/v1/projects/{project_id}/captions")
def get_captions(project_id:str):
    p=load_project(project_id); offset=0.0; lines=[]
    def stamp(seconds):
        ms=int(max(0,seconds)*1000); h,ms=divmod(ms,3600000); m,ms=divmod(ms,60000); s,ms=divmod(ms,1000)
        return f"{h:02}:{m:02}:{s:02},{ms:03}"
    for i,scene in enumerate(p["storyboard"].get("scenes",[]),1):
        duration=float(scene.get("duration_seconds",5) or 5)
        lines.append(f"{i}\n{stamp(offset)} --> {stamp(offset+duration)}\n{scene.get('narration',scene.get('title',''))}\n")
        offset+=duration
    return {"project_id":project_id,"format":"srt","content":"\n".join(lines)}

@app.post("/api/v1/projects/{project_id}/renders")
def render_project(project_id:str,req:RenderRequest):
    p=load_project(project_id)
    if not shutil.which("docker"): raise HTTPException(503,"Docker is required for isolated rendering. Install Docker Desktop and start it.")
    rid=new_id(); work=(RENDERS/rid).resolve(); work.mkdir(parents=True,exist_ok=False)
    (work/"scene.py").write_text(p["code"],encoding="utf-8")
    quality="l" if req.quality=="preview" else "m"
    cmd=["docker","run","--rm","--network","none","--memory","2g","--cpus","2","--pids-limit","128","--read-only","--tmpfs","/tmp:rw,nosuid,size=512m","-e","HOME=/tmp","-v",str(work)+":/work:rw","-w","/work",os.getenv("MANIM_DOCKER_IMAGE","manimcommunity/manim:stable"),"manim","-q"+quality,"--disable_caching","scene.py","GeneratedScene"]
    started=time.monotonic()
    try: result=subprocess.run(cmd,capture_output=True,text=True,timeout=300,check=False)
    except subprocess.TimeoutExpired: raise HTTPException(504,"Render exceeded the 5-minute limit. Try a shorter animation.")
    if result.returncode!=0: raise HTTPException(422,detail={"message":"Manim render failed.","logs":(result.stderr or result.stdout or "Unknown error")[-4000:]})
    videos=list(work.rglob("*.mp4"))
    if not videos: raise HTTPException(500,"Renderer produced no MP4.")
    video=max(videos,key=lambda f:f.stat().st_size)
    p["status"]="rendered"; p["latest_render"]={"id":rid,"path":str(video.relative_to(RENDERS)),"quality":req.quality,"duration_seconds":round(time.monotonic()-started,2)}
    project_path(project_id).write_text(json.dumps(p,indent=2),encoding="utf-8")
    return {"render_id":rid,"project_id":project_id,"status":"completed","duration_seconds":p["latest_render"]["duration_seconds"],"video_url":"/api/v1/renders/"+rid+"/video"}

@app.get("/api/v1/renders/{render_id}/video")
def render_video(render_id:str):
    if not re.fullmatch(r"[a-f0-9]{12}",render_id): raise HTTPException(400,"Invalid render ID.")
    for path in PROJECTS.glob("*.json"):
        try:
            p=json.loads(path.read_text(encoding="utf-8")); latest=p.get("latest_render",{})
            if latest.get("id")==render_id:
                video=(RENDERS/latest["path"]).resolve()
                if video.is_file() and RENDERS in video.parents: return FileResponse(video,media_type="video/mp4",filename="team-grit-"+p["id"]+".mp4")
        except Exception: continue
    raise HTTPException(404,"Render not found.")
