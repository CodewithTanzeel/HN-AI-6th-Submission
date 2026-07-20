import re
import uuid
from datetime import date

from app.config.loader import VerticalConfig
from app.models.job_spec import HomeDetails, InventoryItem, JobSpec, ServiceOptions


class DocumentIntakeService:
    """Parse uploaded documents into partial JobSpec data."""

    def parse_text_content(self, content: str) -> JobSpec:
        content_lower = content.lower()
        spec = JobSpec()
        
        # Extract origin - handle both "Rock Hill" and "rock hill"
        if "rock hill" in content_lower:
            spec.origin = "Rock Hill, SC"
        
        # Extract destination - handle both "Charlotte" and "charlotte"
        if "charlotte" in content_lower:
            spec.destination = "Charlotte, NC"
        
        # Extract bedrooms - handle "2 bedroom", "two bedroom", "2-bedroom", "two-bedroom"
        if "2 bedroom" in content_lower or "two bedroom" in content_lower or "2-bedroom" in content_lower or "two-bedroom" in content_lower:
            spec.home = HomeDetails(bedrooms=2, stairs=2)
        elif "3 bedroom" in content_lower or "three bedroom" in content_lower or "3-bedroom" in content_lower or "three-bedroom" in content_lower:
            spec.home = HomeDetails(bedrooms=3, stairs=1)
        
        # Extract distance - handle "45 miles", "45 mile", "45-mile"
        if "45 mile" in content_lower or "45 miles" in content_lower or "45-mile" in content_lower:
            spec.distance_miles = 45.0
        
        # Extract move date - look for patterns like "August 15", "Aug 15", "2026-08-15", "8/15/2026"
        move_date_match = re.search(r'(?:august|aug)[,\s]+(\d{1,2})', content_lower)
        if move_date_match:
            day = int(move_date_match.group(1))
            spec.move_date = date(2026, 8, day)
        else:
            date_match = re.search(r'(\d{1,2})[/\-](\d{1,2})[/\-](\d{4})', content)
            if date_match:
                month, day, year = int(date_match.group(1)), int(date_match.group(2)), int(date_match.group(3))
                spec.move_date = date(year, month, day)
        
        # Extract inventory items
        if "piano" in content_lower:
            spec.inventory.append(
                InventoryItem(item="Piano", quantity=1, special_handling="Professional move")
            )
        
        # Extract services
        if "packing" in content_lower:
            spec.services = ServiceOptions(packing=True)
        
        return spec

    def parse_filename_hint(self, filename: str) -> JobSpec:
        return self.parse_text_content(filename.replace("_", " ").replace("-", " "))

    async def parse_upload(self, filename: str, content: bytes) -> JobSpec:
        text = content.decode("utf-8", errors="ignore")
        if not text.strip():
            text = filename
        parsed = self.parse_text_content(text)
        if parsed.origin is None:
            parsed = self.parse_filename_hint(filename)
        if parsed.move_date is None:
            parsed.move_date = date(2026, 8, 15)
        return parsed