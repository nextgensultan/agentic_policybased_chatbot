from langchain.agents import  initialize_agent, AgentType
from langchain.memory import ConversationBufferMemory
from langchain_huggingface import HuggingFaceEndpoint
from langchain.tools.base import ToolException
from langchain_core.tools import StructuredTool
import pandas as pd
import os
from datetime import datetime
from knowledege_base import search_return_policy

orders_df = pd.read_csv('orders.csv')

def setup_llm():
    os.environ["HUGGINGFACEHUB_API_TOKEN"] = "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"
    
    llm = HuggingFaceEndpoint(
        repo_id="mistralai/Mistral-7B-Instruct-v0.2", 
        temperature=0.7,
        max_new_tokens=512,
        task="text-generation",  
    )
    return llm



# 1. Order Lookup Tool
def lookup_order(order_id=None, customer_email=None):
    """Look up an order by ID or customer email."""
    try:
        if order_id:
            # Convert to integer since CSV stores IDs as numbers
            order_id = int(order_id)
            order = orders_df[orders_df['id'] == order_id]
            if not order.empty:
                order_dict = order.iloc[0].to_dict()
                # Add estimated delivery information for better user experience
                if 'location' in order_dict:
                    order_dict['estimated_delivery'] = calculate_estimated_delivery(order.iloc[0])
                return order_dict
            else:
                return {"error": f"Order {order_id} not found"}
        
        elif customer_email:
            customer_orders = orders_df[orders_df['customer_email'] == customer_email]
            if not customer_orders.empty:
                # Add estimated delivery information to each order
                orders_list = customer_orders.to_dict('records')
                for order in orders_list:
                    if 'location' in order:
                        order['estimated_delivery'] = calculate_estimated_delivery(pd.Series(order))
                return orders_list
            else:
                return {"error": f"No orders found for {customer_email}"}
        
        else:
            return {"error": "Please provide either order_id or customer_email"}
            
    except Exception as e:
        raise ToolException(f"Error looking up order: {str(e)}")

def check_return_eligibility(order_id):
    try:
        order_id = int(order_id)
        order = orders_df[orders_df['id'] == order_id]
        
        if order.empty:
            return {"error": f"Order {order_id} not found"}
            
        order = order.iloc[0]
        
        if order['status'] == 'returned':
            return {
                "eligible": False,
                "reason": "This order has already been returned."
            }
            
        if order['status'] == 'pending':
            return {
                "eligible": False,
                "reason": "This order is still pending and hasn't shipped yet."
            }
            
        order_date = datetime.strptime(order['order_date'], '%Y-%m-%d')
        today = datetime.now()
        days_since_order = (today - order_date).days
        
        if days_since_order > 30:
            return {
                "eligible": False,
                "reason": f"Return period has expired. Items must be returned within 30 days of order date (ordered {days_since_order} days ago)."
            }
            
        return {
            "eligible": True,
            "days_remaining": 30 - days_since_order,
            "order_details": order.to_dict()
        }
            
    except Exception as e:
        raise ToolException(f"Error checking return eligibility: {str(e)}")

def process_return_request(order_id, reason=None):
    try:
        eligibility = check_return_eligibility(order_id)
        
        if not eligibility.get("eligible", False):
            return {
                "status": "rejected",
                "reason": eligibility.get("reason", "Order is not eligible for return")
            }
            

        order_id = int(order_id)
        orders_df[order_id]["status"] = "returned"
        orders_df.to_csv('orders.csv', index=False)

        return {
            "status": "approved",
            "return_id": f"RET-{order_id}-{datetime.now().strftime('%Y%m%d')}",
            "instructions": """
            1. Package the items in their original packaging
            2. Include your order number on the return label
            3. Ship to our return center
            4. Refund will be processed within 5-7 business days after receipt
            """
        }
            
    except Exception as e:
        raise ToolException(f"Error processing return: {str(e)}")

# New function: Track Order Location
def track_order_location(order_id):
    """Track the current location of an order."""
    try:
        order_id = int(order_id)
        order = orders_df[orders_df['id'] == order_id]
        
        if order.empty:
            return {"error": f"Order {order_id} not found"}
        
        order = order.iloc[0]
        
        # Return location and status information
        return {
            "order_id": order_id,
            "status": order['status'],
            "location": order['location'],
            "order_date": order['order_date'],
            "estimated_delivery": calculate_estimated_delivery(order)
        }
    
    except Exception as e:
        raise ToolException(f"Error tracking order: {str(e)}")

