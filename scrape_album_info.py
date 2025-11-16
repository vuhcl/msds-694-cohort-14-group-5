import cloudscraper
from bs4 import BeautifulSoup
import pandas as pd


def scrape_album_info(url):

    slug = url.split("/")[-1].replace(".php", "")
    scraper = cloudscraper.create_scraper()
    html = scraper.get(url).text
    soup = BeautifulSoup(html, "lxml")

    artist_tag = soup.find("div", class_="artist")
    artist = artist_tag.find("span", itemprop="name").get_text()

    album_tag = soup.find("h1", class_="albumTitle")
    album = album_tag.find("span", itemprop="name").get_text()

    critic_score = soup.select_one("div.albumCriticScore a").get_text()
    user_score = soup.select_one("div.albumUserScore a").get_text()

    detail_row = soup.select_one("div.albumTopBox.info div.detailRow")
    texts = list(detail_row.stripped_strings)
    month, date, year = texts[0], texts[1].replace(",", ""), texts[2]
    release_date = f"{date} {month} {year}"

    genre_metas = soup.select('div.detailRow meta[itemprop="genre"]')
    genres = [m["content"] for m in genre_metas]

    review_rows = soup.select("div.albumReviewRow")
    review_records = []

    for row in review_rows:
        pub = row.select_one("div.publication a")
        pub = pub.get_text() if pub else None

        author = row.select_one("div.author a")
        author = author.get_text() if author else None

        text_tag = row.select_one("div.albumReviewText p")
        review_text = text_tag.get_text() if text_tag else None

        date_tag = row.select_one("div.albumReviewLinks div.actionContainer[title]")
        review_date = date_tag.get("title") if date_tag else None

        score_tag = row.select_one("div.albumReviewRating.first, div.albumReviewRating")
        review_score = score_tag.get_text() if score_tag else None

        review_records.append(
            {
                "slug": slug,
                "publication": pub,
                "author": author,
                "review_text": review_text,
                "review_date": review_date,
                "review_score": review_score,
            }
        )

    return {
        "slug": slug,
        "artist": artist,
        "album": album,
        "critic_score": critic_score,
        "user_score": user_score,
        "release_date": release_date,
        "genres": genres,
        "reviews": review_records,
    }


if __name__ == "__main__":
    url = "https://www.albumoftheyear.org/album/1507961-rosalia-lux.php"
    data = scrape_album_info(url)

    df = pd.DataFrame(data["reviews"])

    df["slug"] = data["slug"]
    df["artist"] = data["artist"]
    df["album"] = data["album"]
    df["critic_score"] = data["critic_score"]
    df["user_score"] = data["user_score"]
    df["release_date"] = data["release_date"]
    df["genres"] = ", ".join(data["genres"])

    df.to_csv("rosalia_lux_reviews.csv", index=False)

    print(df.head())
    print("\nSaved as rosalia_lux_reviews.csv")
