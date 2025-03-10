import pandas as pd
from pandas.api.types import is_string_dtype
from utils import load_data, impute_day01, is_null_or_empty,is_null_or_empty2,is_null_or_empty_numeric, pass_check, fail_check, lacks_any, dtc_dupl_early, missing_month, convert_date, format_dates
import os
import plotly.express as px
from dash import dcc
from datetime import datetime
def subject_timeline(data_path):
    data = load_data(data_path, 'se')
    data['SESTDTC'] = pd.to_datetime(data['SESTDTC'], errors='coerce')  # Convert, setting invalid entries to NaT
    data['SEENDTC'] = pd.to_datetime(data['SEENDTC'], errors='coerce')

    # Fill missing times for SESTDTC and SEENDTC if necessary (optional)
    # Example: Replace missing SESTDTC/SEENDTC with SESTDTC/SEENDTC at 00:00 (start of the day)
    #data['SESTDTC'] = data['SESTDTC'].fillna(pd.Timestamp.min)
    #data['SEENDTC'] = data['SEENDTC'].fillna(pd.Timestamp.min)

    # Gantt chart
    fig = px.timeline(data, x_start='SESTDTC', x_end='SEENDTC', y='USUBJID', color='EPOCH', title='Subject Progression Timeline')
    fig.update_xaxes(title='Date')
    fig.update_yaxes(title='Subjects')
    return [dcc.Graph(figure=fig)]
def subject_time_spent(data_path):
    data = load_data(data_path, 'se')
    data['SESTDTC'] = pd.to_datetime(data['SESTDTC'], errors='coerce')  # Handle invalid strings with 'coerce'
    data['SEENDTC'] = pd.to_datetime(data['SEENDTC'], errors='coerce')

    # Verify the conversion
    #print(data.dtypes)  # Should show datetime64[ns] for SESTDTC and SEENDTC

    # Today's date for handling missing SEENDTC
    today = pd.Timestamp(datetime.now())

    # Calculate duration with handling for missing values
    data['Duration'] = data.apply(
        lambda row: (row['SEENDTC'] - row['SESTDTC']).days if pd.notnull(row['SEENDTC']) and pd.notnull(row['SESTDTC']) else
        (today - row['SESTDTC']).days if pd.notnull(row['SESTDTC']) else
        None,
        axis=1
    )

    fig = px.histogram(data, x='Duration', color='EPOCH', title='Time Spent in Study Epochs', nbins=10)
    fig.update_xaxes(title='Duration (Days)')
    fig.update_yaxes(title='Frequency')
    return [dcc.Graph(figure=fig)]
def subject_duration(data_path):

    data = load_data(data_path, 'se')
    
    # Convert to datetime and handle invalid strings with 'coerce'
    data['SESTDTC'] = pd.to_datetime(data['SESTDTC'], errors='coerce')
    data['SEENDTC'] = pd.to_datetime(data['SEENDTC'], errors='coerce')

    # Today's date for handling missing SEENDTC
    today = pd.Timestamp(datetime.now())

    # Calculate duration with handling for missing values
    data['Duration'] = data.apply(
        lambda row: (row['SEENDTC'] - row['SESTDTC']).days if pd.notnull(row['SEENDTC']) and pd.notnull(row['SESTDTC']) else
        (today - row['SESTDTC']).days if pd.notnull(row['SESTDTC']) else
        None,
        axis=1
    )

    # Heat Map Data
    heatmap_data = data.pivot(index='USUBJID', columns='EPOCH', values='Duration')

    # Heat Map
    fig = px.imshow(
        heatmap_data,
        text_auto=True,
        title='Duration of Study Epochs',
        color_continuous_scale='Viridis'
    )

    # Update layout for better sizing
    fig.update_layout(
        autosize=True,
        height=600,  # Adjust the height
        width=1000,  # Adjust the width
        margin=dict(l=80, r=80, t=80, b=80),  # Adjust margins
        title_x=0.5  # Center the title
    )

    fig.update_xaxes(title='Epochs')
    fig.update_yaxes(title='Subjects')

    # Return the figure wrapped in Dash Core Components Graph
    return [dcc.Graph(figure=fig, style={'width': '100%'})]
def study_elements(data_path):

    data = load_data(data_path, 'se')
    data['SESTDTC'] = pd.to_datetime(data['SESTDTC'], errors='coerce')
    data['SEENDTC'] = pd.to_datetime(data['SEENDTC'], errors='coerce')

    # Today's date for handling missing SEENDTC
    today = pd.Timestamp(datetime.now())

    # Calculate duration with handling for missing values
    data['Duration'] = data.apply(
        lambda row: (row['SEENDTC'] - row['SESTDTC']).days if pd.notnull(row['SEENDTC']) and pd.notnull(row['SESTDTC']) else
        (today - row['SESTDTC']).days if pd.notnull(row['SESTDTC']) else
        None,
        axis=1
    )

    # Box Plot
    fig = px.box(data, x='EPOCH', y='Duration', title='Duration of Study Elements')
    fig.update_xaxes(title='Study Element')
    fig.update_yaxes(title='Duration (Days)')
    return [dcc.Graph(figure=fig)]