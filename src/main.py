#TODO gets the teams data
#TODO get the players individual data
#TODO Create the web interface
#TODO Create the dropdown for user selections
#TODO Calculate the chosen player's stats
#TODO Show the plots with respect to user choices

import base64

from nba_api.stats.endpoints import commonplayerinfo
from nba_api.stats.static import players as players_api

import dash
import dash_core_components as dcc
import dash_html_components as html


from plotly.subplots import make_subplots
import plotly.graph_objects as go

from basketball_reference_web_scraper import client
from basketball_reference_web_scraper.errors import InvalidPlayerAndSeason

from sklearn.linear_model import LinearRegression
import numpy as np
import time
from unidecode import unidecode

slug = {}
players = []
teams = []

#getting statistics of all Nba players until 2020
data = client.players_season_totals(season_end_year=2020)

#adding all of the teams and players into their seperate lists
for i in data:
    players.append([" ".join(str(i["team"]).split(".")[1].split("_")), i["name"]])
    slug[i["name"]] = i["slug"]
    teams.append(" ".join(str(i["team"]).split(".")[1].split("_")))

#Creating dictionary and put all of the teams to the dictionary as a keys. set() provide getting each team name 1 time.
team_player = dict([(i, []) for i in list(set(teams))])

#Putting players name to the dictionary as a values. Their keys came from above cell.
for i, j in players:
    team_player[i].append(j)

#This function return a data which include information of players like assist steals etc. between 1990 and 2020
def player_stats(value):
    data = []
    for i in range(2020, 1990, -1):
        total_assists = 0
        total_steals = 0
        total_blocks = 0
        total_rebounds = 0
        total_points = 0
        total_seconds_played = 0
        try:
            current_season = client.regular_season_player_box_scores(player_identifier=value, season_end_year=i)

            for game in current_season:
                total_assists += game["assists"]
                total_steals += game["steals"]
                total_blocks += game["blocks"]
                total_rebounds += game["offensive_rebounds"] + game["defensive_rebounds"]
                total_points += game["points_scored"]
                total_seconds_played += game["seconds_played"]

            total_assists /= len(current_season)
            total_steals /= len(current_season)
            total_blocks /= len(current_season)
            total_rebounds /= len(current_season)
            total_points /= len(current_season)
            total_seconds_played /= len(current_season)
            total_seconds_played /= 60

            data.append(
                {"season": i,
                 "assist": total_assists,
                 "steal": total_steals,
                 "block": total_blocks,
                 "rebound": total_rebounds,
                 "point": total_points,
                 "minutes": total_seconds_played})
        except InvalidPlayerAndSeason:
            break
    return data

#This function returns a prediction of a player's next year stats.
def predict_graph(X,y):
    y_range = []
    if (len(X) > 1):
        if len(X) == 2:
            x_range = np.linspace(max(X) - 1, 2021, 100)

        else:
            x_range = np.linspace(max(X) - 2, 2021, 100)

        for i in range(len(y)):
            model = LinearRegression()
            model.fit(np.array(X).reshape(-1,1), y[i])
            y_range.append(model.predict(x_range.reshape(-1, 1)))
    else:
        x_range = np.linspace(2020, 2021, 100)
        for i in range(len(y)):
            y_range_temp = np.zeros(x_range.reshape(-1, 1).shape)
            y_range_temp[:] = y[i][0]
            y_range.append(y_range_temp)
    return x_range,y_range


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
#put the NBA LOGO to the interface
image_filename = "../nba_logo.png"
encoded_image = base64.b64encode(open(image_filename, 'rb').read())

