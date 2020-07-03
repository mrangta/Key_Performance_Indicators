import dash
import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_html_components as html
import dash_table as dt
import plotly.graph_objs as go
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from dash.dependencies import Input, Output

# Import all functions from main file
from main import *

# create a subset of openIssuesFilter dataframe for datatable
df_open_critical_issues = openIssuesFilter()[["Git Issue Id", "Title", "AssigneeName", "Severity", "Target"]]

# Filter: Keep only about_to_violate and violated data
df_open_critical_issues = df_open_critical_issues.loc[
    (df_open_critical_issues["Target"] == "about_to_violate") | (df_open_critical_issues["Target"] == "violated")
]

# Dropdown to filter datatable values
dpdown = []
for i in df_open_critical_issues["Target"].unique():
    str(dpdown.append({"label": i, "value": (i)}))


"""
DASH app begins here
"""

BS = "https://stackpath.bootstrapcdn.com/bootstrap/4.4.1/css/bootstrap.min.css"
app = dash.Dash(__name__, external_stylesheets=[BS])
server=app.server


app.title = "Key Performance Indicators"


@app.callback(
    dash.dependencies.Output("table-container", "children"), [dash.dependencies.Input("dropdown", "value")],
)

# Datatable app layout
def display_table(dpdown):
    df_temp = df_open_critical_issues[df_open_critical_issues["Target"] == dpdown]
    return html.Div(
        [
            dt.DataTable(
                id="main-table",
                columns=[{"name": i, "id": i} for i in df_temp.columns],
                data=df_temp.to_dict("rows"),
                style_cell={"textAlign": "center"},
                style_as_list_view=True,
                style_header={"backgroundColor": "rgb(230, 230, 230)", "fontWeight": "bold",},
                style_cell_conditional=[{"if": {"column_id": "Title"}, "textAlign": "left"}],
            )
        ]
    )


body = dbc.Container(
    [
        dbc.Row([html.P("Security KPIs", className="text-center")]),
        html.P([html.Label("KPI Target"), html.Div(dcc.Dropdown(id="dropdown", options=dpdown)),]),
        html.Div(id="table-container", className="tableDiv"),
    ]
)

app.layout = html.Div(
    [
        html.Div([html.H4("Security KPIs", className="text-center")]),
        html.Div(
            [dcc.Graph(id="Open Issues vs Closed Issues", figure=issuesTimeChart())],
            className="shadow-sm p-2 bg-white rounded m-2",
        ),
        html.Div(
            [dcc.Graph(id="Open Issues with Assignee Name", figure=openIssuesWithAssignee())],
            className="shadow-sm p-2 bg-white rounded m-2",
        ),
        html.Div(
            [
                dcc.Graph(id="Open issues KPI targets", figure=openCriticalIssues(), className="col",),
                dcc.Graph(
                    id="Open issues KPI target as per Severity", figure=openIssuesSeverityKPITargets(), className="col",
                ),
            ],
            className="shadow-sm bg-white rounded row m-2",
        ),
        html.Div(
            [
                html.Div(
                    [dcc.Graph(id="Open critical issues with Assignee name", figure=openCriticalIssuesWithAssignee(),)]
                ),
                html.Div(
                    [
                        html.Label("KPI Status", style={"width": "10%"}),
                        dcc.Dropdown(id="dropdown", options=dpdown, style={"width": "90%"}, className="col-4",),
                    ],
                    className="bg-white row pb-2 ",
                ),
                html.Div(id="table-container"),
            ],
            className="shadow-sm bg-white rounded col p-4",
        ),
        html.Div(
            [
                dcc.Graph(id="Closed Issues KPI Targets", figure=closedIssuesKPITargets(), className="col-6"),
                dcc.Graph(
                    id="Closed issues KPI target as per Severity",
                    figure=closedIssuesSeverityKPITargets(),
                    className="col-6",
                ),
            ],
            className="shadow-sm bg-white rounded row m-2",
        ),
        html.Div(
            [
                dcc.Graph(id="Avergae Issues Resolution Time", figure=averageIssueResolutionTime(), className="col-5",),
                dcc.Graph(id="Total Open Issues", figure=totalOpenIssues(), className="col-7"),
            ],
            className="shadow-sm bg-light rounded row m-2",
        ),
    ],
    className="bg-light p-4 text-dark",
)


if __name__ == "__main__":
    app.run_server(debug=True,port=8050)
