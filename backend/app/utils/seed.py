# path: backend/app/utils/seed.py
"""
Seeds the database and vectorstore with LeetCode problems on startup.
Run once: python -m app.utils.seed
"""
import json, os, sys, uuid, logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app.models.base import SessionLocal, engine
from app.models.user import Base, User, Dataset
from app.core.security import hash_password
from app.rag.vectorstore import add_documents

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_leetcode_data():
    """Load from dataset/leetcode_seed.json"""
    seed_path = os.path.join(
        os.path.dirname(__file__), "../../../dataset/leetcode_seed.json"
    )
    if not os.path.exists(seed_path):
        logger.warning("Seed file not found, using inline data")
        return INLINE_SEED_DATA
    with open(seed_path) as f:
        return json.load(f)


def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # Create admin user
    admin = db.query(User).filter(User.email == "admin@ragcode.ai").first()
    if not admin:
        admin = User(
            id=str(uuid.uuid4()),
            email="admin@ragcode.ai",
            hashed_password=hash_password("Admin@12345"),
            name="Admin",
            role="admin",
        )
        db.add(admin)
        db.commit()
        logger.info("Created admin user: admin@ragcode.ai / Admin@12345")

    # Seed LeetCode problems
    problems = load_leetcode_data()
    new_docs = []
    for p in problems:
        existing = db.query(Dataset).filter(Dataset.slug == p["slug"]).first()
        if not existing:
            dataset = Dataset(
                id=str(uuid.uuid4()),
                title=p["title"],
                slug=p["slug"],
                difficulty=p["difficulty"],
                tags=p["tags"],
                problem_text=p["problem_text"],
                solution_code=p["solution_code"],
                time_complexity=p["time_complexity"],
                space_complexity=p["space_complexity"],
            )
            db.add(dataset)
            new_docs.append({**p, "id": dataset.id})

    if new_docs:
        db.commit()
        logger.info(f"Seeded {len(new_docs)} LeetCode problems")
        add_documents(new_docs)
        # Mark as embedded
        for d in new_docs:
            ds = db.query(Dataset).filter(Dataset.slug == d["slug"]).first()
            if ds:
                ds.is_embedded = True
        db.commit()

    db.close()
    logger.info("Seed complete")


# Inline fallback seed data (10 problems — full 50 in leetcode_seed.json)
INLINE_SEED_DATA = [
    {
        "title": "Two Sum",
        "slug": "two-sum",
        "difficulty": "Easy",
        "tags": "array,hash-map",
        "problem_text": "Given an array of integers nums and an integer target, return indices of the two numbers such that they add up to target.",
        "solution_code": """def twoSum(nums, target):
    seen = {}
    for i, num in enumerate(nums):
        complement = target - num
        if complement in seen:
            return [seen[complement], i]
        seen[num] = i
    return []""",
        "time_complexity": "O(n)",
        "space_complexity": "O(n)",
    },
    {
        "title": "Best Time to Buy and Sell Stock",
        "slug": "best-time-buy-sell-stock",
        "difficulty": "Easy",
        "tags": "array,dynamic-programming",
        "problem_text": "You are given an array prices where prices[i] is the price on the ith day. Maximize profit by choosing a single day to buy and a different day in the future to sell.",
        "solution_code": """def maxProfit(prices):
    min_price = float('inf')
    max_profit = 0
    for price in prices:
        if price < min_price:
            min_price = price
        elif price - min_price > max_profit:
            max_profit = price - min_price
    return max_profit""",
        "time_complexity": "O(n)",
        "space_complexity": "O(1)",
    },
    {
        "title": "Valid Parentheses",
        "slug": "valid-parentheses",
        "difficulty": "Easy",
        "tags": "stack,string",
        "problem_text": "Given a string s containing just the characters '(', ')', '{', '}', '[' and ']', determine if the input string is valid.",
        "solution_code": """def isValid(s):
    stack = []
    mapping = {')': '(', '}': '{', ']': '['}
    for char in s:
        if char in mapping:
            top = stack.pop() if stack else '#'
            if mapping[char] != top:
                return False
        else:
            stack.append(char)
    return not stack""",
        "time_complexity": "O(n)",
        "space_complexity": "O(n)",
    },
    {
        "title": "Merge Two Sorted Lists",
        "slug": "merge-two-sorted-lists",
        "difficulty": "Easy",
        "tags": "linked-list,recursion",
        "problem_text": "Merge two sorted linked lists and return it as a new sorted list.",
        "solution_code": """def mergeTwoLists(l1, l2):
    dummy = ListNode(0)
    current = dummy
    while l1 and l2:
        if l1.val <= l2.val:
            current.next = l1
            l1 = l1.next
        else:
            current.next = l2
            l2 = l2.next
        current = current.next
    current.next = l1 or l2
    return dummy.next""",
        "time_complexity": "O(n+m)",
        "space_complexity": "O(1)",
    },
    {
        "title": "Maximum Subarray",
        "slug": "maximum-subarray",
        "difficulty": "Medium",
        "tags": "array,dynamic-programming,divide-conquer",
        "problem_text": "Given an integer array nums, find the contiguous subarray which has the largest sum and return its sum.",
        "solution_code": """def maxSubArray(nums):
    max_sum = current_sum = nums[0]
    for num in nums[1:]:
        current_sum = max(num, current_sum + num)
        max_sum = max(max_sum, current_sum)
    return max_sum""",
        "time_complexity": "O(n)",
        "space_complexity": "O(1)",
    },
]


if __name__ == "__main__":
    seed()