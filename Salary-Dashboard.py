import streamlit as st
import pandas as pd
from datetime import datetime
import os
import itertools

# configure main page; must be first streamlit command

st.set_page_config(
    page_title="EMU Salary Dashboard",
    initial_sidebar_state="expanded",
    menu_items={
        'Report a bug': "mailto:jrodri30@emich.edu"
        # 'About': "# This is a header. This is an _extremely_ cool app!"
    }
)

# file_directory = "F:\Python-2\EMU-AAUP\Salary-Dashboard" # to run locally
file_directory = "."  # relative path for local development
file_pattern = 'FY*-Salaries.xlsx'  # relative path for Streamlit sharing

@st.cache_data
def load_data():
    data_frames = []
    current_date = datetime.now()

    for file_name in os.listdir(file_directory):

        if file_name.startswith('FY') and file_name.endswith('-Salaries.xlsx'):
            fiscal_year = file_name[2:4]  # Extract the fiscal year from the filename (e.g., FY24 -> 2024)

            try:
                fiscal_year_int = int(fiscal_year)  # Convert '24' to 2024, for example
            except ValueError:
                # If conversion to integer fails, skip this file and optionally log an error or warning
                print(f"Warning: Could not parse year from filename '{file_name}'. Skipping.")
                continue

            file_path = os.path.join(file_directory, file_name)
            df = pd.read_excel(file_path)
            df['FISCAL_YEAR'] = fiscal_year_int
            df['HIRE_DATE'] = pd.to_datetime(df['HIRE_DATE'])
            df['RANK_DATE'] = pd.to_datetime(df['RANK_DATE'])
            df['APPT_STATUS'] = df['APPT'].map({100: 'Full Time', 50: 'VPR'})
            df['UNION_STATUS'] = df['MEM1'].map({'Member': 'Member', 'Non-Member': 'Non-Member'})

            df.loc[df['COLLEGE'] == 'COET', 'COLLEGE'] = 'GACET'  # change college name to GACET

            # Time employed and time in rank calculations
            end_of_academic_year = pd.to_datetime(f'20{fiscal_year}-06-30')
            if end_of_academic_year < current_date:
                df['TIME_EMPLOYED'] = (end_of_academic_year - df['HIRE_DATE']).dt.days / 365.25
                df['TIME_IN_RANK'] = (end_of_academic_year - df['RANK_DATE']).dt.days / 365.25
            else:
                df['TIME_EMPLOYED'] = (current_date - df['HIRE_DATE']).dt.days / 365.25
                df['TIME_IN_RANK'] = (current_date - df['RANK_DATE']).dt.days / 365.25

            data_frames.append(df)
            # df = df.copy()
            # departments_to_remove = ["General Education", "Honors College", "Graduate School"]
            # data_2024 = data_2024[~data_2024['DEPARTMENT'].isin(departments_to_remove)]

    if data_frames:
        data = pd.concat(data_frames, ignore_index=True)
    else:
        st.error(f"No files found matching the pattern '{file_pattern}'. Please upload a valid file.")
        data = pd.DataFrame()

    return data

data = load_data()

# st.write(data.head())

department_merger_years = {
    'CIS': 2023,
    'DET': 2023
    # Add more departments and their merger years as needed
    # Year listed is the first year the department was merged or reorganized e.g., CIS 2022 is last year of
    # available data for CIS before it was merged
}

