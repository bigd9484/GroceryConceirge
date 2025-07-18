#!/usr/bin/env python3
"""
GroceryConcierge - Smart Fridge Management System
================================================

A comprehensive smart fridge system that manages inventory, generates meal plans,
creates grocery lists, and handles ordering and scheduling.

Author: Claude AI
Version: 1.0.0
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import openai
import requests
from dataclasses import dataclass, asdict
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class FridgeItem:
    """Represents a single item in the fridge inventory."""
    name: str
    quantity: int
    unit: str
    expiry_date: str
    category: str = "misc"
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class GroceryItem:
    """Represents a grocery item for shopping."""
    name: str
    quantity: int
    unit: str
    category: str
    estimated_price: float = 0.0
    store_item_id: Optional[str] = None


class FridgeInventory:
    """
    Manages the smart fridge inventory system.
    
    Handles loading, saving, and manipulating fridge contents.
    Can work with either a JSON file or hardcoded data.
    """
    
    def __init__(self, inventory_file: str = "fridge_inventory.json"):
        self.inventory_file = inventory_file
        self.items: List[FridgeItem] = []
        self.load_inventory()
    
    def load_inventory(self) -> None:
        """Load inventory from JSON file or create default if file doesn't exist."""
        try:
            if os.path.exists(self.inventory_file):
                with open(self.inventory_file, 'r') as f:
                    data = json.load(f)
                    self.items = [FridgeItem(**item) for item in data]
                logger.info(f"Loaded {len(self.items)} items from {self.inventory_file}")
            else:
                # Create default inventory if file doesn't exist
                self._create_default_inventory()
                self.save_inventory()
                logger.info("Created default inventory")
        except Exception as e:
            logger.error(f"Error loading inventory: {e}")
            self._create_default_inventory()
    
    def _create_default_inventory(self) -> None:
        """Create a default inventory with sample items."""
        default_items = [
            FridgeItem("Milk", 1, "gallon", "2025-07-25", "dairy"),
            FridgeItem("Eggs", 8, "pieces", "2025-07-30", "dairy"),
            FridgeItem("Chicken Breast", 2, "lbs", "2025-07-22", "meat"),
            FridgeItem("Broccoli", 1, "head", "2025-07-21", "vegetable"),
            FridgeItem("Carrots", 5, "pieces", "2025-07-28", "vegetable"),
            FridgeItem("Bread", 1, "loaf", "2025-07-20", "grain"),
            FridgeItem("Cheese", 8, "oz", "2025-08-01", "dairy"),
            FridgeItem("Tomatoes", 3, "pieces", "2025-07-23", "vegetable"),
            FridgeItem("Onion", 2, "pieces", "2025-08-05", "vegetable"),
            FridgeItem("Rice", 2, "cups", "2026-01-01", "grain")
        ]
        self.items = default_items
    
    def save_inventory(self) -> None:
        """Save current inventory to JSON file."""
        try:
            with open(self.inventory_file, 'w') as f:
                json.dump([item.to_dict() for item in self.items], f, indent=2)
            logger.info(f"Saved inventory to {self.inventory_file}")
        except Exception as e:
            logger.error(f"Error saving inventory: {e}")
    
    def get_expiring_soon(self, days: int = 3) -> List[FridgeItem]:
        """Get items expiring within specified days."""
        cutoff_date = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
        expiring = [item for item in self.items 
                   if item.expiry_date <= cutoff_date]
        return expiring
    
    def get_low_stock(self, threshold: int = 2) -> List[FridgeItem]:
        """Get items with low stock (quantity below threshold)."""
        return [item for item in self.items if item.quantity <= threshold]
    
    def remove_item(self, name: str, quantity: int = 1) -> bool:
        """Remove quantity of an item from inventory."""
        for item in self.items:
            if item.name.lower() == name.lower():
                if item.quantity >= quantity:
                    item.quantity -= quantity
                    if item.quantity == 0:
                        self.items.remove(item)
                    self.save_inventory()
                    return True
                else:
                    logger.warning(f"Not enough {name} in inventory")
                    return False
        logger.warning(f"{name} not found in inventory")
        return False
    
    def add_item(self, item: FridgeItem) -> None:
        """Add a new item to inventory or update existing quantity."""
        for existing_item in self.items:
            if existing_item.name.lower() == item.name.lower():
                existing_item.quantity += item.quantity
                self.save_inventory()
                return
        self.items.append(item)
        self.save_inventory()
    
    def get_inventory_summary(self) -> Dict[str, List[FridgeItem]]:
        """Get inventory organized by category."""
        summary = {}
        for item in self.items:
            if item.category not in summary:
                summary[item.category] = []
            summary[item.category].append(item)
        return summary


