import dash
import dash_core_components as dcc
import plotly.graph_objs as go
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


# Reading CSV file 
file_df = pd.read_csv("Analytics_data.csv", delimiter=";", error_bad_lines=False, skip_blank_lines=False,)

# Filter only security data from file
security_data = file_df[file_df["Labels"].str.contains("security")]

# Filter: Show only a year old data
# prev_year = pd.to_datetime((datetime.today() - timedelta(days=366)))
today_date ="03-07-2020"
start = datetime.strptime(today_date, "%d-%m-%Y") #string to date
prev_year = pd.to_datetime(start - timedelta(days=366))

security_data.loc[:, "IssueCreatedAt"] = pd.to_datetime(security_data["IssueCreatedAt"])
security_data = security_data.loc[(security_data["IssueCreatedAt"] >= prev_year)]


# Replace Nan values of column "AssigneeName" with "No assignee"
security_data["AssigneeName"] = security_data["AssigneeName"].fillna("No Assignee")

# Filter: Show only State="opened" data
open_issues = security_data["State"].str.strip() == "opened"
df_open = security_data[open_issues]

# Filter: Show only State="closed" data
closed_issues = security_data["State"].str.strip() == "closed"
df_close = security_data[closed_issues]

# Logic to calculate business days by ignoring NaTs value and insert Nan where we cannot calculate businessdays
def business_days(start, end):
    mask = pd.notnull(start) & pd.notnull(end)
    start = start.values.astype("datetime64[D]")[mask]
    end = end.values.astype("datetime64[D]")[mask]
    result = np.empty(len(mask), dtype=float)
    result[mask] = np.busday_count(start, end)
    result[~mask] = np.nan
    return result


# Convert string to pandas date time format for open issues dataframe
df_open.loc[:, "Today_Date"] = pd.to_datetime(today_date, format="%d-%m-%Y") # Can add current date 
df_open.loc[:, "IssueCreatedAt"] = pd.to_datetime(df_open["IssueCreatedAt"])

# Add a column in Open issues dataframe of name bussinessdays to calculate number of days between currentdate and Issue creation date
df_open.loc[:, "bussinessDays"] = business_days(df_open["IssueCreatedAt"], df_open["Today_Date"])

# Sanatize date format for closed issues
df_close.loc[:, "IssueClosedDate"] = pd.to_datetime(
    df_close["IssueClosedDate"], dayfirst=False, yearfirst=True
)
df_close.loc[:, "IssueCreatedAt"] = pd.to_datetime(df_close["IssueCreatedAt"], dayfirst=True, yearfirst=True)
df_close.loc[:, "IssueCreatedAt"] = df_close["IssueCreatedAt"].dt.strftime("%d-%m-%Y")
df_close.loc[:, "IssueClosedDate"] = df_close["IssueClosedDate"].dt.strftime("%Y-%m-%d")

# Convert string to pandas date time format for closed issues dataframe
df_close.loc[:, "IssueClosedDate"] = pd.to_datetime(df_close["IssueClosedDate"])
df_close.loc[:, "IssueCreatedAt"] = pd.to_datetime(df_close["IssueCreatedAt"])

# Add a column in Open issues dataframe of name bussinessdays to calculate number of days between IssueClosedDate and Issue creation date
df_close.loc[:, "days_to_KPI_target"] = business_days(df_close["IssueCreatedAt"], df_close["IssueClosedDate"])

# Filter Open Issues as per their KPI targets
def openIssuesFilter():
    df = df_open
    df.loc[
        (
            (df["bussinessDays"].between(7, 14))
            & (
                (df["Severity"] == "Major")
                | (df["Severity"] == "Critical")
                | (df["Severity"] == "Blocker")
            )
        ),
        "Target",
    ] = "about_to_violate"

    df.loc[((df["bussinessDays"].between(83, 90)) & (df["Severity"] == "Medium")), "Target",] = "about_to_violate"

    df.loc[((df["bussinessDays"].between(358, 365)) & (df["Severity"] == "Minor")), "Target",] = "about_to_violate"

    df.loc[
        (
            (df["bussinessDays"] > 14)
            & (
                (df["Severity"] == "Major")
                | (df["Severity"] == "Critical")
                | (df["Severity"] == "Blocker")
            )
        ),
        "Target",
    ] = "violated"

    df.loc[((df["bussinessDays"] > 90) & (df["Severity"] == "Medium")), "Target"] = "violated"
    df.loc[((df["bussinessDays"] > 365) & (df["Severity"] == "Minor")), "Target"] = "violated"

    df.loc[
        (
            (df["bussinessDays"] < 7)
            & (
                (df["Severity"] == "Major")
                | (df["Severity"] == "Critical")
                | (df["Severity"] == "Blocker")
            )
        ),
        "Target",
    ] = "normal"

    df.loc[((df["bussinessDays"] < 83) & (df["Severity"] == "Medium")), "Target"] = "normal"

    df.loc[((df["bussinessDays"] < 358) & (df["Severity"] == "Minor")), "Target"] = "normal"

    return df


