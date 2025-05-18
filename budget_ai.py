import os
import json
import time
from datetime import timedelta, datetime
import requests
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

def get_ai_budget_recommendation(income, categories, saving_preference, has_debt, 
                               planning_major_purchase, purchase_item="", purchase_cost=0, 
                               purchase_deadline=None, financial_goal="", life_stage="", custom_notes="",
                               currency_symbol="₹"):
    """
    Get budget recommendations using Gemini API with fallback to simulated response
    
    Args:
        income (float): Monthly income amount
        categories (list): List of budget categories
        saving_preference (float): Desired savings percentage
        has_debt (bool): Whether the user has significant debt
        planning_major_purchase (bool): Whether planning a major purchase
        purchase_item (str): Item to be purchased
        purchase_cost (float): Cost of the planned purchase
        purchase_deadline (datetime.date): Deadline for the purchase
        financial_goal (str): Primary financial goal
        life_stage (str): User's life stage
        custom_notes (str): Additional notes
        currency_symbol (str): Currency symbol
        
    Returns:
        dict: Budget recommendation data
    """
    try:
        # First try using Gemini API
        api_response = get_gemini_recommendation(
            income=income,
            categories=categories,
            saving_preference=saving_preference,
            has_debt=has_debt,
            planning_major_purchase=planning_major_purchase,
            purchase_item=purchase_item,
            purchase_cost=purchase_cost,
            purchase_deadline=purchase_deadline,
            financial_goal=financial_goal,
            life_stage=life_stage,
            custom_notes=custom_notes,
            currency_symbol=currency_symbol
        )
        
        # If successful, return the Gemini response
        if api_response:
            return api_response
            
    except Exception as e:
        print(f"Error calling Gemini API: {str(e)}")
        
    # Fall back to simulated response if Gemini API call fails
    return generate_simulated_ai_response(
        income=income,
        categories=categories,
        saving_preference=saving_preference,
        has_debt=has_debt,
        planning_major_purchase=planning_major_purchase,
        purchase_item=purchase_item,
        purchase_cost=purchase_cost,
        purchase_deadline=purchase_deadline,
        financial_goal=financial_goal,
        life_stage=life_stage
    )


def get_gemini_recommendation(income, categories, saving_preference, has_debt, 
                          planning_major_purchase, purchase_item, purchase_cost, 
                          purchase_deadline, financial_goal, life_stage, custom_notes="",
                          currency_symbol="₹"):
    """
    Get budget recommendations using Gemini API
    
    Args:
        Same as get_ai_budget_recommendation
        
    Returns:
        dict: Budget recommendation data or None if API call fails
    """
    # Initialize Gemini client
    # You'll need to sign up at https://makersuite.google.com/ and get your API key
    api_key = os.environ.get("GEMINI_API_KEY", "")  # Get from environment variable
    
    # If no API key found, try to read from file
    if not api_key:
        try:
            with open("gemini_key.txt", "r") as file:
                api_key = file.read().strip()
        except (FileNotFoundError, IOError):
            # If still no API key, return None to trigger fallback
            return None

    # Initialize Gemini client
    try:
        genai.configure(api_key=api_key)
    except Exception as e:
        print(f"Failed to initialize Gemini client: {str(e)}")
        # If Gemini client initialization fails, try direct API call with requests
        return get_gemini_api_fallback(
            api_key=api_key, 
            income=income,
            categories=categories,
            saving_preference=saving_preference,
            has_debt=has_debt,
            planning_major_purchase=planning_major_purchase,
            purchase_item=purchase_item,
            purchase_cost=purchase_cost,
            purchase_deadline=purchase_deadline,
            financial_goal=financial_goal,
            life_stage=life_stage,
            custom_notes=custom_notes,
            currency_symbol=currency_symbol
        )
    
    # Create prompt for AI that includes user-selected categories
    prompt = create_budget_prompt(
        income=income,
        categories=categories,
        saving_preference=saving_preference,
        has_debt=has_debt,
        planning_major_purchase=planning_major_purchase,
        purchase_item=purchase_item,
        purchase_cost=purchase_cost,
        purchase_deadline=purchase_deadline,
        financial_goal=financial_goal,
        life_stage=life_stage,
        custom_notes=custom_notes,
        currency_symbol=currency_symbol
    )
    
    try:
        # Configure the model
        generation_config = {
            "temperature": 0.1,
            "top_p": 0.9,
            "top_k": 40,
            "max_output_tokens": 2048,
        }
        
        safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }
        
        model = genai.GenerativeModel(
            model_name="gemini-1.5-pro",
            generation_config=generation_config,
            safety_settings=safety_settings
        )
        
        # Create system instructions and user message
        system_instruction = "You are a financial advisor expert who specializes in personal budgeting and financial planning."
        
        convo = model.start_chat(history=[
            {"role": "user", "parts": [system_instruction]},
            {"role": "model", "parts": ["I'm ready to provide expert financial advice and budgeting guidance."]}
        ])
        
        # Send the prompt
        response = convo.send_message(prompt)
        response_text = response.text
        
        # Extract JSON from response text
        try:
            # Find JSON within response (between triple backticks or just the JSON)
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                json_text = response_text[json_start:json_end]
                ai_response = json.loads(json_text)
                
                # Ensure the AI response has all required keys
                return validate_and_fix_ai_response(
                    ai_response=ai_response,
                    categories=categories,
                    income=income,
                    planning_major_purchase=planning_major_purchase,
                    purchase_item=purchase_item,
                    purchase_cost=purchase_cost,
                    purchase_deadline=purchase_deadline
                )
                
        except Exception as e:
            print(f"Error parsing Gemini response: {e}")
            print(f"Response text: {response_text[:300]}...")
            return None
            
    except Exception as e:
        print(f"Gemini API call error: {str(e)}")
        return None