# Streamlit app
def main():
    st.markdown(
        """
        <style>
        .reportview-container .main .block-container {
            font-family: 'Tahoma', sans-serif;
        }
        h1 {
            color: darkblue;
            font-size: 40px;
        }
        .stContainer {
            margin-bottom: 40px;
            padding-bottom: 20px;
            border-bottom: 2px solid #ccc;
        }
        .sidebar .sidebar-content {
            font-family: 'Tahoma', sans-serif;
        }
        span[data-baseweb="tag"] {
          background-color: darkblue !important; # changes color of filter tags
          font-family: 'Tahoma', sans-serif;
        }
        div[data-baseweb="select"]>div { # changes border of color filter box 
          background-color:#fff;
          font-family: 'Tahoma', sans-serif;
          border-color: darkblue;
          width: 75%;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

        # The title of the dashboard, which will now be styled with the above CSS
    st.title("EMU Faculty Salary Dashboard")

    # sidebar filters
    st.sidebar.title("Filters")
    st.sidebar.markdown("Filter the data by selecting one or more items from each of the lists below:")

    st.sidebar.markdown("**Select Academic Year(s):**")
    # st.sidebar.markdown("Filter the data by selecting one or more academic years from the list.")
    sorted_years = sorted(data['YEAR'].unique())
    years = st.sidebar.multiselect("", sorted_years)

    st.sidebar.markdown("**Select Department(s):**")
    # st.sidebar.markdown("Filter the data by selecting one or more departments from the list.")
    sorted_departments = sorted(data['DEPARTMENT'].dropna().unique())
    selected_departments = st.sidebar.multiselect("", sorted_departments, key='departments')
    departments = selected_departments[:5]

    if len(selected_departments) > 5:
        st.sidebar.warning('Only the first 5 tables of the selected departments will be displayed.')

    st.sidebar.markdown("**Select College(s):**")
    # st.sidebar.markdown("Filter the data by selecting one or more colleges from the list.")
    sorted_colleges = sorted(data['COLLEGE'].dropna().unique())
    colleges = st.sidebar.multiselect("", sorted_colleges)

    st.sidebar.markdown("**Select Rank(s):**")
    # st.sidebar.markdown("Filter the data by selecting one or more faculty ranks from the list.")
    ranks = st.sidebar.multiselect("", data['RANK'].dropna().unique())

    st.sidebar.markdown("**Select Appointment Status:**")
    # st.sidebar.markdown("Filter the data by selecting one or more appointment statuses from the list.")
    appt_status = st.sidebar.multiselect("", data['APPT_STATUS'].dropna().unique())

    st.sidebar.markdown("**Select Union Membership Status:**")
    # st.sidebar.markdown("Filter the data by selecting the union membership status.")
    union_status = st.sidebar.multiselect("", data['UNION_STATUS'].dropna().unique())

    # filter data based on user selection
    filtered_data = data.copy()
    if years:
        filtered_data = filtered_data[filtered_data['YEAR'].isin(years)]
    if departments:
        filtered_data = filtered_data[filtered_data['DEPARTMENT'].isin(departments)]
    if colleges:
        filtered_data = filtered_data[filtered_data['COLLEGE'].isin(colleges)]
    if ranks:
        filtered_data = filtered_data[filtered_data['RANK'].isin(ranks)]
    if appt_status:
        filtered_data = filtered_data[filtered_data['APPT_STATUS'].isin(appt_status)]
    if union_status:
        filtered_data = filtered_data[filtered_data['UNION_STATUS'].isin(union_status)]

    # display instructions for using the table
    st.subheader('')
    st.markdown(
        f"<p style='font-family:Tahoma;'>{'1. Use the filters in the menu to the left to view the selected aggregated data.'}</p>",
        unsafe_allow_html=True)
    st.markdown(
        f"<p style='font-family:Tahoma;'>{'2. The table below will update automatically based on your selections.'}</p>",
        unsafe_allow_html=True)
    # st.text('2. The table below will update automatically based on your selections.')
    st.write("<br>", unsafe_allow_html=True)

    # display aggregated statistics if multiple years are selected
    # ensure no table appears until years is selected.
    # orders the tables in ascending order and limits the number of tables to 3

    if years:
        # Take the first three years as selected by the user
        years_to_display = years[:3]

        # Sort the list of years to display the tables in ascending order
        years_to_display_sorted = sorted(years_to_display)

        for year in years_to_display_sorted:
            year_int = int(str(year)[-2:])  # Convert to two-digit year if necessary
            year_data = filtered_data[filtered_data['FISCAL_YEAR'] == year_int]

            with st.container():

                if colleges:
                    for college in sorted(colleges):
                        college_data = year_data[year_data['COLLEGE'] == college]
                        st.subheader(f'{year} Salary Table - {college}')
                        display_table(college_data, year=year, department=None)
                        st.write("<br>", unsafe_allow_html=True) # Add space between tables
                        st.markdown(
                            f"<p style='font-family:Tahoma;'>{f'This table displays the {year} data at the college-level for the selected filters.'}</p>",
                            unsafe_allow_html=True)
                        #st.text(f'This table displays the {year} data at the college-level for the selected filters.')

                elif departments:
                    for department in sorted(departments):
                        department_data = year_data[year_data['DEPARTMENT'] == department]
                        st.subheader(f'{year} Salary Table - {department}')
                        display_table(department_data, year=year, department=department)
                        st.write("<br>", unsafe_allow_html=True)
                        st.markdown(
                            f"<p style='font-family:Tahoma;'>{f'This table displays the {year} data at the department-level for the selected filters.'}</p>",
                            unsafe_allow_html=True)
                        #st.text(f'This table displays the {year} data at the department-level for the selected filters.')

                else:
                    if not year_data.empty:
                        st.subheader(f'{year} Salary Table - University')
                        display_table(year_data, year=year)
                        st.write("<br>", unsafe_allow_html=True)
                        st.markdown(
                            f"<p style='font-family:Tahoma;'>{f'This table displays the {year} data at the university-level for the selected filters.'}</p>",
                            unsafe_allow_html=True)
                        #st.text(f'This table displays the {year} data at the university-level for the selected filters.')
                    else:
                        st.warning(f'Data is not yet available for {year}.')

            st.markdown("""
                <hr style="border: 2px solid #00008B; border-radius: 2px; margin-top: 40px; margin-bottom: 40px;">
            """, unsafe_allow_html=True) # add the border separator between years

        # Display a warning if more than three years are selected
        if len(years) > 3:
            st.warning('Only the first 3 selected academic years are displayed.')

    else:
        st.info("Please select at least one academic year and any additional filters.")

    # display filter summary for the users below the table
    if not any([departments, colleges, ranks, appt_status, union_status, years]):
        filter_summary = ["No filter has been applied to the table."]
    else:
        filter_summary = ["The table(s) reflect the following selected filters:\n"]
        filter_count = 1
        if years:
            filter_summary.append(f"{filter_count}. Years: {', '.join(map(str,years))}")
            filter_count += 1
        if departments:
            filter_summary.append(f"{filter_count}. Departments: {', '.join(departments)}")
            filter_count += 1
        if colleges:
            filter_summary.append(f"{filter_count}. Colleges: {', '.join(colleges)}")
            filter_count += 1
        if ranks:
            filter_summary.append(f"{filter_count}. Ranks: {', '.join(ranks)}")
            filter_count += 1
        if appt_status:
            filter_summary.append(f"{filter_count}. Appointment Status: {', '.join(appt_status)}")
            filter_count += 1
        if union_status:
            filter_count += 1
            filter_summary.append(f"{filter_count}. Union Membership Status: {', '.join(union_status)}")

    # Display the filter summary below the table
    st.write("\n".join(filter_summary))

# Function to display aggregated statistics in a table
def display_table(data, year, department=None):
    if not data.empty:
        agg_data = data.agg({
            'SALARY': ['mean', 'median', 'min', 'max'],
            'TIME_EMPLOYED': ['mean', 'median', 'min', 'max'],
            'TIME_IN_RANK': ['mean', 'median', 'min', 'max']
        })
        if agg_data.isnull().values.all():
            st.warning(f"Data is not yet available for {year}.")
        else:
            agg_data.columns = ['_'.join(col).strip() for col in agg_data.columns.values]
            agg_data = agg_data.T
            agg_data.index = ['Base Salary', 'Time Employed', 'Time in Rank']  # row variable names
            agg_data.columns = ['Average', 'Median', 'Minimum', 'Maximum']  # column variable names
            # For the 'Base Salary' row, format as USD currency
            format_dict = {'Average': "{0:,.2f}", 'Median': "{0:,.2f}", 'Minimum': "{0:,.2f}", 'Maximum': "{0:,.2f}"}
            agg_data_styled = agg_data.style.format(format_dict).set_table_styles([
                {'selector': 'th.col_heading.level0', 'props': [('font-size', '1.02em'), ('text-align', 'center'),
                                                                ('font-weight', 'normal'), ('font-family', 'Tahoma')]},
                {'selector': 'td', 'props': [('font-size', '1.0em'), ('color', 'black'), ('text-align', 'center'),
                                             ('font-family', 'Tahoma')]},
                {'selector': 'th.row_heading.level0', 'props': [('font-size', '1.02em'), ('text-align', 'left'),
                                                                ('font-weight', 'normal'), ('font-family', 'Tahoma')]},
                ], overwrite=False)
            agg_data_styled = agg_data_styled.format("${0:,.2f}", subset=pd.IndexSlice['Base Salary', :])

            st.markdown(agg_data_styled.to_html(), unsafe_allow_html=True)

            # st.table(agg_data_styled)

    else:
        if department and department in department_merger_years and year >= department_merger_years[department]:
            st.warning(f"{department} was merged or reorganized beginning AY {department_merger_years[department]}.")
        else:
            st.warning('Data is not yet available for the selected years.')

if __name__ == '__main__':
    main()





