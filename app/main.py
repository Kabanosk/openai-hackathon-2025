from datetime import datetime, timedelta

from dotenv import load_dotenv
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from dataclasses import dataclass
import asyncio
from typing import List, Optional

from app.agent import get_result_from_agent, DateIdeaOutput
from app.models import DateForm

app = FastAPI()
templates = Jinja2Templates(directory="app/templates")
app.mount("/static", StaticFiles(directory="app/static"), name="static")
load_dotenv()

app.mount(
    "/static",                           
    StaticFiles(directory="app/static"),
    name="static" 
)

@dataclass
class PlaceV2:
    id: int
    dateIdeaOutput: DateIdeaOutput


class AppState:
    def __init__(self):
        self.places_db: list[PlaceV2] = []
        self.liked_places: set[int] = set()
        self.disliked_places: set[int] = set()
        self.last_form: DateForm | None = None
        self.current_place_info = None

    def clear_feedback(self):
        self.liked_places.clear()
        self.disliked_places.clear()

    def like_place(self, place_id: int):
        self.liked_places.add(place_id)
        self.disliked_places.discard(place_id)

    def dislike_place(self, place_id: int):
        self.disliked_places.add(place_id)
        self.liked_places.discard(place_id)

    def info_place(self, place_id: int):
        print(f"LOOK FOR ID {place_id}")
        for place in self.places_db:
            if place.id == place_id:
                print(f"FOUND {place_id}")
                self.current_place_info = place
                return place
        return None

    def get_available_places(self):
        return [p for p in self.places_db if p.id not in self.disliked_places]


state = AppState()


async def get_all_places(
    city: str,
    date_time: datetime,
    partner_name: Optional[str] = None,
    partner_age: Optional[int] = None,
    partner_gender: Optional[str] = None,
    interests: Optional[List[str]] = None,
    date_type: Optional[str] = None,
    budget: Optional[str] = None
) -> list[PlaceV2]:
    tasks = [
        get_result_from_agent(
            location=city,
            date_str=date_time.strftime("%Y-%m-%d"),
            time_str=date_time.strftime("%H:%M"),
            partner_name=partner_name,
            partner_age=partner_age,
            partner_gender=partner_gender,
            date_type=date_type,
            budget=budget,
            interests=", ".join(interests) if interests else ""
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
    name: Optional[str] = Form(...),
    age: int = Form(...),
    gender: Optional[str] = Form(...),
    interests: str = Form(...),
    date_time: datetime = Form(...),
    city: str = Form(...),
    date_type: str = Form(...),
    budget: Optional[str] = Form(...),
):
    form_data = DateForm(
        name=name,
        age=age,
        gender=gender,
        interests=interests.split(","),
        date_time=date_time,
        city=city,
        date_type=date_type,
        budget=budget,
    )

    state.last_form = form_data  # Save the form for recalculation
    state.clear_feedback()
    state.places_db = await get_all_places(
        city=form_data.city,
        date_time=form_data.date_time,
        partner_name=form_data.name,
        partner_age=form_data.age,
        partner_gender=form_data.gender,
        interests=form_data.interests,
        date_type=form_data.date_type,
        budget=form_data.budget
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
    for i in range(3):
        if place_id != i:
             state.dislike_place(place_id)
    state.like_place(place_id)

    return RedirectResponse(url="/place-details?show=false", status_code=303)


@app.post("/dislike-place")
async def dislike_place(place_id: int = Form(...)):
    state.dislike_place(place_id)
    return RedirectResponse(url="/places", status_code=303)

@app.post("/info-place")
async def info_place(place_id: int = Form(...)):
    state.info_place(place_id)
    return RedirectResponse(url="/place-details", status_code=303)

@app.get("/place-details", response_class=HTMLResponse)
async def get_place_details(request: Request, show: str = "true"):
    show_bool = show.lower() == "true"
    place = state.current_place_info

    if place and place.dateIdeaOutput.itinerary:
        fmt = "%H:%M"
        itinerary = place.dateIdeaOutput.itinerary
        start_time = datetime.strptime(itinerary[0].time, fmt)
        end_time = datetime.strptime(itinerary[-1].time, fmt) + timedelta(hours=1)

        now = datetime.utcnow()
        start_utc = datetime(now.year, now.month, now.day, start_time.hour, start_time.minute)
        end_utc = datetime(now.year, now.month, now.day, end_time.hour, end_time.minute)

        start_str = start_utc.strftime("%Y%m%dT%H%M%SZ")
        end_str = end_utc.strftime("%Y%m%dT%H%M%SZ")
        calendar_dates = f"{start_str}/{end_str}"
    else:
        calendar_dates = ""

    return templates.TemplateResponse(
        "place_details.html",
        {
            "request": request,
            "place": place,
            "show": show_bool,
            "calendar_dates": calendar_dates
        },
    )

@app.post("/recalculate-places")
async def recalculate_places():
    if state.last_form is None:
        return RedirectResponse(url="/", status_code=303)

    state.clear_feedback()
    state.places_db = await get_all_places(
        city=state.last_form.city,
        date_time=state.last_form.date_time,
        partner_name=state.last_form.name,
        partner_age=state.last_form.age,
        partner_gender=state.last_form.gender,
        interests=state.last_form.interests,
        date_type=state.last_form.date_type,
        budget=state.last_form.budget
    )

    return RedirectResponse(url="/places", status_code=303)