def get_gemini_api_fallback(api_key, income, categories, saving_preference, has_debt, 
                        planning_major_purchase, purchase_item, purchase_cost, 
                        purchase_deadline, financial_goal, life_stage, custom_notes="",
                        currency_symbol="₹"):
    """
    Fallback method using direct requests to Gemini API
    
    Args:
        Same as get_ai_budget_recommendation, plus api_key
        
    Returns:
        dict: Budget recommendation data or None if direct API call fails
    """
    prompt = create_budget_prompt(
        income=income,
        categories=categories,
        saving_preference=saving_preference,
        has_debt=has_debt,
        planning_major_purchase=planning_major_purchase,
        purchase_item=purchase_item,
        purchase_cost=purchase_cost,
        purchase_deadline=purchase_deadline,
        financial_goal=financial_goal,
        life_stage=life_stage,
        custom_notes=custom_notes,
        currency_symbol=currency_symbol
    )
    
    headers = {
        "Content-Type": "application/json",
    }
    
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": "You are a financial advisor expert who specializes in personal budgeting and financial planning."}]
            },
            {
                "role": "model",
                "parts": [{"text": "I'm ready to provide expert financial advice and budgeting guidance."}]
            },
            {
                "role": "user",
                "parts": [{"text": prompt}]
            }
        ],
        "generationConfig": {
            "temperature": 0.1,
            "topP": 0.9,
            "topK": 40,
            "maxOutputTokens": 2048,
        }
    }
    
    try:
        response = requests.post(
            f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-pro:generateContent?key={api_key}",
            headers=headers,
            json=payload,
            timeout=30  # Add timeout to prevent hanging
        )
        
        if response.status_code == 200:
            response_data = response.json()
            response_text = response_data["candidates"][0]["content"]["parts"][0]["text"]
            
            # Extract JSON from response text
            try:
                json_start = response_text.find('{')
                json_end = response_text.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    json_text = response_text[json_start:json_end]
                    ai_response = json.loads(json_text)
                    
                    # Ensure the AI response has all required keys
                    return validate_and_fix_ai_response(
                        ai_response=ai_response,
                        categories=categories,
                        income=income,
                        planning_major_purchase=planning_major_purchase,
                        purchase_item=purchase_item,
                        purchase_cost=purchase_cost,
                        purchase_deadline=purchase_deadline
                    )
                    
            except Exception as e:
                print(f"Error parsing direct API response: {e}")
                return None
        else:
            print(f"Direct API call failed with status code {response.status_code}: {response.text}")
            return None
            
    except Exception as e:
        print(f"Error in direct API call: {str(e)}")
        return None


