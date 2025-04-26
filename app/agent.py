from __future__ import annotations

import os
from datetime import datetime
from dataclasses import dataclass
from typing import List

import requests
from agents import Agent, Runner, WebSearchTool
from agents.model_settings import ModelSettings

# ----------------------------------------------------------------------------
# Data Models
# ----------------------------------------------------------------------------


@dataclass
class DateStep:
    time: str
    place_name: str
    place_address: str
    transport: str
    description: str
    price: int


@dataclass
class DateIdeaOutput:
    title: str
    description: str
    itinerary: List[DateStep]
    budget_pln: int


# ----------------------------------------------------------------------------
# Weather Utility
# ----------------------------------------------------------------------------


def geocode_city(city_name: str) -> tuple[float, float]:
    """Returns geographic coordinates (lat, lon) for a given city name."""
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": city_name, "format": "json", "limit": 1}
    headers = {
        "User-Agent": "DatePlannerApp/1.0 (contact@yourdomain.com)"  # <-- Replace with your contact info
    }

    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        if not data:
            raise ValueError(f"Coordinates not found for: {city_name}")
        lat = float(data[0]["lat"])
        lon = float(data[0]["lon"])
        return lat, lon
    except requests.RequestException as e:
        raise RuntimeError(f"Error fetching coordinates: {e}")


def get_weather(location: str, date_str: str) -> str:
    """Returns a brief weather description for the given location and date."""

    lat, lon = geocode_city(location)
    date_obj = datetime.fromisoformat(date_str)
    start, end = date_obj.replace(hour=0), date_obj.replace(hour=23)

    url = (
        "https://api.open-meteo.com/v1/forecast?"
        f"latitude={lat}&longitude={lon}&hourly=temperature_2m,precipitation_probability"
        f"&start={start.isoformat()}&end={end.isoformat()}&timezone=Europe%2FWarsaw"
    )

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise RuntimeError(f"Error fetching weather forecast: {exc}")

    data = response.json()
    temps = data["hourly"]["temperature_2m"]
    prec_probs = data["hourly"].get("precipitation_probability", [0] * len(temps))

    avg_temp = sum(temps) / len(temps)
    max_prec = max(prec_probs)

    return f"Average temperature around {avg_temp:.0f} °C; chance of precipitation up to {max_prec:.0f}%."


# ----------------------------------------------------------------------------
# Agents
# ----------------------------------------------------------------------------

places_agent = Agent(
    name="Place Finder",
    instructions=(
        "You are an agent that searches for meetup spots. "
        "Using web.search, find the 10 best suggestions in the provided location, "
        "tailored to the user's interests, meetup type, budget, and time of day. "
        "For each place, provide its name and a one‑sentence description. Consider local reviews and ratings."
    ),
    tools=[WebSearchTool()],
    model="gpt-4.1",
    model_settings=ModelSettings(tool_choice="required"),
)

date_idea_agent = Agent(
    name="Meetup Idea Generator",
    instructions=(
        "You are a creative dating advisor. Based on location, date, time, companion (name, age, gender), "
        "interests, weather, meetup type, budget, and a list of places – propose an original meet idea. "
        "Include the order of activities, a plan B for bad weather, and adapt the proposal to the time of day. "
        "The description should be short, specific, and realistic."
    ),
    tools=[],
    model="gpt-4o",
    output_type=DateIdeaOutput
)


# ----------------------------------------------------------------------------
# Main Logic
# ----------------------------------------------------------------------------


async def get_result_from_agent(
    location: str,
    date_str: str,
    time_str: str | None = None,
    partner_name: str | None = None,
    partner_age: int | None = None,
    partner_gender: str | None = None,
    date_type: str | None = None,
    budget: str | None = None,
    interests: str | None = None,
) -> DateIdeaOutput:
    """Main orchestration function that coordinates the entire date‑generation process."""

    weather_summary = get_weather(location, date_str)

    # Build a standardized companion description from available info
    person_description_parts: List[str] = []
    if partner_name:
        person_description_parts.append(f"{partner_name}")
    if partner_age:
        person_description_parts.append(f"{partner_age} years old")
    if partner_gender:
        person_description_parts.append(partner_gender)

    # Default description if no specific details provided
    if not person_description_parts:
        person_description = "a friendly, energetic person who loves adventures"
    else:
        person_description = ", ".join(person_description_parts)

    # Combine date & time info
    datetime_info = date_str
    if time_str:
        datetime_info = f"{date_str} at {time_str}"

    # Budget info
    budget_info = f"Budget: {budget}" if budget else ""

    # Date type info
    date_type_info = f"Date type: {date_type}" if date_type else ""

    places_prompt = (
        f"Location: {location}\n"
        f"Date & time: {datetime_info}\n"
        f"{date_type_info}\n"
        if date_type
        else (
            "" f"{budget_info}\n"
            if budget
            else ""
            f"Interests: {interests}\n"
            f"Weather: {weather_summary}\n"
            "Please provide a list of suitable places matching these parameters."
        )
    )
    places_result = await Runner.run(places_agent, input=places_prompt)

    print("Places calculated!")
    suggested_places = places_result.final_output

    date_prompt = (
        f"Location: {location}\n"
        f"Date & time: {datetime_info}\n"
        f"Partner description: {person_description}\n"
        f"{date_type_info}\n"
        if date_type
        else (
            "" f"{budget_info}\n"
            if budget
            else ""
            f"Interests: {interests}\n"
            f"Suggested places: {suggested_places}\n"
            f"Weather: {weather_summary}\n"
            "Please propose a meetup idea."
        )
    )
    date_result = await Runner.run(date_idea_agent, input=date_prompt)

    return date_result.final_output
