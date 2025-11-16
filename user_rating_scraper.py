import asyncio
import csv
import os

import httpx
from bs4 import BeautifulSoup

os.makedirs("data/user_ratings", exist_ok=True)
DELAY = 0.1


async def scrape_user_rating_page(html, slug):
    soup = BeautifulSoup(html, "lxml")
    rating_entries = soup.find_all("div", class_="userRatingBlock")
    results = []
    for entry in rating_entries:
        score_tag = entry.find("div", class_="rating")
        score = score_tag.text.strip() if score_tag else "N/A"
        username = entry.find("div", class_="userName").text.strip()
        date = entry.find("div", class_="date")["title"]

        results.append(
            {"slug": slug, "username": username, "score": score, "date": date}
        )
    return results


async def scrape_user_ratings(slug):
    results = []
    base_url = f"https://www.albumoftheyear.org/album/{slug}/user-reviews/?type=ratings"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }
    async with httpx.AsyncClient() as client:
        r = await client.get(base_url, headers=headers)
        soup = BeautifulSoup(r.text, "lxml")
        page = soup.select("div.pageSelectSmall")
        if page:
            last_page = int(page[-1].text)
            for p in range(1, last_page + 1):
                r = await client.get(f"{base_url}&p={p}", headers=headers)
                data = await scrape_user_rating_page(r.text, slug)
                results.extend(data)
                await asyncio.sleep(DELAY)
        else:
            data = await scrape_user_rating_page(r.text, slug)
            results.extend(data)
    return results


async def scrape_user_ratings_decade(decade):
    results = []
    input_file = f"data/slugs/album_slugs_{decade}s.csv"
    output_file = f"data/user_ratings/user_ratings_{decade}s.csv"
    with open(input_file, "r") as csvfile:
        reader = csv.reader(csvfile)
        next(reader)
        for row in reader:
            try:
                data = await scrape_user_ratings(row[-1])
                results.extend(data)
            except httpx.ReadTimeout:
                print("Scraping failed", row[-1])
    print(f"Completed decade {decade}s")
    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)
    print(f"Saved to file '{output_file}'")


async def main():
    coroutines = [
        scrape_user_ratings_decade(decade) for decade in range(1970, 2021, 10)
    ]
    results = await asyncio.gather(*coroutines)
    return results


if __name__ == "__main__":
    asyncio.run(main())
