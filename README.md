# 🥬 GroceryConcierge - Smart Fridge Management System

A comprehensive Python application that simulates a smart fridge system, managing inventory, planning meals using AI, and automating grocery ordering with calendar integration.

## 🌟 Features

- **Smart Inventory Management**: Track fridge contents with expiration dates and quantities
- **AI-Powered Meal Planning**: Generate personalized meal plans using OpenAI GPT
- **Automated Grocery Ordering**: Simulate ordering through grocery delivery APIs (Instacart-style)
- **Calendar Integration**: Schedule delivery reminders and meal prep notifications
- **Expiration Alerts**: Get notified about items expiring soon
- **Low Stock Monitoring**: Track items running low and suggest restocking
- **Mock API Support**: Works with or without real API keys for testing

## 🏗️ Project Structure

```
GroceryConcierge/
├── main.py                 # Main application logic
├── requirements.txt        # Python dependencies
├── README.md              # This documentation
├── fridge_inventory.json  # Auto-generated inventory file
└── .env                   # Environment variables (create manually)
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- pip package manager
- Optional: OpenAI API key for AI meal planning

### Installation

1. **Clone or download the project files**
   ```bash
   mkdir GroceryConcierge
   cd GroceryConcierge
   # Copy main.py, requirements.txt, and README.md to this directory
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables (optional)**
   Create a `.env` file for API keys:
   ```bash
   # .env file
   OPENAI_API_KEY=your_openai_api_key_here
   STORE_API_KEY=your_store_api_key_here
   CALENDAR_CREDENTIALS=your_calendar_credentials_here
   ```

4. **Run the application**
   ```bash
   python main.py
   ```

## 📖 Usage Guide

### Basic Operation

The application automatically creates a default inventory on first run and performs the following workflow:

1. **Daily Fridge Check**: Analyzes current inventory for expiring items and low stock
2. **Meal Planning**: Generates a 7-day meal plan using available ingredients
3. **Grocery List Creation**: Identifies missing ingredients needed for meal plan
4. **Price Lookup**: Searches mock store catalog for pricing and availability
5. **Order Simulation**: Creates mock grocery orders with delivery scheduling
6. **Calendar Events**: Schedules reminders for deliveries and meal prep

### Working with Inventory

The system uses a `fridge_inventory.json` file to store current inventory:

```json
[
  {
    "name": "Milk",
    "quantity": 1,
    "unit": "gallon",
    "expiry_date": "2025-07-25",
    "category": "dairy"
  }
]
```

### API Integration Modes

#### Mock Mode (Default)
- Works without API keys
- Uses hardcoded responses for demonstration
- Perfect for testing and development

#### Full API Mode
- Requires OpenAI API key for meal planning
- Connects to real services for enhanced functionality
- Set environment variables to enable

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | OpenAI API key for GPT meal planning | No (uses mock data) |
| `STORE_API_KEY` | Grocery store API key | No (uses mock catalog) |
| `CALENDAR_CREDENTIALS` | Calendar API credentials | No (uses mock events) |

### Customization Options

#### Dietary Preferences
Modify the `plan_and_order()` call in `main()`:
```python
workflow_result = concierge.plan_and_order(
    days=7, 
    dietary_preferences=['vegetarian', 'gluten-free'],
    auto_order=False
)
```

#### Inventory Management
```python
# Add new items
concierge.fridge.add_item(FridgeItem(
    name="Avocado",
    quantity=3,
    unit="pieces",
    expiry_date="2025-07-22",
    category="fruit"
))

# Remove items
concierge.fridge.remove_item("Milk", quantity=1)
```

#### Custom Thresholds
```python
# Check items expiring in 5 days
expiring = concierge.fridge.get_expiring_soon(days=5)

# Get items with quantity <= 1
low_stock = concierge.fridge.get_low_stock(threshold=1)
```

## 🏭 Architecture

### Core Components

1. **FridgeInventory**: Manages inventory storage and retrieval
2. **MealPlanner**: AI-powered meal plan generation
3. **GroceryManager**: Product search and order management
4. **CalendarManager**: Event scheduling and reminders
5. **GroceryConcierge**: Main orchestrator class

### Data Models

```python
@dataclass
class FridgeItem:
    name: str
    quantity: int
    unit: str
    expiry_date: str
    category: str = "misc"

@dataclass
class GroceryItem:
    name: str
    quantity: int
    unit: str
    category: str
    estimated_price: float = 0.0
```

