# -*- coding: utf-8 -*-
"""
Created on Wed Aug 16 18:07:39 2023

@author: User
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import requests


# Load the CSV data from Google Drive
@st.cache_data
def download_file_from_drive(file_id, destination_path):
  '''
    Downloads a file from Google Drive using the provided file ID and saves it to the specified destination path.
    Inputs:
        - file_id (str): The ID of the file to download from Google Drive.
        - destination_path (str): The path where the downloaded file will be saved.
    Process:
        - Constructs the download URL using the file ID.
        - Sends a GET request to the URL to download the file.
        - Reads and cleans the data from the downloaded file using pandas.
    Output:
        - data: pandas dataframe.
  '''
  url = f"https://docs.google.com/spreadsheets/d/1gs61UphojSzk69jGkWHEGMvBp-WTq9JG3kJGdsA9Oqs/edit#gid={file_id}"
  response = requests.get(url)

  if response.status_code == 200:
      with open(destination_path, "wb") as file:
          file.write(response.content)
      print("File downloaded successfully.")
  else:
      print("Failed to download file.")
  # read and clean the data
  data = pd.read_csv("Merged-licor-loggernet-30min.csv")
  data['TIMESTAMP'] = pd.to_datetime(data['TIMESTAMP'])  # Convert timestamp to datetime
  data['air_temperature'] = data['air_temperature']-273.15
  
  return data
  

# Load data from drive
file_id =  st.secrets["FILE_ID"]
destination_path = "Merged-licor-loggernet-30min.csv"
fit_model = download_file_from_drive(file_id, destination_path)

# Define the color palette and columns for the graphs
color_palette = {
    'Tau': '#f5f5f5',
    'ET': '#40e0d0',
    'RH_LoggerNet': '#ffff00',
    'wind_speed': '#6600ff',
    'P_rain_Tot': '#0000ff',
    'Soil_EC_Surface_Avg': '#ff7f50'
}

# Streamlit app layout
st.title('Hula Lake Environmental Data')


# Quality Check Button
with st.expander("Run Quality Check"):
    co2_signal_column = 'co2_signal_strength_7500_mean'
    values_to_check = data[co2_signal_column].head(10)  # Assuming you want to check the first 10 values
    average_value = values_to_check.mean()
    delta_label = 'CO2 Strenth Signal'
    text = ' '
    st.metric(label=text, value=delta_label, delta=average_value,)
    

# Quality Check Metrics (placed at the top within an expander)
with st.expander("Last Week Mean"):
    columns_to_check = ['RH_LoggerNet', 'P_rain_Tot', 'air_temperature', 'co2_flux', 'ET']
    last_week_data = data[(data['TIMESTAMP'] >= (datetime.now() - timedelta(weeks=1))) & (data['TIMESTAMP'] <= datetime.now())]
    prev_week_data = data[(data['TIMESTAMP'] >= (datetime.now() - timedelta(weeks=2))) & (data['TIMESTAMP'] <= (datetime.now() - timedelta(weeks=1)))]
    
    start_date = (datetime.now() - timedelta(weeks=1)).strftime('%d.%m')
    end_date = datetime.now().strftime('%d.%m')
    
    expander_title = f"Averages  {start_date}-{end_date}"
    st.subheader(expander_title)
    
    col1, col2, col3 = st.columns(3)
    
    # Define dict for labels
    labels_dict = {'RH_LoggerNet':'RH',
                   'P_rain_Tot': 'Total Rain',
                    'air_temperature':'Air Temperature',
                    'co2_flux':'CO$_{2}$ Flux',
                    'ET': "ET (mm)"
        }
    
for idx, column in enumerate(columns_to_check):
        last_week_avg = round(last_week_data[column].mean(), 2)
        prev_week_avg = round(prev_week_data[column].mean(), 2)
        delta_val = round(last_week_avg - prev_week_avg, 2)
        
        if idx < 2:
            with col1:
                st.metric(label=labels_dict[column], value=last_week_avg, delta=delta_val)
        elif 2 <= idx < 4:
            with col2:
                st.metric(label=labels_dict[column], value=last_week_avg, delta=delta_val)
        else:
            with col3:
                st.metric(label=labels_dict[column], value=last_week_avg, delta=delta_val)
   

    
    

# Display graphs for each selected column
st.header('Environmental Data Time Series')

# Columns to group in the same graph
grouped_columns = ['NET_Avg', 'H', 'LE']
temp_columns = ['air_temperature', 'Temp_Surface_Avg', 'Temp_Deep_Avg']
co2_col = ['co2_flux']

remaining_columns = [col for col in color_palette.keys() if col not in grouped_columns and col not in temp_columns and col not in co2_col]

# create sub-data with energy balance columns
sub_data = data[grouped_columns]
sub_data.columns = ['Rn', 'H', 'LE']
sub_data['TIMESTAMP'] = data['TIMESTAMP'].values

# Grouped columns plot
grouped_fig = px.line(sub_data, x="TIMESTAMP", y=sub_data.columns,
                  hover_data={"TIMESTAMP": "|%B %d, %Y"},
                  color_discrete_sequence=['#ffdd00','#8f00ff','#01befe'],
                  title='Time Series of Energy Balance')

grouped_fig.update_xaxes(rangeslider_visible=True)
grouped_fig.update_layout(yaxis_title='W/m^2')
st.plotly_chart(grouped_fig)


# create sub-data with temperature columns
temp_data = data[temp_columns]
# Convert temp to Celsius
temp_data['TIMESTAMP'] = data['TIMESTAMP'].values

# Grouped columns plot
temp_fig = px.line(temp_data, x="TIMESTAMP", y=temp_data.columns,
                  hover_data={"TIMESTAMP": "|%B %d, %Y"},
                  color_discrete_sequence=['#009fb7', '#fed766', '#fe4a49'],
                  title='Time Series of Temperature')

temp_fig.update_xaxes(rangeslider_visible=True)
st.plotly_chart(temp_fig)


# create sub-data with CO2 columns
co2_data = data[co2_col]
co2_data['TIMESTAMP'] = data['TIMESTAMP'].values

# co2 columns plot
co2_fig = px.area(co2_data, x="TIMESTAMP", y=co2_data.columns,
                  hover_data={"TIMESTAMP": "|%B %d, %Y"},
                  color_discrete_sequence=['#00ff00',],
                  title='Time Series of CO2 Flux')

co2_fig.update_xaxes(rangeslider_visible=True)
# Set y-axis limits (adjust the values as needed)
co2_fig.update_yaxes(range=[-70, 70])
st.plotly_chart(co2_fig)

# User selection for individual column
selected_column = st.selectbox("Select a column to display", remaining_columns)

# Display selected column graph
try:
    fig = px.line(data, x='TIMESTAMP', y=selected_column, title=f'Time Series {selected_column}')
    fig.update_xaxes(
        rangeslider_visible=True,
        rangeselector=dict(
            buttons=list([
                dict(count=2, label="2d", step="day", stepmode="backward"),
                dict(count=7, label="week", step="day", stepmode="backward"),
                dict(count=1, label="1month", step="month", stepmode="backward"),
                dict(count=3, label="3m", step="month", stepmode="backward"),
                dict(count=6, label="6m", step="month", stepmode="backward"),
                dict(count=1, label="1y", step="year", stepmode="backward"),
                dict(step="all")
            ])
        )
    )
    fig.update_traces(line=dict(color=color_palette[selected_column]), name=f'{selected_column} - Separate')
    st.plotly_chart(fig)
except KeyError:
    st.error(f"Column '{selected_column}' not found in the dataset.")
except Exception as e:
    st.error(f"An error occurred: {e}")