def calculate_estimated_delivery(order):
    """Calculate estimated delivery date based on order status and location."""
    # Convert order date to datetime
    order_date = datetime.strptime(order['order_date'], '%Y-%m-%d')
    status = order['status']
    location = order['location']
    
    # Basic estimates based on status and location text
    if status == 'pending':
        # Pending orders ship in 1-3 days
        return (order_date + pd.Timedelta(days=5)).strftime('%Y-%m-%d')
    elif status == 'shipped':
        if 'Delivered' in location:
            return "Delivered"
        elif 'Out for Delivery' in location:
            return "Today"
        elif 'In Transit' in location:
            return (datetime.now() + pd.Timedelta(days=2)).strftime('%Y-%m-%d')
        elif 'Local Carrier' in location:
            return (datetime.now() + pd.Timedelta(days=1)).strftime('%Y-%m-%d')
        else:
            return (datetime.now() + pd.Timedelta(days=3)).strftime('%Y-%m-%d')
    elif status == 'returned':
        return "N/A - Order returned"
    else:
        return "Unknown"

def search_policy(query: str) -> dict:
    """
    Search the return policy knowledge base for specific information.
    
    Args:
        query: Question or keywords about return policies
        
    Returns:
        Relevant policy information from the knowledge base
    """
    try:
        return search_return_policy(query)
    except Exception as e:
        raise ToolException(f"Error searching policy knowledge base: {str(e)}")

def setup_agent(llm):
    # Create tools using StructuredTool for better parameter handling
    tools = [
        StructuredTool.from_function(
            func=lookup_order,
            name="LookupOrder",
            description="Look up order information by either order_id (number) or customer_email (string)",
        ),
        StructuredTool.from_function(
            func=check_return_eligibility,
            name="CheckReturnEligibility",
            description="Check if an order is eligible for return based on order_id (number)",
        ),
        StructuredTool.from_function(
            func=track_order_location,
            name="TrackOrderLocation",
            description="Track an order's current location and get estimated delivery date using order_id (number)",
        ),
        StructuredTool.from_function(
            func=process_return_request,
            name="ProcessReturn",
            description="Process a return request using order_id (number) and optional reason (string)",
        ),
        StructuredTool.from_function(
            func=search_policy,
            name="SearchReturnPolicy",
            description="Search for specific return policy information using a query. Use this for detailed policy questions.",
        )
    ]
    
    # Create memory
    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
    
    # Use the structured chat agent
    agent = initialize_agent(
        tools,
        llm,
        agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
        memory=memory,
        verbose=True,
        handle_parsing_errors=True,
        max_iterations=6
    )
    
    return agent

def run_example():
    try:
        # Initialize the agent
        print("Setting up LLM...")
        llm = setup_llm()
        print("LLM set up complete")
        print("Setting up agent with FAISS-powered policy search...")
        agent = setup_agent(llm)
        print("Agent setup complete")
        
        # Run a few test examples
        print("\n----- TEST EXAMPLE 1: Return Policy -----")
        response = agent.invoke({
            "input": "What's your return policy?"
        })
        print("Example Response:", response.get("output", "No output"))
        
        print("\n----- TEST EXAMPLE 2: Order Location Tracking -----")
        response = agent.invoke({
            "input": "Where is my order #5 right now?"
        })
        print("Example Response:", response.get("output", "No output"))
        
        print("\n----- TEST EXAMPLE 3: Location Details and Delivery Estimate -----")
        response = agent.invoke({
            "input": "When will order 10 be delivered and where is it currently?"
        })
        print("Example Response:", response.get("output", "No output"))
        
        print("\n----- TEST EXAMPLE 4: Specific Policy Question (FAISS Search) -----")
        response = agent.invoke({
            "input": "Can I return electronics after 20 days? I need to know the policy for tech items."
        })
        print("Example Response:", response.get("output", "No output"))
        
        print("\n----- TEST EXAMPLE 5: Order Lookup with Location -----")
        response = agent.invoke({
            "input": "Look up all orders for customer3@example.com and tell me their locations."
        })
        print("Example Response:", response.get("output", "No output"))
        
        print("\nTests completed successfully")
        
    except Exception as e:
        print(f"Error during example run: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_example()
