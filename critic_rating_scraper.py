import asyncio
import csv
import os

import httpx
from bs4 import BeautifulSoup

os.makedirs("data/critic_ratings", exist_ok=True)


async def get_album_info(soup, slug):
    artist = soup.find("div", class_="artist").string
    album = soup.find("h1", class_="albumTitle").string
    critic_score = soup.select_one("div.albumCriticScore a").text
    user_score = soup.select_one("div.albumUserScore a").text
    detail_row = soup.select_one("div.albumTopBox.info div.detailRow")
    texts = list(detail_row.stripped_strings)
    month = texts[0]
    date = texts[1].replace(",", "")
    release_year = texts[2]
    release_date = f"{month} {date}"
    genre_metas = soup.select('div.detailRow meta[itemprop="genre"]')
    genres = "|".join([m["content"] for m in genre_metas])
    return {
        "slug": slug,
        "artist": artist,
        "album": album,
        "critic_score": critic_score,
        "user_score": user_score,
        "release_date": release_date,
        "release_year": release_year,
        "genres": genres,
    }


async def get_critic_reviews(soup, slug):
    results = []
    reviews = soup.select("div.albumReviewRow")
    for row in reviews:
        pub = row.select_one("div.publication").string
        author = row.select_one("div.author a").string
        review_text = row.select_one("div.albumReviewText")
        if review_text:
            review_text = review_text.text
        date = row.select_one("div.albumReviewLinks div.actionContainer[title]")[
            "title"
        ]
        review_score = row.select_one("div.albumReviewRating").string
        results.append(
            {
                "slug": slug,
                "publication": pub,
                "author": author,
                "snippet": review_text,
                "date": date,
                "score": review_score,
            }
        )
    return results


async def scrape_critic_ratings(slug):
    url = f"https://www.albumoftheyear.org/album/{slug}.php"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }
    reviews = []
    async with httpx.AsyncClient() as client:
        r = await client.get(url, headers=headers)
        soup = BeautifulSoup(r.text, "lxml")
        info = await get_album_info(soup, slug)
        data = await get_critic_reviews(soup, slug)
        reviews.extend(data)
    return info, reviews


async def scrape_critic_ratings_decade(decade):
    results = []
    albums = []
    input_file = f"data/slugs/album_slugs_{decade}s.csv"
    output_file = f"data/user_ratings/user_ratings_{decade}s.csv"
    info_file = f"data/album_{decade}s.csv"
    with open(input_file, "r") as csvfile:
        reader = csv.reader(csvfile)
        next(reader)
    for row in reader:
        info, data = await scrape_critic_ratings(row[-1])
        results.extend(data)
        albums.append(info)
    print(f"Completed decade {decade}s")
    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)
    print(f"Saved to file '{output_file}'")
    with open(info_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(albums)
    print(f"Saved to file '{info_file}'")


async def main():
    coroutines = [
        scrape_critic_ratings_decade(decade) for decade in range(1950, 2021, 10)
    ]
    results = await asyncio.gather(*coroutines)
    return results


if __name__ == "__main__":
    asyncio.run(main())