def create_budget_prompt(income, categories, saving_preference, has_debt, 
                       planning_major_purchase, purchase_item, purchase_cost, 
                       purchase_deadline, financial_goal, life_stage, custom_notes="",
                       currency_symbol="₹"):
    """
    Create a well-formatted prompt for the AI
    
    Args:
        Same as get_ai_budget_recommendation
        
    Returns:
        str: Formatted prompt for AI
    """
   
    formatted_income = f"{income:,.2f}"
    
    prompt = f"""
As a financial advisor, create a monthly budget allocation for a person with the following profile:
- Monthly income: {currency_symbol} {formatted_income}
- Primary financial goal: {financial_goal}
- Life stage: {life_stage}
- Desired savings rate: {saving_preference}%
- Has significant debt: {"Yes" if has_debt else "No"}
- Planning major purchase soon: {"Yes" if planning_major_purchase else "No"}
"""

    # Add purchase details if applicable
    if planning_major_purchase and purchase_item and purchase_cost > 0 and purchase_deadline:
        days_until_goal = (purchase_deadline - datetime.now().date()).days
        months_until = max(1, round(days_until_goal / 30))
        formatted_cost = f"{purchase_cost:,.2f}"
        prompt += f"""
- Saving for: {purchase_item}
- Estimated cost: {currency_symbol} {formatted_cost}
- Target date: {purchase_deadline.strftime('%Y-%m-%d')} ({days_until_goal} days from now)
- Timeline: Approximately {months_until} months
"""

    if custom_notes:
        prompt += f"- Additional context: {custom_notes}\n"

    prompt += """
Allocate the monthly income ONLY across these specific user-selected categories:
""" + ", ".join(categories) + """

For each category:
- Provide the recommended allocation as both a percentage and an absolute amount
- Give a brief explanation of the reasoning based on the user's situation
- Provide 1-2 tips for optimizing spending in this category

If the user is saving for a specific purchase, create a dedicated savings plan that shows:
- Monthly amount needed to reach the goal by the deadline
- Percentage of income this represents
- Whether this saving goal is realistic given their income and other expenses
- Suggestions for adjusting the timeline if the goal is not realistic

Return the response ONLY as a valid JSON object with this exact structure:
```json
{
    "allocations": {
        "Category1": {"percentage": 10, "amount": 1000},
        "Category2": {"percentage": 20, "amount": 2000}
    },
    "explanations": {
        "Category1": "Explanation text...",
        "Category2": "Explanation text..."
    },
    "tips": {
        "Category1": ["Tip 1", "Tip 2"],
        "Category2": ["Tip 1", "Tip 2"]
    },
    "savings_plan": {
        "item": "Name of item or empty if none",
        "total_cost": 10000,
        "monthly_amount": 500,
        "timeline_months": 20,
        "percentage_of_income": 10,
        "is_realistic": true,
        "recommendation": "Recommendation text if adjustment needed"
    },
    "summary": "Overall budget strategy summary..."
}
```

Make sure all budget allocations correctly add up to 100% of income (or very close to it), and that you include ALL the categories I listed above in your response.
"""
    
    return prompt


def validate_and_fix_ai_response(ai_response, categories, income, planning_major_purchase=False,
                               purchase_item="", purchase_cost=0, purchase_deadline=None):
    """
    Validate and fix the AI response to ensure it has all required keys and data
    
    Args:
        ai_response (dict): Response from AI
        categories (list): Budget categories
        income (float): Monthly income
        planning_major_purchase (bool): Whether planning a major purchase
        purchase_item (str): Item being purchased
        purchase_cost (float): Cost of purchase
        purchase_deadline (datetime.date): Deadline for purchase
        
    Returns:
        dict: Validated and fixed AI response
    """
    # Check for required keys
    required_keys = ["allocations", "explanations", "tips", "summary"]
    missing_keys = [key for key in required_keys if key not in ai_response]
    
    if missing_keys:
        print(f"Missing keys in AI response: {missing_keys}")
        for key in missing_keys:
            if key == "allocations":
                ai_response["allocations"] = {}
            elif key == "explanations":
                ai_response["explanations"] = {}
            elif key == "tips":
                ai_response["tips"] = {}
            elif key == "summary":
                ai_response["summary"] = "This budget is designed to balance your needs and financial goals."
    
    # Ensure all categories are covered
    for category in categories:
        if category not in ai_response.get("allocations", {}):
            # Default allocation of 5% for missing categories
            ai_response.setdefault("allocations", {})[category] = {"percentage": 5, "amount": income * 0.05}
            
        if category not in ai_response.get("explanations", {}):
            ai_response.setdefault("explanations", {})[category] = f"This allocation for {category} is based on your financial profile."
            
        if category not in ai_response.get("tips", {}):
            ai_response.setdefault("tips", {})[category] = ["Track spending in this category", "Review periodically to ensure it aligns with your priorities"]
    

    total_percentage = sum(alloc.get("percentage", 0) for alloc in ai_response.get("allocations", {}).values())
    
    if abs(total_percentage - 100) > 5:  # If more than 5% off from 100%
        # Normalize the percentages
        factor = 100 / total_percentage if total_percentage > 0 else 1
        for cat, alloc in ai_response.get("allocations", {}).items():
            new_percentage = alloc.get("percentage", 0) * factor
            alloc["percentage"] = round(new_percentage, 1)
            alloc["amount"] = round(income * new_percentage / 100, 2)
    
    # Add savings plan if needed
    if planning_major_purchase and purchase_item and purchase_cost > 0 and purchase_deadline:
        if "savings_plan" not in ai_response or not ai_response.get("savings_plan", {}).get("item"):
            days_until_goal = (purchase_deadline - datetime.now().date()).days
            months_until = max(1, round(days_until_goal / 30))
            monthly_amount = purchase_cost / months_until
            percentage = (monthly_amount / income) * 100
            
            ai_response["savings_plan"] = {
                "item": purchase_item,
                "total_cost": purchase_cost,
                "monthly_amount": round(monthly_amount, 2),
                "timeline_months": months_until,
                "percentage_of_income": round(percentage, 2),
                "is_realistic": percentage <= 25,
                "recommendation": f"Save {monthly_amount:,.2f} monthly to reach your goal."
            }
    
    return ai_response


