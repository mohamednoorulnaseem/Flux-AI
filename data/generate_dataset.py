"""
Flux AI – Dataset Generator
Generates a JSONL dataset of code review instruction-input-output pairs.
Target: 1,000+ samples ready for QLoRA fine-tuning.

Usage:
    python data/generate_dataset.py
    python data/generate_dataset.py --output data/dataset.jsonl --count 1000
"""
import json
import random
import argparse
from pathlib import Path


# ─── Seed Examples ────────────────────────────────────────────────────────────
# Each entry: (code_snippet, review_output)
# These form the base; the generator expands them with variations.

SEED_EXAMPLES = [
    # ── SQL Injection ──────────────────────────────────────────────────────────
    (
        """\
def get_user(username):
    query = "SELECT * FROM users WHERE username = '" + username + "'"
    return db.execute(query)
""",
        """{
  "bugs": "None detected.",
  "improvements": "Use parameterized queries to prevent SQL injection.",
  "performance": "Query lacks indexing hint; ensure username column is indexed.",
  "security": "CRITICAL: SQL injection vulnerability. The username parameter is directly concatenated into the SQL query. An attacker can inject malicious SQL code. Use parameterized queries: db.execute('SELECT * FROM users WHERE username = ?', (username,))",
  "score": 2
}"""
    ),
    # ── Hardcoded password ────────────────────────────────────────────────────
    (
        """\
def connect_db():
    password = "admin123"
    conn = psycopg2.connect(host="localhost", password=password)
    return conn
""",
        """{
  "bugs": "None detected.",
  "improvements": "Load secrets from environment variables or a secrets manager.",
  "performance": "Connection should be pooled rather than opened on every call.",
  "security": "HIGH: Hardcoded credential. 'admin123' is stored in plaintext source code. Use os.environ.get('DB_PASSWORD') or a secrets manager.",
  "score": 3
}"""
    ),
    # ── O(n²) loop ────────────────────────────────────────────────────────────
    (
        """\
def find_duplicates(lst):
    duplicates = []
    for i in range(len(lst)):
        for j in range(i + 1, len(lst)):
            if lst[i] == lst[j] and lst[i] not in duplicates:
                duplicates.append(lst[i])
    return duplicates
""",
        """{
  "bugs": "None detected.",
  "improvements": "Use a set-based approach for O(n) time complexity.",
  "performance": "MEDIUM: O(n²) nested loop with additional O(n) 'not in' check on list, giving O(n³) worst case. Use: seen = set(); return [x for x in lst if lst.count(x) > 1]... or better: from collections import Counter; return [k for k, v in Counter(lst).items() if v > 1]",
  "security": "None detected.",
  "score": 5
}"""
    ),
    # ── Missing error handling ─────────────────────────────────────────────────
    (
        """\
def read_file(path):
    f = open(path)
    content = f.read()
    f.close()
    return content
""",
        """{
  "bugs": "HIGH: File handle is not closed if an exception occurs between open() and close(). Use 'with open(path) as f:' for guaranteed cleanup.",
  "improvements": "Use context manager 'with open(path) as f: return f.read()'. Add error handling for FileNotFoundError and PermissionError.",
  "performance": "For large files, consider reading in chunks.",
  "security": "MEDIUM: No path validation. Ensure 'path' is sanitized to prevent path traversal attacks.",
  "score": 4
}"""
    ),
    # ── Good code ─────────────────────────────────────────────────────────────
    (
        """\
def calculate_average(numbers: list[float]) -> float:
    \"\"\"Calculate the arithmetic mean of a list of numbers.

    Args:
        numbers: A non-empty list of numeric values.

    Returns:
        The arithmetic mean.

    Raises:
        ValueError: If the list is empty.
    \"\"\"
    if not numbers:
        raise ValueError("Cannot calculate average of empty list")
    return sum(numbers) / len(numbers)
""",
        """{
  "bugs": "None detected.",
  "improvements": "Consider adding type validation to handle non-numeric inputs gracefully.",
  "performance": "Efficient O(n) implementation using built-in sum().",
  "security": "None detected.",
  "score": 9
}"""
    ),
    # ── Global mutable state ──────────────────────────────────────────────────
    (
        """\
cache = {}

def expensive_compute(x):
    if x in cache:
        return cache[x]
    result = x * x * x
    cache[x] = result
    return result
""",
        """{
  "bugs": "MEDIUM: Global mutable cache grows unbounded and is not thread-safe. In concurrent environments this can cause race conditions.",
  "improvements": "Use functools.lru_cache for thread-safe, bounded memoization: @functools.lru_cache(maxsize=128)",
  "performance": "Caching is a good optimization. However, unbounded cache can cause memory issues over time.",
  "security": "None detected.",
  "score": 6
}"""
    ),
    # ── Exception swallowing ──────────────────────────────────────────────────
    (
        """\
def safe_divide(a, b):
    try:
        return a / b
    except:
        pass
""",
        """{
  "bugs": "HIGH: Bare 'except:' swallows ALL exceptions including KeyboardInterrupt and SystemExit. Returns None silently on ZeroDivisionError, which can cause subtle bugs downstream.",
  "improvements": "Catch specific exceptions: except ZeroDivisionError: return None. Log the error. Consider raising or returning a sentinel value with documentation.",
  "performance": "None detected.",
  "security": "None detected.",
  "score": 3
}"""
    ),
    # ── Mutable default argument ───────────────────────────────────────────────
    (
        """\
def add_item(item, collection=[]):
    collection.append(item)
    return collection
""",
        """{
  "bugs": "CRITICAL: Mutable default argument. The list [] is created once and shared across all calls. Subsequent calls accumulate items from previous calls. Fix: def add_item(item, collection=None): if collection is None: collection = []",
  "improvements": "Document the function behavior. Use None as default and initialize inside the function.",
  "performance": "None detected.",
  "security": "None detected.",
  "score": 2
}"""
    ),
    # ── No input validation ───────────────────────────────────────────────────
    (
        """\
def process_age(age):
    category = ""
    if age < 18:
        category = "minor"
    elif age < 65:
        category = "adult"
    else:
        category = "senior"
    return category
""",
        """{
  "bugs": "MEDIUM: No input validation. Negative ages or non-integer values will cause incorrect results or errors.",
  "improvements": "Add type hints: def process_age(age: int) -> str. Add validation: if not isinstance(age, int) or age < 0: raise ValueError('Age must be a non-negative integer')",
  "performance": "None detected. Simple conditional is O(1).",
  "security": "None detected.",
  "score": 6
}"""
    ),
    # ── Command injection ──────────────────────────────────────────────────────
    (
        """\
import os

def ping_host(hostname):
    os.system("ping -c 1 " + hostname)
""",
        """{
  "bugs": "None detected.",
  "improvements": "Use subprocess.run() with a list of arguments for proper argument handling.",
  "performance": "None detected.",
  "security": "CRITICAL: Command injection vulnerability. If 'hostname' contains shell metacharacters (e.g., '; rm -rf /'), arbitrary commands can be executed. Use subprocess.run(['ping', '-c', '1', hostname], check=True) and validate hostname with a regex pattern.",
  "score": 1
}"""
    ),
    # ── N+1 query ─────────────────────────────────────────────────────────────
    (
        """\
def get_user_posts(user_ids):
    result = []
    for user_id in user_ids:
        posts = db.query(f"SELECT * FROM posts WHERE user_id = {user_id}")
        result.extend(posts)
    return result
""",
        """{
  "bugs": "None detected.",
  "improvements": "Fetch all posts in a single query using IN clause.",
  "performance": "HIGH: N+1 query pattern. For N users, N separate database queries are made. Use: posts = db.query(f'SELECT * FROM posts WHERE user_id IN ({','.join(map(str, user_ids))})')",
  "security": "CRITICAL: SQL injection via f-string interpolation of user_id values. Use parameterized queries.",
  "score": 2
}"""
    ),
    # ── Recursion without base case ───────────────────────────────────────────
    (
        """\
def factorial(n):
    return n * factorial(n - 1)
""",
        """{
  "bugs": "CRITICAL: Missing base case. factorial(0) and factorial(1) will recurse infinitely, causing a RecursionError. Fix: if n <= 1: return 1",
  "improvements": "Add base case. Consider iterative approach for large n to avoid stack overflow. Handle negative inputs.",
  "performance": "MEDIUM: Recursive implementation has O(n) stack depth. For large n use math.factorial() or an iterative loop.",
  "security": "None detected.",
  "score": 1
}"""
    ),
    # ── Magic numbers ─────────────────────────────────────────────────────────
    (
        """\
def classify_temperature(temp):
    if temp < 0:
        return "freezing"
    elif temp < 15:
        return "cold"
    elif temp < 25:
        return "comfortable"
    elif temp < 35:
        return "warm"
    else:
        return "hot"
""",
        """{
  "bugs": "None detected.",
  "improvements": "Extract magic numbers into named constants: FREEZING_THRESHOLD = 0, COLD_THRESHOLD = 15, etc. Add type hints and docstring.",
  "performance": "None detected. Simple O(1) comparisons.",
  "security": "None detected.",
  "score": 7
}"""
    ),
    # ── Thread safety ─────────────────────────────────────────────────────────
    (
        """\
counter = 0

def increment():
    global counter
    counter += 1
""",
        """{
  "bugs": "HIGH: Race condition. counter += 1 is not atomic (read-modify-write). In a multi-threaded environment, two threads could read the same value simultaneously, causing lost increments. Use threading.Lock() or threading.Event or collections.atomic types.",
  "improvements": "Use threading.Lock: lock = threading.Lock(); with lock: counter += 1. Or use multiprocessing.Value for process-safe counters.",
  "performance": "None detected.",
  "security": "None detected.",
  "score": 4
}"""
    ),
    # ── No type hints, no docs ─────────────────────────────────────────────────
    (
        """\
def calc(x, y, op):
    if op == "add":
        return x + y
    elif op == "sub":
        return x - y
    elif op == "mul":
        return x * y
    elif op == "div":
        return x / y
""",
        """{
  "bugs": "HIGH: Division by zero not handled when op='div' and y=0. Unknown operations return None silently.",
  "improvements": "Add type hints: def calc(x: float, y: float, op: str) -> float. Add docstring. Use enum for op. Raise ValueError for unknown operations. Handle ZeroDivisionError.",
  "performance": "None detected.",
  "security": "None detected.",
  "score": 4
}"""
    ),
    # ── Proper class design ────────────────────────────────────────────────────
    (
        """\
class BankAccount:
    def __init__(self, balance: float = 0.0) -> None:
        \"\"\"Initialize account with optional starting balance.\"\"\"
        if balance < 0:
            raise ValueError("Initial balance cannot be negative")
        self._balance = balance

    def deposit(self, amount: float) -> None:
        \"\"\"Deposit a positive amount.\"\"\"
        if amount <= 0:
            raise ValueError("Deposit amount must be positive")
        self._balance += amount

    def withdraw(self, amount: float) -> None:
        \"\"\"Withdraw amount if sufficient funds exist.\"\"\"
        if amount <= 0:
            raise ValueError("Withdrawal amount must be positive")
        if amount > self._balance:
            raise ValueError("Insufficient funds")
        self._balance -= amount

    @property
    def balance(self) -> float:
        \"\"\"Current account balance.\"\"\"
        return self._balance
""",
        """{
  "bugs": "None detected.",
  "improvements": "Consider using Decimal instead of float for monetary values to avoid floating-point precision issues. Add transaction history logging.",
  "performance": "None detected.",
  "security": "LOW: No thread safety for concurrent transactions. Consider using threading.Lock for multi-threaded environments.",
  "score": 9
}"""
    ),
    # ── XSS vulnerability ─────────────────────────────────────────────────────
    (
        """\
from flask import Flask, request, render_template_string

app = Flask(__name__)

@app.route('/search')
def search():
    query = request.args.get('q', '')
    return render_template_string(f'<h1>Results for: {query}</h1>')
""",
        """{
  "bugs": "None detected.",
  "improvements": "Use render_template() with a separate template file. Separate logic from presentation.",
  "performance": "None detected.",
  "security": "CRITICAL: Cross-Site Scripting (XSS) vulnerability. User input 'query' is directly embedded in HTML without escaping. An attacker can inject <script> tags. Use Flask's escape() or jinja2's |e filter. Never use f-strings to build HTML from user input.",
  "score": 2
}"""
    ),
    # ── Off-by-one ────────────────────────────────────────────────────────────
    (
        """\
def get_last_n_items(lst, n):
    result = []
    for i in range(len(lst) - n, len(lst) + 1):
        result.append(lst[i])
    return result
""",
        """{
  "bugs": "CRITICAL: Off-by-one error. range ends at len(lst) + 1, but valid indices are 0 to len(lst) - 1. lst[len(lst)] will raise IndexError. Fix: range(len(lst) - n, len(lst)) or simply return lst[-n:]",
  "improvements": "Use Python slice notation: return lst[-n:]. This is idiomatic, safe, and handles edge cases automatically.",
  "performance": "MEDIUM: Manual loop is O(n) but list slicing is more Pythonic and often faster.",
  "security": "None detected.",
  "score": 2
}"""
    ),
    # ── Insecure random ───────────────────────────────────────────────────────
    (
        """\
import random

def generate_token():
    return ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=32))
""",
        """{
  "bugs": "None detected.",
  "improvements": "Use secrets module for cryptographically secure token generation.",
  "performance": "None detected.",
  "security": "HIGH: Using random module which is not cryptographically secure. Tokens can be predicted. Use: import secrets; return secrets.token_urlsafe(32)",
  "score": 4
}"""
    ),
    # ── Clean async code ──────────────────────────────────────────────────────
    (
        """\
import asyncio
import aiohttp

async def fetch_data(url: str, session: aiohttp.ClientSession) -> dict:
    \"\"\"Fetch JSON data from URL asynchronously.

    Args:
        url: The URL to fetch from.
        session: Shared aiohttp session.

    Returns:
        Parsed JSON response.

    Raises:
        aiohttp.ClientError: On network errors.
    \"\"\"
    async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
        response.raise_for_status()
        return await response.json()
""",
        """{
  "bugs": "None detected.",
  "improvements": "Consider adding retry logic with exponential backoff for transient failures.",
  "performance": "Good use of async/await and shared session. Timeout is properly configured.",
  "security": "MEDIUM: No SSL certificate verification disabled check. Ensure ssl=True (default) is not overridden at the session level.",
  "score": 9
}"""
    ),
]


