from datetime import datetime
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from dataclasses import dataclass
import asyncio

from app.test import get_result_from_agent, DateIdeaOutput
from app.models import DateForm

app = FastAPI()
templates = Jinja2Templates(directory="app/templates")
app.mount("/static", StaticFiles(directory="app/static"), name="static")


@dataclass
class PlaceV2:
    id: int
    dateIdeaOutput: DateIdeaOutput


class AppState:
    def __init__(self):
        self.places_db: list[PlaceV2] = []
        self.liked_places: set[int] = set()
        self.disliked_places: set[int] = set()

    def clear_feedback(self):
        self.liked_places.clear()
        self.disliked_places.clear()

    def like_place(self, place_id: int):
        self.liked_places.add(place_id)
        self.disliked_places.discard(place_id)

    def dislike_place(self, place_id: int):
        self.disliked_places.add(place_id)
        self.liked_places.discard(place_id)

    def get_available_places(self):
        return [p for p in self.places_db if p.id not in self.disliked_places]


state = AppState()


async def get_all_places(city: str, date_str: str, person_description: str, interests: str) -> list[PlaceV2]:
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

    return [
        PlaceV2(id=i, dateIdeaOutput=result)
        for i, result in enumerate(results)
    ]


@app.get("/", response_class=HTMLResponse)
async def get_form(request: Request):
    return templates.TemplateResponse("form.html", {"request": request})


@app.post("/submit-date-form")
async def submit_form(
    age: int = Form(...),
    interests: str = Form(...),
    date_time: datetime = Form(...),
    city: str = Form(...),
    date_type: str = Form(...),
):
    form_data = DateForm(
        age=age,
        interests=interests.split(","),
        date_time=date_time,
        city=city,
        date_type=date_type,
    )

    state.clear_feedback()
    state.places_db = await get_all_places(
        city=form_data.city,
        date_str=form_data.date_time.strftime("%Y-%m-%d"),
        person_description="miła, energiczna osoba, lubiąca przygody",
        interests=", ".join(form_data.interests),
    )

    return RedirectResponse(url="/places", status_code=303)


@app.get("/places", response_class=HTMLResponse)
async def get_places(request: Request):
    return templates.TemplateResponse("places.html", {
        "request": request,
        "places": state.get_available_places(),
    })


@app.post("/like-place")
async def like_place(place_id: int = Form(...)):
    state.like_place(place_id)
    return RedirectResponse(url="/places", status_code=303)


@app.post("/dislike-place")
async def dislike_place(place_id: int = Form(...)):
    state.dislike_place(place_id)
    return RedirectResponse(url="/places", status_code=303)


@app.post("/recalculate-places")
async def recalculate_places():
    # TODO for @zielu: Call AI agent again based on liked_places
    return RedirectResponse(url="/places", status_code=303)