# Filter Closed Issues as per their KPI targets
def closedIssuesFilter():
    df = df_close
    df.loc[
        (
            (df["days_to_KPI_target"] <= 14)
            & (
                (df["Severity"] == "Major")
                | (df["Severity"] == "Critical")
                | (df["Severity"] == "Blocker")
            )
        ),
        "Target",
    ] = "hit"

    df.loc[((df["days_to_KPI_target"] <= 90) & (df["Severity"] == "Medium")), "Target"] = "hit"

    df.loc[((df["days_to_KPI_target"] <= 365) & (df["Severity"] == "Minor")), "Target"] = "hit"

    df.loc[
        (
            (df["days_to_KPI_target"] > 14)
            & (
                (df["Severity"] == "Major")
                | (df["Severity"] == "Critical")
                | (df["Severity"] == "Blocker")
            )
        ),
        "Target",
    ] = "miss"

    df.loc[((df["days_to_KPI_target"] > 90) & (df["Severity"] == "Medium")), "Target"] = "miss"

    df.loc[((df["days_to_KPI_target"] > 365) & (df["Severity"] == "Minor")), "Target"] = "miss"

    return df


"""
KPI designing begins here
"""

# Open vs Closed Issues
def issuesTimeChart():
    count_issues = security_data.groupby(["IssueCreatedAt", "State"]).size()
    df = count_issues.to_frame(name="Count").reset_index()

    KPI = {
        "data": [
            go.Scatter(x=df[df["State"] == i]["IssueCreatedAt"], y=df[df["State"] == i]["Count"], name=i, mode="lines")
            for i in df.State.unique()
        ],
        "layout": {
            "title": "Open and Closed Issues",
            "xaxis": dict(
                # Sliding window for Graph
                rangeselector=dict(
                    buttons=list(
                        [
                            dict(count=1, label="1m", step="month", stepmode="backward"),
                            dict(count=3, label="3m", step="month", stepmode="backward"),
                            dict(count=6, label="6m", step="month", stepmode="backward"),
                            dict(count=1, label="YTD", step="year", stepmode="todate"),
                            dict(count=1, label="1y", step="year", stepmode="backward"),
                            dict(step="all"),
                        ]
                    )
                ),
                rangeslider=dict(visible=True),
                type="date",
                title="Issue Reported Date",
            ),
            "yaxis": {"title": "Number of Issues"},
            "hovermode": "closest",
            "height": 500,
        },
    }
    return KPI


# Open Issues with Assignee Name
def openIssuesWithAssignee():
    df = df_open.groupby(["AssigneeName", "Severity"]).size().reset_index(name="count")

    KPI = {
        "data": [
            go.Bar(
                x=df[df["Severity"] == i]["AssigneeName"],
                y=df[df["Severity"] == i]["count"],
                name=i,
                text=df[df["Severity"] == i]["count"],
                textposition="inside",
            )
            for i in df.Severity.unique()
        ],
        "layout": {
            "title": "Open Issues with Assignee Name",
            "xaxis": {"title": "Assignee Name"},
            "yaxis": {"title": "Number of Issues"},
            "hovermode": "closest",
            "barmode": "stack",
            "margin": dict(b=180),
            "height": 600,
        },
    }
    return KPI


# Highlight open issues about to violate KPI targets, has violated KPI targets and in KPI targets
def openCriticalIssues():
    df = openIssuesFilter()
    counts = {"normal": 0, "about_to_violate": 0, "violated": 0}
    counts_fill = df["Target"].value_counts().to_dict()
    counts.update(counts_fill)
    labels = [
        "Issues in KPI targets",
        "Issues about to violate KPI targets",
        "Issues have violated KPI targets",
    ]
    values = [counts["normal"], counts["about_to_violate"], counts["violated"]]

    data = [
        go.Pie(
            labels=labels,
            values=values,
            hole=0.4,
            marker={"colors": ["rgb(0, 204, 150)", "rgb(239, 85, 59)", "rgb(99, 110, 250)"]},
        )
    ]
    KPI = {
        "data": data,
        "layout": {"title": "Open Issues KPI Targets statistics", "hovermode": "closest",},
    }
    return KPI