### Workflow Pipeline

```
Inventory Check → Meal Planning → Grocery Search → Order Creation → Calendar Scheduling
```

## 🧪 Example Outputs

### Daily Check Results
```
📊 Daily Fridge Check:
Date: 2025-07-18
Total items in fridge: 10

⚠️  Expiring soon (2 items):
  - Bread: 1 loaf (expires 2025-07-20)
  - Broccoli: 1 head (expires 2025-07-21)

📉 Low stock (1 items):
  - Eggs: 2 pieces

💡 Recommendations:
  - Use 2 expiring items in today's meals
  - Consider restocking 1 low-stock items
```

### Meal Plan Output
```
🍽️  Generating 7-Day Meal Plan:

Day 1:
  🌅 Breakfast: Scrambled eggs with cheese
  🌞 Lunch: Chicken and vegetable stir-fry
  🌙 Dinner: Grilled salmon with rice and broccoli

Day 2:
  🌅 Breakfast: Toast with eggs
  🌞 Lunch: Leftover chicken stir-fry
  🌙 Dinner: Pasta with tomato sauce
```

### Grocery List
```
🛒 Grocery Shopping List:
✅ Spinach: 1 bag - $2.99
✅ Salmon: 1 lb - $12.99
✅ Pasta: 1 box - $1.49
❌ Specialty Item: Not available

Estimated total: $17.47
```

## 🔌 API Integrations

### OpenAI Integration
- Uses GPT-3.5-turbo for meal planning
- Generates context-aware meal suggestions
- Considers dietary restrictions and preferences
- Optimizes ingredient usage

### Mock Grocery API
- Simulates Instacart-style ordering
- Includes pricing and availability checking
- Handles order creation and tracking
- Calculates delivery fees and tips

### Mock Calendar API
- Simulates Google Calendar integration
- Schedules delivery reminders
- Creates meal prep notifications
- Manages event tracking

## 🛠️ Development

### Adding New Features

1. **Custom Stores**: Extend `GroceryManager.store_catalog`
2. **New Meal Types**: Modify meal plan structure in `MealPlanner`
3. **Additional APIs**: Implement new manager classes
4. **Enhanced UI**: Add web interface using Flask/FastAPI

### Testing

Run the application with different configurations:

```python
# Test with mock data
concierge = GroceryConcierge()

# Test with partial API integration
concierge = GroceryConcierge(openai_api_key="your_key")

# Test auto-ordering
workflow_result = concierge.plan_and_order(auto_order=True)
```

### Extending Functionality

```python
# Add nutrition tracking
class NutritionTracker:
    def analyze_meal_plan(self, meal_plan):
        # Calculate nutritional information
        pass

# Add budget management
class BudgetManager:
    def set_weekly_budget(self, amount):
        # Track spending against budget
        pass
```

## 📝 Logging

The application includes comprehensive logging:

- **INFO**: Normal operations and workflow progress
- **WARNING**: Non-critical issues (missing items, API fallbacks)
- **ERROR**: Critical errors and exceptions

View logs in console output or configure file logging:

```python
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('grocery_concierge.log'),
        logging.StreamHandler()
    ]
)
```

## 🚨 Troubleshooting

### Common Issues

**Issue**: `ModuleNotFoundError` for dependencies
**Solution**: Run `pip install -r requirements.txt`

**Issue**: OpenAI API errors
**Solution**: Check API key and usage limits, falls back to mock mode

**Issue**: JSON file corruption
**Solution**: Delete `fridge_inventory.json` to regenerate default inventory

**Issue**: Permission errors on file operations
**Solution**: Ensure write permissions in application directory

### Debug Mode

Enable detailed logging for troubleshooting:

```python
import logging
logging.getLogger().setLevel(logging.DEBUG)
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

### Code Style
- Follow PEP 8 guidelines
- Use type hints
- Add comprehensive docstrings
- Include error handling

## 📄 License

This project is licensed under the MIT License. See LICENSE file for details.

## 🙏 Acknowledgments

- OpenAI for GPT integration
- Mock APIs inspired by Instacart and Google Calendar
- Python community for excellent libraries

## 📞 Support

For questions, issues, or feature requests:
- Create an issue in the repository
- Check troubleshooting section above
- Review example outputs for expected behavior

---

**Happy cooking with GroceryConcierge! 🍳✨**
