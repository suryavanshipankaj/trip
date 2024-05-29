import streamlit as st
import pandas as pd
import io

# Initialize session state variables if not already present
if 'trips' not in st.session_state:
    st.session_state.trips = {}

if 'current_trip' not in st.session_state:
    st.session_state.current_trip = None

# Function to add a new trip
def add_trip(trip_name):
    if trip_name and trip_name not in st.session_state.trips:
        st.session_state.trips[trip_name] = {'members': [], 'expenses': [], 'total_expense': 0.0}

# Function to switch to a selected trip
def switch_trip(trip_name):
    st.session_state.current_trip = trip_name

# Function to delete a trip
def delete_trip(trip_name):
    if trip_name in st.session_state.trips:
        del st.session_state.trips[trip_name]
        if st.session_state.current_trip == trip_name:
            st.session_state.current_trip = None

# Function to add a member to the current trip
def add_member(trip_name, member_name):
    if trip_name in st.session_state.trips and member_name:
        st.session_state.trips[trip_name]['members'].append(member_name)

# Function to add an expense to the current trip
def add_expense(trip_name, member, description, amount):
    if trip_name in st.session_state.trips:
        trip = st.session_state.trips[trip_name]
        trip['expenses'].append({"member": member, "description": description, "amount": amount})
        trip['total_expense'] += amount

# Function to calculate individual shares for the current trip
def calculate_shares(trip_name):
    if trip_name in st.session_state.trips:
        trip = st.session_state.trips[trip_name]
        num_members = len(trip['members'])
        if num_members == 0:
            return {}
        share_per_member = trip['total_expense'] / num_members
        member_shares = {member: share_per_member for member in trip['members']}
        return member_shares
    return {}

# Function to calculate how much each member needs to give or receive
def calculate_give_receive(trip_name):
    if trip_name in st.session_state.trips:
        trip = st.session_state.trips[trip_name]
        shares = calculate_shares(trip_name)
        member_expenses = {member: 0.0 for member in trip['members']}
        
        for expense in trip['expenses']:
            member_expenses[expense['member']] += expense['amount']
        
        give_receive = {member: member_expenses[member] - shares[member] for member in trip['members']}
        return give_receive
    return {}

# Function to export expenses to Excel
def export_expenses_to_excel(expenses, shares, give_receive):
    output = io.BytesIO()
    expenses_df = pd.DataFrame(expenses)
    shares_df = pd.DataFrame(list(shares.items()), columns=["Member", "Share"])
    give_receive_df = pd.DataFrame(list(give_receive.items()), columns=["Member", "Amount"])
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        expenses_df.to_excel(writer, index=False, sheet_name='Expenses')
        shares_df.to_excel(writer, index=False, sheet_name='Shares')
        give_receive_df.to_excel(writer, index=False, sheet_name='Give_Receive')
    processed_data = output.getvalue()
    return processed_data

# Streamlit app layout
st.title("Expense Management for Group")

st.sidebar.header("Manage Trips")
trip_name = st.sidebar.text_input("Trip name")
if st.sidebar.button("Add Trip") and trip_name:
    add_trip(trip_name)

if st.sidebar.button("Delete Selected Trip"):
    delete_trip(st.session_state.current_trip)

if st.session_state.trips:
    selected_trip = st.sidebar.selectbox("Select Trip", st.session_state.trips.keys(), index=list(st.session_state.trips.keys()).index(st.session_state.current_trip) if st.session_state.current_trip else 0)
    switch_trip(selected_trip)
else:
    selected_trip = None

if selected_trip:
    st.sidebar.header("Add Member to Trip")
    new_member = st.sidebar.text_input("Member name")
    if st.sidebar.button("Add Member") and new_member:
        add_member(selected_trip, new_member)

    st.sidebar.header("Add Expense to Trip")
    selected_member = st.sidebar.selectbox("Select Member", st.session_state.trips[selected_trip]['members'])
    expense_description = st.sidebar.text_input("Expense Description")
    expense_amount = st.sidebar.number_input("Expense Amount", min_value=0.0, format="%.2f")
    if st.sidebar.button("Add Expense"):
        if selected_member and expense_description and expense_amount > 0:
            add_expense(selected_trip, selected_member, expense_description, expense_amount)
        else:
            st.sidebar.error("Please fill all fields with valid data.")

    st.header(f"Trip: {selected_trip}")

    st.subheader("Members")
    st.write(st.session_state.trips[selected_trip]['members'])

    st.subheader("Expenses")
    expenses_df = pd.DataFrame(st.session_state.trips[selected_trip]['expenses'])
    if not expenses_df.empty:
        st.write(expenses_df)
    else:
        st.write("No expenses added yet.")

    st.subheader("Total Expense")
    st.write(f"Total Expense: ₹{st.session_state.trips[selected_trip]['total_expense']:.2f}")

    st.subheader("Individual Shares")
    shares = calculate_shares(selected_trip)
    if shares:
        shares_df = pd.DataFrame(list(shares.items()), columns=["Member", "Share"])
        st.write(shares_df)
    else:
        st.write("No members added yet.")

    st.subheader("Give or Receive Amounts")
    give_receive = calculate_give_receive(selected_trip)
    if give_receive:
        give_receive_df = pd.DataFrame(list(give_receive.items()), columns=["Member", "Amount"])
        st.write(give_receive_df)
    else:
        st.write("No members added yet.")

    # Export button
    if st.button("Export Expenses to Excel"):
        if st.session_state.trips[selected_trip]['expenses']:
            excel_data = export_expenses_to_excel(st.session_state.trips[selected_trip]['expenses'], shares, give_receive)
            st.download_button(label="Download Excel File",
                               data=excel_data,
                               file_name=f'{selected_trip}_expenses_and_shares.xlsx',
                               mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        else:
            st.error("No expenses to export.")
else:
    st.write("Please create or select a trip.")

