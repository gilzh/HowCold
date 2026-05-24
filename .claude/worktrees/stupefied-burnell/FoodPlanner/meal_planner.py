import json
import random
import argparse
from pathlib import Path


def load_recipes(path: Path) -> list:
    """Load the JSON file produced by the scraper and return list of recipes."""
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def suggest_menus(recipes: list, days: int = 7) -> list:
    """Return a list of *days* distinct recipes chosen from the input list.

    The function ensures that the recipes have a URL field and that there
    are enough candidates.  The selection is random; you can seed
    ``random`` externally for reproducible plans.
    """
    candidates = [r for r in recipes if r.get("url")]
    if len(candidates) < days:
        raise ValueError(f"need at least {days} recipes but only {len(candidates)} available")
    return random.sample(candidates, days)


def format_plan(plan: list) -> str:
    """Return a human-readable string for the proposed weekly plan."""
    lines = []
    for i, r in enumerate(plan, start=1):
        lines.append(f"Day {i}: {r.get('name')} - {r.get('url')}")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a simple 7-day meal plan from saved recipes JSON",
    )
    parser.add_argument(
        "--file",
        type=Path,
        default=Path("saved_recipes_detailed.json"),
        help="path to the detailed recipes JSON",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="number of days/menus to suggest",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="optional file to write the suggested plan (json)"
    )

    args = parser.parse_args()
    recipes = load_recipes(args.file)
    plan = suggest_menus(recipes, args.days)

    print(format_plan(plan))

    if args.output:
        with args.output.open("w", encoding="utf-8") as out_f:
            json.dump(plan, out_f, indent=2)
        print(f"Written plan to {args.output}")


if __name__ == "__main__":
    main()