def generate_simulated_ai_response(income, categories, saving_preference, has_debt, 
                                 planning_major_purchase, purchase_item="", purchase_cost=0, 
                                 purchase_deadline=None, financial_goal="", life_stage=""):
    """
    Generate a simulated AI response based on user inputs
    
    Returns:
        dict: Simulated budget recommendation
    """
    
    
    if has_debt:
        category_weights = {
            "Essentials": 0.45,
            "Lifestyle": 0.15,
            "Savings & Investments": saving_preference / 100,
            "Debt & EMIs": 0.25,
            "Other / Subscriptions": 0.05
        }
    elif financial_goal in ["Save for emergency fund", "Save for major purchase"]:
        category_weights = {
            "Essentials": 0.45,
            "Lifestyle": 0.2,
            "Savings & Investments": saving_preference / 100,
            "Debt & EMIs": 0.05,
            "Other / Subscriptions": 0.05
        }
    elif financial_goal == "Build long-term wealth":
        category_weights = {
            "Essentials": 0.4,
            "Lifestyle": 0.15,
            "Savings & Investments": saving_preference / 100,
            "Debt & EMIs": 0.05,
            "Other / Subscriptions": 0.05
        }
    else:
        category_weights = {
            "Essentials": 0.4,
            "Lifestyle": 0.3,
            "Savings & Investments": saving_preference / 100,
            "Debt & EMIs": 0.05,
            "Other / Subscriptions": 0.05
        }

    
    total_weight = sum(category_weights.values())
    if total_weight != 1.0:
        for cat in category_weights:
            category_weights[cat] /= total_weight

    
    category_types = {
        "Essentials": ["Essentials", "Food & Dining", "Transportation", "Health"],
        "Lifestyle": ["Lifestyle", "Entertainment", "Shopping", "Travel"],
        "Savings & Investments": ["Savings & Investments", "Investments"],
        "Debt & EMIs": ["Debt & EMIs"],
        "Other / Subscriptions": ["Other / Subscriptions", "Subscriptions", "Gifts & Donations", "Education"]
    }

    category_map = {}
    for cat in categories:
        for main_cat, sub_cats in category_types.items():
            if cat in sub_cats:
                category_map[cat] = main_cat
                break
        else:
            category_map[cat] = "Other / Subscriptions"

    # Count how many categories fall into each type
    type_counts = {}
    for cat_type in category_map.values():
        type_counts[cat_type] = type_counts.get(cat_type, 0) + 1

    # Calculate allocation per category
    allocations = {}
    for cat in categories:
        main_type = category_map[cat]
        weight = category_weights.get(main_type, 0) / max(1, type_counts.get(main_type, 1))
        amount = round(income * weight, 2)
        allocations[cat] = {
            "percentage": round(weight * 100, 1),
            "amount": amount
        }

    # Savings plan setup
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
        days_until = (purchase_deadline - datetime.now().date()).days
        months_until = max(1, round(days_until / 30))
        monthly_amount = purchase_cost / months_until
        perc_income = (monthly_amount / income) * 100 if income > 0 else 0
        is_realistic = perc_income <= 25

        recommendation = ""
        if not is_realistic:
            if days_until < 365:
                new_timeline = round(purchase_cost / (income * 0.25))
                recommendation = f"This goal requires {perc_income:.1f}% of your income, which is high. Consider extending your timeline to {new_timeline} months."
            else:
                recommendation = f"This goal requires {perc_income:.1f}% of your income. Consider reducing your target amount or extending your timeline."

        savings_plan = {
            "item": purchase_item,
            "total_cost": purchase_cost,
            "monthly_amount": round(monthly_amount, 2),
            "timeline_months": months_until,
            "percentage_of_income": round(perc_income, 2),
            "is_realistic": is_realistic,
            "recommendation": recommendation
        }

        # Adjust allocations
        savings_cats = [cat for cat in categories if "Savings" in cat or "Investments" in cat]
        if savings_cats:
            savings_cat = max(savings_cats, key=lambda c: allocations.get(c, {"amount": 0})["amount"])
            shortfall = monthly_amount - allocations[savings_cat]["amount"]
            if shortfall > 0:
                lifestyle_cats = [c for c in categories if c in category_types["Lifestyle"]]
                total_lifestyle = sum([allocations[c]["amount"] for c in lifestyle_cats])
                if total_lifestyle > shortfall:
                    for c in lifestyle_cats:
                        reduce_amt = (allocations[c]["amount"] / total_lifestyle) * shortfall
                        allocations[c]["amount"] -= reduce_amt
                        allocations[c]["percentage"] = round((allocations[c]["amount"] / income) * 100, 1)
                    allocations[savings_cat]["amount"] = monthly_amount
                    allocations[savings_cat]["percentage"] = round((monthly_amount / income) * 100, 1)

    # Tips and explanations
    explanations = {}
    tips = {}

    common_explanations = {
        "Essentials": f"This allocation covers your basic needs based on your {life_stage} life stage.",
        "Food & Dining": "This covers groceries and occasional dining out.",
        "Transportation": "Covers your regular transport costs with some flexibility.",
        "Health": "Health is essential for stability.",
        "Lifestyle": "Lets you enjoy life within limits.",
        "Entertainment": "Entertainment to recharge yourself.",
        "Shopping": "Encourages smart spending habits.",
        "Travel": "Allows budget-conscious exploration.",
        "Savings & Investments": f"This {saving_preference}% savings rate helps build your financial future.",
        "Investments": "Helps grow your wealth.",
        "Debt & EMIs": "Reducing debt enhances future flexibility.",
        "Other / Subscriptions": "Covers various miscellaneous expenses.",
        "Subscriptions": "Manage your recurring digital expenses.",
        "Gifts & Donations": "For giving back, wisely.",
        "Education": "Boosts your career and learning."
    }

    sample_tips = {
        "Essentials": ["Bundle services to cut utility costs", "Buy groceries in bulk"],
        "Food & Dining": ["Limit eating out", "Meal prep to save money"],
        "Transportation": ["Use public transport", "Maintain your vehicle"],
        "Health": ["Use preventive care", "Check employer health benefits"],
        "Lifestyle": ["Set a 'fun budget'", "Look for free events"],
        "Savings & Investments": ["Automate savings", "Use tax-saving accounts"],
        "Debt & EMIs": ["Pay high-interest debt first", "Consider refinancing"],
        "Other / Subscriptions": ["Audit quarterly", "Cancel unused ones"],
        "Education": ["Use free resources", "Check for online course discounts"]
    }

    for cat in categories:
        explanations[cat] = common_explanations.get(cat, f"This allocation is suited to your {life_stage} life stage.")
        tips[cat] = sample_tips.get(cat, ["Track this category monthly", "Look for ways to reduce recurring costs"])

    # Summary
    if has_debt:
        summary = f"This budget prioritizes debt reduction while maintaining a {saving_preference}% savings rate."
    elif planning_major_purchase:
        summary = f"This budget helps save for your {purchase_item} within {savings_plan['timeline_months']} months."
    elif financial_goal == "Save for emergency fund":
        summary = f"This plan builds your emergency fund with {saving_preference}% savings."
    elif financial_goal == "Build long-term wealth":
        summary = f"This budget emphasizes long-term wealth building with {saving_preference}% to savings."
    else:
        summary = f"This budget balances current lifestyle with a {saving_preference}% savings rate."

    return {
        "allocations": allocations,
        "explanations": explanations,
        "tips": tips,
        "savings_plan": savings_plan,
        "summary": summary
    }