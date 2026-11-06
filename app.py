
import streamlit as st
import pandas as pd
import ast

# ----------------------------------
# 1. PAGE CONFIGURATION
# ----------------------------------

st.set_page_config(
    page_title="IMDb Movie Dashboard",
    page_icon="🎬",
    layout="wide"
)

# ----------------------------------
# 2. LOAD DATASET
# ----------------------------------

@st.cache_data
def load_data():
    df = pd.read_csv("ToP 250 movies on imdb in 2026 (2).csv")
    return df

df = load_data()

# Convert list-like text columns into Python lists
def convert_list(value):
    if isinstance(value, list):
        return value
    if pd.isna(value):
        return []
    try:
        result = ast.literal_eval(value)
        if isinstance(result, list):
            return result
        return [str(result)]
    except (ValueError, SyntaxError):
        return [str(value)]

df["genres_list"] = df["genres"].apply(convert_list)
df["countries_list"] = df["countriesOfOrigin"].apply(convert_list)

st.title("🎬 IMDb Top 250 Movies Dashboard")
st.success("IMDb Dataset Loaded Successfully!")

# ----------------------------------
# QUESTION 1: DATASET EXPLORATION
# ----------------------------------

st.header("1. Dataset Loading and Initial Exploration")

st.subheader("First 10 Movie Records")
st.dataframe(df.head(10), use_container_width=True)

st.subheader("Dataset Information")

col1, col2 = st.columns(2)

col1.metric("Total Rows", df.shape[0])
col2.metric("Total Columns", df.shape[1])

st.write("Column Names:")
st.write(df.columns.tolist())

st.write("Data Types:")
st.write(df.dtypes.astype(str))

st.subheader("Missing Values")
st.dataframe(
    df.isnull().sum().reset_index().rename(
        columns={"index": "Column", 0: "Missing Values"}
    ),
    use_container_width=True
)

with st.expander("Additional Dataset Information"):
    st.write("Total Records:", len(df))
    st.write("Available Columns:", len(df.columns))
    st.write("Movie Information:", df["primaryTitle"].count())

st.divider()

# ----------------------------------
# QUESTION 2: KPI METRICS
# ----------------------------------

st.header("2. Movie Analytics Dashboard")

total_movies = len(df)
average_rating = df["averageRating"].mean()
highest_rating = df["averageRating"].max()
total_votes = df["numVotes"].sum()

col1, col2, col3, col4 = st.columns(4)

col1.metric("Total Movies", total_movies)
col2.metric("Average Rating", round(average_rating, 2))
col3.metric("Highest Rating", highest_rating)
col4.metric("Total Votes", f"{total_votes:,}")

st.divider()

# ----------------------------------
# QUESTION 3: DATA VISUALIZATION
# ----------------------------------

st.header("3. Data Visualization")

tab1, tab2, tab3 = st.tabs([
    "Genre Analysis",
    "Rating Analysis",
    "Gross Collection"
])

# Genre bar chart
with tab1:
    st.subheader("Number of Movies by Genre")

    genre_data = df.explode("genres_list")
    genre_counts = genre_data["genres_list"].value_counts()

    st.bar_chart(genre_counts)

# Rating histogram
with tab2:
    st.subheader("IMDb Rating Distribution")

    rating_bins = pd.cut(
        df["averageRating"],
        bins=10
    ).value_counts().sort_index()

    rating_chart = pd.DataFrame({
        "Number of Movies": rating_bins.values
    }, index=rating_bins.index.astype(str))

    st.bar_chart(rating_chart)

    st.subheader("Rating vs Number of Votes")

    st.scatter_chart(
        df,
        x="averageRating",
        y="numVotes"
    )

# Top 10 gross movies
with tab3:
    st.subheader("Top 10 Movies by Worldwide Gross")

    gross_df = df.dropna(
        subset=["grossWorldwide"]
    ).sort_values(
        by="grossWorldwide",
        ascending=False
    ).head(10)

    st.bar_chart(
        gross_df.set_index("primaryTitle")["grossWorldwide"]
    )

    st.dataframe(
        gross_df[["primaryTitle", "grossWorldwide"]],
        use_container_width=True
    )

st.divider()

# ----------------------------------
# QUESTION 5: INTERACTIVE MOVIE EXPLORER
# ----------------------------------

st.header("4. Interactive Movie Explorer")

