import pandas as pd

EXPORT_FIELDS = {
    "id": "id",
    "title": "title",
    "description": "description",
    "category__name": "category",
    "address": "address",
    "latitude": "latitude",
    "longitude": "longitude",
    "author__username": "author",
    "created_at": "created_at",
    "rating": "rating",
    "reviews_count": "reviews_count",
    "views_last_7d": "views_last_7d",
    "popularity": "popularity",
}
EXPORT_LIMIT = 10000
EXPORT_CONTENT_TYPES = {
    "csv": "text/csv; charset=utf-8",
    "json": "application/json; charset=utf-8",
}


def build_locations_dataframe(locations):
    rows = locations.values(*EXPORT_FIELDS)[:EXPORT_LIMIT]
    dataframe = pd.DataFrame.from_records(rows, columns=list(EXPORT_FIELDS))
    dataframe = dataframe.rename(columns=EXPORT_FIELDS)

    dataframe[["latitude", "longitude"]] = dataframe[["latitude", "longitude"]].astype(float)
    dataframe["created_at"] = pd.to_datetime(dataframe["created_at"]).dt.strftime("%Y-%m-%dT%H:%M:%S%z")
    dataframe[["rating", "popularity"]] = dataframe[["rating", "popularity"]].round(2)
    return dataframe


def export_locations(locations, export_format):
    dataframe = build_locations_dataframe(locations)
    if export_format == "csv":
        return dataframe.to_csv(index=False).encode("utf-8-sig")
    return dataframe.to_json(orient="records", force_ascii=False, indent=2).encode("utf-8")
