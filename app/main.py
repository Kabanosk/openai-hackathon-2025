from datetime import datetime

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.test import get_result_from_agent, DateStep, DateIdeaOutput
from app.models import DateForm, Place

import asyncio

app = FastAPI()
templates = Jinja2Templates(directory="app/templates")

# Mock agent storage (replace with real later)
places_db = [

    # Place(id=1, name="Romantic Cafe", description="Cozy place for first dates."),
    # Place(id=2, name="Art Museum", description="Beautiful art to admire together."),
    # Place(id=3, name="City Park", description="Walk under the stars."),
]

liked_places = set()
disliked_places = set()


@app.get("/", response_class=HTMLResponse)
async def get_form(request: Request):
    return templates.TemplateResponse("form.html", {"request": request})

async def get_all_places(city, date_str, person_description, interests):
    tasks = [
        get_result_from_agent(
            location=city,
            date_str=date_str,
            person_description=person_description,
            interests=interests,
        )
        for _ in range(3)    
    ]
    results = await asyncio.gather(*tasks)
    return results

@app.post("/submit-date-form")
async def submit_form(
    age: int = Form(...),
    interests: str = Form(...),
    date_time: datetime = Form(...),
    city: str = Form(...),
    date_type: str = Form(...),
):
    date_form = DateForm(
        age=age,
        interests=interests.split(","),
        date_time=date_time,
        city=city,
        date_type=date_type,
    )
    print(date_form)

    global places_db
    places_db = await get_all_places(
        city=date_form.city,
        date_str=date_form.date_time.strftime("%Y-%m-%d"),
        person_description=f"miła, energiczna osoba, lubiąca przygody",
        interests=", ".join(date_form.interests),
    )
    print("Sugerowane miejsca:", places_db)


    
    # TODO for @zielu: Here you would send date_form to the openai-agents
    return RedirectResponse(url="/places", status_code=303)


@app.get("/places", response_class=HTMLResponse)
async def get_places(request: Request):
    # Filter out disliked
    # available_places = [p for p in places_db if p.id not in disliked_places]
    available_places = [p for p in places_db]
    return templates.TemplateResponse(
        "places.html",
        {
            "request": request,
            "places": available_places,
        },
    )


@app.post("/like-place")
async def like_place(place_id: int = Form(...)):
    liked_places.add(place_id)
    if place_id in disliked_places:
        disliked_places.remove(place_id)
    return RedirectResponse(url="/places", status_code=303)


@app.post("/dislike-place")
async def dislike_place(place_id: int = Form(...)):
    disliked_places.add(place_id)
    if place_id in liked_places:
        liked_places.remove(place_id)
    return RedirectResponse(url="/places", status_code=303)


@app.post("/recalculate-places")
async def recalculate_places():
    # TODO for @zielu: Call AI agent again based on liked_places
    return RedirectResponse(url="/places", status_code=303)


app.mount("/static", StaticFiles(directory="app/static"), name="static")
