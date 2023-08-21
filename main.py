"""
Created on Wed Aug 16 18:07:39 2023

@author: Yehuda Yungstein
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import requests
import openpyxl


# Load the CSV data from Google Drive
@st.cache_data
def read_data_from_drive(url):
    """
    Downloads a file from the provided Google Drive URL and processes the data.
    
    Inputs:
        - url (str): The URL of the Google Drive file to download.
        
    Outputs:
        - data: Processed pandas DataFrame containing the data.
    """
    # Find the ID of the file from the URL
    file_id = url.split('/')[-2]
    dwn_url = 'https://drive.google.com/uc?id=' + file_id
    
    # Read the file into a DataFrame
    data = pd.read_csv(dwn_url)
    
    # Convert the date column to datetime
    data['TIMESTAMP'] = pd.to_datetime(data['TIMESTAMP'])
    
    # Convert temperature to Celsius
    data['air_temperature'] = data['air_temperature'] - 273.15

    # Specify the start date
    start_date = pd.to_datetime('2023-05-18')

    # Filter the DataFrame starting from the specified date
    data = data[data['TIMESTAMP'] >= start_date]

    # Clac G from Energy Balance
    data['G'] = data['NET_Avg']-data['H']- data['LE']
    
    return data
 

# Load data from drive
url =  st.secrets["URL"]
data = read_data_from_drive(url)

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
st.title('Hula Lake Eddy Covariance Station Data Viewer')
st.write("This application displays data from the Eddy Covariance measuring station, located in the Hula lake vegetation island, Israel. The data is updated once a week. You can use this application to view, control, and visualize the data.")
st.markdown("""
**Developed by:** Yehuda Yungstein

*The Monitoring and Modeling Vegetation Systems* lab, The Hebrew University, Israel.


""")

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
grouped_columns = ['NET_Avg', 'H', 'LE','G']
temp_columns = ['air_temperature', 'Temp_Surface_Avg', 'Temp_Deep_Avg']
co2_col = ['co2_flux']

remaining_columns = [col for col in color_palette.keys() if col not in grouped_columns and col not in temp_columns and col not in co2_col]

# create sub-data with energy balance columns
sub_data = data[grouped_columns]
sub_data.columns = ['Rn', 'H', 'LE', 'G']
sub_data['TIMESTAMP'] = data['TIMESTAMP'].values

# Grouped columns plot
grouped_fig = px.line(sub_data, x="TIMESTAMP", y=sub_data.columns,
                  hover_data={"TIMESTAMP": "|%B %d, %Y"},
                  color_discrete_sequence=['#ffb703','#edf2f4','#219ebc','#ef233c'],
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
co2_fig.update_layout(yaxis_title=r'umol/(m^2*sec)')
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

# Read NDVI file from drive an Plot NDVI Time Series

# Find the ID of the file from the URL
dwn_url = 'https://docs.google.com/spreadsheets/d/1WTrp7f2PXoEUyRGc2t4geVufzpCja8gH/edit?usp=drive_link&ouid=102952062029422280975&rtpof=true&sd=true'
reconstructed_url='https://drive.google.com/uc?id=' + dwn_url.split('/')[-2]

# Read the file into a DataFrame
df_ndvi = pd.read_excel(reconstructed_url)

# Convert column to dtetime
df_ndvi['C0/date'] = pd.to_datetime(df_ndvi['C0/date'])
# Calculate the mean and standard deviation
mean = df_ndvi['C0/mean']
std = df_ndvi['C0/stDev']

# Create the plot
ndvi_fig = go.Figure()

# Add the mean line
ndvi_fig.add_trace(
    go.Scatter(
        x=df_ndvi['C0/date'],
        y=mean,
        mode='lines',
        line=dict(color='green', width=2),
        name='Mean'
    )
)

# Add the standard deviation area
ndvi_fig.add_trace(
    go.Scatter(
        x=df_ndvi['C0/date'],
        y=mean + std,
        mode='lines',
        line=dict(color='rgba(0, 255, 0, 0.2)', width=0),
        fillcolor='rgba(0, 255, 0, 0.2)',
        fill='tonexty',
        name='+1 Std Dev'
    )
)

ndvi_fig.add_trace(
    go.Scatter(
        x=df_ndvi['C0/date'],
        y=mean - std,
        mode='lines',
        line=dict(color='rgba(0, 255, 0, 0.2)', width=0),
        fillcolor='rgba(0, 255, 0, 0.2)',
        fill='tonexty',
        name='-1 Std Dev'
    )
)

ndvi_fig.update_layout(
    title='NDVI Mean and STD ',
    xaxis_title='Date',
    yaxis_title='Value'
)
# plot the NDVI
st.plotly_chart(ndvi_fig)