#These are the codes about layout and titles of the interface. Briefly they arrange the view of title, image etc.
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.title = 'NBA 2020 Player Stats'
app.layout = html.Div([
    html.Div(dcc.Dropdown(
        id='teams-dropdown',
        options=[{'label': key, 'value': key} for key in team_player.keys()],
        value="ATLANTA HAWKS",clearable=False
    ),style={'display': 'inline-block',"width": "20%"}),

    html.Div(dcc.Dropdown(id='players-dropdown',clearable=False),style={'display': 'inline-block',"width": "20%"}),
    html.Div([html.Img(src='data:image/png;base64,{}'.format(encoded_image.decode()),style={'display': 'inline-block',"width":"70px","height":"40px"}),html.H1(id='title-page', children=["NBA Player Stats"],style={'display': 'inline-block'})], style={'display': 'inline-block',"margin-left":"300px"}),
    html.Div(children=[html.Div(
        children=[
            dcc.Loading(id="loading-page",children=[html.Div([html.Div(id="loading-output-2")])],type="circle",style={'display': 'block',"margin-right": "60px","margin-bottom": "60px"}),
            html.Img(id='image', style={'display': 'block', "margin-left": "40px"}),
            html.H4(id='player-bio', children=[""], style={'display': 'block'})],
        style={'display': 'inline-block', "margin-top": "100px","margin-left": "50px","vertical-align": "center"}),
        dcc.Graph(id="player-graphs", style={'display': 'inline-block', "vertical-align": "top"})])
])

#the first dropdown which provide teams to the users.
@app.callback(
    dash.dependencies.Output('players-dropdown', 'options'),
    [dash.dependencies.Input('teams-dropdown', 'value')])
def set_teams_options(selected_team):
    return [{'label': i, 'value': i} for i in team_player[selected_team]]

#the second dropdown which provide player to the user with respect to chosen team.
@app.callback(
    dash.dependencies.Output('players-dropdown', 'value'),
    [dash.dependencies.Input('players-dropdown', 'options')])
def set_teams_value(available_options):
    return available_options[0]['value']

#with respect to choices of the user
@app.callback(
    [dash.dependencies.Output("loading-page", "children"),
     dash.dependencies.Output('player-graphs', 'figure'),
     dash.dependencies.Output('image', 'src'),
     dash.dependencies.Output('player-bio', 'children')],
    [dash.dependencies.Input('players-dropdown', 'value')])

