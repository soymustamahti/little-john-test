SYSTEM_PROMPT = """You classify business documents into the best available document category.

Rules:
- Prefer an existing category whenever it is a reasonable reusable fit.
- Suggest a new category only when none of the existing categories fits the document well enough.
- Base the decision only on the provided document excerpt and category list.
- Keep the rationale short, concrete, and grounded in the excerpt.
- If you suggest a new category, make the label_key lowercase snake_case.
- Keep suggested category names broad enough to be reused.
"""


def build_user_prompt(
    *,
    original_filename: str,
    excerpt_text: str,
    categories_text: str,
) -> str:
    return f"""Document filename:
{original_filename}

Sampled document excerpt:
{excerpt_text}

Existing document categories:
{categories_text}

Return either:
1. a match to one existing category by id, or
2. a suggested new category with name and label_key.
"""
