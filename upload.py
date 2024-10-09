import streamlit as st
import pandas as pd
import io
import plotly.express as px
from datetime import datetime

# Set page configuration to enhance layout
st.set_page_config(page_title='Employee Details Tracker', layout='wide')
# Custom CSS for dark background
st.markdown(
    """
    <style>
    body {
        background-color: #2E2E2E;
        color: white;
    }
    .sidebar .sidebar-content {
        background-color: #2E2E2E;
    }
    .stButton>button {
        background-color: #4CAF50;
        color: white;
    }
    .stTextInput>div>div>input {
        background-color: #333333;
        color: white;
    }
    .stDataFrame {
        background-color: #333333;
        color: white;
    }
    </style>
    """,
    unsafe_allow_html=True
)
# Display the image above the title
st.image("https://comcast.github.io/security/uploads/2018/06/21/comcast_cyber_2019.png", use_column_width=True)

# Sidebar: File upload
st.sidebar.title('Upload File')
uploaded_file = st.sidebar.file_uploader("Upload an Excel file", type=['xlsx'])

# Sidebar: Option to add a new column
new_column_name = st.sidebar.text_input("Add a new column:")

if st.sidebar.button("Add Column"):
    if new_column_name and new_column_name not in st.session_state.df.columns:
        # Add new column with None values
        st.session_state.df[new_column_name] = None  
        st.sidebar.success(f"New column '{new_column_name}' added.")
    elif new_column_name in st.session_state.df.columns:
        st.sidebar.warning(f"Column '{new_column_name}' already exists.")
    else:
        st.sidebar.warning("Please enter a valid column name.")

# Initialize session state for the DataFrame if it doesn't exist
if 'df' not in st.session_state:
    st.session_state.df = None

# If a file is uploaded, load it into the session state
if uploaded_file is not None:
    if st.session_state.df is None:  # Load the DataFrame only the first time the file is uploaded
        st.session_state.df = pd.read_excel(uploaded_file)
        # Add an "Updated on" column if it doesn't exist
        if 'Updated on' not in st.session_state.df.columns:
            st.session_state.df['Updated on'] = None

# Check if the DataFrame is initialized
if st.session_state.df is not None:
    st.title('Employee Details Tracker - Cyber Product Development(CPD)')

    # Display the DataFrame with a wide layout for better visibility
    st.subheader("Current Employee Data")
    edited_df = st.data_editor(st.session_state.df, key="editable_table")

    # Update 'Updated on' timestamp when data is edited
    edited_df['Updated on'] = edited_df.apply(
        lambda row: datetime.now().strftime('%Y-%m-%d %H:%M:%S') if any(
            row[col] != st.session_state.df.at[row.name, col] for col in edited_df.columns if col != 'Updated on') 
        else row['Updated on'],
        axis=1
    )

    # Update the session state with the edited DataFrame
    st.session_state.df = edited_df

    # Filter for Team Manager
    if 'Team Manager' in edited_df.columns:
        # Create a unique list of team managers
        unique_managers = edited_df['Team Manager'].unique()
        selected_managers = st.multiselect(
            "Filter by Team Manager:",
            options=unique_managers,
            default=unique_managers.tolist()  # Default to all
        )

        # Filter the DataFrame based on selected managers
        if selected_managers:
            filtered_df = edited_df[edited_df['Team Manager'].isin(selected_managers)]
        else:
            filtered_df = edited_df  # No filter applied

        # Display the filtered DataFrame
        st.write("Filtered Data:")
        st.dataframe(filtered_df)

        # Count of employees by Team Manager in the filtered data
        manager_count = filtered_df['Team Manager'].value_counts().reset_index()
        manager_count.columns = ['Team Manager', 'Employee Count']

        # Create a bar chart using Plotly
        fig = px.bar(manager_count, x='Team Manager', y='Employee Count', 
                     title='Employee Count by Team Manager',
                     color='Employee Count', color_continuous_scale=px.colors.sequential.Viridis)
        st.plotly_chart(fig)

    # Form to add a new row
    st.sidebar.subheader("Add a new row")
    new_row_data = {}
    for col in st.session_state.df.columns:
        if col != 'Updated on':
            new_row_data[col] = st.sidebar.text_input(f"Enter {col}")

    if st.sidebar.button("Add Row"):
        new_row_data['Updated on'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        new_row_df = pd.DataFrame([new_row_data])
        st.session_state.df = pd.concat([st.session_state.df, new_row_df], ignore_index=True)
        st.sidebar.success("New row added.")

    # Form to delete a row
    st.sidebar.subheader("Delete a row")
    row_indices = st.sidebar.multiselect("Select row indices to delete", st.session_state.df.index)
    if st.sidebar.button("Delete Row"):
        if row_indices:
            st.session_state.df = st.session_state.df.drop(row_indices).reset_index(drop=True)
            st.sidebar.success("Selected row(s) deleted.")
        else:
            st.sidebar.warning("Please select at least one row to delete.")

    # Save the edited data to Excel
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        edited_df.to_excel(writer, index=False)

    # Reset file pointer
    output.seek(0)

    # Provide an option to download the edited data
    st.download_button(
        label="Download Updated Data",
        data=output,
        file_name="updated_data.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # Create an organizational chart using a treemap
    if 'Team Manager' in st.session_state.df.columns and 'Name' in st.session_state.df.columns:
        fig = px.treemap(st.session_state.df, path=['Team Manager', 'Name'], 
                         title='Organizational Chart')
        st.plotly_chart(fig)

else:
    st.write("Please upload an Excel file to edit.")
