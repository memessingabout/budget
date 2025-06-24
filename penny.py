#!/usr/bin/env python3
import argparse
from datetime import datetime, date
import json
from pathlib import Path
from typing import Dict, List, Optional, Union
import sys
from enum import Enum
import csv

class Frequency(Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"
    ONE_TIME = "one-time"

class ExpenseCategory(Enum):
    BUSINESS = "business"
    PERSONAL = "personal"

class SavingsCategory(Enum):
    SHORT_TERM = "short-term"
    EMERGENCY = "emergency"
    LONG_TERM = "long-term"
    ELECTRONICS = "electronics"
    OTHER = "other"

class Transaction:
    def __init__(self, amount: float, description: str, date: Optional[date] = None):
        if amount <= 0:
            raise ValueError("Amount must be positive")
        self.amount = amount
        self.description = description
        self.date = date or date.today()
        self.id = str(hash(f"{self.date}-{self.description}-{self.amount}"))

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "amount": self.amount,
            "description": self.description,
            "date": self.date.isoformat()
        }

class Income(Transaction):
    def __init__(self, amount: float, source: str, frequency: Frequency, 
                 description: str = "", is_target: bool = False):
        super().__init__(amount, description or f"Income from {source}")
        self.source = source
        self.frequency = frequency.value
        self.is_target = is_target

    def to_dict(self) -> Dict:
        data = super().to_dict()
        data.update({
            "type": "income",
            "source": self.source,
            "frequency": self.frequency,
            "is_target": self.is_target
        })
        return data

class Expense(Transaction):
    def __init__(self, amount: float, category: ExpenseCategory, subcategory: str,
                 description: str = "", is_recurring: bool = False):
        super().__init__(amount, description or f"{category.value} expense: {subcategory}")
        self.category = category.value
        self.subcategory = subcategory
        self.is_recurring = is_recurring

    def to_dict(self) -> Dict:
        data = super().to_dict()
        data.update({
            "type": "expense",
            "category": self.category,
            "subcategory": self.subcategory,
            "is_recurring": self.is_recurring
        })
        return data

class SavingsGoal:
    def __init__(self, name: str, target_amount: float, category: SavingsCategory,
                 deadline: Optional[date] = None, priority: int = 3):
        if target_amount <= 0:
            raise ValueError("Target amount must be positive")
        if priority < 1 or priority > 5:
            raise ValueError("Priority must be between 1 and 5")
        
        self.name = name
        self.target_amount = target_amount
        self.current_amount = 0.0
        self.category = category.value
        self.deadline = deadline
        self.priority = priority
        self.id = str(hash(f"{name}-{target_amount}-{category}"))
        self.contributions: List[Dict] = []

    def add_contribution(self, amount: float, date: Optional[date] = None):
        if amount <= 0:
            raise ValueError("Contribution amount must be positive")
        self.current_amount += amount
        self.contributions.append({
            "amount": amount,
            "date": (date or date.today()).isoformat()
        })

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "target_amount": self.target_amount,
            "current_amount": self.current_amount,
            "category": self.category,
            "deadline": self.deadline.isoformat() if self.deadline else None,
            "priority": self.priority,
            "contributions": self.contributions
        }

