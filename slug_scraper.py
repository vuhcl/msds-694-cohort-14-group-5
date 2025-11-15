import asyncio
import csv
import os
from itertools import product

import httpx
from bs4 import BeautifulSoup

os.makedirs("data/slugs", exist_ok=True)


async def scrape_album_slug(html, m_type):
    """
    Given html, return a list albums with type,
    artist name, album name, and slug
    """
    results = []
    soup = BeautifulSoup(html, "lxml")
    for block in soup.select("div.albumBlock.small"):
        if (
            len(block.select("div.ratingRow")) == 2
        ):  # if album has both critic and user score
            slug = block.select_one('a[href^="/album"]')["href"][7:-4]
            artist = block.select_one(".artistTitle").get_text(strip=True)
            album = block.select_one(".albumTitle").get_text(strip=True)
            results.append(
                {"type": m_type, "artist": artist, "album": album, "slug": slug}
            )
    return results


async def scrape_decade(decade):
    base = "https://www.albumoftheyear.org"
    output_file = f"slugs/album_slugs_{decade}s.csv"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.99 Safari/537.36"
    }
    results = []
    if decade == 2020:
        years = range(decade, decade + 6)
    else:
        years = range(decade, decade + 10)
    for year, m_type in product(years, ["lp", "mixtape"]):
        page_num = 0
        stop_flag = True
        while stop_flag:
            page_num += 1
            url = f"{base}/{year}/releases/{page_num}/?type={m_type}"
            async with httpx.AsyncClient() as client:
                r = await client.get(url, headers=headers)
            data = await scrape_album_slug(r.text, m_type)
            if len(data) > 0:
                results.extend(data)
            else:
                # Since the albums are sorted by popularity, if a page has
                # nothing with both critic and user score, the following pages
                # will also have nothing so we can stop scraping
                stop_flag = False
    print(f"Completed decade {decade}s")
    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)
    print(f"Saved to file '{output_file}'")


async def main():
    coroutines = [scrape_decade(decade) for decade in range(1950, 2021, 10)]
    results = await asyncio.gather(*coroutines)
    return results


if __name__ == "__main__":
    asyncio.run(main())