# Highlight open issues as per their severity violating, within and missing KPI targets
def openIssuesSeverityKPITargets():
    df = openIssuesFilter()
    counts = {"normal": 0, "about_to_violate": 0, "violated": 0}
    counts_fill = df["Target"].value_counts().to_dict()
    counts.update(counts_fill)

    critical_within = df[(df["Target"] == "normal") & (df["Severity"] == "Critical")].shape[0]
    blocker_within = df[(df["Target"] == "normal") & (df["Severity"] == "Blocker")].shape[0]
    major_within = df[(df["Target"] == "normal") & (df["Severity"] == "Major")].shape[0]
    medium_within = df[(df["Target"] == "normal") & (df["Severity"] == "Medium")].shape[0]
    minor_within = df[(df["Target"] == "normal") & (df["Severity"] == "Minor")].shape[0]
    none_within = df[(df["Target"] == "normal") & (df["Severity"] == "Not Assigned")].shape[0]

    critical_miss = df[(df["Target"] == "violated") & (df["Severity"] == "Critical")].shape[0]
    blocker_miss = df[(df["Target"] == "violated") & (df["Severity"] == "Blocker")].shape[0]
    major_miss = df[(df["Target"] == "violated") & (df["Severity"] == "Major")].shape[0]
    medium_miss = df[(df["Target"] == "violated") & (df["Severity"] == "Medium")].shape[0]
    minor_miss = df[(df["Target"] == "violated") & (df["Severity"] == "Minor")].shape[0]
    none_miss = df[(df["Target"] == "violated") & (df["Severity"] == "Not Assigned")].shape[0]

    critical_about_to = df[(df["Target"] == "about_to_violate") & (df["Severity"] == "Critical")].shape[0]
    blocker_about_to = df[(df["Target"] == "about_to_violate") & (df["Severity"] == "Blocker")].shape[0]
    major_about_to = df[(df["Target"] == "about_to_violate") & (df["Severity"] == "Major")].shape[0]
    medium_about_to = df[(df["Target"] == "about_to_violate") & (df["Severity"] == "Medium")].shape[0]
    minor_about_to = df[(df["Target"] == "about_to_violate") & (df["Severity"] == "Minor")].shape[0]
    none_about_to = df[(df["Target"] == "about_to_violate") & (df["Severity"] == "Not Assigned")].shape[0]

    in_target = "Still in KPI targets ({})".format(counts["normal"])
    missed_target = "Violated KPI targets ({})".format(counts["violated"])
    about_to_violate_target = "About to violate KPI targets ({})".format(counts["about_to_violate"])

    parent = [
        in_target,
        in_target,
        in_target,
        in_target,
        in_target,
        in_target,
        missed_target,
        missed_target,
        missed_target,
        missed_target,
        missed_target,
        missed_target,
        about_to_violate_target,
        about_to_violate_target,
        about_to_violate_target,
        about_to_violate_target,
        about_to_violate_target,
        about_to_violate_target,
    ]
    categories = [
        "Critical ({})".format(critical_within),
        "Blocker ({})".format(blocker_within),
        "Major ({})".format(major_within),
        "Medium ({})".format(medium_within),
        "Minor ({})".format(minor_within),
        "Not Assigned ({})".format(none_within),
        "Critical ({})".format(critical_miss),
        "Blocker ({})".format(blocker_miss),
        "Major ({})".format(major_miss),
        "Medium ({})".format(medium_miss),
        "Minor ({})".format(minor_miss),
        "Not Assigned ({})".format(none_miss),
        "Critical ({})".format(critical_about_to),
        "Blocker ({})".format(blocker_about_to),
        "Major ({})".format(major_about_to),
        "Medium ({})".format(medium_about_to),
        "Minor ({})".format(minor_about_to),
        "Not Assigned ({})".format(none_about_to),
    ]

    values = [
        critical_within,
        blocker_within,
        major_within,
        medium_within,
        minor_within,
        none_within,
        critical_miss,
        blocker_miss,
        major_miss,
        medium_miss,
        minor_miss,
        none_miss,
        critical_about_to,
        blocker_about_to,
        major_about_to,
        medium_about_to,
        minor_about_to,
        none_about_to,
    ]

    df = pd.DataFrame(dict(parent=parent, categories=categories, values=values))
    fig = px.sunburst(
        df,
        path=["parent", "categories"],
        values="values",
        color_discrete_sequence=["rgb(99, 110, 250)", "rgb(0, 204, 150)", "rgb(239, 85, 59)",],
    )
    fig.update_layout(uniformtext=dict(minsize=10), margin=dict(t=10, l=10, r=10, b=10))
    return fig