# Reset button
if st.button("Reset All Filters"):
    for key in [
        "genre_filter", "country_filter", "rating_filter",
        "votes_filter", "title_filter", "sort_filter"
    ]:
        st.session_state[key] = None
    st.rerun()

filtered_df = df.copy()

# Genre selectbox
all_genres = sorted(
    genre for genre in
    df["genres_list"].explode().dropna().unique()
)

selected_genre = st.selectbox(
    "Select Movie Genre",
    ["All"] + all_genres,
    key="genre_filter"
)

if selected_genre != "All":
    filtered_df = filtered_df[
        filtered_df["genres_list"].apply(
            lambda genres: selected_genre in genres
        )
    ]

# Country multiselect
all_countries = sorted(
    country for country in
    df["countries_list"].explode().dropna().unique()
)

selected_countries = st.multiselect(
    "Select Countries of Origin",
    all_countries,
    key="country_filter"
)

if selected_countries:
    filtered_df = filtered_df[
        filtered_df["countries_list"].apply(
            lambda countries: any(
                country in countries
                for country in selected_countries
            )
        )
    ]

# Rating slider
min_rating = float(df["averageRating"].min())
max_rating = float(df["averageRating"].max())

rating_range = st.slider(
    "Select IMDb Rating Range",
    min_value=min_rating,
    max_value=max_rating,
    value=(min_rating, max_rating),
    step=0.1,
    key="rating_filter"
)

filtered_df = filtered_df[
    (filtered_df["averageRating"] >= rating_range[0]) &
    (filtered_df["averageRating"] <= rating_range[1])
]

# Minimum votes
minimum_votes = st.number_input(
    "Minimum Number of Votes",
    min_value=0,
    value=0,
    step=1000,
    key="votes_filter"
)

filtered_df = filtered_df[
    filtered_df["numVotes"] >= minimum_votes
]

# Movie title search
search_title = st.text_input(
    "Search Movie by Title",
    key="title_filter"
)

if search_title:
    filtered_df = filtered_df[
        filtered_df["primaryTitle"].str.contains(
            search_title,
            case=False,
            na=False
        )
    ]

# Sorting radio button
sort_order = st.radio(
    "Sort IMDb Ratings",
    ["Descending", "Ascending"],
    horizontal=True,
    key="sort_filter"
)

filtered_df = filtered_df.sort_values(
    by="averageRating",
    ascending=(sort_order == "Ascending")
)

# Display filtered results
st.subheader("Filtered Movie Results")

st.metric("Movies Remaining", len(filtered_df))

st.dataframe(
    filtered_df[
        ["primaryTitle", "genres", "countriesOfOrigin",
         "averageRating", "numVotes", "grossWorldwide"]
    ],
    use_container_width=True
)

st.divider()

# ----------------------------------
# QUESTION 6: SESSION STATE AND FORM
# ----------------------------------

st.header("5. Session State and Movie Search Form")

if "selected_movie" not in st.session_state:
    st.session_state.selected_movie = None

with st.form("movie_search_form"):

    movie_title = st.text_input("Enter Movie Title")

    preferred_genre = st.selectbox(
        "Select Preferred Genre",
        all_genres
    )

    preferred_rating = st.slider(
        "Minimum IMDb Rating",
        min_value=min_rating,
        max_value=max_rating,
        value=min_rating,
        step=0.1
    )

    submitted = st.form_submit_button("Search Movie")

if submitted:

    search_df = df[
        (df["primaryTitle"].str.contains(
            movie_title,
            case=False,
            na=False
        )) &
        (df["genres_list"].apply(
            lambda genres: preferred_genre in genres
        )) &
        (df["averageRating"] >= preferred_rating)
    ]

    if not search_df.empty:
        st.session_state.selected_movie = search_df.iloc[0].to_dict()
        st.success("Matching Movie Found Successfully!")

    else:
        st.session_state.selected_movie = None
        st.info("No matching movie found. Try different preferences.")

# Display selected movie
if st.session_state.selected_movie is not None:

    movie = st.session_state.selected_movie

    st.subheader("Selected Movie Information")

    st.write("Movie Title:", movie["primaryTitle"])
    st.write("Genre:", movie["genres"])
    st.write("IMDb Rating:", movie["averageRating"])
    st.write("Number of Votes:", f'{movie["numVotes"]:,}')

st.divider()

st.success("IMDb Movie Analytics Dashboard Completed!")
