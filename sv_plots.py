import pandas as pd
import plotly.express as px
from dash import dcc


df = load_data(data_path, 'sv')
# 1. Subject Compliance by Visit (Bar Chart)
def subject_compliance_plot(data):
    compliance = data.groupby("VISIT")["SUBJID"].nunique().reset_index()
    compliance.columns = ["Visit", "Number of Subjects"]

    fig = px.bar(
        compliance,
        x="Visit",
        y="Number of Subjects",
        title="Subject Compliance by Visit",
        labels={"Visit": "Visit", "Number of Subjects": "Number of Subjects"},
        text="Number of Subjects"
    )
    return dcc.Graph(figure=fig)

# 2. Visit Timing Distribution (Box Plot)
def visit_timing_distribution_plot(data):
    fig = px.box(
        data,
        x="VISIT",
        y="VISITDATE",
        title="Visit Timing Distribution",
        labels={"VISIT": "Visit", "VISITDATE": "Visit Date"},
    )
    return dcc.Graph(figure=fig)

# 3. Visit Sequence for Each Subject (Line Plot)
def visit_sequence_plot(data):
    fig = px.line(
        data,
        x="VISITDATE",
        y="VISIT",
        color="SUBJID",
        title="Visit Sequence for Each Subject",
        labels={"VISITDATE": "Visit Date", "VISIT": "Visit", "SUBJID": "Subject ID"},
        markers=True
    )
    return dcc.Graph(figure=fig)

# 4. Cumulative Visit Completion Over Time (Line Plot)
def cumulative_visit_completion_plot(data):
    data['Cumulative_Visits'] = data.groupby("VISITDATE")["SUBJID"].transform('count').cumsum()

    fig = px.line(
        data,
        x="VISITDATE",
        y="Cumulative_Visits",
        title="Cumulative Visit Completion Over Time",
        labels={"VISITDATE": "Visit Date", "Cumulative_Visits": "Cumulative Visits"}
    )
    return dcc.Graph(figure=fig)

# 5. Subject Dropout Analysis (Stacked Bar Chart)
def subject_dropout_analysis_plot(data):
    dropout = data.groupby(["VISIT", "DROPOUT_FLAG"])["SUBJID"].count().reset_index()
    dropout.columns = ["Visit", "Dropout Status", "Number of Subjects"]

    fig = px.bar(
        dropout,
        x="Visit",
        y="Number of Subjects",
        color="Dropout Status",
        title="Dropout Analysis by Visit",
        labels={"Visit": "Visit", "Number of Subjects": "Number of Subjects", "Dropout Status": "Status"},
    )
    return dcc.Graph(figure=fig)
