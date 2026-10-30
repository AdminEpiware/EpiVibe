from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import initialize
from app.modules.projects.router import router as projects_router
from app.modules.research.router import router as research_router
from app.modules.concept.router import router as concept_router
from app.modules.refinement.router import router as refinement_router
from app.modules.execution_plan.router import router as execution_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize()
    yield

app = FastAPI(title='EpiVibe API', description='AI Event Strategist Backend', version='1.0.0', lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=['http://localhost:5173','http://127.0.0.1:5173'], allow_credentials=False, allow_methods=['GET','PUT','POST','DELETE','OPTIONS'], allow_headers=['*'])
app.include_router(projects_router)
app.include_router(research_router)
app.include_router(concept_router)
app.include_router(refinement_router)
app.include_router(execution_router)

@app.get('/')
def root():
    return {'application':'EpiVibe','message':'AI Event Strategist API','status':'running'}

@app.get('/api/health')
def health_check():
    return {'status':'healthy','service':'epivibe-backend'}