# Highlight open issues about to violate KPI targets with assignee name
def openCriticalIssuesWithAssignee():
    df = openIssuesFilter()
    count_issues = df.groupby(["AssigneeName", "Target"]).size()
    df = count_issues.to_frame(name="Count").reset_index()

    KPI = {
        "data": [
            go.Bar(
                x=df[df["Target"] == "about_to_violate"]["AssigneeName"],
                y=df[df["Target"] == "about_to_violate"]["Count"],
                text=df[df["Target"] == "about_to_violate"]["Count"],
                textposition="inside",
                name="Issues about to violate KPI targets",
            ),
            go.Bar(
                x=df[df["Target"] == "violated"]["AssigneeName"],
                y=df[df["Target"] == "violated"]["Count"],
                text=df[df["Target"] == "violated"]["Count"],
                textposition="inside",
                name="Issues have violated KPI targets",
            ),
        ],
        "layout": {
            "title": "Open Issues violating KPI targets with Assignee Name",
            "xaxis": {"title": "Assignee Name"},
            "yaxis": {"title": "Number of Issues"},
            "hovermode": "closest",
            "barmode": "stack",
            "margin": dict(b=200),
            "height": 500,
        },
    }
    return KPI


# Highlight closed issues meeting and missing KPI targets
def closedIssuesKPITargets():
    df = closedIssuesFilter()
    counts = {"hit": 0, "miss": 0}
    counts_fill = df["Target"].value_counts().to_dict()
    counts.update(counts_fill)

    labels = ["Issues fixed in KPI targets", "Issues missing KPI targets"]
    values = [counts["hit"], counts["miss"]]

    data = [
        go.Pie(labels=labels, values=values, hole=0.4, marker={"colors": ["rgb(99, 110, 250)", "rgb(239, 85, 59)"]},)
    ]
    KPI = {
        "data": data,
        "layout": {"title": "Closed Issues missing and meeting KPI targets (%)", "hovermode": "closest",},
    }
    return KPI


# Highlight closed issues as per their severity meeting and missing KPI targets
def closedIssuesSeverityKPITargets():
    df = closedIssuesFilter()
    counts = {"hit": 0, "miss": 0}
    counts_fill = df["Target"].value_counts().to_dict()
    counts.update(counts_fill)

    critical_hit = df[(df["Target"] == "hit") & (df["Severity"] == "Critical")].shape[0]

    blocker_hit = df[(df["Target"] == "hit") & (df["Severity"] == "Blocker")].shape[0]
    major_hit = df[(df["Target"] == "hit") & (df["Severity"] == "Major")].shape[0]
    medium_hit = df[(df["Target"] == "hit") & (df["Severity"] == "Medium")].shape[0]
    minor_hit = df[(df["Target"] == "hit") & (df["Severity"] == "Minor")].shape[0]
    none_hit = df[(df["Target"] == "hit") & (df["Severity"] == "Not Assigned")].shape[0]

    critical_miss = df[(df["Target"] == "miss") & (df["Severity"] == "Critical")].shape[0]
    blocker_miss = df[(df["Target"] == "miss") & (df["Severity"] == "Blocker")].shape[0]
    major_miss = df[(df["Target"] == "miss") & (df["Severity"] == "Major")].shape[0]
    medium_miss = df[(df["Target"] == "miss") & (df["Severity"] == "Medium")].shape[0]
    minor_miss = df[(df["Target"] == "miss") & (df["Severity"] == "Minor")].shape[0]
    none_miss = df[(df["Target"] == "miss") & (df["Severity"] == "Not Assigned")].shape[0]

    in_target = "Fixed in KPI targets ({})".format(counts["hit"])
    missed_target = "Missed KPI targets ({})".format(counts["miss"])

    parent = [
        in_target,
        in_target,
        in_target,
        in_target,
        in_target,
        in_target,
        missed_target,
        missed_target,
        missed_target,
        missed_target,
        missed_target,
        missed_target,
    ]
    categories = [
        "Critical ({})".format(critical_hit),
        "Blocker ({})".format(blocker_hit),
        "Major ({})".format(major_hit),
        "Medium ({})".format(medium_hit),
        "Minor ({})".format(minor_hit),
        "Not Assigned ({})".format(none_hit),
        "Critical ({})".format(critical_miss),
        "Blocker ({})".format(blocker_miss),
        "Major ({})".format(major_miss),
        "Medium ({})".format(medium_miss),
        "Minor ({})".format(minor_miss),
        "Not Assigned ({})".format(none_miss),
    ]

    values = [
        critical_hit,
        blocker_hit,
        major_hit,
        medium_hit,
        minor_hit,
        none_hit,
        critical_miss,
        blocker_miss,
        major_miss,
        medium_miss,
        minor_miss,
        none_miss,
    ]

    df = pd.DataFrame(dict(parent=parent, categories=categories, values=values))
    fig = px.sunburst(
        df,
        path=["parent", "categories"],
        values="values",
        color_discrete_sequence=["rgb(99, 110, 250)", "rgb(239, 85, 59)"],
    )
    fig.update_layout(uniformtext=dict(minsize=10), margin=dict(t=10, l=10, r=10, b=10))
    return fig