class MealPlanner:
    """
    AI-powered meal planning system using OpenAI GPT.
    
    Generates meal plans based on available ingredients and dietary preferences.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize with OpenAI API key."""
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if self.api_key:
            openai.api_key = self.api_key
        else:
            logger.warning("OpenAI API key not provided. Using mock responses.")
    
    def generate_meal_plan(self, 
                          inventory: List[FridgeItem], 
                          days: int = 7,
                          dietary_preferences: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Generate a meal plan based on available inventory.
        
        Args:
            inventory: List of available fridge items
            days: Number of days to plan for
            dietary_preferences: List of dietary restrictions/preferences
        
        Returns:
            Dictionary containing meal plan and shopping list
        """
        if not self.api_key:
            return self._generate_mock_meal_plan(inventory, days)
        
        try:
            # Create inventory string for GPT prompt
            inventory_str = "\n".join([
                f"- {item.name}: {item.quantity} {item.unit} (expires: {item.expiry_date})"
                for item in inventory
            ])
            
            dietary_str = ""
            if dietary_preferences:
                dietary_str = f"\nDietary preferences/restrictions: {', '.join(dietary_preferences)}"
            
            prompt = f"""
            Create a {days}-day meal plan using the following fridge inventory as much as possible:
            
            {inventory_str}
            {dietary_str}
            
            Please provide:
            1. A day-by-day meal plan (breakfast, lunch, dinner)
            2. A grocery shopping list for missing ingredients
            3. Prioritize using items that expire soon
            
            Format as JSON with structure:
            {{
                "meal_plan": {{
                    "day_1": {{"breakfast": "...", "lunch": "...", "dinner": "..."}},
                    ...
                }},
                "grocery_list": [
                    {{"name": "item", "quantity": 1, "unit": "piece", "category": "vegetable", "reason": "for recipe X"}}
                ],
                "notes": ["helpful cooking tips or substitutions"]
            }}
            """
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2000,
                temperature=0.7
            )
            
            # Parse the JSON response
            content = response.choices[0].message.content
            meal_plan = json.loads(content)
            
            logger.info(f"Generated {days}-day meal plan with {len(meal_plan.get('grocery_list', []))} shopping items")
            return meal_plan
            
        except Exception as e:
            logger.error(f"Error generating meal plan: {e}")
            return self._generate_mock_meal_plan(inventory, days)
    
    def _generate_mock_meal_plan(self, inventory: List[FridgeItem], days: int) -> Dict[str, Any]:
        """Generate a mock meal plan when API is not available."""
        mock_plan = {
            "meal_plan": {},
            "grocery_list": [
                GroceryItem("Spinach", 1, "bag", "vegetable", 2.99).__dict__,
                GroceryItem("Salmon", 1, "lb", "seafood", 12.99).__dict__,
                GroceryItem("Pasta", 1, "box", "grain", 1.49).__dict__,
                GroceryItem("Olive Oil", 1, "bottle", "condiment", 4.99).__dict__
            ],
            "notes": [
                "This is a mock meal plan. Connect OpenAI API for personalized planning.",
                "Use ingredients expiring soon first.",
                "Consider batch cooking for efficiency."
            ]
        }
        
        # Generate simple meal plan
        for day in range(1, days + 1):
            mock_plan["meal_plan"][f"day_{day}"] = {
                "breakfast": "Scrambled eggs with cheese",
                "lunch": "Chicken and vegetable stir-fry",
                "dinner": "Grilled salmon with rice and broccoli"
            }
        
        return mock_plan


class GroceryManager:
    """
    Manages grocery shopping and ordering through simulated APIs.
    
    Simulates integration with services like Instacart for automated ordering.
    """
    
    def __init__(self, store_api_key: Optional[str] = None):
        self.store_api_key = store_api_key
        self.base_url = "https://api.instacart.com/v1"  # Mock URL
        
        # Mock store inventory with prices
        self.store_catalog = {
            "milk": {"price": 3.99, "unit": "gallon", "available": True, "store_id": "MILK001"},
            "eggs": {"price": 2.49, "unit": "dozen", "available": True, "store_id": "EGG001"},
            "chicken breast": {"price": 8.99, "unit": "lb", "available": True, "store_id": "CHKN001"},
            "broccoli": {"price": 1.99, "unit": "head", "available": True, "store_id": "BROC001"},
            "spinach": {"price": 2.99, "unit": "bag", "available": True, "store_id": "SPIN001"},
            "salmon": {"price": 12.99, "unit": "lb", "available": True, "store_id": "SALM001"},
            "pasta": {"price": 1.49, "unit": "box", "available": True, "store_id": "PAST001"},
            "olive oil": {"price": 4.99, "unit": "bottle", "available": True, "store_id": "OIL001"}
        }
    
    def search_products(self, grocery_list: List[GroceryItem]) -> List[Dict[str, Any]]:
        """
        Search for products in store catalog and get pricing.
        
        Args:
            grocery_list: List of items to search for
        
        Returns:
            List of found products with pricing and availability
        """
        found_products = []
        
        for item in grocery_list:
            # Simulate API search
            item_key = item.name.lower()
            if item_key in self.store_catalog:
                store_item = self.store_catalog[item_key]
                found_products.append({
                    "requested_item": item.__dict__,
                    "store_item": {
                        "name": item.name,
                        "store_id": store_item["store_id"],
                        "price": store_item["price"],
                        "unit": store_item["unit"],
                        "available": store_item["available"],
                        "total_cost": store_item["price"] * item.quantity
                    }
                })
            else:
                # Item not found in catalog
                found_products.append({
                    "requested_item": item.__dict__,
                    "store_item": None,
                    "error": "Product not found in store catalog"
                })
        
        logger.info(f"Found {len([p for p in found_products if p.get('store_item')])} out of {len(grocery_list)} items")
        return found_products
    
    def create_order(self, products: List[Dict[str, Any]], delivery_time: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a grocery order (simulated).
        
        Args:
            products: List of products to order
            delivery_time: Preferred delivery time
        
        Returns:
            Order confirmation details
        """
        available_products = [p for p in products if p.get('store_item') and p['store_item']['available']]
        
        if not available_products:
            return {"error": "No available products to order"}
        
        # Calculate total cost
        total_cost = sum(p['store_item']['total_cost'] for p in available_products)
        delivery_fee = 5.99
        tip = total_cost * 0.15  # 15% tip
        total_with_fees = total_cost + delivery_fee + tip
        
        # Generate mock order
        order = {
            "order_id": f"ORD_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "status": "confirmed",
            "items": available_products,
            "subtotal": round(total_cost, 2),
            "delivery_fee": delivery_fee,
            "tip": round(tip, 2),
            "total": round(total_with_fees, 2),
            "estimated_delivery": delivery_time or (datetime.now() + timedelta(hours=2)).strftime("%Y-%m-%d %H:%M"),
            "store": "Mock Grocery Store",
            "created_at": datetime.now().isoformat()
        }
        
        logger.info(f"Created order {order['order_id']} for ${order['total']:.2f}")
        return order
    
    def get_order_status(self, order_id: str) -> Dict[str, Any]:
        """Get order status (simulated)."""
        return {
            "order_id": order_id,
            "status": "in_progress",
            "estimated_delivery": (datetime.now() + timedelta(hours=1)).strftime("%Y-%m-%d %H:%M"),
            "driver": "Mock Driver",
            "tracking_url": f"https://mockstore.com/track/{order_id}"
        }


class CalendarManager:
    """
    Manages calendar integration for scheduling deliveries and meal reminders.
    
    Simulates Google Calendar API integration.
    """
    
    def __init__(self, calendar_credentials: Optional[str] = None):
        self.credentials = calendar_credentials
        self.events = []  # Mock event storage
    
    def schedule_delivery_reminder(self, order: Dict[str, Any]) -> Dict[str, Any]:
        """
        Schedule a calendar reminder for grocery delivery.
        
        Args:
            order: Order details from grocery manager
        
        Returns:
            Calendar event details
        """
        delivery_time = datetime.fromisoformat(order['estimated_delivery'].replace('Z', '+00:00'))
        reminder_time = delivery_time - timedelta(minutes=30)
        
        event = {
            "event_id": f"DELIVERY_{order['order_id']}",
            "title": f"Grocery Delivery Arriving - Order {order['order_id']}",
            "description": f"Grocery delivery from {order['store']}\nTotal: ${order['total']:.2f}\nItems: {len(order['items'])} items",
            "start_time": delivery_time.isoformat(),
            "reminder_time": reminder_time.isoformat(),
            "type": "delivery_reminder",
            "status": "scheduled"
        }
        
        self.events.append(event)
        logger.info(f"Scheduled delivery reminder for {delivery_time.strftime('%Y-%m-%d %H:%M')}")
        return event
    
    def schedule_meal_prep_reminders(self, meal_plan: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Schedule meal preparation reminders based on meal plan.
        
        Args:
            meal_plan: Generated meal plan
        
        Returns:
            List of scheduled events
        """
        events = []
        base_date = datetime.now().replace(hour=18, minute=0, second=0, microsecond=0)  # 6 PM start
        
        for day_key, meals in meal_plan.get('meal_plan', {}).items():
            day_num = int(day_key.split('_')[1]) - 1
            event_date = base_date + timedelta(days=day_num)
            
            event = {
                "event_id": f"MEAL_PREP_{day_key}",
                "title": f"Meal Prep - Day {day_num + 1}",
                "description": f"Tonight's dinner: {meals.get('dinner', 'TBD')}\nTomorrow's breakfast: {meals.get('breakfast', 'TBD')}",
                "start_time": event_date.isoformat(),
                "duration_minutes": 60,
                "type": "meal_prep",
                "status": "scheduled"
            }
            
            events.append(event)
            self.events.append(event)
        
        logger.info(f"Scheduled {len(events)} meal prep reminders")
        return events
    
    def get_upcoming_events(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get upcoming events for the next specified days."""
        cutoff_date = datetime.now() + timedelta(days=days)
        upcoming = [
            event for event in self.events
            if datetime.fromisoformat(event['start_time']) <= cutoff_date
        ]
        return sorted(upcoming, key=lambda x: x['start_time'])


class GroceryConcierge:
    """
    Main orchestrator class for the smart fridge system.
    
    Coordinates all components to provide a comprehensive smart fridge experience.
    """
    
    def __init__(self, 
                 openai_api_key: Optional[str] = None,
                 store_api_key: Optional[str] = None,
                 calendar_credentials: Optional[str] = None):
        """
        Initialize the GroceryConcierge system.
        
        Args:
            openai_api_key: OpenAI API key for meal planning
            store_api_key: Store API key for grocery ordering
            calendar_credentials: Calendar API credentials
        """
        self.fridge = FridgeInventory()
        self.meal_planner = MealPlanner(openai_api_key)
        self.grocery_manager = GroceryManager(store_api_key)
        self.calendar = CalendarManager(calendar_credentials)
        
        logger.info("GroceryConcierge system initialized")
    
    def daily_check(self) -> Dict[str, Any]:
        """
        Perform daily inventory check and recommendations.
        
        Returns:
            Dictionary with daily insights and recommendations
        """
        logger.info("Performing daily fridge check...")
        
        # Check expiring items
        expiring_items = self.fridge.get_expiring_soon(days=3)
        low_stock_items = self.fridge.get_low_stock(threshold=2)
        
        insights = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "expiring_soon": [item.__dict__ for item in expiring_items],
            "low_stock": [item.__dict__ for item in low_stock_items],
            "total_items": len(self.fridge.items),
            "recommendations": []
        }
        
        # Generate recommendations
        if expiring_items:
            insights["recommendations"].append(f"Use {len(expiring_items)} expiring items in today's meals")
        
        if low_stock_items:
            insights["recommendations"].append(f"Consider restocking {len(low_stock_items)} low-stock items")
        
        if not expiring_items and not low_stock_items:
            insights["recommendations"].append("Your fridge is well-stocked and organized!")
        
        logger.info(f"Daily check complete: {len(expiring_items)} expiring, {len(low_stock_items)} low stock")
        return insights
    
    def plan_and_order(self, 
                      days: int = 7, 
                      dietary_preferences: Optional[List[str]] = None,
                      auto_order: bool = False) -> Dict[str, Any]:
        """
        Complete meal planning and grocery ordering workflow.
        
        Args:
            days: Number of days to plan for
            dietary_preferences: Dietary restrictions/preferences
            auto_order: Whether to automatically place grocery order
        
        Returns:
            Complete workflow results
        """
        logger.info(f"Starting {days}-day meal planning and ordering workflow...")
        
        # Step 1: Generate meal plan
        meal_plan = self.meal_planner.generate_meal_plan(
            self.fridge.items, 
            days=days, 
            dietary_preferences=dietary_preferences
        )
        
        # Step 2: Process grocery list
        grocery_items = [
            GroceryItem(**item) for item in meal_plan.get('grocery_list', [])
        ]
        
        # Step 3: Search products and get pricing
        products = self.grocery_manager.search_products(grocery_items)
        
        workflow_result = {
            "meal_plan": meal_plan,
            "grocery_search_results": products,
            "total_estimated_cost": 0,
            "order": None,
            "calendar_events": []
        }
        
        # Calculate estimated cost
        available_products = [p for p in products if p.get('store_item')]
        if available_products:
            workflow_result["total_estimated_cost"] = sum(
                p['store_item']['total_cost'] for p in available_products
            )
        
        # Step 4: Auto-order if requested
        if auto_order and available_products:
            preferred_delivery = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d 16:00")
            order = self.grocery_manager.create_order(available_products, preferred_delivery)
            workflow_result["order"] = order
            
            # Step 5: Schedule calendar events
            if order and "error" not in order:
                delivery_event = self.calendar.schedule_delivery_reminder(order)
                meal_events = self.calendar.schedule_meal_prep_reminders(meal_plan)
                workflow_result["calendar_events"] = [delivery_event] + meal_events
        
        logger.info("Meal planning and ordering workflow completed")
        return workflow_result
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status."""
        return {
            "fridge_status": {
                "total_items": len(self.fridge.items),
                "categories": list(self.fridge.get_inventory_summary().keys()),
                "expiring_soon": len(self.fridge.get_expiring_soon()),
                "low_stock": len(self.fridge.get_low_stock())
            },
            "upcoming_events": len(self.calendar.get_upcoming_events()),
            "system_time": datetime.now().isoformat(),
            "components": {
                "fridge": "operational",
                "meal_planner": "operational" if self.meal_planner.api_key else "mock_mode",
                "grocery_manager": "operational",
                "calendar": "operational"
            }
        }


def main():
    """Main application entry point with example usage."""
    print("🥬 Welcome to GroceryConcierge - Your Smart Fridge Assistant! 🥬\n")
    
    # Initialize the system
    # Note: Add your actual API keys as environment variables
    concierge = GroceryConcierge(
        openai_api_key=os.getenv('OPENAI_API_KEY'),
        store_api_key=os.getenv('STORE_API_KEY'),
        calendar_credentials=os.getenv('CALENDAR_CREDENTIALS')
    )
    
    # Perform daily check
    print("📊 Daily Fridge Check:")
    print("=" * 50)
    daily_insights = concierge.daily_check()
    
    print(f"Date: {daily_insights['date']}")
    print(f"Total items in fridge: {daily_insights['total_items']}")
    
    if daily_insights['expiring_soon']:
        print(f"\n⚠️  Expiring soon ({len(daily_insights['expiring_soon'])} items):")
        for item in daily_insights['expiring_soon']:
            print(f"  - {item['name']}: {item['quantity']} {item['unit']} (expires {item['expiry_date']})")
    
    if daily_insights['low_stock']:
        print(f"\n📉 Low stock ({len(daily_insights['low_stock'])} items):")
        for item in daily_insights['low_stock']:
            print(f"  - {item['name']}: {item['quantity']} {item['unit']}")
    
    print(f"\n💡 Recommendations:")
    for rec in daily_insights['recommendations']:
        print(f"  - {rec}")
    
    # Generate meal plan and grocery list
    print("\n\n🍽️  Generating 7-Day Meal Plan:")
    print("=" * 50)
    
    workflow_result = concierge.plan_and_order(
        days=7, 
        dietary_preferences=['vegetarian'],  # Example preference
        auto_order=False  # Set to True to simulate auto-ordering
    )
    
    # Display meal plan
    meal_plan = workflow_result['meal_plan']
    for day, meals in meal_plan.get('meal_plan', {}).items():
        day_num = day.split('_')[1]
        print(f"\nDay {day_num}:")
        print(f"  🌅 Breakfast: {meals.get('breakfast', 'TBD')}")
        print(f"  🌞 Lunch: {meals.get('lunch', 'TBD')}")
        print(f"  🌙 Dinner: {meals.get('dinner', 'TBD')}")
    
    # Display grocery list
    print(f"\n\n🛒 Grocery Shopping List:")
    print("=" * 50)
    grocery_results = workflow_result['grocery_search_results']
    total_cost = 0
    
    for result in grocery_results:
        item = result['requested_item']
        store_item = result.get('store_item')
        
        if store_item:
            cost = store_item['total_cost']
            total_cost += cost
            print(f"✅ {item['name']}: {item['quantity']} {item['unit']} - ${cost:.2f}")
        else:
            print(f"❌ {item['name']}: Not available")
    
    print(f"\nEstimated total: ${total_cost:.2f}")
    
    # Display system status
    print(f"\n\n🔧 System Status:")
    print("=" * 50)
    status = concierge.get_system_status()
    
    for component, state in status['components'].items():
        status_emoji = "✅" if state == "operational" else "⚠️"
        print(f"{status_emoji} {component.title()}: {state}")
    
    print(f"\nUpcoming events: {status['upcoming_events']}")
    print(f"System time: {status['system_time']}")
    
    print("\n🎉 GroceryConcierge workflow complete!")
    print("💡 Tip: Set up API keys for full functionality!")


if __name__ == "__main__":
    main()
