# Penny Power Plan - Changelog

## Version 0.0.1 (MVP) - Initial Release

### Features Implemented:
- **Income Management**
  - Add income with source, amount, frequency
  - Mark incomes as targets
  - Track actual vs target income

- **Expense Tracking**
  - Categorize expenses as business/personal
  - Add subcategories
  - Mark expenses as recurring

- **Savings Goals**
  - Create savings goals with targets
  - Categorize goals (short-term, emergency, etc.)
  - Track contributions
  - Set priorities and deadlines

- **Data Management**
  - JSON storage
  - Import/export to JSON and CSV
  - Interactive mode for all functions

- **Reporting**
  - Financial summaries
  - Progress tracking
  - Target vs actual comparisons

### Usage Examples:
1. Add income: `penny income add 1500 "Salary" monthly --target`
2. Add expense: `penny expense add 200 personal food --recurring`
3. Add savings goal: `penny savings add "New Laptop" 1200 electronics --deadline 2023-12-31`
4. Interactive mode: `penny --interactive`