#Showing all the statistics of chosen player.
def line(selected_player):
    #waiting time for the user.
    time.sleep(10)
    slug_code = slug[selected_player]

    #created a figure in order to arrange the graphs' places and show their names to the user.
    player = player_stats(slug_code)
    fig = make_subplots(rows=2, cols=3, subplot_titles=(
    "Points by Year", "Assists by Year", "Rebounds by Year", "Blocks by Years", "Steals by Year", "Minutes by Year"))
    for i in fig['layout']['annotations']:
        i['font'] = dict(size=25, color='#361414')


    years_plot = []
    point_plot = []
    assist_plot = []
    rebound_plot = []
    block_plot = []
    steal_plot = []
    minutes_plot = []

    #take values into plot lists to use them in plots
    for i in player:
        years_plot.append(i["season"])
        point_plot.append(i["point"])
        assist_plot.append(i["assist"])
        rebound_plot.append(i["rebound"])
        block_plot.append(i["block"])
        steal_plot.append(i["steal"])
        minutes_plot.append(i["minutes"])

    years_plot.append(2021)
    point_plot.append(None)
    assist_plot.append(None)
    rebound_plot.append(None)
    block_plot.append(None)
    steal_plot.append(None)
    minutes_plot.append(None)

    #these following codes are adding the x and y  values of each graph.
    X,y = predict_graph(years_plot[:-1],[point_plot[:-1],assist_plot[:-1],rebound_plot[:-1],block_plot[:-1],steal_plot[:-1],minutes_plot[:-1]])

    #actual point stats of player
    fig.add_trace(
        go.Scatter(name="Point", x=years_plot, y=point_plot,hovertemplate = "Year=%{x}<br>Average Point per Game=%{y}<extra></extra>"),
        row=1, col=1
    )
    #estimated point stats of player for next season
    fig.add_trace(
        go.Scatter(x=X, y=y[0], name='Point Prediction',marker_color='rgba(152, 0, 0, .8)',line=dict(dash='dash')),
        row=1, col=1
    )
    #actual assist stats of player
    fig.add_trace(
        go.Scatter(name="Assist", x=years_plot, y=assist_plot,hovertemplate = "Year=%{x}<br>Average Assist per Game=%{y}<extra></extra>"),
        row=1, col=2
    )
    #estimated assist stats of player for next season
    fig.add_trace(
        go.Scatter(x=X, y=y[1], name='Assist Prediction',marker_color='rgba(152, 0, 0, .8)',line=dict(dash='dash')),
        row=1, col=2
    )
    #actual rebound stats of player
    fig.add_trace(
        go.Scatter(name="Rebound", x=years_plot, y=rebound_plot,hovertemplate = "Year=%{x}<br>Average Rebound per Game=%{y}<extra></extra>"),
        row=1, col=3
    )
    #estimated rebound stats of player for next season
    fig.add_trace(
        go.Scatter(x=X, y=y[2], name='Rebound Prediction',marker_color='rgba(152, 0, 0, .8)',line=dict(dash='dash')),
        row=1, col=3
    )
    #actual block stats of player
    fig.add_trace(
        go.Scatter(name="Block", x=years_plot, y=block_plot,hovertemplate = "Year=%{x}<br>Average Block per Game=%{y}<extra></extra>"),
        row=2, col=1
    )
    #estimated block stats of player for next season
    fig.add_trace(
        go.Scatter(x=X, y=y[3], name='Block Prediction',marker_color='rgba(152, 0, 0, .8)',line=dict(dash='dash')),
        row=2, col=1
    )
    #actual steal stats of player
    fig.add_trace(
        go.Scatter(name="Steal", x=years_plot, y=steal_plot,hovertemplate = "Year=%{x}<br>Average Steal per Game=%{y}<extra></extra>"),
        row=2, col=2
    )

    #estimated steal stats of player for next season
    fig.add_trace(
        go.Scatter(x=X, y=y[4], name='Steal Prediction',marker_color='rgba(152, 0, 0, .8)',line=dict(dash='dash')),
        row=2, col=2
    )
    #actual minute stats of player
    fig.add_trace(
        go.Scatter(name="Minute", x=years_plot, y=minutes_plot,hovertemplate = "Year=%{x}<br>Average Minute per Game=%{y}<extra></extra>"),
        row=2, col=3
    )
    #estimated minute stats of player for next season
    fig.add_trace(
        go.Scatter(x=X, y=y[5], name='Minute Prediction',marker_color='rgba(152, 0, 0, .8)',line=dict(dash='dash')),
        row=2, col=3
    )
    fig.update_layout(height=800, width=1500, title_text="Stats of " + selected_player)
    #The layout of the graphs
    fig.update_yaxes(title_text="average point", row=1, col=1)
    fig.update_yaxes(title_text="average assist", row=1, col=2)
    fig.update_yaxes(title_text="average rebound", row=1, col=3)
    fig.update_yaxes(title_text="average block", row=2, col=1)
    fig.update_yaxes(title_text="average steal", row=2, col=2)
    fig.update_yaxes(title_text="average minute", row=2, col=3)

    fig.update_xaxes(title_text="years", row=1, col=1)
    fig.update_xaxes(title_text="years", row=1, col=2)
    fig.update_xaxes(title_text="years", row=1, col=3)
    fig.update_xaxes(title_text="years", row=2, col=1)
    fig.update_xaxes(title_text="years", row=2, col=2)
    fig.update_xaxes(title_text="years", row=2, col=3)

    fig.update_yaxes(linecolor='Grey', gridcolor='Gainsboro')
    fig.update_xaxes(linecolor='Grey', gridcolor='Gainsboro')
    fig.update_xaxes(
        tickmode='linear',
        dtick=1
    )

    player_info = commonplayerinfo.CommonPlayerInfo(
        player_id=players_api.find_players_by_full_name(unidecode(selected_player))[0]["id"]).common_player_info.get_dict()[
        "data"][0]

    #shares the player's information with the user in a tab on the side
    text = [selected_player, html.Br(),
            "Age: " + str(2021 - int(player_info[7][:4])), html.Br(),
            "School: " + player_info[8], html.Br(),
            "Height: " + player_info[11], html.Br(),
            "Weight: " + player_info[12], html.Br(),
            "Position: " + player_info[15], html.Br(),
            "Draft Year: " + player_info[29], html.Br()]
    #adding the picture of a player
    return "",fig, "https://d2cwpp38twqe55.cloudfront.net/req/202006192/images/players/" + slug_code + ".jpg", text

#In order to run app
if __name__ == '__main__':
    app.run_server(debug=True)