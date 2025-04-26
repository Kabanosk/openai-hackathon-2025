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
    """Zwraca współrzędne geograficzne (lat, lon) na podstawie nazwy miasta."""
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": city_name,
        "format": "json",
        "limit": 1
    }
    headers = {
        "User-Agent": "DatePlannerApp/1.0 (kontakt@twojadomena.pl)"  # <-- Replace with your contact info
    }

    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        if not data:
            raise ValueError(f"Nie znaleziono współrzędnych dla: {city_name}")
        lat = float(data[0]["lat"])
        lon = float(data[0]["lon"])
        return lat, lon
    except requests.RequestException as e:
        raise RuntimeError(f"Błąd pobierania współrzędnych: {e}")


def get_weather(location: str, date_str: str) -> str:
    """Zwraca opis pogody dla podanej lokalizacji i daty."""

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
        raise RuntimeError(f"Błąd pobierania prognozy: {exc}")

    data = response.json()
    temps = data["hourly"]["temperature_2m"]
    prec_probs = data["hourly"].get("precipitation_probability", [0] * len(temps))

    avg_temp = sum(temps) / len(temps)
    max_prec = max(prec_probs)

    return f"Średnia temperatura około {avg_temp:.0f} °C; szansa opadów do {max_prec:.0f}%."


# ----------------------------------------------------------------------------
# Agents
# ----------------------------------------------------------------------------

places_agent = Agent(
    name="Wyszukiwarka miejsc",
    instructions=(
        "Jesteś pomocnym agentem, który znajduje ciekawe miejsca na randki. "
        "Użyj narzędzia web.search, aby zwrócić krótką listę 10 najlepszych miejsc "
        "w podanej lokalizacji, pasujących do zainteresowań użytkownika i typu randki. "
        "Uwzględnij przedział budżetowy i porę dnia. "
        "Dostarcz gotową listę nazw i jednozdaniowy opis każdego miejsca."
    ),
    tools=[WebSearchTool()],
    model="gpt-4.1",
    model_settings=ModelSettings(tool_choice="required"),
)

date_idea_agent = Agent(
    name="Pomysł na randkę",
    instructions=(
        "Jesteś kreatywnym doradcą randkowym. "
        "Na podstawie lokalizacji, daty, godziny, opisu osoby (imię, wiek, płeć), "
        "zainteresowań, pogody, typu randki i budżetu oraz listy sugerowanych miejsc – "
        "zaproponuj unikalny, szczegółowy pomysł na randkę. "
        "Uwzględnij kolejność aktywności, trzymaj się określonego budżetu i planu B na złą pogodę. "
        "Opis powinien być krótki, ale zawierać wszystkie istotne informacje. "
        "Dopasuj plan do pory dnia i godziny. "
        "Wszystko po polsku."
    ),
    tools=[],
    model="o3-mini",
    output_type=DateIdeaOutput
)


# ----------------------------------------------------------------------------
# Main Logic
# ----------------------------------------------------------------------------

async def get_result_from_agent(
    location: str,
    date_str: str,
    time_str: str = None,
    partner_name: str = None,
    partner_age: int = None,
    partner_gender: str = None,
    date_type: str = None,
    budget: str = None,
    interests: str = None
) -> DateIdeaOutput:
    """Główna funkcja orchestrująca cały proces generowania randki."""

    weather_summary = get_weather(location, date_str)
    
    # Create a standardized person description using all available information
    person_description_parts = []
    if partner_name:
        person_description_parts.append(f"{partner_name}")
    if partner_age:
        person_description_parts.append(f"{partner_age} lat")
    if partner_gender:
        person_description_parts.append(partner_gender)
    
    # Set default description if no specific details provided
    if not person_description_parts:
        person_description = "miła, energiczna osoba, lubiąca przygody"
    else:
        person_description = ", ".join(person_description_parts)
    
    # Format date and time information
    datetime_info = date_str
    if time_str:
        datetime_info = f"{date_str} o godz. {time_str}"
    
    # Format budget information
    budget_info = ""
    if budget:
        budget_info = f"Budżet: {budget}"
    
    # Format date type information
    date_type_info = ""
    if date_type:
        date_type_info = f"Typ randki: {date_type}"

    places_prompt = (
        f"Lokalizacja: {location}\n"
        f"Data i czas: {datetime_info}\n"
        f"{date_type_info}\n" if date_type else ""
        f"{budget_info}\n" if budget else ""
        f"Zainteresowania: {interests}\n"
        f"Pogoda: {weather_summary}\n"
        "Proszę podaj listę propozycji miejsc pasujących do tych parametrów."
    )
    places_result = await Runner.run(places_agent, input=places_prompt)
    suggested_places = places_result.final_output

    date_prompt = (
        f"Lokalizacja: {location}\n"
        f"Data i czas: {datetime_info}\n"
        f"Opis osoby: {person_description}\n"
        f"{date_type_info}\n" if date_type else ""
        f"{budget_info}\n" if budget else ""
        f"Zainteresowania: {interests}\n"
        f"Sugerowane miejsca: {suggested_places}\n"
        f"Pogoda: {weather_summary}\n"
        "Proszę zaproponuj pomysł na randkę."
    )
    date_result = await Runner.run(date_idea_agent, input=date_prompt)

    return date_result.final_output