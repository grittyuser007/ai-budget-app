import streamlit as st
from firebase_admin import firestore
from shared import db
from datetime import datetime, timedelta

def onboarding_screen(user_id=None):
    if user_id is None:
        st.error("User ID is required.")
        return
    st.markdown("""
    <div class="header-banner">
        <h1>🎯 Set Up Your Profile</h1>
        <p>Let's personalize your budgeting experience</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Progress indicator
    step = st.session_state.get("onboarding_step", 1)
    total_steps = 4  # Updated to 4 steps to include budget setup
    progress = (step - 1) / (total_steps - 1) if total_steps > 1 else 0
    st.progress(progress)
    
    # Step labels
    cols = st.columns(total_steps)
    steps = ["Personal Info", "Income", "Categories", "Budget"]
    
    for i, col in enumerate(cols):
        with col:
            if i + 1 < step:
                st.markdown(f"<p style='text-align: center; color: var(--success);'>✓ {steps[i]}</p>", unsafe_allow_html=True)
            elif i + 1 == step:
                st.markdown(f"<p style='text-align: center; color: var(--primary); font-weight: bold;'>{steps[i]}</p>", unsafe_allow_html=True)
            else:
                st.markdown(f"<p style='text-align: center; color: #adb5bd;'>{steps[i]}</p>", unsafe_allow_html=True)
    
    # Step content
    if step == 1:
        with st.form("step1_form"):
            st.subheader("Tell us about yourself")
            user_type = st.selectbox("What best describes you?", 
                                  ["Student", "Salaried Employee", "Freelancer", "Business Owner", "Other"])
            name = st.text_input("Your Name")
            submit = st.form_submit_button("Continue")
            
            if submit:
                if not name:
                    st.warning("Please enter your name")
                else:
                    st.session_state.name = name
                    st.session_state.user_type = user_type
                    st.session_state.onboarding_step = 2
                    st.rerun()
    
    elif step == 2:
        with st.form("step2_form"):
            st.subheader("Income Details")
            col1, col2 = st.columns(2)
            with col1:
                income = st.number_input("Monthly Income", min_value=0, step=1000)
            with col2:
                currency = st.selectbox("Currency", ["₹ INR", "$ USD", "€ EUR", "£ GBP"])
            
            col1, col2 = st.columns(2)
            with col1:
                submit_back = st.form_submit_button("Back")
            with col2:
                submit = st.form_submit_button("Continue")
            
            if submit_back:
                st.session_state.onboarding_step = 1
                st.rerun()
            
            if submit:
                if income <= 0:
                    st.warning("Please enter your income")
                else:
                    st.session_state.income = income
                    st.session_state.currency = currency
                    st.session_state.onboarding_step = 3
                    st.rerun()
                    
    elif step == 3:
        with st.form("step3_form"):
            st.subheader("Spending Categories")
            st.markdown("Select spending categories relevant to your lifestyle:")

            # Suggested categories list
            all_categories = [
                "🏠 Essentials (Rent, Utilities)", 
                "🚌 Transportation",
                "🍔 Food & Dining",
                "🎬 Entertainment",
                "🛍️ Shopping",
                "💊 Health",
                "📚 Education",
                "📱 Subscriptions",
                "💸 Investments",
                "🎁 Gifts & Donations",
                "✈️ Travel"
            ]

            # You can customize this list dynamically based on st.session_state.user_type too
            default_selection = all_categories[:4]

            selected_categories = st.multiselect(
                "Choose your categories:", 
                all_categories, 
                default=default_selection
            )

            col1, col2 = st.columns(2)
            with col1:
                back_btn = st.form_submit_button("Back")
            with col2:
                continue_btn = st.form_submit_button("Continue")

            if back_btn:
                st.session_state.onboarding_step = 2
                st.rerun()

            if continue_btn:
                if len(selected_categories) == 0:
                    st.warning("Please select at least one category.")
                else:
                    # Store selected categories in session state
                    st.session_state.categories = selected_categories
                    st.session_state.onboarding_step = 4
                    st.rerun()
    
    elif step == 4:
        st.subheader("Budget Allocation")
        st.write("Let's set up your initial budget allocation.")
        
        # Get categories from session state
        categories = st.session_state.get("categories", [])
        clean_categories = [cat.split(" ", 1)[1] if " " in cat else cat for cat in categories]
        
        if not clean_categories:
            clean_categories = ["Essentials", "Lifestyle", "Savings & Investments", "Debt & EMIs", "Other / Subscriptions"]
        
        st.write("Based on your selected categories, we'll help you create a balanced budget.")
        
        # Choose between quick setup and detailed setup
        setup_option = st.radio(
            "How would you like to set up your budget?",
            ["Quick Setup (50/30/20 rule)", "AI Recommendation", "Skip for now"]
        )
        
        if setup_option == "Quick Setup (50/30/20 rule)":
            st.write("The 50/30/20 rule suggests spending 50% on needs, 30% on wants, and 20% on savings.")
            
            # Classify user categories
            essentials = []
            lifestyle = []
            savings = []
            debt = []
            other = []
            
            # Category classification dictionary
            category_types = {
                "Essentials": ["Essentials", "Food & Dining", "Transportation", "Health"],
                "Lifestyle": ["Lifestyle", "Entertainment", "Shopping", "Travel"],
                "Savings": ["Savings & Investments", "Investments"],
                "Debt": ["Debt & EMIs"],
                "Other": ["Other / Subscriptions", "Subscriptions", "Education", "Gifts & Donations"]
            }
            
            # Simple category sorting logic
            for cat in clean_categories:
                if cat in category_types["Essentials"]:
                    essentials.append(cat)
                elif cat in category_types["Lifestyle"]:
                    lifestyle.append(cat)
                elif cat in category_types["Savings"]:
                    savings.append(cat)
                elif cat in category_types["Debt"]:
                    debt.append(cat)
                else:
                    other.append(cat)
            
            # Calculate budget allocations
            income = st.session_state.get("income", 0)
            budget_allocations = {}
            
            # Distribute essentials (50%)
            if essentials:
                per_essential = (income * 0.5) / len(essentials)
                for cat in essentials:
                    budget_allocations[cat] = per_essential
                    
            # Distribute lifestyle (30%)
            if lifestyle:
                per_lifestyle = (income * 0.3) / len(lifestyle)
                for cat in lifestyle:
                    budget_allocations[cat] = per_lifestyle
                    
            # Distribute savings (15%)
            if savings:
                per_savings = (income * 0.15) / len(savings)
                for cat in savings:
                    budget_allocations[cat] = per_savings
                    
            # Distribute debt (5%)
            if debt:
                per_debt = (income * 0.05) / len(debt)
                for cat in debt:
                    budget_allocations[cat] = per_debt
                    
            # Distribute other
            if other:
                remaining = income - sum(budget_allocations.values())
                per_other = max(0, remaining) / len(other)
                for cat in other:
                    budget_allocations[cat] = per_other
            
            # Ensure all categories are covered
            for cat in clean_categories:
                if cat not in budget_allocations:
                    # Allocate a small default amount for any missing categories
                    budget_allocations[cat] = income * 0.05
            
            # Display budget distribution
            currency = st.session_state.get("currency", "₹ INR").split()[0]
            
            # Create columns based on number of categories (max 3 per row)
            cols_per_row = 3
            rows = (len(clean_categories) + cols_per_row - 1) // cols_per_row
            
            for row in range(rows):
                cols = st.columns(cols_per_row)
                for col_idx in range(cols_per_row):
                    idx = row * cols_per_row + col_idx
                    if idx < len(clean_categories):
                        cat = clean_categories[idx]
                        amount = budget_allocations.get(cat, 0)
                        percent = (amount / income) * 100 if income > 0 else 0
                        with cols[col_idx]:
                            st.metric(cat, f"{currency} {amount:,.0f}", f"{percent:.1f}%")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Back"):
                    st.session_state.onboarding_step = 3
                    st.rerun()
            with col2:
                if st.button("Complete Setup", type="primary"):
                    # Build and save user data
                    user_data = {
                        "name": st.session_state.get("name", ""),
                        "user_type": st.session_state.get("user_type", ""),
                        "income": st.session_state.get("income", 0),
                        "currency": st.session_state.get("currency", "₹ INR"),
                        "categories": st.session_state.get("categories", []),
                        "budget_allocations": budget_allocations,
                        "profile_set": True,
                        "onboarding_completed_at": firestore.SERVER_TIMESTAMP
                    }
                    
                    try:
                        db.collection("users").document(user_id).set(user_data, merge=True)
                        st.success("✅ Profile setup complete!")
                        st.session_state.onboarded = True
                        st.balloons()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to save data: {e}")
        
        elif setup_option == "AI Recommendation":
            st.write("We'll help you create a personalized budget based on your income and preferences.")
            
            # Collect user preferences for AI recommendation
            col1, col2 = st.columns(2)
            with col1:
                financial_goal = st.selectbox(
                    "What's your primary financial goal?",
                    ["Save for emergency fund", "Pay off debt", "Save for major purchase", 
                     "Build long-term wealth", "Enjoy life now", "Balance savings and lifestyle"]
                )
            with col2:
                saving_preference = st.slider(
                    "Desired savings rate (%)",
                    5, 50, 20, 5
                )
            
            has_debt = st.checkbox("I have significant debt to pay off")
            
            # Check if user is saving for a specific purchase
            is_saving_for_purchase = st.checkbox("I'm saving for a specific purchase")
            purchase_item = ""
            purchase_amount = 0
            purchase_deadline = None
            
            if is_saving_for_purchase:
                col1, col2 = st.columns(2)
                with col1:
                    purchase_item = st.text_input("What are you saving for?", placeholder="e.g., Car, Vacation, House")
                    purchase_amount = st.number_input("Estimated cost", min_value=0, step=1000)
                with col2:
                    purchase_deadline = st.date_input("Target date", value=datetime.now() + timedelta(days=365))
            
            if st.button("Generate Budget Plan"):
                with st.spinner("Creating your personalized budget plan..."):
                    # Classify user categories
                    essentials = []
                    lifestyle = []
                    savings = []
                    debt = []
                    other = []
                    
                    # Category classification dictionary
                    category_types = {
                        "Essentials": ["Essentials", "Food & Dining", "Transportation", "Health"],
                        "Lifestyle": ["Lifestyle", "Entertainment", "Shopping", "Travel"],
                        "Savings": ["Savings & Investments", "Investments"],
                        "Debt": ["Debt & EMIs"],
                        "Other": ["Other / Subscriptions", "Subscriptions", "Education", "Gifts & Donations"]
                    }
                    
                    # Sort categories
                    for cat in clean_categories:
                        if cat in category_types["Essentials"]:
                            essentials.append(cat)
                        elif cat in category_types["Lifestyle"]:
                            lifestyle.append(cat)
                        elif cat in category_types["Savings"]:
                            savings.append(cat)
                        elif cat in category_types["Debt"]:
                            debt.append(cat)
                        else:
                            other.append(cat)
                    
                    # Calculate budget allocations based on user preferences
                    income = st.session_state.get("income", 0)
                    budget_allocations = {}
                    
                    # Adjust percentages based on goals and preferences
                    if has_debt:
                        essentials_pct = 45
                        lifestyle_pct = 20
                        savings_pct = saving_preference
                        debt_pct = 25
                        other_pct = 10 - (saving_preference - 10) if saving_preference > 10 else 10
                    elif financial_goal in ["Save for emergency fund", "Save for major purchase"]:
                        essentials_pct = 50
                        lifestyle_pct = 30 - (saving_preference - 10) if saving_preference > 10 else 30
                        savings_pct = saving_preference
                        debt_pct = 5
                        other_pct = 5
                    elif financial_goal == "Build long-term wealth":
                        essentials_pct = 45
                        lifestyle_pct = 25
                        savings_pct = saving_preference
                        debt_pct = 5
                        other_pct = 100 - (essentials_pct + lifestyle_pct + savings_pct + debt_pct)
                    else:  # Enjoy life or balanced
                        essentials_pct = 50
                        lifestyle_pct = 35
                        savings_pct = saving_preference
                        debt_pct = 5
                        other_pct = 100 - (essentials_pct + lifestyle_pct + savings_pct + debt_pct)
                        
                    # Normalize to 100%
                    total = essentials_pct + lifestyle_pct + savings_pct + debt_pct + other_pct
                    if total != 100:
                        factor = 100 / total
                        essentials_pct *= factor
                        lifestyle_pct *= factor
                        savings_pct *= factor
                        debt_pct *= factor
                        other_pct *= factor
                    
                    # Distribute essentials
                    if essentials:
                        per_essential = (income * essentials_pct/100) / len(essentials)
                        for cat in essentials:
                            budget_allocations[cat] = per_essential
                            
                    # Distribute lifestyle
                    if lifestyle:
                        per_lifestyle = (income * lifestyle_pct/100) / len(lifestyle)
                        for cat in lifestyle:
                            budget_allocations[cat] = per_lifestyle
                            
                    # Distribute savings
                    if savings:
                        per_savings = (income * savings_pct/100) / len(savings)
                        for cat in savings:
                            budget_allocations[cat] = per_savings
                            
                    # Distribute debt
                    if debt:
                        per_debt = (income * debt_pct/100) / len(debt)
                        for cat in debt:
                            budget_allocations[cat] = per_debt
                            
                    # Distribute other
                    if other:
                        per_other = (income * other_pct/100) / len(other)
                        for cat in other:
                            budget_allocations[cat] = per_other
                    
                    # Ensure all categories are covered
                    for cat in clean_categories:
                        if cat not in budget_allocations:
                            # Allocate a small default amount for any missing categories
                            budget_allocations[cat] = income * 0.05
                    
                    # Create savings goal if applicable
                    savings_goal = None
                    if is_saving_for_purchase and purchase_item and purchase_amount > 0 and purchase_deadline:
                        days_until = (purchase_deadline - datetime.now().date()).days
                        months_until = max(1, round(days_until / 30))
                        monthly_amount = purchase_amount / months_until
                        
                        # Check if savings goal is realistic
                        percentage_of_income = (monthly_amount / income) * 100 if income > 0 else 0
                        is_realistic = percentage_of_income <= 25  # Consider unrealistic if >25% of income
                        
                        savings_goal = {
                            "item": purchase_item,
                            "total_cost": purchase_amount,
                            "monthly_amount": monthly_amount,
                            "timeline_months": months_until,
                            "target_date": purchase_deadline.isoformat(),
                            "start_date": datetime.now().date().isoformat(),
                            "current_savings": 0,
                            "percentage_of_income": percentage_of_income
                        }
                        
                        # If user has savings category and goal is realistic, adjust budget
                        if savings and is_realistic:
                            # Ensure savings category has enough for the monthly goal amount
                            savings_cat = savings[0]  # Use first savings category
                            if budget_allocations[savings_cat] < monthly_amount:
                                # Take proportionally from lifestyle categories
                                shortfall = monthly_amount - budget_allocations[savings_cat]
                                
                                if lifestyle:
                                    reduction_per_cat = shortfall / len(lifestyle)
                                    for cat in lifestyle:
                                        budget_allocations[cat] = max(0, budget_allocations[cat] - reduction_per_cat)
                                
                                budget_allocations[savings_cat] = monthly_amount
                    
                    # Display the AI-generated budget
                    st.success("Budget plan generated!")
                    
                    currency = st.session_state.get("currency", "₹ INR").split()[0]
                    
                    # Create columns based on number of categories (max 3 per row)
                    cols_per_row = 3
                    rows = (len(clean_categories) + cols_per_row - 1) // cols_per_row
                    
                    for row in range(rows):
                        cols = st.columns(cols_per_row)
                        for col_idx in range(cols_per_row):
                            idx = row * cols_per_row + col_idx
                            if idx < len(clean_categories):
                                cat = clean_categories[idx]
                                amount = budget_allocations.get(cat, 0)
                                percent = (amount / income) * 100 if income > 0 else 0
                                with cols[col_idx]:
                                    st.metric(cat, f"{currency} {amount:,.0f}", f"{percent:.1f}%")
                    
                    # If saving for a specific purchase, show savings plan
                    if savings_goal:
                        st.subheader(f"Savings Plan: {savings_goal['item']}")
                        
                        cols = st.columns(3)
                        with cols[0]:
                            st.metric("Total Cost", f"{currency} {savings_goal['total_cost']:,.0f}")
                        with cols[1]:
                            st.metric("Monthly Savings", f"{currency} {savings_goal['monthly_amount']:,.0f}")
                        with cols[2]:
                            st.metric("Timeline", f"{savings_goal['timeline_months']} months")
                        
                        if savings_goal["percentage_of_income"] > 25:
                            st.warning(f"This savings goal requires {savings_goal['percentage_of_income']:.1f}% of your income, which may be challenging. Consider extending your timeline or reducing the target amount.")
                        else:
                            st.success(f"This savings goal is achievable with your current income!")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("Back to Categories"):
                            st.session_state.onboarding_step = 3
                            st.rerun()
                    
                    with col2:
                        if st.button("Accept and Complete Setup", type="primary"):
                            # Build and save user data
                            user_data = {
                                "name": st.session_state.get("name", ""),
                                "user_type": st.session_state.get("user_type", ""),
                                "income": st.session_state.get("income", 0),
                                "currency": st.session_state.get("currency", "₹ INR"),
                                "categories": st.session_state.get("categories", []),
                                "budget_allocations": budget_allocations,
                                "profile_set": True,
                                "onboarding_completed_at": firestore.SERVER_TIMESTAMP
                            }
                            
                            # Add savings goal if applicable
                            if savings_goal:
                                user_data["savings_goal"] = savings_goal
                            
                            try:
                                db.collection("users").document(user_id).set(user_data, merge=True)
                                st.success("✅ Profile setup complete!")
                                st.session_state.onboarded = True
                                st.balloons()
                                st.rerun()
                            except Exception as e:
                                st.error(f"Failed to save data: {e}")
        
        else:  # Skip for now
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Back to Categories"):
                    st.session_state.onboarding_step = 3
                    st.rerun()
            with col2:
                if st.button("Complete Setup", type="primary"):
                    # Build and save user data without budget allocations
                    user_data = {
                        "name": st.session_state.get("name", ""),
                        "user_type": st.session_state.get("user_type", ""),
                        "income": st.session_state.get("income", 0),
                        "currency": st.session_state.get("currency", "₹ INR"),
                        "categories": st.session_state.get("categories", []),
                        "profile_set": True,
                        "onboarding_completed_at": firestore.SERVER_TIMESTAMP
                    }
                    
                    try:
                        db.collection("users").document(user_id).set(user_data, merge=True)
                        st.success("✅ Profile setup complete!")
                        st.session_state.onboarded = True
                        st.balloons()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to save data: {e}")