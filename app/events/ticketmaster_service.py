import httpx
import logging
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import status

from app.events.models import Event
from app.core.exceptions import CustomError
from app.core.config import settings 
import random


logger = logging.getLogger(__name__)

class TicketmasterService:
    
    BASE_URL = "https://app.ticketmaster.com/discovery/v2/events.json"

    @staticmethod
    async def fetch_and_save_events(db: AsyncSession, manager_id: int):
        # We don't need to check "if not api_key" manually anymore.
        # Pydantic Settings guarantees it exists if the app started successfully.

        random_page = random.randint(0, 5)
        # 1. Prepare Query
        params = {
            "apikey": settings.TICKETMASTER_API_KEY, 
            "classificationName": "music",
            "size": 10,
            "page": random_page,
            "sort": "date,asc",
            "countryCode": "US" 
        }
        logger.info(f"Manager {manager_id} started Ticketmaster import...")

        # Opens a connection to the internet.
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(TicketmasterService.BASE_URL, params=params)     
                if response.status_code != 200:
                    logger.error(f"Ticketmaster API Error: {response.status_code}")
                    raise CustomError("External API Error", status_code=status.HTTP_502_BAD_GATEWAY)
                # text to dictionary so we can access using key names
                data = response.json()
            except httpx.RequestError as e:
                logger.error(f"Network error connecting to Ticketmaster: {e}")
                raise CustomError("Network Error", status_code=status.HTTP_503_SERVICE_UNAVAILABLE)

        if "_embedded" not in data:
            logger.warning("No events found in Ticketmaster response.")
            return {"message": "No events found."}

        events_list = data["_embedded"]["events"]
        saved_count = 0

        # 3. Process & Save
        for item in events_list:
            try:
                tm_name = item.get("name") # getting the name of event from list of events and that list is a list of dictionary 
                
                # --- DATE PARSING ---
                # Ticketmaster sends: "2025-06-21T19:00:00Z"
                try:
                    date_str = item["dates"]["start"]["dateTime"]
                    # Convert ISO string to Python datetime
                    event_date = datetime.fromisoformat(date_str.replace("Z", "+00:00")) 
                except (KeyError, ValueError, TypeError):
                    # Skip events with missing dates
                    continue 

                # --- DESCRIPTION ---
                venue = "Unknown Venue"
                if "_embedded" in item and "venues" in item["_embedded"]:
                    venue = item["_embedded"]["venues"][0].get("name")
                
                description_text = f"Live at {venue}. Imported from Ticketmaster."

                # --- DUPLICATE CHECK ---
                # Check if event with same name already exists
                existing = await db.execute(select(Event).where(Event.name == tm_name))
                if existing.scalars().first():
                    continue

                # --- CREATE MODEL ---
                new_event = Event(
                    name=tm_name,
                    description=description_text,
                    event_time=event_date,
                    ticket_price=20.00,
                    total_tickets=100,      # Default value
                    available_tickets=100,  # Initially all are available
                    manager_id=manager_id,  # Assigned to the user who ran the import
                    status="UPCOMING"
                )       
                db.add(new_event)
                saved_count += 1
                
            except Exception as e:
                logger.warning(f"Skipping specific event due to error: {e}")
                continue

        await db.commit()
        logger.info(f"Import complete. Saved {saved_count} new events.")
        
        return {
            "status": "success", 
            "events_imported": saved_count
        }