# ─── Code Templates for Variation ────────────────────────────────────────────

CODE_TEMPLATES = [
    # Template: dict access without .get()
    (
        """\
def process_config(config):
    host = config['host']
    port = config['port']
    timeout = config['timeout']
    return f"{host}:{port}"
""",
        """{
  "bugs": "HIGH: Direct dictionary access with [] raises KeyError if keys are missing. Use config.get('host') with a default value.",
  "improvements": "Use config.get('host', 'localhost'), config.get('port', 8080), etc. Consider dataclass or Pydantic model for config validation.",
  "performance": "None detected.",
  "security": "None detected.",
  "score": 5
}"""
    ),
    # Template: list comprehension vs loop
    (
        """\
def filter_even(numbers):
    result = []
    for n in numbers:
        if n % 2 == 0:
            result.append(n)
    return result
""",
        """{
  "bugs": "None detected.",
  "improvements": "Use list comprehension: return [n for n in numbers if n % 2 == 0]. Add type hints: def filter_even(numbers: list[int]) -> list[int].",
  "performance": "LOW: Manual loop is valid but list comprehension is faster and more Pythonic.",
  "security": "None detected.",
  "score": 7
}"""
    ),
    # Template: print debugging
    (
        """\
def calculate(a, b):
    print("a =", a)
    print("b =", b)
    result = a * b + a / b
    print("result =", result)
    return result
""",
        """{
  "bugs": "MEDIUM: ZeroDivisionError if b=0. No input validation.",
  "improvements": "Remove debug print statements. Use logging module instead. Add docstring and type hints.",
  "performance": "None detected.",
  "security": "None detected.",
  "score": 4
}"""
    ),
    # Template: string concatenation in loop
    (
        """\
def build_html(items):
    html = ""
    for item in items:
        html += "<li>" + item + "</li>"
    return "<ul>" + html + "</ul>"
""",
        """{
  "bugs": "None detected.",
  "improvements": "Use str.join() for efficiency: return '<ul>' + ''.join(f'<li>{item}</li>' for item in items) + '</ul>'.",
  "performance": "MEDIUM: String concatenation in loop is O(n²). Use list + join for O(n).",
  "security": "HIGH: XSS vulnerability. 'item' values are not HTML-escaped. Use html.escape(item).",
  "score": 4
}"""
    ),
    # Template: broad exception
    (
        """\
def load_json(filepath):
    try:
        with open(filepath) as f:
            return json.load(f)
    except Exception as e:
        print(f"Error: {e}")
        return {}
""",
        """{
  "bugs": "MEDIUM: Returning empty dict on any error silently hides failures. Callers cannot distinguish between an empty file and a read error.",
  "improvements": "Catch specific exceptions: FileNotFoundError, json.JSONDecodeError. Use logging instead of print. Consider re-raising or returning None with documentation.",
  "performance": "None detected.",
  "security": "None detected.",
  "score": 6
}"""
    ),
    # Template: missing __str__
    (
        """\
class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def distance_to(self, other):
        return ((self.x - other.x)**2 + (self.y - other.y)**2)**0.5
""",
        """{
  "bugs": "None detected.",
  "improvements": "Add __str__ and __repr__ methods. Add type hints. Consider using @dataclass decorator. Add __eq__ for comparisons.",
  "performance": "MEDIUM: Consider using math.hypot(dx, dy) which is faster and more accurate than manual sqrt.",
  "security": "None detected.",
  "score": 7
}"""
    ),
    # Template: wildcard import
    (
        """\
from os.path import *
from math import *

def get_file_size(filepath):
    if exists(filepath):
        return getsize(filepath)
    return 0
""",
        """{
  "bugs": "None detected.",
  "improvements": "Replace wildcard imports with explicit: from os.path import exists, getsize. Wildcard imports pollute namespace and can cause name collisions.",
  "performance": "None detected.",
  "security": "MEDIUM: Wildcard imports can accidentally import unexpected names, potentially overriding built-ins.",
  "score": 5
}"""
    ),
    # Template: subprocess shell=True
    (
        """\
import subprocess

def run_command(cmd):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout
""",
        """{
  "bugs": "None detected.",
  "improvements": "Pass command as a list: subprocess.run(['cmd', 'arg1'], ...) and set shell=False.",
  "performance": "None detected.",
  "security": "HIGH: shell=True with a string command is dangerous if 'cmd' contains user input. It enables shell injection attacks. Use shell=False with a list of arguments.",
  "score": 4
}"""
    ),
    # Template: deeply nested code
    (
        """\
def process(data):
    if data:
        if isinstance(data, dict):
            if 'items' in data:
                if len(data['items']) > 0:
                    for item in data['items']:
                        if item.get('active'):
                            print(item['name'])
""",
        """{
  "bugs": "MEDIUM: item['name'] raises KeyError if 'name' is missing. Use item.get('name', '').",
  "improvements": "Flatten nesting with early returns (guard clauses). Extract inner logic to a helper function. Reduce cyclomatic complexity.",
  "performance": "None detected.",
  "security": "None detected.",
  "score": 4
}"""
    ),
    # Template: correct use of dataclass
    (
        """\
from dataclasses import dataclass, field
from typing import List

@dataclass
class Order:
    id: int
    customer: str
    items: List[str] = field(default_factory=list)
    total: float = 0.0

    def add_item(self, item: str, price: float) -> None:
        \"\"\"Add an item to the order.\"\"\"
        self.items.append(item)
        self.total += price

    def is_empty(self) -> bool:
        \"\"\"Check if the order has no items.\"\"\"
        return len(self.items) == 0
""",
        """{
  "bugs": "None detected.",
  "improvements": "Consider using Decimal for 'total' to avoid floating-point precision issues. Add validation for negative prices.",
  "performance": "None detected.",
  "security": "None detected.",
  "score": 9
}"""
    ),
]


