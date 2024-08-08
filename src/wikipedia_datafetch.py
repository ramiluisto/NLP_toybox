import requests
import json
import os
from tqdm import tqdm


def get_random_article_ids(language="en", count=10):
    S = requests.Session()
    URL = f"https://{language}.wikipedia.org/w/api.php"

    article_ids = []
    for _ in tqdm(range(count), desc="Fetching Random Article IDs"):
        PARAMS = {
            "action": "query",
            "format": "json",
            "list": "random",
            "rnnamespace": "0",
            "rnlimit": "1",
        }

        response = S.get(url=URL, params=PARAMS)
        data = response.json()
        article_ids.append(data["query"]["random"][0]["id"])

    return article_ids


def fetch_article_with_langlinks(
    article_id, primary_lang="en", target_langs=["sv", "fi", "de", "cs"]
):
    S = requests.Session()
    URL = f"https://{primary_lang}.wikipedia.org/w/api.php"
    article_data = {}

    PARAMS = {
        "action": "query",
        "format": "json",
        "prop": "extracts|pageprops|langlinks",
        "exintro": True,
        "explaintext": True,
        "pageids": article_id,
        "llprop": "url|langname",
        "lllang": "|".join(target_langs),
    }

    response = S.get(url=URL, params=PARAMS)
    data = response.json()
    page = next(iter(data["query"]["pages"].values()))
    langlinks = {link["lang"]: link["*"] for link in page.get("langlinks", [])}

    article_data[primary_lang] = {
        "content": page.get("extract"),
        "type": page.get("pageprops", {}).get("wikibase_item"),
    }

    for lang, title in tqdm(
        langlinks.items(),
        desc=f"Fetching {primary_lang} Article {article_id} Langlinks",
    ):
        URL = f"https://{lang}.wikipedia.org/w/api.php"
        PARAMS = {
            "action": "query",
            "format": "json",
            "prop": "extracts|pageprops",
            "exintro": True,
            "explaintext": True,
            "titles": title,
        }

        response = S.get(url=URL, params=PARAMS)
        data = response.json()
        page = next(iter(data["query"]["pages"].values()))

        article_data[lang] = {
            "content": page.get("extract", "Content not available"),
            "type": page.get("pageprops", {}).get(
                "wikibase_item", "Metadata not available"
            ),
        }

    return article_data


def save_articles_to_json(articles, file_path):
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=4)


def main(file_path="./wikipedia_dumps/wikipedia_articles.json"):
    article_ids = get_random_article_ids()
    articles = []
    for article_id in tqdm(article_ids, desc="Processing Articles"):
        article_data = fetch_article_with_langlinks(article_id)
        articles.append(article_data)

    save_articles_to_json(articles, file_path)
    print(f"Articles saved to {file_path}")


if __name__ == "__main__":
    main()
