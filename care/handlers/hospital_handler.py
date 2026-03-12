import logging
import math
from typing import Tuple, List, Dict
import aiohttp
from telegram import (
    Update,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    KeyboardButton,
)
from telegram.ext import (
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

from config import MAPS_GEOSERVICE, MAPS_MAX_RESULTS, MAPS_API_EMAIL

logger = logging.getLogger(__name__)

ASKING_LOCATION = 0


def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return distance in kilometers between two coordinates."""
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(d_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


async def start_hospital(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Entry point for /hospital command."""
    keyboard = ReplyKeyboardMarkup(
        [[KeyboardButton("📍 Share live location", request_location=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )

    await update.message.reply_text(
        "🏥 Nearby Hospitals Finder\n\n"
        "Please share your live location or type your city/address.\n"
        "I'll list the nearest hospitals/clinics for you.",
        reply_markup=keyboard,
    )

    return ASKING_LOCATION


async def receive_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle user location or text input and return hospitals."""
    await update.message.reply_text("🔍 Looking for hospitals near you...", reply_markup=ReplyKeyboardRemove())

    try:
        if update.message.location:
            lat = update.message.location.latitude
            lon = update.message.location.longitude
        else:
            query = update.message.text
            lat, lon = await _geocode_text(query)

        hospitals = await _fetch_hospitals(lat, lon)

        if not hospitals:
            await update.message.reply_text(
                "😔 I couldn't find hospitals near that location. "
                "Please try another address or share your live location."
            )
            return ASKING_LOCATION

        response = "🏥 Nearest Hospitals:\n\n"
        for idx, hospital in enumerate(hospitals, start=1):
            response += _format_hospital(idx, hospital)

        await update.message.reply_text(response)
        await update.message.reply_text(
            "Stay safe! Use /hospital again anytime you need nearby facilities."
        )

    except ValueError as exc:
        await update.message.reply_text(str(exc))
        return ASKING_LOCATION
    except Exception as exc:
        logger.error("Hospital lookup failed: %s", exc, exc_info=True)
        await update.message.reply_text(
            "❌ Sorry, I couldn't fetch hospital details right now. Please try again soon."
        )
        return ConversationHandler.END

    return ConversationHandler.END


async def _geocode_text(query: str) -> Tuple[float, float]:
    """Convert place text to coordinates using Nominatim."""
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": query, "format": "json", "limit": 1}

    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15)) as session:
        headers = {"User-Agent": f"CareGenieBot ({MAPS_API_EMAIL})"}
        async with session.get(url, params=params, headers=headers) as resp:
            data = await resp.json()
            if not data:
                raise ValueError("I couldn't find that location. Please try again.")
            return float(data[0]["lat"]), float(data[0]["lon"])


async def _fetch_hospitals(lat: float, lon: float) -> List[Dict]:
    """Fetch hospitals using Overpass API around provided coordinates."""
    radius = MAPS_GEOSERVICE.get("radius", 5000)
    query = f"""
    [out:json][timeout:25];
    (
      node["amenity"="hospital"](around:{radius},{lat},{lon});
      node["healthcare"="clinic"](around:{radius},{lat},{lon});
    );
    out body;
    """

    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=25)) as session:
        headers = {"User-Agent": f"CareGenieBot ({MAPS_API_EMAIL})"}
        async with session.post(
            "https://overpass-api.de/api/interpreter",
            data={"data": query},
            headers=headers,
        ) as resp:
            payload = await resp.json()

    elements = payload.get("elements", [])
    hospitals = []
    for element in elements:
        tags = element.get("tags", {})
        name = tags.get("name")
        if not name:
            continue

        distance = _haversine(lat, lon, element["lat"], element["lon"])

        hospitals.append(
            {
                "name": name,
                "lat": element["lat"],
                "lon": element["lon"],
                "distance": distance,
                "address": tags.get("addr:full")
                or f"{tags.get('addr:street', '')} {tags.get('addr:city', '')}".strip(),
                "phone": tags.get("phone") or tags.get("contact:phone"),
                "opening_hours": tags.get("opening_hours"),
            }
        )

    hospitals.sort(key=lambda h: h["distance"])
    return hospitals[:MAPS_MAX_RESULTS]


def _format_hospital(index: int, hospital: Dict) -> str:
    """Format hospital data into a user-friendly message."""
    parts = [
        f"{index}. {hospital['name']} ({hospital['distance']:.1f} km)",
    ]
    if hospital["address"]:
        parts.append(f"📍 {hospital['address']}")
    parts.append(f"📌 Map: https://maps.google.com/?q={hospital['lat']},{hospital['lon']}")

    if hospital["phone"]:
        parts.append(f"☎️ {hospital['phone']}")
    if hospital["opening_hours"]:
        parts.append(f"🕒 Hours: {hospital['opening_hours']}")

    return "\n".join(parts) + "\n\n"


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel the hospital finder conversation."""
    await update.message.reply_text(
        "Cancelled. Use /hospital whenever you need nearby facilities.",
        reply_markup=ReplyKeyboardRemove(),
    )
    return ConversationHandler.END


def get_handler():
    return ConversationHandler(
        entry_points=[CommandHandler("hospital", start_hospital)],
        states={
            ASKING_LOCATION: [
                MessageHandler(filters.LOCATION, receive_location),
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_location),
            ]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        name="hospital_locator",
        persistent=False,
        allow_reentry=True,
        conversation_timeout=300,
    )


def get_additional_handlers():
    return []

