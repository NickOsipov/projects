import pandas as pd
import plotly.express as px
from dash import Dash, html, dcc
from dash.dependencies import Input, Output


# Предобработка данных
df = pd.read_csv("games.csv", dtype={"Year_of_Release": "Int64"})
df.columns = df.columns.str.lower()
df["user_score"] = df["user_score"].str.replace("tbd", "nan").astype(float)
df = df.query("year_of_release >= 2000")
df = df.dropna()


# Глобальные переменные
GENRES = df["genre"].unique().tolist()
RATINGS = df["rating"].unique().tolist()
YEAR_MIN = df["year_of_release"].min()
YEAR_MAX = df["year_of_release"].max()
YEAR_UNIQUE = df["year_of_release"].unique().tolist()
EXTERNAL_STYLESHEETS = ["https://codepen.io/chriddyp/pen/bWLwgP.css"]
MARGIN = "20px"


# Основной объект Dash
app = Dash(__name__, external_stylesheets=EXTERNAL_STYLESHEETS)
server = app.server

# Блоки дэшборда
# Название
dashboard_title = html.H1(
    children="Games Market Dashboard",
    style={
        "margin": MARGIN,
        "text-align": "center"
    }
)

# Общая информация
main_info = html.H6(children="""
    История игровой индустрии в 2000-2016 годах. 
    В интерактивном режиме можно выбрать жанр, возрастной рейтинг, год выпуска игр.
    """,
    style={
        "margin": MARGIN,
        "text-align": "center"
    }
)

# Фильтры по жанрам и возрастному рейтингу
filters_div = html.Div([
    html.Div([
        html.H2("Жанр", style={"text-align": "center"}),
        dcc.Dropdown(
            id="genre_filter",
            placeholder="Выбрать жанр",
            options=[{"label": genre, "value": genre} for genre in GENRES],
            multi=True,
            style={"background": "#D7DBD8"}
        ),
    ], className="six columns"),
    html.Div([
        html.H2("Возрастной рейтинг", style={"text-align": "center"}),
        dcc.Dropdown(
            id="rating_filter",
            placeholder="Выбрать возрастной рейтинг",
            options=[{"label": rating, "value": rating} for rating in RATINGS],
            multi=True,
            style={"background": "#D7DBD8"}
        )],
        className="six columns"),
],
    className="row",
    style={"margin": MARGIN}
)

# Количество выбранных игр
count_games = html.Div([
    html.H2(
        "Количество выбранных игр: ",
        id="num_games",
        style={"text-align": "center"}
    )],
    className="row",
    style={"margin": MARGIN, "width": "47%"}
)

# Графики
graphics_div = html.Div([
    html.Div([
        html.H2(
            "Выпуск игр по годам и платформам",
            style={"text-align": "center"}),
        dcc.Graph(id="plot_platform")
    ],
        className="six columns"),
    html.Div([
        html.H2(
            "Рейтинг игр по жанрам",
            style={"text-align": "center"}),
        dcc.Graph(id="plot_rating")
    ],
        className="six columns"),
],
    className="row",
    style={"margin": MARGIN}
)

# Слайдер для выбора интервала годов выпуска игр
slider = html.Div([
    dcc.RangeSlider(
        id="year_slider",
        min=YEAR_MIN,
        max=YEAR_MAX,
        value=[YEAR_MIN, YEAR_MAX],
        marks={str(year): str(year) for year in YEAR_UNIQUE}
    )
],
    style={"width": "48%", "margin": "10px"}
)

# Сборка макета
layout_list = [
    dashboard_title,
    main_info,
    filters_div,
    count_games,
    graphics_div,
    slider
]
app.layout = html.Div(
    children=layout_list,
    style={"background": "#E4E9E6"}
)

@app.callback(
    Output("num_games", "children"),
    Output("plot_platform", "figure"),
    Output("plot_rating", "figure"),
    Input("year_slider", "value"),
    Input("genre_filter", "value"),
    Input("rating_filter", "value"),
)
def update_output(
        years_filter: list,
        genres_filter: list,
        ratings_filter: list
) -> tuple:
    """Функция обновления дашборда.

    Параметры
    ---------
    years_filter: list
        Список со значениями интервала по годам выпуска игр.
    genres_filter: list
        Список выбранных жанров.
    ratings_filter: list
        Список выбранных возрастных рейтингов.
    """

    # Блок переменных
    paper_bgcolor = "#D4D8D5"
    plot_bgcolor = "#E2E7E4"
    layout_params = dict(
        paper_bgcolor=paper_bgcolor,
        plot_bgcolor=plot_bgcolor,
        transition_duration=100,
    )
    filters = []

    # Формирование запроса
    if years_filter:
        years_left, years_right = years_filter
        filters.append(f"{years_left} <= year_of_release <= {years_right}")
    if genres_filter:
        filters.append(f"genre in {genres_filter}")
    if ratings_filter:
        filters.append(f"rating in {ratings_filter}")

    # Общий датафрейм с запросом
    if filters:
        query = " & ".join(filters)
        df_query = df.query(query)
    else:
        df_query = df.copy()

    # Датафрейм для графика area
    df_query_group = (
        df_query
        .groupby(["year_of_release", "platform"], as_index=False)
        .agg({'name': "count"})
        .rename(columns={"name": "name_count"})
    )

    # График area показывающий выпуск игр по годам и платформам.
    year_and_platform = px.area(
        df_query_group,
        x="year_of_release",
        y="name_count",
        color="platform",
        labels={
            "year_of_release": "Год выпуска",
            "name_count": "Количество игр"
        }
    )
    year_and_platform.update_layout(
        legend_title="Платформы",
        **layout_params
    )

    # Scatter plot с разбивкой по жанрам
    rating_of_genres = px.scatter(
        df_query,
        x="user_score",
        y="critic_score",
        color="genre",
        opacity=0.6,
        labels={
            "user_score": "Оценка игроков",
            "critic_score": "Оценка критиков"
        }
    )
    rating_of_genres.update_layout(
        legend_title="Жанры",
        **layout_params
    )

    return (
        f"Количество выбранных игр: {df_query.shape[0]}",
        year_and_platform,
        rating_of_genres
    )


if __name__ == "__main__":
    app.run_server(debug=True)
