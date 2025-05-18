import os
import google.generativeai as genai


def setup_gemini():
    """Setup the Gemini API"""
    try:
        # Get API key from environment variable
        api_key = os.getenv("GEMINI_API_KEY")
        
        if not api_key:
            # For local development, try to read from a .env file
            try:
                with open(".env", "r") as f:
                    for line in f:
                        if line.startswith("GEMINI_API_KEY="):
                            api_key = line.strip().split("=", 1)[1].strip('"\'')
                            break
            except:
                pass
        
        if not api_key:
            return None
            
        # Configure the Gemini API
        genai.configure(api_key=api_key)
        
        # Get available models
        models = [m for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        if not models:
            return None
            
        # Use the first suitable model (usually the most powerful one)
        model = genai.GenerativeModel("gemini-1.5-pro")
        return model
        
    except Exception as e:
        print(f"Error setting up Gemini: {e}")
        return None

def get_financial_advice_with_gemini(query, context):
    """Get financial advice using Gemini"""
    try:
        model = setup_gemini()
        
        if not model:
            # Fallback to rule-based responses if Gemini isn't available
            return None
        
        # Format the financial context for the prompt
        prompt = create_financial_prompt(query, context)
        
        # Generate the response
        response = model.generate_content(prompt)
        
        if response and hasattr(response, 'text'):
            return response.text
        
        return None
    except Exception as e:
        print(f"Error with Gemini: {e}")
        return None

def create_financial_prompt(query, context):
    """Create a prompt for Gemini based on the user's financial data"""
    # Extract key information from context
    user_name = context.get('user_name', 'User')
    income = context.get('income', 0)
    currency = context.get('currency', '$')
    
    # Format budget data
    budget_allocations = context.get('budget_allocations', {})
    budget_text = ""
    for category, amount in budget_allocations.items():
        percentage = (amount / income * 100) if income > 0 else 0
        budget_text += f"- {category}: {currency} {amount:,.0f} ({percentage:.1f}% of income)\n"
    
    # Format expense data
    expenses_by_category = context.get('category_breakdown', {})
    expense_text = ""
    for category, amount in expenses_by_category.items():
        budget_for_cat = budget_allocations.get(category, 0)
        if budget_for_cat > 0:
            percentage = (amount / budget_for_cat * 100)
            expense_text += f"- {category}: {currency} {amount:,.0f} spent ({percentage:.1f}% of category budget)\n"
        else:
            expense_text += f"- {category}: {currency} {amount:,.0f} spent (no budget set)\n"
    
    # Format savings goal
    savings_text = ""
    if context.get('has_savings_goal'):
        savings_text = f"""
Savings Goal: {context.get('savings_goal_item', 'Goal')}
Total Cost: {currency} {context.get('savings_goal_amount', 0):,.0f}
Current Progress: {currency} {context.get('savings_goal_current', 0):,.0f} ({context.get('savings_goal_progress', 0):.1f}% complete)
"""

    # Build the prompt
    prompt = f"""You are a helpful, friendly financial assistant for a personal budgeting app called Smart Budget.
You're speaking with {user_name} and should provide personalized advice based on their financial data.

USER'S FINANCIAL DATA:
- Monthly Income: {currency} {income:,.0f}
- Total Monthly Budget: {currency} {context.get('total_budget', 0):,.0f}
- This Month's Expenses (so far): {currency} {context.get('monthly_expenses', 0):,.0f}
- Last 30 Days Total Expenses: {currency} {context.get('expenses_last_30_days', 0):,.0f}
- Top Spending Category: {context.get('top_spending_category', 'Unknown')} ({currency} {context.get('top_spending_amount', 0):,.0f})

BUDGET ALLOCATIONS:
{budget_text or "No budget allocations set"}

CURRENT MONTH SPENDING BY CATEGORY:
{expense_text or "No expenses recorded"}

{savings_text}

User's Question: {query}

Respond concisely as a helpful financial assistant. Provide specific advice based on their financial situation, but keep answers brief and actionable. If the question isn't about their finances, politely steer them back to financial topics.
"""
    return prompt

def process_query_with_gemini(query, financial_context):
    """Process user query with Gemini, falling back to rule-based responses if needed"""
    # First try with Gemini
    gemini_response = get_financial_advice_with_gemini(query, financial_context)
    
    if gemini_response:
        return gemini_response
        
    # Fall back to rule-based responses
    return process_query_rule_based(query, financial_context)
    
def process_query_rule_based(query, financial_context):
    """Process the user's financial query using rule-based responses"""
    # Format financial context to make it easier to reference
    context = financial_context
    
    # Common questions and their answers
    income = context["income"]
    currency = context["currency"]
    
    # List of predefined questions and answers
    qa_pairs = [
        {
            "keywords": ["income", "earn", "salary", "make"],
            "response": f"Your monthly income is {currency} {income:,.0f}."
        },
        {
            "keywords": ["total budget", "budget total", "overall budget"],
            "response": f"Your total monthly budget is {currency} {context['total_budget']:,.0f}."
        },
        {
            "keywords": ["spent", "spend", "expense", "month"],
            "response": f"This month, you've spent {currency} {context['monthly_expenses']:,.0f} so far."
        },
        {
            "keywords": ["last 30 days", "recent expense", "past month"],
            "response": f"In the last 30 days, you've spent a total of {currency} {context['expenses_last_30_days']:,.0f}."
        },
        {
            "keywords": ["most", "highest", "top", "category"],
            "response": f"Your highest spending category is '{context['top_spending_category']}' with {currency} {context['top_spending_amount']:,.0f} spent."
        },
        {
            "keywords": ["saving", "goal", "target", "save"],
            "response": get_savings_response(context)
        },
        {
            "keywords": ["budget breakdown", "allocation", "split", "distribution"],
            "response": get_budget_breakdown(context)
        },
        {
            "keywords": ["remaining", "left", "available"],
            "response": get_remaining_budget(context)
        },
        {
            "keywords": ["tip", "advice", "recommend", "suggest"],
            "response": get_financial_advice(context)
        }
    ]
    
    # Check for query in predefined answers
    query_lower = query.lower()
    for qa in qa_pairs:
        if any(keyword in query_lower for keyword in qa["keywords"]):
            return qa["response"]
    
    # Handle category-specific questions
    for category, amount in context.get("category_breakdown", {}).items():
        if category.lower() in query_lower:
            budget_for_cat = context["budget_allocations"].get(category, 0)
            if budget_for_cat > 0:
                percentage = (amount / budget_for_cat) * 100
                return f"For '{category}', you've spent {currency} {amount:,.0f} out of your {currency} {budget_for_cat:,.0f} budget ({percentage:.1f}%)."
            else:
                return f"You've spent {currency} {amount:,.0f} on '{category}' in the last 30 days."
    
    # Generate a fallback response when no specific match is found
    return generate_fallback_response(query, context)

def get_savings_response(context):
    """Generate a response about savings goals"""
    if context.get("has_savings_goal"):
        return f"You're saving for {context['savings_goal_item']}. " + \
               f"So far, you've saved {context['currency']} {context['savings_goal_current']:,.0f} " + \
               f"out of your {context['currency']} {context['savings_goal_amount']:,.0f} goal " + \
               f"({context['savings_goal_progress']:.1f}% complete)."
    else:
        return "You don't have any active savings goals set up. Would you like to create one?"

def get_budget_breakdown(context):
    """Generate a response about budget allocation breakdown"""
    if not context["budget_allocations"]:
        return "You haven't set up your budget allocations yet."
    
    response = "Here's your current budget breakdown:\n"
    total = context["total_budget"]
    
    for category, amount in context["budget_allocations"].items():
        percentage = (amount / total) * 100 if total else 0
        response += f"- {category}: {context['currency']} {amount:,.0f} ({percentage:.1f}%)\n"
    
    return response

def get_remaining_budget(context):
    """Calculate and return remaining budget"""
    total_budget = context["total_budget"]
    spent = context["monthly_expenses"]
    remaining = total_budget - spent
    
    if remaining > 0:
        return f"You have {context['currency']} {remaining:,.0f} remaining in your budget this month."
    else:
        return f"You've exceeded your monthly budget by {context['currency']} {abs(remaining):,.0f}."

def get_financial_advice(context):
    """Generate personalized financial advice based on user data"""
    income = context["income"]
    monthly_expenses = context["monthly_expenses"]
    budget = context["total_budget"]
    
    # Calculate spending ratio
    spending_ratio = monthly_expenses / income if income else 1
    
    if spending_ratio > 0.9:
        return "Your spending is close to or exceeding your income. Consider cutting back on non-essential categories and creating a stricter budget."
    elif spending_ratio > 0.7:
        return "You're spending a significant portion of your income. Try to increase your savings rate to at least 20% of your income for better financial health."
    else:
        return "You're doing well with your spending habits! Consider investing the surplus or increasing your savings for future goals."

def generate_fallback_response(query, context):
    """Generate a fallback response when no specific match is found"""
    # Simple response templates
    templates = [
        f"I don't have enough information about '{query}'. Would you like to know about your overall budget or recent expenses instead?",
        f"I'm not sure about that. Your current monthly expenses are {context['currency']} {context['monthly_expenses']:,.0f} if that helps.",
        f"I don't have specific data for that query. Would you like to know about your savings progress or budget breakdown?",
        f"I couldn't find information about that. As a quick summary, your income is {context['currency']} {context['income']:,.0f} and you've spent {context['currency']} {context['monthly_expenses']:,.0f} this month."
    ]
    
    import random
    return random.choice(templates)