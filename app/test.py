from __future__ import annotations

import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import requests
from agents import Agent, Runner, WebSearchTool
from agents.model_settings import ModelSettings


load_dotenv()

# ----------------------------------------------------------------------------
# Agent wyszukujący ciekawe miejsca
# ----------------------------------------------------------------------------

places_agent = Agent(
    name="Wyszukiwarka miejsc",
    instructions=(
        "Jesteś pomocnym agentem, który znajduje ciekawe miejsca na randki. "
        "Użyj narzędzia web.search, aby zwrócić krótką listę 10 najlepszych "
        "miejsc w podanej lokalizacji, pasujących do zainteresowań użytkownika. "
        "Dostarcz gotową listę nazw i jednozdaniowy opis każdego miejsca."
    ),
    tools=[WebSearchTool()],
    model="gpt-4.1",
    model_settings=ModelSettings(tool_choice="required"),
)

# ----------------------------------------------------------------------------
# Funkcja pobierająca prognozę pogody z Open-Meteo
# ----------------------------------------------------------------------------

def get_weather(location: str, date_str: str) -> str:
    """Zwraca jednozdaniowy opis pogody w danym dniu dla podanej lokalizacji.

    Aktualnie obsługiwane lokalizacje (można łatwo rozszerzyć słownik):
    * Warszawa
    * Kraków
    * Wrocław
    """

    # Prosta mapa miasto → współrzędne; dla produkcji warto użyć geokodera.
    coords = {
        "Warszawa": (52.2298, 21.0118),
        "Kraków": (50.0647, 19.9450),
        "Wrocław": (51.1079, 17.0385),
    }

    if location not in coords:
        raise ValueError(
            f"Nie znam współrzędnych dla lokalizacji '{location}'. "
            "Dodaj ją do słownika 'coords'."
        )

    lat, lon = coords[location]

    # Open-Meteo oczekuje formatu ISO 8601 z godziną.
    date_obj = datetime.fromisoformat(date_str)
    start = date_obj.replace(hour=0, minute=0, second=0)
    end = start + timedelta(hours=23)

    url = (
        "https://api.open-meteo.com/v1/forecast?"
        f"latitude={lat}&longitude={lon}&hourly=temperature_2m,precipitation_probability"
        f"&start={start.isoformat()}&end={end.isoformat()}&timezone=Europe%2FWarsaw"
    )

    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
    except requests.RequestException as exc:
        raise RuntimeError(f"Błąd pobierania prognozy z Open-Meteo: {exc}")

    data = r.json()

    temps = data["hourly"]["temperature_2m"]
    prec_probs = data["hourly"].get("precipitation_probability", [0] * len(temps))

    avg_temp = sum(temps) / len(temps)
    max_prec = max(prec_probs) if prec_probs else 0

    summary = (
        f"Średnia temperatura około {avg_temp:.0f} °C; szansa opadów do {max_prec:.0f}%."
    )
    return summary

from dataclasses import dataclass
from typing import List

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
    """Struktura danych zwracana przez date_idea_agent."""
    title: str                 
    description: str           
    itinerary: List[DateStep]       
    budget_pln: int            


date_idea_agent = Agent(
    name="Pomysł na randkę",
    instructions=(
        "Jesteś kreatywnym doradcą randkowym. "
        "Na podstawie lokalizacji, daty, opisu osoby, zainteresowań, pogody i "
        "listy sugerowanych miejsc – zaproponuj unikalny, szczegółowy pomysł "
        "na randkę, uwzględniający kolejność aktywności, budżet i plan B na złą "
        "pogodę. Utrzymaj opis całkiem krótki, ale zawierający wszystkie "
        "istotne informacje. "
        "Wszystko po polsku."
    ),
    tools=[],
    model="o3-mini",
    output_type=DateIdeaOutput
)

async def get_result_from_agent(location: str = "Warszawa", date_str: str = None, person_description: str = None, interests: str = None):
    # location = "Warszawa"
    # date_str = datetime.now().strftime("%Y-%m-%d")
    # person_description = "miła, energiczna osoba, lubiąca przygody"
    # interests = "kino, sztuka, spacery, sport"

    weather = get_weather(location, date_str)
    print("Prognoza pogody:", weather)

    places_prompt = (
        f"Lokalizacja: {location}\n"
        f"Zainteresowania: {interests}\n"
        f"Pogoda: {weather}\n"
        "Proszę podaj listę propozycji miejsc."
    )

    places_result = await Runner.run(places_agent, input=places_prompt)
    suggested_places = places_result.final_output

    print("\nSugerowane miejsca obliczone!\n")

    user_input = (
        f"Lokalizacja: {location}\n"
        f"Data: {date_str}\n"
        f"Opis osoby: {person_description}\n"
        f"Zainteresowania: {interests}\n"
        f"Sugerowane miejsca: {suggested_places}\n"
        f"Pogoda: {weather}\n"
        "Proszę zaproponuj pomysł na randkę."
    )

    result = await Runner.run(date_idea_agent, input=user_input)


    print("\nPomysł na randkę:")
    print(result.final_output)

    return result.final_output

# if __name__ == "__main__":
#     main()