class FinanceManager:
    def __init__(self, data_file: Path = Path("finance_data.json")):
        self.data_file = data_file
        self.data = {
            "incomes": [],
            "expenses": [],
            "savings_goals": [],
            "version": "0.0.1"
        }
        self.load_data()
    
    def load_data(self):
        if self.data_file.exists():
            try:
                with open(self.data_file, "r") as f:
                    self.data = json.load(f)
            except json.JSONDecodeError:
                print("Warning: Data file corrupted. Starting with fresh data.")
    
    def save_data(self):
        with open(self.data_file, "w") as f:
            json.dump(self.data, f, indent=2, default=self._serializer)
    
    def _serializer(self, obj):
        if isinstance(obj, (date, datetime)):
            return obj.isoformat()
        raise TypeError(f"Type {type(obj)} not serializable")
    
    def add_income(self, income: Income):
        self.data["incomes"].append(income.to_dict())
        self.save_data()
    
    def add_expense(self, expense: Expense):
        self.data["expenses"].append(expense.to_dict())
        self.save_data()
    
    def add_savings_goal(self, goal: SavingsGoal):
        self.data["savings_goals"].append(goal.to_dict())
        self.save_data()
    
    def contribute_to_goal(self, goal_id: str, amount: float):
        for goal in self.data["savings_goals"]:
            if goal["id"] == goal_id:
                goal["current_amount"] += amount
                goal["contributions"].append({
                    "amount": amount,
                    "date": date.today().isoformat()
                })
                self.save_data()
                return True
        return False
    
    def get_summary(self) -> Dict:
        total_income = sum(i["amount"] for i in self.data["incomes"] if not i["is_target"])
        total_expenses = sum(e["amount"] for e in self.data["expenses"])
        total_savings = sum(g["current_amount"] for g in self.data["savings_goals"])
        
        income_targets = [i for i in self.data["incomes"] if i["is_target"]]
        expense_targets = [e for e in self.data["expenses"] if e.get("is_recurring", False)]
        
        return {
            "net_balance": total_income - total_expenses,
            "total_income": total_income,
            "total_expenses": total_expenses,
            "total_savings": total_savings,
            "income_targets": income_targets,
            "expense_targets": expense_targets,
            "savings_goals": self.data["savings_goals"]
        }
    
    def export_data(self, format: str = "json", file_path: Optional[Path] = None):
        if format == "json":
            file_path = file_path or Path("penny_export.json")
            with open(file_path, "w") as f:
                json.dump(self.data, f, indent=2)
        elif format == "csv":
            file_path = file_path or Path("penny_export.csv")
            self._export_to_csv(file_path)
        else:
            raise ValueError("Unsupported export format")
        return file_path
    
    def _export_to_csv(self, file_path: Path):
        with open(file_path, "w", newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["Type", "Amount", "Description", "Date", "Category", "Details"])
            
            for income in self.data["incomes"]:
                writer.writerow([
                    "Income",
                    income["amount"],
                    income["description"],
                    income["date"],
                    income["source"],
                    f"Frequency: {income['frequency']}, Target: {income['is_target']}"
                ])
            
            for expense in self.data["expenses"]:
                writer.writerow([
                    "Expense",
                    expense["amount"],
                    expense["description"],
                    expense["date"],
                    f"{expense['category']}/{expense['subcategory']}",
                    f"Recurring: {expense.get('is_recurring', False)}"
                ])
            
            for goal in self.data["savings_goals"]:
                writer.writerow([
                    "Savings Goal",
                    f"{goal['current_amount']}/{goal['target_amount']}",
                    goal["name"],
                    goal.get("deadline", ""),
                    goal["category"],
                    f"Priority: {goal['priority']}"
                ])
    
    def import_data(self, file_path: Path):
        if file_path.suffix == ".json":
            with open(file_path, "r") as f:
                imported_data = json.load(f)
        elif file_path.suffix == ".csv":
            imported_data = self._import_from_csv(file_path)
        else:
            raise ValueError("Unsupported import format")
        
        # Basic validation
        required_keys = {"incomes", "expenses", "savings_goals"}
        if not all(key in imported_data for key in required_keys):
            raise ValueError("Invalid data format")
        
        self.data = imported_data
        self.save_data()
    
    def _import_from_csv(self, file_path: Path) -> Dict:
        # Simplified CSV import for MVP
        data = {"incomes": [], "expenses": [], "savings_goals": []}
        
        with open(file_path, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row["Type"] == "Income":
                    data["incomes"].append({
                        "amount": float(row["Amount"]),
                        "description": row["Description"],
                        "date": row["Date"],
                        "source": row["Category"],
                        "frequency": row["Details"].split(",")[0].split(":")[1].strip(),
                        "is_target": "True" in row["Details"]
                    })
                elif row["Type"] == "Expense":
                    category, subcategory = row["Category"].split("/")
                    data["expenses"].append({
                        "amount": float(row["Amount"]),
                        "description": row["Description"],
                        "date": row["Date"],
                        "category": category,
                        "subcategory": subcategory,
                        "is_recurring": "True" in row["Details"]
                    })
                elif row["Type"] == "Savings Goal":
                    current, target = map(float, row["Amount"].split("/"))
                    data["savings_goals"].append({
                        "name": row["Description"],
                        "target_amount": target,
                        "current_amount": current,
                        "category": row["Category"],
                        "deadline": row["Date"] if row["Date"] else None,
                        "priority": int(row["Details"].split(":")[1].strip())
                    })
        
        return data

def interactive_mode(manager: FinanceManager):
    print("\nWelcome to Penny Power Plan Interactive Mode!")
    print("Type 'help' for commands or 'exit' to quit\n")
    
    while True:
        try:
            cmd = input("penny> ").strip().lower()
            
            if cmd in ("exit", "quit"):
                break
            elif cmd == "help":
                print("\nAvailable commands:")
                print("  income - Add income")
                print("  expense - Add expense")
                print("  savings - Manage savings goals")
                print("  summary - View financial summary")
                print("  export - Export data")
                print("  import - Import data")
                print("  exit - Quit interactive mode\n")
            elif cmd == "income":
                add_income_interactive(manager)
            elif cmd == "expense":
                add_expense_interactive(manager)
            elif cmd == "savings":
                manage_savings_interactive(manager)
            elif cmd == "summary":
                show_summary(manager)
            elif cmd == "export":
                export_interactive(manager)
            elif cmd == "import":
                import_interactive(manager)
            else:
                print("Unknown command. Type 'help' for available commands.")
        except Exception as e:
            print(f"Error: {e}")

def add_income_interactive(manager: FinanceManager):
    print("\nAdd New Income")
    amount = float(input("Amount: "))
    source = input("Source: ")
    print("Frequency options: daily, weekly, monthly, yearly, one-time")
    frequency = Frequency(input("Frequency: "))
    description = input("Description (optional): ")
    is_target = input("Is this a target? (y/n): ").lower() == "y"
    
    income = Income(amount, source, frequency, description, is_target)
    manager.add_income(income)
    print(f"Added income: {income.description}")

def add_expense_interactive(manager: FinanceManager):
    print("\nAdd New Expense")
    amount = float(input("Amount: "))
    print("Category options: business, personal")
    category = ExpenseCategory(input("Category: "))
    subcategory = input("Subcategory: ")
    description = input("Description (optional): ")
    is_recurring = input("Is this recurring? (y/n): ").lower() == "y"
    
    expense = Expense(amount, category, subcategory, description, is_recurring)
    manager.add_expense(expense)
    print(f"Added expense: {expense.description}")

def manage_savings_interactive(manager: FinanceManager):
    print("\nSavings Management")
    print("1. Add new savings goal")
    print("2. Contribute to existing goal")
    choice = input("Choose option (1-2): ")
    
    if choice == "1":
        name = input("Goal name: ")
        target = float(input("Target amount: "))
        print("Category options: short-term, emergency, long-term, electronics, other")
        category = SavingsCategory(input("Category: "))
        deadline_str = input("Deadline (YYYY-MM-DD, optional): ")
        deadline = datetime.strptime(deadline_str, "%Y-%m-%d").date() if deadline_str else None
        priority = int(input("Priority (1-5): "))
        
        goal = SavingsGoal(name, target, category, deadline, priority)
        manager.add_savings_goal(goal)
        print(f"Added savings goal: {name}")
    elif choice == "2":
        goals = manager.data["savings_goals"]
        if not goals:
            print("No savings goals found")
            return
        
        print("\nExisting Goals:")
        for i, goal in enumerate(goals, 1):
            print(f"{i}. {goal['name']} ({goal['current_amount']}/{goal['target_amount']})")
        
        goal_idx = int(input("Select goal (number): ")) - 1
        amount = float(input("Contribution amount: "))
        
        if manager.contribute_to_goal(goals[goal_idx]["id"], amount):
            print(f"Added {amount} to {goals[goal_idx]['name']}")
        else:
            print("Failed to contribute to goal")

def show_summary(manager: FinanceManager):
    summary = manager.get_summary()
    print("\nFinancial Summary")
    print("=" * 40)
    print(f"Income: ${summary['total_income']:.2f}")
    print(f"Expenses: ${summary['total_expenses']:.2f}")
    print(f"Net Balance: ${summary['net_balance']:.2f}")
    print(f"Total Savings: ${summary['total_savings']:.2f}")
    
    print("\nIncome Targets:")
    for target in summary["income_targets"]:
        print(f"- {target['source']}: ${target['amount']} {target['frequency']}")
    
    print("\nRecurring Expenses:")
    for expense in summary["expense_targets"]:
        print(f"- {expense['category']}/{expense['subcategory']}: ${expense['amount']}")
    
    print("\nSavings Goals Progress:")
    for goal in summary["savings_goals"]:
        progress = (goal["current_amount"] / goal["target_amount"]) * 100
        print(f"- {goal['name']}: {progress:.1f}% (${goal['current_amount']}/${goal['target_amount']})")

def export_interactive(manager: FinanceManager):
    print("\nExport Data")
    print("1. JSON format")
    print("2. CSV format")
    choice = input("Choose format (1-2): ")
    
    format = "json" if choice == "1" else "csv"
    file_path = input(f"File path (default: penny_export.{format}): ") or f"penny_export.{format}"
    
    try:
        exported_path = manager.export_data(format, Path(file_path))
        print(f"Data exported to {exported_path}")
    except Exception as e:
        print(f"Export failed: {e}")

def import_interactive(manager: FinanceManager):
    print("\nImport Data")
    file_path = input("File path to import: ")
    
    if not Path(file_path).exists():
        print("File not found")
        return
    
    try:
        manager.import_data(Path(file_path))
        print("Data imported successfully")
    except Exception as e:
        print(f"Import failed: {e}")

def main():
    parser = argparse.ArgumentParser(prog="penny", description="Penny Power Plan - Personal Finance Manager")
    parser.add_argument("--interactive", "-i", action="store_true", help="Enter interactive mode")
    
    subparsers = parser.add_subparsers(dest="command")
    
    # Income commands
    income_parser = subparsers.add_parser("income", help="Manage income")
    income_subparsers = income_parser.add_subparsers(dest="subcommand")
    
    add_income_parser = income_subparsers.add_parser("add", help="Add income")
    add_income_parser.add_argument("amount", type=float, help="Income amount")
    add_income_parser.add_argument("source", type=str, help="Income source")
    add_income_parser.add_argument("frequency", type=str, choices=[f.value for f in Frequency], 
                                  help="Income frequency")
    add_income_parser.add_argument("--description", type=str, default="", help="Description")
    add_income_parser.add_argument("--target", action="store_true", help="Set as income target")
    
    # Expense commands
    expense_parser = subparsers.add_parser("expense", help="Manage expenses")
    expense_subparsers = expense_parser.add_subparsers(dest="subcommand")
    
    add_expense_parser = expense_subparsers.add_parser("add", help="Add expense")
    add_expense_parser.add_argument("amount", type=float, help="Expense amount")
    add_expense_parser.add_argument("category", type=str, choices=[c.value for c in ExpenseCategory], 
                                   help="Expense category")
    add_expense_parser.add_argument("subcategory", type=str, help="Expense subcategory")
    add_expense_parser.add_argument("--description", type=str, default="", help="Description")
    add_expense_parser.add_argument("--recurring", action="store_true", help="Set as recurring expense")
    
    # Savings commands
    savings_parser = subparsers.add_parser("savings", help="Manage savings goals")
    savings_subparsers = savings_parser.add_subparsers(dest="subcommand")
    
    add_goal_parser = savings_subparsers.add_parser("add", help="Add savings goal")
    add_goal_parser.add_argument("name", type=str, help="Goal name")
    add_goal_parser.add_argument("target", type=float, help="Target amount")
    add_goal_parser.add_argument("category", type=str, choices=[c.value for c in SavingsCategory], 
                                help="Goal category")
    add_goal_parser.add_argument("--deadline", type=str, help="Deadline (YYYY-MM-DD)")
    add_goal_parser.add_argument("--priority", type=int, choices=range(1, 6), default=3, 
                                help="Priority (1-5)")
    
    contribute_parser = savings_subparsers.add_parser("contribute", help="Contribute to goal")
    contribute_parser.add_argument("goal_id", type=str, help="Goal ID")
    contribute_parser.add_argument("amount", type=float, help="Contribution amount")
    
    # Report commands
    report_parser = subparsers.add_parser("report", help="Generate reports")
    report_parser.add_argument("type", type=str, choices=["summary", "detailed"], 
                             help="Report type")
    
    # Import/export commands
    export_parser = subparsers.add_parser("export", help="Export data")
    export_parser.add_argument("format", type=str, choices=["json", "csv"], help="Export format")
    export_parser.add_argument("--file", type=str, help="Output file path")
    
    import_parser = subparsers.add_parser("import", help="Import data")
    import_parser.add_argument("file", type=str, help="File path to import")
    
    args = parser.parse_args()
    manager = FinanceManager()
    
    if args.interactive or not hasattr(args, "command"):
        interactive_mode(manager)
        return
    
    try:
        if args.command == "income" and args.subcommand == "add":
            frequency = Frequency(args.frequency)
            income = Income(
                amount=args.amount,
                source=args.source,
                frequency=frequency,
                description=args.description,
                is_target=args.target
            )
            manager.add_income(income)
            print(f"Income added: {income.description}")
        
        elif args.command == "expense" and args.subcommand == "add":
            category = ExpenseCategory(args.category)
            expense = Expense(
                amount=args.amount,
                category=category,
                subcategory=args.subcategory,
                description=args.description,
                is_recurring=args.recurring
            )
            manager.add_expense(expense)
            print(f"Expense added: {expense.description}")
        
        elif args.command == "savings":
            if args.subcommand == "add":
                category = SavingsCategory(args.category)
                deadline = datetime.strptime(args.deadline, "%Y-%m-%d").date() if args.deadline else None
                goal = SavingsGoal(
                    name=args.name,
                    target_amount=args.target,
                    category=category,
                    deadline=deadline,
                    priority=args.priority
                )
                manager.add_savings_goal(goal)
                print(f"Savings goal added: {goal.name}")
            
            elif args.subcommand == "contribute":
                if manager.contribute_to_goal(args.goal_id, args.amount):
                    print(f"Contributed ${args.amount} to goal {args.goal_id}")
                else:
                    print("Failed to contribute to goal")
        
        elif args.command == "report":
            summary = manager.get_summary()
            if args.type == "summary":
                print("\nFinancial Summary")
                print("=" * 40)
                print(f"Income: ${summary['total_income']:.2f}")
                print(f"Expenses: ${summary['total_expenses']:.2f}")
                print(f"Net Balance: ${summary['net_balance']:.2f}")
                print(f"Total Savings: ${summary['total_savings']:.2f}")
            else:
                print(json.dumps(summary, indent=2))
        
        elif args.command == "export":
            file_path = Path(args.file) if args.file else None
            exported_path = manager.export_data(args.format, file_path)
            print(f"Data exported to {exported_path}")
        
        elif args.command == "import":
            manager.import_data(Path(args.file))
            print("Data imported successfully")
    
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()