# ─── Generator ────────────────────────────────────────────────────────────────

INSTRUCTIONS = [
    "Review the following Python code and identify bugs, improvements, performance issues, and security risks.",
    "Perform a code review of the following Python code. Identify any bugs, suggest improvements, flag performance issues, and highlight security concerns.",
    "Analyze this Python code snippet. Provide structured feedback on bugs, code improvements, performance, and security.",
    "As a senior software engineer, review the following Python code for quality, correctness, and security.",
    "Conduct a thorough code review of the Python code below. Report bugs, improvements, performance bottlenecks, and security vulnerabilities.",
]


def make_sample(code: str, review: str, instruction: str | None = None) -> dict:
    """Create a single JSONL sample."""
    return {
        "instruction": instruction or random.choice(INSTRUCTIONS),
        "input": code.strip(),
        "output": review.strip(),
    }


def validate_sample(sample: dict) -> bool:
    """Basic validation of a sample."""
    if not sample.get("instruction") or not sample.get("input") or not sample.get("output"):
        return False
    # Rough token estimate (1 token ≈ 4 chars)
    total_chars = len(sample["instruction"]) + len(sample["input"]) + len(sample["output"])
    if total_chars > 8192 * 4:  # ~8192 tokens limit
        return False
    # Must be valid JSON output
    try:
        json.loads(sample["output"])
    except json.JSONDecodeError:
        return False
    return True


