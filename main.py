import streamlit as st
from auth import login_signup
from onboarding import onboarding_screen
from firebase_admin import firestore
import firebase_admin
from firebase_admin import credentials
import pyrebase
import json
from datetime import datetime,timedelta,time
import plotly.express as px

import pandas as pd
from shared import db, auth, firebase
from budget_setup import budget_setup
from finance_chatbot import process_query_with_gemini

# Page configuration
st.set_page_config(
    page_title="Smart Budget App",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply custom styling
def apply_vibrant_styles():
    st.markdown("""
    <style>
        /* Color Palette */
        :root {
            --primary: #4361EE;
            --secondary: #3ABEFF;
            --accent: #FF5E78;
            --success: #06D6A0;
            --warning: #FFD166;
            --dark: #2B2D42;
            --light: #F8F9FA;
            --gradient: linear-gradient(90deg, #4361EE, #3ABEFF);
        }
        
        /* Global styling */
        .main {
            background-color: var(--light);
            color: var(--dark);
            font-family: 'Segoe UI', Arial, sans-serif;
            padding: 1rem;
        }
        
        .main .block-container {
            max-width: 1200px;
            padding-top: 2rem;
            padding-bottom: 2rem;
        }
        
        /* Headers */
        h1, h2, h3 {
            color: var(--primary);
            font-weight: 600;
        }
        
        h1 {
            font-size: 2.5rem;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid var(--secondary);
            margin-bottom: 1.5rem;
        }
        
        /* Buttons */
        .stButton > button {
            background: var(--gradient);
            border: none;
            color: white;
            border-radius: 8px;
            padding: 0.5rem 1.5rem;
            transition: all 0.3s ease;
            font-weight: 500;
            box-shadow: 0 4px 10px rgba(67, 97, 238, 0.3);
        }
        
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 15px rgba(67, 97, 238, 0.4);
        }
        
        /* Forms */
        [data-testid="stForm"] {
            background-color: white;
            padding: 2rem;
            border-radius: 12px;
            box-shadow: 0 6px 18px rgba(0,0,0,0.08);
            border-top: 5px solid var(--accent);
            margin-bottom: 2rem;
        }
        
        /* Inputs */
        input[type="text"], input[type="number"], input[type="password"], textarea, select {
            border-radius: 6px !important;
            border-color: #e2e8f0 !important;
        }
        
        input[type="text"]:focus, input[type="number"]:focus, input[type="password"]:focus, textarea:focus, select:focus {
            border-color: var(--accent) !important;
            box-shadow: 0 0 0 3px rgba(255, 94, 120, 0.2) !important;
        }
        
        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
        }
        
        .stTabs [data-baseweb="tab"] {
            background-color: #f1f3f9;
            border-radius: 6px 6px 0 0;
            padding: 8px 16px;
            color: var(--dark);
        }
        
        .stTabs [aria-selected="true"] {
            background-color: var(--primary) !important;
            color: white !important;
        }
        
        /* Metrics */
        [data-testid="stMetric"] {
            background-color: white;
            border-radius: 10px;
            padding: 1rem;
            box-shadow: 0 4px 10px rgba(0,0,0,0.05);
            border-left: 4px solid var(--primary);
        }
        
        [data-testid="stMetricLabel"] {
            color: var(--dark);
            font-weight: 600;
        }
        
        [data-testid="stMetricValue"] {
            color: var(--primary);
            font-weight: 700;
        }
        
        [data-testid="stMetricDelta"] {
            color: var(--success);
        }
        
        /* Charts */
        [data-testid="stPlotlyChart"] {
            background-color: white;
            border-radius: 10px;
            padding: 1rem;
            box-shadow: 0 4px 10px rgba(0,0,0,0.05);
        }
        
        /* Banner */
        .header-banner {
            background: var(--gradient);
            padding: 2rem;
            border-radius: 10px;
            color: white;
            text-align: center;
            margin-bottom: 2rem;
            position: relative;
            overflow: hidden;
        }
        
        .header-banner h1 {
            color: white;
            border-bottom: none;
            padding-bottom: 0;
            margin-bottom: 0.5rem;
            text-shadow: 0 2px 4px rgba(0,0,0,0.2);
        }
        
        .header-banner::before {
            content: "";
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: repeating-linear-gradient(
                45deg,
                rgba(255,255,255,0.1),
                rgba(255,255,255,0.1) 10px,
                rgba(255,255,255,0.05) 10px,
                rgba(255,255,255,0.05) 20px
            );
            animation: move-bg 20s linear infinite;
        }
        
        @keyframes move-bg {
            0% { transform: translate(0%, 0%) rotate(0deg); }
            100% { transform: translate(-25%, -25%) rotate(360deg); }
        }
        
        /* Cards */
        .card {
            background-color: white;
            border-radius: 10px;
            padding: 1.5rem;
            box-shadow: 0 4px 10px rgba(0,0,0,0.05);
            transition: all 0.3s;
            margin-bottom: 1rem;
        }
        
        .card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 20px rgba(0,0,0,0.1);
        }
        
        /* Alerts */
        .element-container div[data-testid="stAlert"] {
            border-radius: 8px;
        }
        
        /* Success messages */
        div[data-testid="stAlert"][data-baseweb="notification"] {
            background-color: rgba(6, 214, 160, 0.1);
            border-color: var(--success);
        }
        
        /* Sidebar */
        [data-testid="stSidebar"] {
            background-color: #ffffff;
            border-right: none;
            box-shadow: 2px 0 10px rgba(0,0,0,0.05);
        }
        
        [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }
        
        .sidebar-header {
            padding: 1rem;
            background: var(--gradient);
            color: white;
            text-align: center;
            border-radius: 8px;
            margin-bottom: 1rem;
        }
        
        /* Expense card */
        .expense-card {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 1rem;
            background-color: white;
            border-radius: 8px;
            box-shadow: 0 2px 6px rgba(0,0,0,0.05);
            margin-bottom: 0.75rem;
            border-left: 4px solid var(--primary);
        }
        
        .expense-category {
            font-weight: 500;
            color: var(--dark);
        }
        
        .expense-amount {
            font-weight: 600;
            color: var(--accent);
        }
        
        .multiselect-card span[data-baseweb="tag"] {
            background-color: var(--primary) !important;
        }
    </style>
    """, unsafe_allow_html=True)

# Initialize Firebase
try:
    # Firebase Admin SDK for Firestore
    if not firebase_admin._apps:
        cred = credentials.Certificate("firebase_key.json")
        firebase_admin.initialize_app(cred)
    
    # Pyrebase for Authentication
    firebase_config = json.load(open("firebase_config.json"))
    firebase = pyrebase.initialize_app(firebase_config)
    auth = firebase.auth()
    db = firestore.client()
except Exception as e:
    st.error(f"Firebase initialization error: {e}")

# Initialize session state
def init_session_state():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "onboarded" not in st.session_state:
        st.session_state.onboarded = False
    if "page" not in st.session_state:
        st.session_state.page = "dashboard"

# Dashboard page
def dashboard(user_id):
    # Get user data
    user_doc = db.collection("users").document(user_id).get()
    user_data = user_doc.to_dict()
    
    # Header with user name
    st.markdown(f"""
    <div class="header-banner">
        <h1>👋 Welcome, {user_data.get('name', 'User')}</h1>
        <p>Your financial dashboard</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Key metrics
    currency_symbol = user_data.get('currency', '₹ INR').split()[0]
    income = user_data.get('income', 0)
    
    # Get budget allocations and calculate metrics
    budget_allocations = user_data.get('budget_allocations', {})
    total_budget = sum(budget_allocations.values()) if budget_allocations else income
    
    # Get recent expenses (last month)
    try:
        now = datetime.now()
        month_ago = (now - timedelta(days=30)).isoformat()
        
        expenses_ref = db.collection("users").document(user_id).collection("expenses")
        recent_expenses_query = expenses_ref.where('date', '>=', month_ago).get()
        
        recent_expenses = []
        for doc in recent_expenses_query:
            expense = doc.to_dict()
            expense['id'] = doc.id
            recent_expenses.append(expense)
        
        # Calculate total expenses
        total_expenses = sum(expense['amount'] for expense in recent_expenses)
        
        # Group expenses by category
        expense_by_category = {}
        for expense in recent_expenses:
            category = expense.get('category', 'Other')
            expense_by_category[category] = expense_by_category.get(category, 0) + expense['amount']
            
    except Exception as e:
        # If error occurs, use simulated data
        total_expenses = total_budget * 0.8  # Simulated as 80% of budget used
        
        # Generate some sample expenses data based on categories
        expense_by_category = {}
        import random
        for cat, amount in budget_allocations.items():
            expense_by_category[cat] = round(random.uniform(0.5, 0.9) * amount, 2)
            
        recent_expenses = []
        for cat, amount in expense_by_category.items():
            # Create 2-3 expenses per category
            num_expenses = random.randint(2, 3)
            for i in range(num_expenses):
                expense_amount = round(amount / num_expenses * random.uniform(0.8, 1.2), 2)
                recent_expenses.append({
                    'category': cat,
                    'amount': expense_amount,
                    'date': (now - timedelta(days=random.randint(0, 29))).isoformat(),
                    'notes': f"Sample {cat} expense #{i+1}"
                })
    
    # Calculate remaining budget
    remaining_budget = total_budget - total_expenses
    
    # Display key metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Monthly Income", f"{currency_symbol} {income:,}", "")
    with col2:
        # Show budget remaining
        budget_percent = (remaining_budget / total_budget) * 100 if total_budget > 0 else 0
        delta = f"{budget_percent:.0f}% of budget"
        st.metric("Budget Remaining", f"{currency_symbol} {remaining_budget:,.0f}", delta)
    with col3:
        # Show total expenses with comparison to budget
        expense_percent = (total_expenses / total_budget) * 100 if total_budget > 0 else 0
        delta = f"{expense_percent:.0f}% of budget"
        delta_color = "normal"
        if expense_percent > 95:
            delta_color = "off"  # Red if close to or exceeding budget
        st.metric("Total Expenses", f"{currency_symbol} {total_expenses:,.0f}", delta, delta_color=delta_color)
    
    # Dashboard tabs
    tab1, tab2 = st.tabs(["Overview", "Add Expense"])
    
    with tab1:
        col1, col2 = st.columns([3, 2])
        
        with col1:
            st.subheader("Expense Breakdown")
            
            # Create a dataframe for the pie chart from actual expense data
            if expense_by_category:
                df = pd.DataFrame({
                    'Category': expense_by_category.keys(),
                    'Amount': expense_by_category.values()
                })
                
                # Create a pie chart
                fig = px.pie(
                    df, 
                    values='Amount', 
                    names='Category',
                    color_discrete_sequence=px.colors.sequential.Bluyl, 
                    hole=0.4
                )
                
                fig.update_layout(
                    margin=dict(l=20, r=20, t=30, b=20),
                    height=300
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No expense data available yet. Add your first expense!")
            
            # Recent transactions (from actual data)
            st.subheader("Recent Transactions")
            
            if recent_expenses:
                # Sort by date (recent first)
                sorted_expenses = sorted(recent_expenses, key=lambda x: x.get('date', ''), reverse=True)
                
                for i, expense in enumerate(sorted_expenses[:5]):  # Show 5 most recent
                    category = expense.get('category', 'Other')
                    amount = expense.get('amount', 0)
                    date_str = expense.get('date', '')
                    
                    # Parse date for display
                    try:
                        date_obj = datetime.fromisoformat(date_str)
                        date_display = date_obj.strftime('%d %b, %Y')
                    except:
                        date_display = "Unknown date"
                    
                    st.markdown(f"""
                    <div class="expense-card">
                        <div>
                            <div class="expense-category">{category}</div>
                            <div style="color: #6c757d; font-size: 0.85rem;">{date_display}</div>
                        </div>
                        <div class="expense-amount">{currency_symbol} {amount:,.2f}</div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No transactions yet. Add your first expense!")
        
        with col2:
            st.subheader("Budget vs Spending")
            
            # Get budget allocations if available
            if budget_allocations:
                # Create a dataframe comparing budget vs actual spending by category
                budget_vs_spent = []
                
                for category, budget_amount in budget_allocations.items():
                    spent_amount = expense_by_category.get(category, 0)
                    percent_used = (spent_amount / budget_amount * 100) if budget_amount > 0 else 0
                    
                    budget_vs_spent.append({
                        'Category': category,
                        'Allocated': budget_amount,
                        'Spent': spent_amount,
                        'Percent_Used': percent_used
                    })
                
                # Sort by percent used (highest first)
                budget_vs_spent = sorted(budget_vs_spent, key=lambda x: x['Percent_Used'], reverse=True)
                
                # Convert to dataframe for visualization
                budget_df = pd.DataFrame(budget_vs_spent)
                
                # Create a horizontal bar chart for budget vs spent
                fig2 = px.bar(
                    budget_df, 
                    x=['Allocated', 'Spent'], 
                    y='Category', 
                    orientation='h',
                    barmode='group',
                    color_discrete_sequence=['#4361EE', '#FF5E78']
                )
                
                fig2.update_layout(
                    margin=dict(l=20, r=20, t=20, b=20),
                    height=240
                )
                
                st.plotly_chart(fig2, use_container_width=True)
                
                # Flag categories that are over budget
                for item in budget_vs_spent:
                    if item['Percent_Used'] > 90:
                        st.warning(f"⚠️ {item['Category']} is at {item['Percent_Used']:.1f}% of budget")
                
                # Add link to budget setup
                if st.button("Adjust Budget Allocations"):
                    st.session_state.page = "budget setup"
                    st.rerun()
            else:
                st.info("You haven't set up your budget allocations yet.")
                if st.button("Set Up Budget Now"):
                    st.session_state.page = "budget setup"
                    st.rerun()
            
            # Enhanced Savings Goal Display
            st.subheader("Savings Goal")
            
            # Get savings goal if available
            savings_goal = user_data.get('savings_goal', None)
            
            if savings_goal:
                # Display specific savings goal
                goal_item = savings_goal.get('item', 'Goal')
                goal_amount = savings_goal.get('total_cost', 0)
                current_amount = savings_goal.get('current_savings', 0)
                progress = current_amount / goal_amount if goal_amount > 0 else 0
                
                # Get target date and calculate days left
                goal_target = savings_goal.get('target_date', datetime.now().date().isoformat())
                
                try:
                    target_date = datetime.fromisoformat(goal_target).date()
                    days_left = (target_date - datetime.now().date()).days
                except:
                    target_date = datetime.now().date() + timedelta(days=365)
                    days_left = 365
                
                st.markdown(f"**Saving for: {goal_item}**")
                st.progress(progress)
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"Target: {currency_symbol} {goal_amount:,.0f}")
                    st.markdown(f"Current: {currency_symbol} {current_amount:,.0f}")
                with col2:
                    st.markdown(f"{progress:.0%} complete")
                    st.markdown(f"Days left: {max(0, days_left)}")
                    
                if st.button("Update Progress"):
                    st.session_state.page = "budget setup"
                    st.session_state.active_tab = "Savings Goals"
                    st.rerun()
            else:
                st.info("No savings goal set. Would you like to create one?")
                if st.button("Set Savings Goal"):
                    st.session_state.page = "budget setup"
                    st.session_state.active_tab = "Savings Goals"
                    st.rerun()
            
    with tab2:
        with st.form("add_expense_form"):
            st.subheader("Record New Expense")
            
            col1, col2 = st.columns(2)
            
            with col1:
                expense_amount = st.number_input("Amount", min_value=0.0, step=100.0)
                expense_date = st.date_input("Date", value=datetime.now())
            
            with col2:
                # Use budget categories if available, otherwise use default categories
                if budget_allocations:
                    categories_list = list(budget_allocations.keys())
                else:
                    # Extract category names from the full category strings (removing emojis)
                    categories = user_data.get('categories', [])
                    categories_list = [cat.split(" ", 1)[1] if " " in cat else cat for cat in categories]
                    if not categories_list:
                        categories_list = ["Essentials", "Food & Dining", "Entertainment", "Transportation"]
                
                expense_category = st.selectbox("Category", categories_list)
                expense_notes = st.text_input("Description (Optional)")
            
            # Add warning if category is close to or over budget
            if budget_allocations and expense_category in budget_allocations and expense_category in expense_by_category:
                budget_for_cat = budget_allocations[expense_category]
                spent_for_cat = expense_by_category.get(expense_category, 0)
                
                # Check if this expense would put the category over budget
                if spent_for_cat + expense_amount > budget_for_cat:
                    st.warning(f"⚠️ This expense will put your {expense_category} category over budget!")
                elif spent_for_cat + expense_amount > budget_for_cat * 0.9:
                    st.warning(f"⚠️ This expense will use over 90% of your {expense_category} budget!")
            
            submitted = st.form_submit_button("Save Expense")
            
            if submitted:
                if expense_amount <= 0:
                    st.warning("Please enter a valid expense amount")
                else:
                    try:
                        # Save the expense to Firestore
                        db.collection("users").document(user_id).collection("expenses").add({
                            "amount": expense_amount,
                            "category": expense_category,
                            "date": expense_date.isoformat(),
                            "notes": expense_notes,
                            "created_at": firestore.SERVER_TIMESTAMP
                        })
                        st.success(f"Expense of {currency_symbol} {expense_amount:.2f} added to {expense_category}!")
                        
                        # If this is for a savings goal item, update savings progress
                        if savings_goal and expense_category.lower().find("savings") >= 0:
                            current_savings = savings_goal.get('current_savings', 0) + expense_amount
                            
                            db.collection("users").document(user_id).update({
                                "savings_goal.current_savings": current_savings
                            })
                            
                            st.success(f"Savings progress updated to {currency_symbol} {current_savings:,.2f}!")
                            
                        # Refresh the page to show the new expense
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to save expense: {str(e)}")

# Add this function after the dashboard function

def transactions_page(user_id):
    """Display and manage user transactions"""
    # Get user data
    user_doc = db.collection("users").document(user_id).get()
    user_data = user_doc.to_dict()
    currency_symbol = user_data.get('currency', '₹ INR').split()[0]
    
    st.markdown("""
    <div class="header-banner">
        <h1>📊 Transactions</h1>
        <p>Track and manage your spending</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Get all expenses
    try:
        expenses_ref = db.collection("users").document(user_id).collection("expenses")
        expenses_query = expenses_ref.order_by('date', direction='DESCENDING').get()
        
        expenses = []
        for doc in expenses_query:
            expense = doc.to_dict()
            expense['id'] = doc.id
            expenses.append(expense)
    except Exception as e:
        st.error(f"Failed to load transactions: {str(e)}")
        expenses = []
    
    # Tabs for transactions view
    tab1, tab2 = st.tabs(["All Transactions", "Add New"])
    
    with tab1:
        if not expenses:
            st.info("No transactions found. Add your first expense!")
        else:
            # Filter and sort controls
            col1, col2, col3 = st.columns(3)
            with col1:
                # Get all categories from user data
                categories = user_data.get('categories', [])
                clean_categories = [cat.split(" ", 1)[1] if " " in cat else cat for cat in categories]
                if not clean_categories:
                    clean_categories = ["Essentials", "Food & Dining", "Entertainment", "Transportation"]
                
                selected_category = st.selectbox("Filter by Category", ["All"] + clean_categories)
            
            with col2:
                time_filter = st.selectbox("Time Period", ["Last 30 Days", "Last 90 Days", "This Month", "Last Month", "This Year", "All Time"])
            
            with col3:
                sort_by = st.selectbox("Sort By", ["Date (Newest)", "Date (Oldest)", "Amount (Highest)", "Amount (Lowest)"])
            
            # Apply filters
            filtered_expenses = expenses.copy()
            
            # Category filter
            if selected_category != "All":
                filtered_expenses = [e for e in filtered_expenses if e.get('category', '') == selected_category]
            
            # Time filter
            now = datetime.now()
            if time_filter == "Last 30 Days":
                cutoff = (now - timedelta(days=30)).isoformat()
                filtered_expenses = [e for e in filtered_expenses if e.get('date', '') >= cutoff]
            elif time_filter == "Last 90 Days":
                cutoff = (now - timedelta(days=90)).isoformat()
                filtered_expenses = [e for e in filtered_expenses if e.get('date', '') >= cutoff]
            elif time_filter == "This Month":
                first_day = datetime(now.year, now.month, 1).isoformat()
                filtered_expenses = [e for e in filtered_expenses if e.get('date', '') >= first_day]
            elif time_filter == "Last Month":
                last_month = now.month - 1 if now.month > 1 else 12
                last_month_year = now.year if now.month > 1 else now.year - 1
                first_day = datetime(last_month_year, last_month, 1).isoformat()
                if last_month == 12:
                    last_day = datetime(last_month_year + 1, 1, 1).isoformat()
                else:
                    last_day = datetime(last_month_year, last_month + 1, 1).isoformat()
                filtered_expenses = [e for e in filtered_expenses if e.get('date', '') >= first_day and e.get('date', '') < last_day]
            elif time_filter == "This Year":
                first_day = datetime(now.year, 1, 1).isoformat()
                filtered_expenses = [e for e in filtered_expenses if e.get('date', '') >= first_day]
            
            # Apply sorting
            if sort_by == "Date (Newest)":
                filtered_expenses = sorted(filtered_expenses, key=lambda x: x.get('date', ''), reverse=True)
            elif sort_by == "Date (Oldest)":
                filtered_expenses = sorted(filtered_expenses, key=lambda x: x.get('date', ''))
            elif sort_by == "Amount (Highest)":
                filtered_expenses = sorted(filtered_expenses, key=lambda x: x.get('amount', 0), reverse=True)
            elif sort_by == "Amount (Lowest)":
                filtered_expenses = sorted(filtered_expenses, key=lambda x: x.get('amount', 0))
            
            # Summary metrics
            if filtered_expenses:
                total = sum(e.get('amount', 0) for e in filtered_expenses)
                avg = total / len(filtered_expenses) if filtered_expenses else 0
                
                cols = st.columns(3)
                with cols[0]:
                    st.metric("Total Expenses", f"{currency_symbol} {total:,.2f}")
                with cols[1]:
                    st.metric("Number of Transactions", f"{len(filtered_expenses)}")
                with cols[2]:
                    st.metric("Average Amount", f"{currency_symbol} {avg:,.2f}")
            
            # Show transactions
            for expense in filtered_expenses:
                category = expense.get('category', 'Other')
                amount = expense.get('amount', 0)
                date_str = expense.get('date', '')
                notes = expense.get('notes', '')
                
                # Parse date for display
                try:
                    date_obj = datetime.fromisoformat(date_str)
                    date_display = date_obj.strftime('%d %b, %Y')
                except:
                    date_display = "Unknown date"
                
                # Create an expandable card for each transaction
                with st.expander(f"{date_display} | {category} | {currency_symbol} {amount:,.2f}"):
                    cols = st.columns([3, 1])
                    with cols[0]:
                        st.write(f"**Category:** {category}")
                        st.write(f"**Date:** {date_display}")
                        st.write(f"**Amount:** {currency_symbol} {amount:,.2f}")
                        if notes:
                            st.write(f"**Notes:** {notes}")
                    
                    with cols[1]:
                        # Action buttons
                        if st.button("Delete", key=f"delete_{expense.get('id', 'unknown')}"):
                            try:
                                # Delete from Firestore
                                db.collection("users").document(user_id).collection("expenses").document(expense['id']).delete()
                                st.success("Transaction deleted!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Failed to delete: {str(e)}")
    
    with tab2:
        # Form to add new expense - similar to the one on dashboard
        with st.form("add_expense_form_transactions"):
            st.subheader("Record New Expense")
            
            col1, col2 = st.columns(2)
            
            with col1:
                expense_amount = st.number_input("Amount", min_value=0.0, step=100.0)
                expense_date = st.date_input("Date", value=datetime.now())
            
            with col2:
                # Use budget categories
                budget_allocations = user_data.get('budget_allocations', {})
                
                if budget_allocations:
                    categories_list = list(budget_allocations.keys())
                else:
                    # Extract category names from the full category strings (removing emojis)
                    categories = user_data.get('categories', [])
                    categories_list = [cat.split(" ", 1)[1] if " " in cat else cat for cat in categories]
                    if not categories_list:
                        categories_list = ["Essentials", "Food & Dining", "Entertainment", "Transportation"]
                
                expense_category = st.selectbox("Category", categories_list)
                expense_notes = st.text_input("Description (Optional)")
            
            submitted = st.form_submit_button("Save Expense", use_container_width=True)
            
            if submitted:
                if expense_amount <= 0:
                    st.warning("Please enter a valid expense amount")
                else:
                    try:
                        # Save the expense to Firestore
                        db.collection("users").document(user_id).collection("expenses").add({
                            "amount": expense_amount,
                            "category": expense_category,
                            "date": expense_date.isoformat(),
                            "notes": expense_notes,
                            "created_at": firestore.SERVER_TIMESTAMP
                        })
                        
                        # Update streak and potentially award achievements
                        update_user_achievements(user_id)
                        
                        st.success(f"Expense of {currency_symbol} {expense_amount:.2f} added to {expense_category}!")
                        
                        # If this is for a savings goal item, update savings progress
                        savings_goal = user_data.get('savings_goal', None)
                        if savings_goal and expense_category.lower().find("savings") >= 0:
                            current_savings = savings_goal.get('current_savings', 0) + expense_amount
                            
                            db.collection("users").document(user_id).update({
                                "savings_goal.current_savings": current_savings
                            })
                            
                            st.success(f"Savings progress updated to {currency_symbol} {current_savings:,.2f}!")
                        
                        st.balloons()  # Small celebration for added expense (gamification)
                        time.sleep(0.5)  # Give time to see the balloons
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to save expense: {str(e)}")

# Add this function after the transactions_page function

def budget_view(user_id):
    """Display the current budget and spending breakdown"""
    # Get user data
    user_doc = db.collection("users").document(user_id).get()
    user_data = user_doc.to_dict()
    
    st.markdown("""
    <div class="header-banner">
        <h1>💵 Budget Overview</h1>
        <p>Monitor your spending against your budget</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Key metrics
    currency_symbol = user_data.get('currency', '₹ INR').split()[0]
    income = user_data.get('income', 0)
    
    # Get budget allocations
    budget_allocations = user_data.get('budget_allocations', {})
    if not budget_allocations:
        st.warning("You haven't set up a budget yet.")
        if st.button("Create My Budget"):
            st.session_state.page = "budget setup"
            st.rerun()
        return
    
    # Get recent expenses (current month)
    try:
        now = datetime.now()
        first_day_month = datetime(now.year, now.month, 1).isoformat()
        
        expenses_ref = db.collection("users").document(user_id).collection("expenses")
        month_expenses_query = expenses_ref.where('date', '>=', first_day_month).get()
        
        month_expenses = []
        for doc in month_expenses_query:
            expense = doc.to_dict()
            expense['id'] = doc.id
            month_expenses.append(expense)
        
        # Group expenses by category
        expense_by_category = {}
        for expense in month_expenses:
            category = expense.get('category', 'Other')
            expense_by_category[category] = expense_by_category.get(category, 0) + expense['amount']
    except Exception as e:
        st.error(f"Failed to load expenses: {str(e)}")
        expense_by_category = {}
    
    # Budget vs Actual comparison
    st.subheader("Monthly Budget Performance")
    
    # Create a dataframe for comparison
    budget_vs_actual = []
    total_budget = 0
    total_spent = 0
    
    for category, budget_amount in budget_allocations.items():
        spent_amount = expense_by_category.get(category, 0)
        percent_used = (spent_amount / budget_amount * 100) if budget_amount > 0 else 0
        remaining = budget_amount - spent_amount
        
        total_budget += budget_amount
        total_spent += spent_amount
        
        budget_vs_actual.append({
            'Category': category,
            'Budget': budget_amount,
            'Spent': spent_amount,
            'Remaining': remaining,
            'Percent_Used': percent_used
        })
    
    # Sort by percent used (highest first)
    budget_vs_actual = sorted(budget_vs_actual, key=lambda x: x['Percent_Used'], reverse=True)
    
    # Show overall status
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Budget", f"{currency_symbol} {total_budget:,.0f}")
    
    with col2:
        st.metric("Total Spent", f"{currency_symbol} {total_spent:,.0f}", f"{total_spent/total_budget:.1%}")
    
    with col3:
        remaining = total_budget - total_spent
        days_in_month = pd.Timestamp(now.year, now.month + 1, 1) - pd.Timestamp(now.year, now.month, 1)
        day_of_month = now.day
        month_progress = day_of_month / days_in_month.days
        
        # Calculate if spending is on track
        budget_used_percent = total_spent / total_budget if total_budget > 0 else 0
        
        if budget_used_percent <= month_progress + 0.05:
            status_delta = "On track 👍"
            delta_color = "normal"
        else:
            status_delta = "Over budget pace 😬"
            delta_color = "inverse"
        
        st.metric("Remaining Budget", f"{currency_symbol} {remaining:,.0f}", status_delta, delta_color=delta_color)
    
    # Budget health score (gamification)
    budget_health = 100 - max(0, min(100, (budget_used_percent - month_progress) * 100 * 2))
    
    st.subheader("Budget Health Score")
    
    # Color coding for health score
    if budget_health >= 80:
        color = "green"
        message = "Excellent! You're managing your budget very well! 🌟"
    elif budget_health >= 60:
        color = "lightgreen"
        message = "Good job! Your budget is on track. 👌"
    elif budget_health >= 40:
        color = "yellow"
        message = "Caution: Your spending is slightly higher than ideal. 🔍"
    else:
        color = "red"
        message = "Warning: Your budget needs attention! ⚠️"
        
    # Custom progress bar with color
    st.markdown(f"""
    <div style="margin-bottom: 10px;">
        <div style="width: 100%; background-color: #e0e0e0; border-radius: 10px; height: 30px;">
            <div style="width: {budget_health}%; background-color: {color}; height: 100%; border-radius: 10px; 
                 display: flex; align-items: center; justify-content: center; color: white; font-weight: bold;">
                {budget_health:.0f}/100
            </div>
        </div>
    </div>
    <p style="text-align: center; margin-top: 0;">{message}</p>
    """, unsafe_allow_html=True)
    
    # Display category breakdown
    st.subheader("Category Breakdown")
    
    # Create a horizontal bar chart comparing budget vs actual
    if budget_vs_actual:
        budget_df = pd.DataFrame(budget_vs_actual)
        
        # Create plots for visualization
        fig1, fig2 = st.columns([3, 2])
        
        with fig1:
            # Budget vs Actual bar chart
            fig = px.bar(
                budget_df,
                y='Category',
                x=['Budget', 'Spent'],
                orientation='h',
                barmode='group',
                color_discrete_sequence=['#4361EE', '#FF5E78'],
                title="Budget vs Actual by Category"
            )
            
            fig.update_layout(
                margin=dict(l=20, r=20, t=40, b=20),
                height=400,
                xaxis_title="Amount",
                yaxis_title="",
                legend_title=""
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        with fig2:
            # Donut chart for budget distribution
            fig2 = px.pie(
                budget_df,
                values='Budget',
                names='Category',
                hole=0.5,
                color_discrete_sequence=px.colors.qualitative.Pastel,
                title="Budget Distribution"
            )
            
            fig2.update_layout(
                margin=dict(l=20, r=20, t=40, b=20),
                height=400
            )
            
            st.plotly_chart(fig2, use_container_width=True)
        
        # Category-by-category breakdown with progress bars
        for item in budget_vs_actual:
            category = item['Category']
            budget = item['Budget']
            spent = item['Spent']
            remaining = item['Remaining']
            percent = item['Percent_Used']
            
            # Determine color based on percentage used
            if percent > 100:
                bar_color = "rgba(255, 0, 0, 0.8)"  # Red for over budget
                emoji = "🚨"
            elif percent > 85:
                bar_color = "rgba(255, 165, 0, 0.8)"  # Orange for close to limit
                emoji = "⚠️"
            else:
                bar_color = "rgba(46, 204, 113, 0.8)"  # Green for good
                emoji = "✅"
            
            # Custom styled progress bar
            st.markdown(f"""
            <div style="margin-bottom: 20px; background-color: white; padding: 15px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
                <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                    <span style="font-weight: bold; font-size: 16px;">{category} {emoji}</span>
                    <span>{currency_symbol} {spent:,.0f} / {currency_symbol} {budget:,.0f}</span>
                </div>
                <div style="width: 100%; background-color: #e0e0e0; border-radius: 5px; height: 10px;">
                    <div style="width: {min(100, percent)}%; background-color: {bar_color}; height: 100%; border-radius: 5px;"></div>
                </div>
                <div style="display: flex; justify-content: space-between; margin-top: 5px; font-size: 14px;">
                    <span>{percent:.1f}% used</span>
                    <span>{currency_symbol} {remaining:,.0f} remaining</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    else:
        st.info("No budget data available to display.")
    
    # Budget tips and insights
    with st.expander("Budget Tips"):
        st.write("### 💡 Smart Budget Tips")
        tips = [
            "Track every expense to get an accurate picture of your spending habits",
            "Aim to save at least 20% of your income each month",
            "Prioritize paying off high-interest debt before increasing discretionary spending",
            "Review your budget at least once a month and adjust as needed",
            "Use the 50/30/20 rule as a starting point: 50% for needs, 30% for wants, 20% for savings"
        ]
        
        for tip in tips:
            st.markdown(f"- {tip}")
    
    # Action buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Adjust Budget", use_container_width=True):
            st.session_state.page = "budget setup"
            st.rerun()
    
    with col2:
        if st.button("Record Expense", use_container_width=True):
            st.session_state.page = "transactions"
            st.rerun()

# Add these gamification functions

def update_user_achievements(user_id):
    """Update user achievements and streak"""
    try:
        user_doc = db.collection("users").document(user_id).get()
        user_data = user_doc.to_dict()
        
        # Get current data
        streak = user_data.get('login_streak', 0)
        last_login = user_data.get('last_login_date', None)
        achievements = user_data.get('achievements', [])
        total_expenses = user_data.get('total_expenses', 0) + 1  # Increment for the new expense
        
        # Check for streak
        today = datetime.now().date()
        
        if last_login:
            try:
                last_date = datetime.fromisoformat(last_login).date()
                # If last login was yesterday, increase streak
                if (today - last_date).days == 1:
                    streak += 1
                # If more than a day passed, reset streak
                elif (today - last_date).days > 1:
                    streak = 1
                # If same day, no change
            except:
                streak = 1
        else:
            streak = 1
        
        # Check for new achievements
        new_achievements = achievements.copy()
        
        # Check for streak-based achievements
        if streak >= 7 and "7-Day Streak" not in achievements:
            new_achievements.append("7-Day Streak")
        
        if streak >= 30 and "30-Day Streak" not in achievements:
            new_achievements.append("30-Day Streak")
        
        # Check for expense tracking achievements
        if total_expenses >= 5 and "Expense Tracker" not in achievements:
            new_achievements.append("Expense Tracker")
            
        if total_expenses >= 20 and "Budget Pro" not in achievements:
            new_achievements.append("Budget Pro")
            
        if total_expenses >= 50 and "Finance Master" not in achievements:
            new_achievements.append("Finance Master")
        
        # Update user data
        db.collection("users").document(user_id).update({
            "login_streak": streak,
            "last_login_date": today.isoformat(),
            "achievements": new_achievements,
            "total_expenses": total_expenses
        })
        
        # Return newly earned achievements
        return [a for a in new_achievements if a not in achievements]
    except Exception as e:
        print(f"Error updating achievements: {str(e)}")
        return []

# Update the sidebar function to add the Financial Assistant option

def render_sidebar(user_id=None):
    if user_id:
        st.sidebar.markdown("""
        <div class="sidebar-header">
            <h3 style="margin: 0; color: white;">💰 Smart Budget</h3>
        </div>
        """, unsafe_allow_html=True)
        
        # Updated navigation links with Financial Assistant
        page = st.sidebar.radio("Navigation", ["Dashboard", "Budget", "Transactions", "Budget Setup", "Financial Assistant"])
        
        if page not in ["Dashboard", "Budget", "Transactions", "Budget Setup", "Financial Assistant"] and st.session_state.page != page.lower():
            st.sidebar.info(f"The {page} page is under development.")
            st.session_state.page = "dashboard"
        else:
            st.session_state.page = page.lower()
        
        # Footer
        st.sidebar.markdown("---")
        
        # Add achievements and streak counter (gamification)
        user_doc = db.collection("users").document(user_id).get()
        user_data = user_doc.to_dict()
        
        # Get streak data (number of consecutive days logged in)
        streak = user_data.get('login_streak', 1)
        achievements = user_data.get('achievements', [])
        
        st.sidebar.markdown("### 🏆 Your Progress")
        st.sidebar.markdown(f"**🔥 Login Streak:** {streak} days")
        
        # Display progress toward next achievement
        if not achievements:
            progress = 0.2  # Initial progress
            next_achievement = "Budget Master"
            st.sidebar.markdown(f"**Next Achievement:** {next_achievement}")
            st.sidebar.progress(progress)
            st.sidebar.markdown(f"Create your first budget to earn this badge!")
        else:
            # Show the latest achievement
            last_achievement = achievements[-1]
            next_level = len(achievements) + 1
            next_achievement = f"Level {next_level} Budgeter"
            progress = 0.7  # Example progress
            st.sidebar.markdown(f"**Current Badge:** {last_achievement}")
            st.sidebar.markdown(f"**Next Badge:** {next_achievement}")
            st.sidebar.progress(progress)
            st.sidebar.markdown(f"Keep tracking expenses to level up!")
        
        if st.sidebar.button("Logout"):
            st.session_state.authenticated = False
            st.session_state.onboarded = False
            st.rerun()

# Add this function for the chatbot feature

def financial_assistant(user_id):
    """AI chatbot assistant that answers questions about user's financial data"""
    # Get user data
    user_doc = db.collection("users").document(user_id).get()
    user_data = user_doc.to_dict()
    
    st.markdown("""
    <div class="header-banner">
        <h1>💬 Financial Assistant</h1>
        <p>Ask anything about your finances and budget</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize chat history in session state if not present
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = [
            {"role": "assistant", "content": "Hello! I'm your financial assistant powered by Gemini AI. I can answer questions about your income, expenses, budget, and savings. How can I help you today?"}
        ]

    # Get user financial data for AI context
    currency_symbol = user_data.get('currency', '₹ INR').split()[0]
    income = user_data.get('income', 0)
    budget_allocations = user_data.get('budget_allocations', {})
    savings_goal = user_data.get('savings_goal', None)
    
    # Fetch recent expenses
    try:
        now = datetime.now()
        month_ago = (now - timedelta(days=30)).isoformat()
        
        expenses_ref = db.collection("users").document(user_id).collection("expenses")
        recent_expenses_query = expenses_ref.where('date', '>=', month_ago).get()
        
        recent_expenses = []
        for doc in recent_expenses_query:
            expense = doc.to_dict()
            recent_expenses.append(expense)
            
        # Calculate total expenses and categorize
        total_expenses = sum(expense['amount'] for expense in recent_expenses)
        expense_by_category = {}
        for expense in recent_expenses:
            category = expense.get('category', 'Other')
            expense_by_category[category] = expense_by_category.get(category, 0) + expense['amount']
            
        # Most expensive category
        most_expensive_category = max(expense_by_category.items(), key=lambda x: x[1], default=("None", 0))
        
        # Get month to date spending
        first_day_month = datetime(now.year, now.month, 1).isoformat()
        month_expenses = [e for e in recent_expenses if e.get('date', '') >= first_day_month]
        month_total = sum(expense['amount'] for expense in month_expenses)
        
    except Exception as e:
        recent_expenses = []
        expense_by_category = {}
        total_expenses = 0
        month_total = 0
        most_expensive_category = ("Unknown", 0)
    
    # Prepare financial context for the AI
    financial_context = {
        "user_name": user_data.get('name', 'User'),
        "income": income,
        "currency": currency_symbol,
        "total_budget": sum(budget_allocations.values()) if budget_allocations else income,
        "budget_allocations": budget_allocations,
        "monthly_expenses": month_total,
        "expenses_last_30_days": total_expenses,
        "category_breakdown": expense_by_category,
        "top_spending_category": most_expensive_category[0],
        "top_spending_amount": most_expensive_category[1],
        "has_savings_goal": savings_goal is not None,
    }
    
    if savings_goal:
        financial_context.update({
            "savings_goal_item": savings_goal.get('item', 'Goal'),
            "savings_goal_amount": savings_goal.get('total_cost', 0),
            "savings_goal_current": savings_goal.get('current_savings', 0),
            "savings_goal_progress": (savings_goal.get('current_savings', 0) / savings_goal.get('total_cost', 1)) * 100
        })
    
    # Display chat messages
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    # Add caption to show if using Gemini
    try:
        from finance_chatbot import setup_gemini
        model = setup_gemini()
        if model:
            st.caption("🔮 Powered by Gemini AI")
        else:
            st.caption("💬 Using built-in assistant")
    except:
        st.caption("💬 Using built-in assistant")

    # User input
    user_query = st.chat_input("Ask about your finances...")
    
    if user_query:
        # Add user query to chat history
        st.session_state.chat_history.append({"role": "user", "content": user_query})
        
        # Display user message
        with st.chat_message("user"):
            st.write(user_query)
        
        # Process query and generate response using Gemini (with fallback)
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = process_query_with_gemini(user_query, financial_context)
                st.write(response)
                
        # Add assistant response to chat history
        st.session_state.chat_history.append({"role": "assistant", "content": response})

# Update the main function to include the Financial Assistant page

def main():
    apply_vibrant_styles()
    init_session_state()
    
    # User authentication flow
    if not st.session_state.authenticated:
        login_signup()
    elif not st.session_state.onboarded:
        onboarding_screen(st.session_state.user_id)
        render_sidebar(st.session_state.user_id)
    else:
        # Check for daily login streak and update
        today = datetime.now().date().isoformat()
        last_login = st.session_state.get("last_login_date", None)
        
        if last_login != today:
            new_achievements = update_user_achievements(st.session_state.user_id)
            st.session_state.last_login_date = today
            
            # Show achievement notifications
            if new_achievements:
                for achievement in new_achievements:
                    st.toast(f"🏆 New Achievement: {achievement}!")
        
        render_sidebar(st.session_state.user_id)
        
        # Show different pages based on navigation
        if st.session_state.page == "dashboard":
            dashboard(st.session_state.user_id)
        elif st.session_state.page == "budget setup":
            budget_setup(st.session_state.user_id)
        elif st.session_state.page == "transactions":
            transactions_page(st.session_state.user_id)
        elif st.session_state.page == "budget":
            budget_view(st.session_state.user_id)
        elif st.session_state.page == "financial assistant":
            financial_assistant(st.session_state.user_id)
        else:
            st.title(f"🚧 {st.session_state.page.capitalize()} Page")
            st.write("This page is under construction... coming soon!")

if __name__ == "__main__":
    main()