import json
import os
from tqdm import tqdm
from openai import OpenAI

client = OpenAI()

INPUT_FILE = "data/papers.json"
OUTPUT_FILE = "data/summaries.json"
MD_DIR = "digests/el_summaries"

os.makedirs(MD_DIR, exist_ok=True)


def build_prompt(title, abstract):
    return f"""
Διάβασε το παρακάτω paper και γράψε περίληψη στα ελληνικά.

Τίτλος:
{title}

Abstract:
{abstract}

Επέστρεψε JSON με:
- short_summary_el
- main_method
- datasets_or_scenarios
- key_results
- why_it_matters_for_thesis
- relevance_score (0-10)
- relevance_label
"""


def summarize_paper(title, abstract):
    prompt = build_prompt(title, abstract)

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )

    return response.choices[0].message.content


def save_markdown(paper, summary_text):
    title = paper["title"].replace("/", "-")
    filename = os.path.join(MD_DIR, f"{title[:80]}.md")

    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"# {paper['title']}\n\n")
        f.write(summary_text)


def main():
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        papers = json.load(f)

    results = []

    for paper in tqdm(papers[:30]):  # start small
        title = paper.get("title", "")
        abstract = paper.get("summary", "")

        if not abstract:
            continue

        try:
            summary = summarize_paper(title, abstract)

            result = {
                "title": title,
                "summary": summary
            }

            results.append(result)
            save_markdown(paper, summary)

        except Exception as e:
            print("Error:", e)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main()