def generate_dataset(count: int = 1000, output_path: str = "data/dataset.jsonl") -> int:
    """Generate dataset and write to JSONL file."""
    all_examples = SEED_EXAMPLES + CODE_TEMPLATES
    dataset = []

    # Add one sample per instruction variant for each example
    for code, review in all_examples:
        for instruction in INSTRUCTIONS:
            sample = make_sample(code, review, instruction)
            if validate_sample(sample):
                dataset.append(sample)

    # Fill remaining count by sampling with random instruction variation
    while len(dataset) < count:
        code, review = random.choice(all_examples)
        sample = make_sample(code, review)
        if validate_sample(sample):
            dataset.append(sample)

    # Shuffle and trim to exactly count
    random.shuffle(dataset)
    dataset = dataset[:count]

    # Write to JSONL
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with open(output, "w", encoding="utf-8") as f:
        for sample in dataset:
            f.write(json.dumps(sample, ensure_ascii=False) + "\n")

    print(f"✅ Dataset generated: {len(dataset)} samples → {output}")
    return len(dataset)


def show_sample(output_path: str = "data/dataset.jsonl", n: int = 2) -> None:
    """Print a few samples for inspection."""
    with open(output_path, encoding="utf-8") as f:
        for i, line in enumerate(f):
            if i >= n:
                break
            sample = json.loads(line)
            print(f"\n{'='*60}")
            print(f"[Sample {i + 1}]")
            print(f"INSTRUCTION: {sample['instruction']}\n")
            print(f"INPUT:\n{sample['input']}\n")
            print(f"OUTPUT:\n{sample['output']}")


# ─── CLI ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate Flux AI training dataset")
    parser.add_argument("--output", default="data/dataset.jsonl", help="Output JSONL file path")
    parser.add_argument("--count", type=int, default=1000, help="Number of samples to generate")
    parser.add_argument("--preview", action="store_true", help="Print sample previews after generation")
    args = parser.parse_args()

    n = generate_dataset(count=args.count, output_path=args.output)
    if args.preview:
        show_sample(args.output)
