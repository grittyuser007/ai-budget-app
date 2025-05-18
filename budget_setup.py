import streamlit as st
import pandas as pd
import plotly.express as px
from shared import db
import json
from firebase_admin import firestore
from datetime import datetime, timedelta
import numpy as np
from budget_ai import get_ai_budget_recommendation
def budget_setup(user_id):
    st.markdown("""
    <div class="header-banner">
        <h1>💸 Smart Budget Setup</h1>
        <p>Create your personalized budget plan</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Get user data
    user_doc = db.collection("users").document(user_id).get()
    user_data = user_doc.to_dict()
    
    income = user_data.get('income', 0)
    currency_symbol = user_data.get('currency', '₹ INR').split()[0]
    
    # Get user-selected categories from Firebase
    user_categories = user_data.get('categories', [])
    # Clean category names (remove emojis)
    clean_categories = [cat.split(" ", 1)[1] if " " in cat else cat for cat in user_categories]
    
    # If no categories are found, use default budget categories
    if not clean_categories:
        clean_categories = ["Essentials", "Lifestyle", "Savings & Investments", "Debt & EMIs", "Other / Subscriptions"]
    
    # Create budget categories dict with descriptions
    budget_categories = {}
    category_descriptions = {
        "Essentials": "Rent/mortgage, utilities, groceries, transportation",
        "Food & Dining": "Groceries, restaurants, food delivery",
        "Transportation": "Public transport, fuel, vehicle maintenance",
        "Entertainment": "Movies, events, hobbies",
        "Shopping": "Clothing, electronics, personal items",
        "Health": "Medical expenses, insurance, fitness",
        "Education": "Courses, books, tuition",
        "Subscriptions": "Streaming services, memberships, apps",
        "Investments": "Stocks, mutual funds, retirement",
        "Gifts & Donations": "Presents, charitable donations",
        "Travel": "Vacations, trips, accommodations",
        "Lifestyle": "Dining out, entertainment, shopping, hobbies",
        "Savings & Investments": "Emergency fund, retirement, investments",
        "Debt & EMIs": "Loan payments, credit card debt, EMIs",
        "Other / Subscriptions": "Streaming services, memberships, miscellaneous"
    }
    
    # Create budget categories dict with descriptions for user-selected categories
    for cat in clean_categories:
        description = category_descriptions.get(cat, "Miscellaneous expenses")
        budget_categories[cat] = description
    
    st.subheader(f"Your Monthly Income: {currency_symbol} {income:,}")
    
    # Tabs for different budget setting approaches
    tab1, tab2, tab3 = st.tabs(["Manual Setup", "AI Assistant", "Savings Goals"])
    
    # Initialize budget allocations in session state if not present
    if "budget_allocations" not in st.session_state:
        # Use existing allocations if available in user data
        existing_allocations = user_data.get('budget_allocations', {})
        if existing_allocations:
            st.session_state.budget_allocations = existing_allocations
        else:
            # Default allocations based on 50/30/20 rule (simplified)
            # Distribute based on category types
            essentials_cats = [c for c in clean_categories if c in ["Essentials", "Food & Dining", "Transportation", "Health"]]
            lifestyle_cats = [c for c in clean_categories if c in ["Lifestyle", "Entertainment", "Shopping", "Travel"]]
            savings_cats = [c for c in clean_categories if c in ["Savings & Investments", "Investments"]]
            debt_cats = [c for c in clean_categories if c in ["Debt & EMIs"]]
            other_cats = [c for c in clean_categories if c not in essentials_cats + lifestyle_cats + savings_cats + debt_cats]
            
            # Calculate default allocations
            st.session_state.budget_allocations = {}
            
            # Distribute essentials (50%)
            if essentials_cats:
                per_essential = (income * 0.5) / len(essentials_cats)
                for cat in essentials_cats:
                    st.session_state.budget_allocations[cat] = per_essential
                    
            # Distribute lifestyle (30%)
            if lifestyle_cats:
                per_lifestyle = (income * 0.3) / len(lifestyle_cats)
                for cat in lifestyle_cats:
                    st.session_state.budget_allocations[cat] = per_lifestyle
                    
            # Distribute savings (15%)
            if savings_cats:
                per_savings = (income * 0.15) / len(savings_cats)
                for cat in savings_cats:
                    st.session_state.budget_allocations[cat] = per_savings
                    
            # Distribute debt (5%)
            if debt_cats:
                per_debt = (income * 0.05) / len(debt_cats)
                for cat in debt_cats:
                    st.session_state.budget_allocations[cat] = per_debt
                    
            # Distribute other
            if other_cats:
                remaining = income - sum(st.session_state.budget_allocations.values())
                per_other = max(0, remaining) / len(other_cats)
                for cat in other_cats:
                    st.session_state.budget_allocations[cat] = per_other
            
            # Ensure all categories are covered
            for cat in clean_categories:
                if cat not in st.session_state.budget_allocations:
                    st.session_state.budget_allocations[cat] = 0
    
    # MANUAL SETUP TAB
    with tab1:
        st.write("Adjust the sliders to allocate your monthly income across categories:")
        
        # For storing updated values
        updated_values = {}
        
        # Create sliders for each category
        for category in clean_categories:
            description = category_descriptions.get(category, "")
            col1, col2 = st.columns([3, 1])
            with col1:
                # Calculate percentage of income
                current_value = st.session_state.budget_allocations.get(category, 0)
                percentage = (current_value / income) * 100 if income > 0 else 0
                
                # Slider for percentage allocation
                new_percentage = st.slider(
                    f"{category}: {description}",
                    0.0, 100.0, float(percentage), 1.0,
                    format="%.1f%%",
                    key=f"slider_{category}"
                )
                
                # Calculate new amount based on percentage
                new_amount = (new_percentage / 100) * income
                updated_values[category] = new_amount
                
                # Add warning if allocation seems excessive based on category
                if category in ["Entertainment", "Shopping", "Travel", "Lifestyle"] and new_percentage > 30:
                    st.warning(f"⚠️ Your allocation for {category} seems high at {new_percentage:.1f}%. Consider reducing it.")
                elif category in ["Essentials", "Food & Dining"] and new_percentage < 20:
                    st.warning(f"⚠️ Your allocation for {category} seems low at {new_percentage:.1f}%. Make sure it's sufficient.")
                elif category in ["Savings & Investments", "Investments"] and new_percentage < 10:
                    st.warning(f"⚠️ Consider allocating at least 10% to savings/investments for financial security.")
            
            with col2:
                st.write(f"{currency_symbol} {new_amount:,.2f}")
        
        # Calculate and show total allocation
        total_allocated = sum(updated_values.values())
        remaining = income - total_allocated
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.progress(min(total_allocated / income, 1.0) if income > 0 else 0)
            if abs(remaining) < 0.01:  # Close to zero
                st.success(f"Perfect! You've allocated 100% of your income.")
            elif remaining > 0:
                st.info(f"You have {currency_symbol} {remaining:,.2f} ({remaining/income:.1%} of income) left to allocate.")
            else:
                st.error(f"You've over-allocated by {currency_symbol} {-remaining:,.2f} ({-remaining/income:.1%} of income). Please adjust your budget.")
        
        with col2:
            st.write(f"**Total:**")
            st.write(f"{currency_symbol} {total_allocated:,.2f}")
        
        # Update session state with new values
        if st.button("Update Budget Allocation"):
            # Check if budget is over-allocated
            if remaining < -0.01*income:  # Allow small rounding errors
                st.error(f"Budget is over-allocated by {currency_symbol} {-remaining:,.2f}. Please reduce some categories.")
            else:
                st.session_state.budget_allocations = updated_values
                
                # Save to Firestore
                db.collection("users").document(user_id).update({
                    "budget_allocations": updated_values,
                    "budget_updated_at": firestore.SERVER_TIMESTAMP
                })
                
                st.success("Budget updated successfully!")
    
    # AI ASSISTANT TAB
    with tab2:
        st.write("Let our AI assistant help you create a balanced budget based on your preferences and selected categories.")
        
        use_ai = st.checkbox("Use AI to help me plan my budget", value=False)
        
        if use_ai:
            # Collect user preferences
            st.subheader("Your Financial Priorities")
            
            col1, col2 = st.columns(2)
            
            with col1:
                financial_goal = st.selectbox(
                    "What's your primary financial goal?",
                    ["Save for emergency fund", "Pay off debt", "Save for major purchase", 
                     "Build long-term wealth", "Enjoy life now", "Balance savings and lifestyle"]
                )
                
                risk_tolerance = st.select_slider(
                    "Risk tolerance for investments",
                    options=["Very low", "Low", "Medium", "High", "Very high"]
                )
            
            with col2:
                life_stage = st.selectbox(
                    "Life stage",
                    ["Student", "Young professional", "Married/Partnered", "Family with children", 
                     "Empty nester", "Retirement planning", "Retired"]
                )
                
                saving_preference = st.slider(
                    "Desired savings rate (%)",
                    5, 50, 20, 5
                )
            
            # Additional financial situation
            st.subheader("Additional Information")
            has_debt = st.checkbox("I have significant debt to pay off")
            has_dependents = st.checkbox("I have dependents to support")
            planning_major_purchase = st.checkbox("I'm planning a major purchase in the next year")
            
            # If planning major purchase, ask for details
            if planning_major_purchase:
                col1, col2, col3 = st.columns(3)
                with col1:
                    purchase_item = st.text_input("What are you saving for?", placeholder="e.g., Car, Vacation, House")
                with col2:
                    purchase_cost = st.number_input("Estimated cost", min_value=0, step=1000)
                with col3:
                    purchase_deadline = st.date_input("Target date", value=datetime.now() + timedelta(days=365))
            else:
                purchase_item = ""
                purchase_cost = 0
                purchase_deadline = None
            
            custom_notes = st.text_area("Any additional context for the AI?", 
                                       placeholder="E.g., I'm saving for a wedding next year, I need to pay medical bills, etc.")
            
            if st.button("Generate AI Budget Recommendation"):
                with st.spinner("AI is creating your personalized budget plan..."):
                    try:
                        # Create prompt for AI that includes user-selected categories
                        prompt = f"""
                        As a financial advisor, create a monthly budget allocation for a person with the following profile:
                        - Monthly income: {currency_symbol} {income:,}
                        - Primary financial goal: {financial_goal}
                        - Life stage: {life_stage}
                        - Risk tolerance: {risk_tolerance}
                        - Desired savings rate: {saving_preference}%
                        - Has significant debt: {"Yes" if has_debt else "No"}
                        - Has dependents: {"Yes" if has_dependents else "No"}
                        - Planning major purchase soon: {"Yes" if planning_major_purchase else "No"}
                        """
                        
                        # Add purchase details if applicable
                        if planning_major_purchase:
                            days_until_goal = (purchase_deadline - datetime.now().date()).days
                            prompt += f"""
                            - Saving for: {purchase_item}
                            - Estimated cost: {currency_symbol} {purchase_cost:,}
                            - Target date: {purchase_deadline.strftime('%Y-%m-%d')} ({days_until_goal} days from now)
                            """
                        
                        prompt += f"""
                        Allocate the monthly income ONLY across these specific user-selected categories:
                        {", ".join(clean_categories)}
                        
                        For each category:
                        - Provide the recommended allocation as both a percentage and an absolute amount
                        - Give a brief explanation of the reasoning based on the user's situation
                        - Provide 1-2 tips for optimizing spending in this category
                        
                        If the user is saving for a specific purchase, create a dedicated savings plan that shows:
                        - Monthly amount needed to reach the goal by the deadline
                        - Percentage of income this represents
                        - Whether this saving goal is realistic given their income and other expenses
                        - Suggestions for adjusting the timeline if the goal is not realistic
                        
                        Return the response as a valid JSON object with allocations, explanations, tips, savings_plan and summary fields.
                        """
                        
                        # In a real implementation, this would call OpenAI's API
                        # For demo purposes, we'll create a sample response
                        
                        # Simulated AI response (in production, replace with actual API call)
                        # Example with OpenAI:
                        # response = openai.chat.completions.create(
                        #     model="gpt-3.5-turbo",
                        #     messages=[{"role": "system", "content": "You are a financial advisor."},
                        #               {"role": "user", "content": prompt}]
                        # )
                        # ai_response = json.loads(response.choices[0].message.content)
                        
                        # Simulated response based on inputs
                        ai_response = get_ai_budget_recommendation(
                            income=income,
                            categories=clean_categories,
                            saving_preference=saving_preference,
                            has_debt=has_debt,
                            planning_major_purchase=planning_major_purchase,
                            purchase_item=purchase_item,
                            purchase_cost=purchase_cost,
                            purchase_deadline=purchase_deadline,
                            financial_goal=financial_goal,
                            life_stage=life_stage
                        )
                        
                        # Update session state with AI recommendations
                        updated_budget = {}
                        for category, allocation in ai_response["allocations"].items():
                            updated_budget[category] = allocation["amount"]
                        
                        st.session_state.budget_allocations = updated_budget
                        st.session_state.budget_explanations = ai_response["explanations"]
                        st.session_state.budget_tips = ai_response["tips"]
                        st.session_state.budget_summary = ai_response["summary"]
                        
                        # Save savings goal if applicable
                        if planning_major_purchase and ai_response["savings_plan"]["item"]:
                            savings_plan = ai_response["savings_plan"]
                            
                            st.session_state.savings_goal = {
                                "item": savings_plan["item"],
                                "total_cost": savings_plan["total_cost"],
                                "monthly_amount": savings_plan["monthly_amount"],
                                "timeline_months": savings_plan["timeline_months"],
                                "target_date": purchase_deadline.isoformat(),
                                "start_date": datetime.now().date().isoformat(),
                                "percentage_of_income": savings_plan["percentage_of_income"]
                            }
                        
                        # Display the recommended budget
                        st.success("AI has generated your personalized budget recommendation!")
                        
                        # Create visualization
                        budget_df = pd.DataFrame({
                            'Category': list(ai_response["allocations"].keys()),
                            'Amount': [allocation["amount"] for allocation in ai_response["allocations"].values()],
                            'Percentage': [allocation["percentage"] for allocation in ai_response["allocations"].values()]
                        })
                        
                        # Create pie chart
                        fig = px.pie(
                            budget_df, 
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
                        
                        # Display explanations and tips
                        st.subheader("Budget Strategy")
                        st.write(ai_response["summary"])
                        
                        # If saving for specific purchase, show savings plan
                        if planning_major_purchase and ai_response["savings_plan"]["item"]:
                            savings_plan = ai_response["savings_plan"]
                            st.subheader(f"Savings Plan: {savings_plan['item']}")
                            
                            savings_cols = st.columns(3)
                            with savings_cols[0]:
                                st.metric("Total Cost", f"{currency_symbol} {savings_plan['total_cost']:,.0f}")
                            with savings_cols[1]:
                                st.metric("Monthly Savings", f"{currency_symbol} {savings_plan['monthly_amount']:,.0f}")
                            with savings_cols[2]:
                                st.metric("Timeline", f"{savings_plan['timeline_months']} months")
                            
                            if savings_plan["is_realistic"]:
                                st.success(f"This savings goal is achievable with your current income!")
                            else:
                                st.warning(f"{savings_plan['recommendation']}")
                        
                        st.subheader("Category Breakdown")
                        for category in budget_df['Category']:
                            allocation = ai_response["allocations"][category]
                            with st.expander(f"{category} - {allocation['percentage']}% ({currency_symbol} {allocation['amount']:,.2f})"):
                                st.write(ai_response["explanations"][category])
                                st.subheader("Tips:")
                                for tip in ai_response["tips"][category]:
                                    st.write(f"• {tip}")
                        
                        # Save button
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("Apply This Budget"):
                                # Save budget to Firestore
                                update_data = {
                                    "budget_allocations": updated_budget,
                                    "budget_updated_at": firestore.SERVER_TIMESTAMP
                                }
                                
                                # Save savings goal if applicable
                                if planning_major_purchase and ai_response["savings_plan"]["item"]:
                                    savings_goal = {
                                        "item": savings_plan["item"],
                                        "total_cost": savings_plan["total_cost"], 
                                        "monthly_amount": savings_plan["monthly_amount"],
                                        "timeline_months": savings_plan["timeline_months"],
                                        "target_date": purchase_deadline.isoformat(),
                                        "start_date": datetime.now().date().isoformat(),
                                        "current_savings": 0,
                                        "percentage_of_income": savings_plan["percentage_of_income"]
                                    }
                                    
                                    update_data["savings_goal"] = savings_goal
                                
                                db.collection("users").document(user_id).update(update_data)
                                st.success("Budget and savings plan saved successfully!")
                        
                        with col2:
                            if st.button("Adjust Manually"):
                                st.session_state.active_tab = "Manual Setup"
                                st.rerun()
                    
                    except Exception as e:
                        st.error(f"Error generating budget recommendation: {str(e)}")
        else:
            st.info("Enable AI assistance to get personalized budget recommendations based on your financial situation.")
    
    # SAVINGS GOALS TAB
    with tab3:
        st.subheader("Set and Track Savings Goals")
        
        # Get existing savings goal if any
        existing_goal = user_data.get('savings_goal', None)
        
        if existing_goal:
            # Display existing goal
            st.write("### Current Savings Goal")
            
            # Calculate progress
            goal_item = existing_goal.get('item', 'Goal')
            goal_cost = existing_goal.get('total_cost', 0)
            goal_monthly = existing_goal.get('monthly_amount', 0)
            goal_timeline = existing_goal.get('timeline_months', 0)
            goal_start = existing_goal.get('start_date', datetime.now().date().isoformat())
            goal_target = existing_goal.get('target_date', datetime.now().date().isoformat())
            current_savings = existing_goal.get('current_savings', 0)
            
            # Convert dates
            try:
                start_date = datetime.fromisoformat(goal_start).date()
            except:
                start_date = datetime.now().date()
                
            try:
                target_date = datetime.fromisoformat(goal_target).date()
            except:
                target_date = datetime.now().date() + timedelta(days=365)
            
            # Calculate progress
            progress_percent = (current_savings / goal_cost) * 100 if goal_cost > 0 else 0
            days_elapsed = (datetime.now().date() - start_date).days
            days_total = (target_date - start_date).days
            time_progress = (days_elapsed / days_total) * 100 if days_total > 0 else 0
            
            # Display goal info
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Saving for", goal_item)
                st.metric("Total Cost", f"{currency_symbol} {goal_cost:,.2f}")
                st.metric("Monthly Contribution", f"{currency_symbol} {goal_monthly:,.2f}")
            
            with col2:
                st.metric("Current Savings", f"{currency_symbol} {current_savings:,.2f}")
                st.metric("Target Date", target_date.strftime("%Y-%m-%d"))
                st.metric("Days Remaining", f"{max(0, (target_date - datetime.now().date()).days)} days")
            
            # Display progress bars
            st.subheader("Savings Progress")
            st.progress(min(progress_percent / 100, 1.0))
            st.write(f"{progress_percent:.1f}% saved ({currency_symbol} {current_savings:,.2f} of {currency_symbol} {goal_cost:,.2f})")
            
            st.subheader("Time Progress")
            st.progress(min(time_progress / 100, 1.0))
            st.write(f"{time_progress:.1f}% of time elapsed")
            
            # Compare savings vs time progress
            if progress_percent > time_progress + 5:
                st.success(f"You're ahead of schedule by {progress_percent - time_progress:.1f}%!")
            elif time_progress > progress_percent + 5:
                st.warning(f"You're behind schedule by {time_progress - progress_percent:.1f}%. Consider increasing your monthly contributions.")
            else:
                st.info("You're on track to meet your savings goal!")
            
            # Update savings
            with st.form("update_savings"):
                st.subheader("Update Your Progress")
                new_savings = st.number_input("Current Savings Amount", min_value=0.0, value=float(current_savings))
                submit_update = st.form_submit_button("Update Progress")
                
                if submit_update:
                    # Update savings in Firestore
                    existing_goal['current_savings'] = new_savings
                    db.collection("users").document(user_id).update({
                        "savings_goal.current_savings": new_savings
                    })
                    st.success(f"Savings progress updated to {currency_symbol} {new_savings:,.2f}!")
            
            # Option to delete goal
            if st.button("Remove This Goal", type="secondary"):
                db.collection("users").document(user_id).update({
                    "savings_goal": firestore.DELETE_FIELD
                })
                st.success("Savings goal removed successfully!")
                st.rerun()
                
        else:
            # Create new goal
            st.write("### Create a New Savings Goal")
            
            with st.form("create_goal"):
                col1, col2 = st.columns(2)
                
                with col1:
                    goal_item = st.text_input("What are you saving for?", placeholder="e.g., Car, Vacation, House")
                    goal_amount = st.number_input("Total amount needed", min_value=0, step=1000)
                
                with col2:
                    goal_date = st.date_input("Target date", value=datetime.now().date() + timedelta(days=365))
                    current_amount = st.number_input("Amount already saved", min_value=0.0, step=100.0)
                
                submit_goal = st.form_submit_button("Create Savings Goal")
                
                if submit_goal:
                    if not goal_item:
                        st.error("Please enter what you're saving for.")
                    elif goal_amount <= 0:
                        st.error("Please enter a valid savings amount.")
                    else:
                        # Calculate months and monthly contribution
                        days_until = (goal_date - datetime.now().date()).days
                        months_until = max(1, round(days_until / 30))
                        amount_needed = goal_amount - current_amount
                        monthly_amount = amount_needed / months_until if months_until > 0 else amount_needed
                        
                        # Create savings goal object
                        savings_goal = {
                            "item": goal_item,
                            "total_cost": goal_amount,
                            "monthly_amount": monthly_amount,
                            "timeline_months": months_until,
                            "target_date": goal_date.isoformat(),
                            "start_date": datetime.now().date().isoformat(),
                            "current_savings": current_amount,
                            "percentage_of_income": (monthly_amount / income) * 100 if income > 0 else 0
                        }
                        
                        # Save to Firestore
                        db.collection("users").document(user_id).update({
                            "savings_goal": savings_goal
                        })
                        
                        st.success(f"Savings goal created! You'll need to save {currency_symbol} {monthly_amount:,.2f} per month to reach your goal by {goal_date.strftime('%Y-%m-%d')}.")
                        st.rerun()
    
    # Display the current allocation (if already set)
    if any(st.session_state.budget_allocations.values()):
        st.subheader("Your Current Budget Allocation")
        
        # Create dataframe for visualization
        current_df = pd.DataFrame({
            'Category': list(st.session_state.budget_allocations.keys()),
            'Amount': list(st.session_state.budget_allocations.values())
        })
        
        # Add percentage column
        current_df['Percentage'] = current_df['Amount'] / current_df['Amount'].sum() * 100
        
        # Create horizontal bar chart
        fig = px.bar(
            current_df,
            y='Category',
            x='Amount',
            orientation='h',
            text=[f"{p:.1f}%" for p in current_df['Percentage']],
            color='Category',
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        
        fig.update_layout(
            margin=dict(l=20, r=20, t=30, b=20),
            height=300,
            xaxis_title="Amount",
            yaxis_title=""
        )
        
        st.plotly_chart(fig, use_container_width=True)


def generate_simulated_ai_response(income, categories, saving_preference, has_debt, 
                                  planning_major_purchase, purchase_item, purchase_cost, 
                                  purchase_deadline, financial_goal, life_stage):
    """Generate a simulated AI response based on user inputs"""
   
    if has_debt:
        category_weights = {
            "Essentials": 0.45,
            "Lifestyle": 0.15,
            "Savings & Investments": saving_preference/100,
            "Debt & EMIs": 0.25,
            "Other / Subscriptions": 0.05
        }
    elif financial_goal == "Save for emergency fund" or financial_goal == "Save for major purchase":
        category_weights = {
            "Essentials": 0.45,
            "Lifestyle": 0.2,
            "Savings & Investments": saving_preference/100,
            "Debt & EMIs": 0.05,
            "Other / Subscriptions": 0.05
        }
    elif financial_goal == "Build long-term wealth":
        category_weights = {
            "Essentials": 0.4,
            "Lifestyle": 0.15,
            "Savings & Investments": saving_preference/100,
            "Debt & EMIs": 0.05,
            "Other / Subscriptions": 0.05
        }
    else:  # Enjoy life now or Balance
        category_weights = {
            "Essentials": 0.4,
            "Lifestyle": 0.3,
            "Savings & Investments": saving_preference/100,
            "Debt & EMIs": 0.05,
            "Other / Subscriptions": 0.05
        }
    
    # Normalize weights to ensure they sum to 1
    total_weight = sum(category_weights.values())
    if total_weight != 1.0:
        for cat in category_weights:
            category_weights[cat] /= total_weight
    
    # Map categories to generic types
    category_types = {
        "Essentials": ["Essentials", "Food & Dining", "Transportation", "Health"],
        "Lifestyle": ["Lifestyle", "Entertainment", "Shopping", "Travel"],
        "Savings & Investments": ["Savings & Investments", "Investments"],
        "Debt & EMIs": ["Debt & EMIs"],
        "Other / Subscriptions": ["Other / Subscriptions", "Subscriptions", "Gifts & Donations", "Education"]
    }
    
    # Create category mapping
    category_map = {}
    for cat in categories:
        matched = False
        for main_cat, sub_cats in category_types.items():
            if cat in sub_cats:
                category_map[cat] = main_cat
                matched = True
                break
        if not matched:
            # Default to Other if no match found
            category_map[cat] = "Other / Subscriptions"
    
    # Count categories in each type
    type_counts = {}
    for cat, cat_type in category_map.items():
        type_counts[cat_type] = type_counts.get(cat_type, 0) + 1
    
    # Allocate budget
    allocations = {}
    for cat in categories:
        cat_type = category_map.get(cat, "Other / Subscriptions")
        # Distribute the type's budget among its categories
        weight = category_weights.get(cat_type, 0.05) / max(1, type_counts.get(cat_type, 1))
        allocations[cat] = {"percentage": round(weight * 100, 1), "amount": round(income * weight, 2)}
    
    # Adjust for savings goal if applicable
    savings_plan = {
        "item": "",
        "total_cost": 0,
        "monthly_amount": 0,
        "timeline_months": 0,
        "percentage_of_income": 0,
        "is_realistic": True,
        "recommendation": ""
    }
    
    if planning_major_purchase and purchase_item and purchase_cost > 0 and purchase_deadline:
        # Calculate months until deadline
        days_until = (purchase_deadline - datetime.now().date()).days
        months_until = max(1, round(days_until / 30))
        
        # Calculate required monthly contribution
        monthly_amount = purchase_cost / months_until
        percentage_of_income = (monthly_amount / income) * 100 if income > 0 else 0
        
        # Check if savings goal is realistic
        is_realistic = percentage_of_income <= 25  # Consider unrealistic if >25% of income
        
        recommendation = ""
        if not is_realistic:
            if days_until < 365:
                new_timeline = round(purchase_cost / (income * 0.25))  # 25% of income
                recommendation = f"This goal requires {percentage_of_income:.1f}% of your income, which is high. Consider extending your timeline to {new_timeline} months."
            else:
                recommendation = f"This goal requires {percentage_of_income:.1f}% of your income. Consider reducing your target amount or extending your timeline."
        
        savings_plan = {
            "item": purchase_item,
            "total_cost": purchase_cost,
            "monthly_amount": monthly_amount,
            "timeline_months": months_until,
            "percentage_of_income": percentage_of_income,
            "is_realistic": is_realistic,
            "recommendation": recommendation
        }
        
        # Adjust budget allocations for savings goal
        savings_cats = [cat for cat in categories if "Savings" in cat or "Investments" in cat]
        if savings_cats:
            # Find savings category with highest allocation
            savings_cat = max(savings_cats, key=lambda cat: allocations.get(cat, {"amount": 0})["amount"])
            # Ensure it has enough for the savings goal
            if allocations[savings_cat]["amount"] < monthly_amount:
                # Find amount to reallocate
                shortfall = monthly_amount - allocations[savings_cat]["amount"]
                # Take from lifestyle categories proportionally
                lifestyle_cats = [cat for cat in categories if cat in category_types["Lifestyle"]]
                total_lifestyle = sum([allocations[cat]["amount"] for cat in lifestyle_cats])
                
                if total_lifestyle > shortfall:
                    for cat in lifestyle_cats:
                        reduction = (allocations[cat]["amount"] / total_lifestyle) * shortfall
                        allocations[cat]["amount"] -= reduction
                        allocations[cat]["percentage"] = (allocations[cat]["amount"] / income) * 100
                    
                    # Increase savings category
                    allocations[savings_cat]["amount"] = monthly_amount
                    allocations[savings_cat]["percentage"] = (monthly_amount / income) * 100
    
    # Create explanations and tips
    explanations = {}
    tips = {}
    
    # Common explanations and tips
    category_explanations = {
        "Essentials": f"This allocation covers your basic needs based on your {life_stage} life stage.",
        "Food & Dining": "This covers groceries and occasional dining out, balancing nutrition with budget.",
        "Transportation": "This covers your regular transportation costs while allowing for some flexibility.",
        "Health": "Health is a priority investment that shouldn't be compromised.",
        "Lifestyle": "This balanced allocation lets you enjoy life while working toward your financial goals.",
        "Entertainment": "This provides for entertainment while staying aligned with your financial goals.",
        "Shopping": "This allows for purchases while encouraging mindful spending.",
        "Travel": "This allocation lets you enjoy travel experiences within your budget.",
        "Savings & Investments": f"This {saving_preference}% savings rate helps you build wealth over time.",
        "Investments": "This allocation helps grow your wealth through strategic investments.",
        "Debt & EMIs": "Prioritizing debt reduction improves your long-term financial health.",
        "Other / Subscriptions": "This covers miscellaneous expenses and subscriptions.",
        "Subscriptions": "This covers digital services while ensuring they provide good value.",
        "Gifts & Donations": "This allows you to be generous while staying within your means.",
        "Education": "Investing in education can provide long-term returns."
    }
    
    category_tips = {
        "Essentials": ["Look for bundled services to reduce utilities cost", "Buy staples in bulk when on sale"],
        "Food & Dining": ["Meal plan weekly to reduce food waste", "Limit takeout to once a week"],
        "Transportation": ["Consider carpooling or public transport", "Keep up with vehicle maintenance to avoid costly repairs"],
        "Health": ["Use preventive care to avoid larger costs later", "Check for employer health benefits and discounts"],
        "Lifestyle": ["Create a 'fun money' allowance to avoid impulse spending", "Look for free or low-cost entertainment options"],
        "Entertainment": ["Use streaming services instead of cable", "Look for free community events"],
        "Shopping": ["Implement a 24-hour rule before making non-essential purchases", "Keep a wish list rather than buying immediately"],
        "Travel": ["Book travel during off-peak times", "Use travel rewards programs"],
        "Savings & Investments": ["Set up automatic transfers to savings on payday", "Consider tax-advantaged investment accounts"],
        "Investments": ["Diversify your investments to reduce risk", "Consider low-cost index funds for long-term growth"],
        "Debt & EMIs": ["Focus on highest-interest debt first", "Consider refinancing options for better rates"],
        "Other / Subscriptions": ["Audit your subscriptions quarterly", "Share subscription costs with family/friends"],
        "Subscriptions": ["Review all subscriptions quarterly and cancel unused ones", "Look for annual subscription options for better rates"],
        "Gifts & Donations": ["Set a gift budget at the beginning of the year", "Consider thoughtful homemade gifts"],
        "Education": ["Look for free or low-cost learning resources", "Check if your employer offers education reimbursement"]
    }
    
    # Apply explanations and tips to each category
    for cat in categories:
        explanations[cat] = category_explanations.get(cat, f"This allocation is appropriate for your {life_stage} life stage.")
        tips[cat] = category_tips.get(cat, ["Track spending in this category to identify savings opportunities", "Review this category monthly to ensure it aligns with your goals"])
    
    # Create summary
    if has_debt:
        summary = f"This budget prioritizes debt reduction while maintaining a {saving_preference}% savings rate. It ensures essential needs are covered while limiting discretionary spending to accelerate your financial freedom."
    elif planning_major_purchase:
        summary = f"This budget is designed to help you save for your {purchase_item} within {savings_plan['timeline_months']} months while maintaining a balanced lifestyle and covering your essential needs."
    elif financial_goal == "Save for emergency fund":
        summary = f"This budget focuses on building your emergency fund with a {saving_preference}% savings rate while ensuring your day-to-day needs are covered."
    elif financial_goal == "Build long-term wealth":
        summary = f"This budget emphasizes wealth building with a {saving_preference}% allocation to savings and investments, balanced with your current lifestyle needs."
    else:
        summary = f"This balanced budget allocates {saving_preference}% to savings while ensuring you can enjoy your current lifestyle and meet all essential obligations."
    
    # Create final response
    return {
        "allocations": allocations,
        "explanations": explanations,
        "tips": tips,
        "savings_plan": savings_plan,
        "summary": summary
    }