# Average Issue resolution time
def averageIssueResolutionTime():
    df = df_close
    avg_critical = df.loc[(df["Severity"] == "Critical", "days_to_KPI_target")].mean().round()
    avg_blocker = df.loc[(df["Severity"] == "Blocker", "days_to_KPI_target")].mean().round()
    avg_major = df.loc[(df["Severity"] == "Major", "days_to_KPI_target")].mean().round()
    avg_medium = df.loc[(df["Severity"] == "Medium", "days_to_KPI_target")].mean()
    avg_minor = df.loc[(df["Severity"] == "Minor", "days_to_KPI_target")].mean().round()
    avg_none = df.loc[(df["Severity"] == "Not Assigned", "days_to_KPI_target")].mean().round()
    total_average = (df["days_to_KPI_target"].sum() / df_close["Severity"].value_counts().sum()).round()

    labels = [
        "Critical",
        "Blocker",
        "Major",
        "Medium",
        "Minor",
        "Not Assigned",
        "Net average",
    ]
    values = [
        avg_critical,
        avg_blocker,
        avg_major,
        avg_medium,
        avg_minor,
        avg_none,
        total_average,
    ]

    data = [
        go.Bar(
            y=labels,
            x=values,
            orientation="h",
            text=values,
            textposition="inside",
            marker={
                "color": [
                    "rgb(99, 110, 250)",
                    "rgb(99, 110, 250)",
                    "rgb(99, 110, 250)",
                    "rgb(99, 110, 250)",
                    "rgb(99, 110, 250)",
                    "rgb(99, 110, 250)",
                    "rgb(222, 51, 79)",
                ]
            },
        )
    ]

    KPI = {
        "data": data,
        "layout": {
            "title": "Average Issues Resolution Time",
            "yaxis": {"title": "Issues Severity"},
            "xaxis": {"title": "Number of Days"},
            "hovermode": "closest",
            "margin": dict(l=100,),
        },
    }
    return KPI


# Total Open Critical/High/Medium/Low Issues at any point of time
def totalOpenIssues():
    df = df_open
    # Filter: Show only 3 months old data
    last_3months = pd.to_datetime((datetime.today() - timedelta(days=92)))
    df.loc[:, "IssueCreatedAt"] = pd.to_datetime(df["IssueCreatedAt"])
    df = df.loc[(df["IssueCreatedAt"] >= last_3months)]

    df = pd.crosstab(df["IssueCreatedAt"], df["Severity"])
    data = []
    for x in df.columns:
        data.append(go.Bar(name=str(x), x=df.index, y=df[x], text=df[x], textposition="outside",))

    KPI = {
        "data": data,
        "layout": dict(
            title="Total Open Issues as per Severity",
            xaxis=dict(
                # Sliding window for Graph
                rangeselector=dict(
                    buttons=list(
                        [
                            dict(count=15, label="15d", step="day", stepmode="backward"),
                            dict(count=1, label="1m", step="month", stepmode="backward"),
                            dict(count=3, label="3m", step="month", stepmode="backward"),
                        ]
                    )
                ),
                type="date",
                title="Issue Reported On",
            ),
            yaxis={"title": "Number of Issues"},
            barmode="stack",
            hovermode="closest",
        ),
    }
    return KPI
