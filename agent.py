from typing import TypedDict, List, Annotated
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.graph.message import add_messages
from langchain_core.tools import tool
from langgraph.checkpoint.memory import InMemorySaver
from aws_utils import *
from palo_utils import *

load_dotenv()

# Define your persistent system prompt
SYSTEM_PROMPT = SystemMessage(
    content=(
        "You are a cloud network agent helping users troubleshoot and collect information about their AWS network resources.\n"
        "If a target group member is unheathly you shoud verify the security group of the instance is allowing the health check port and proocol. \n"
        "Do not answer questions that are not related to cloud networking. Politely respond.\n"
        "Perform a detailed analysis of the firewall policies between VPCs by using your tools to lookup VPC subnets and Cidrs"
        "You can:\n"
        "- List VPCs, subnets, transit gateways, route tables, network interfaces, security groups and Palo Alto firewall policies.\n"
        "- Simulate network path analysis between two IPs.\n"
        "- Validate security configurations with AWS security groups or Palo Alto firewall policies "
        "Respond politely if data is missing from the user request. If possible use your tools to lookup the missing information.\n"
        "When performing path anylsis check VPC route tables, transit gateway route table routes, and resolve transit gateway vpc attachments.\n"
        "Look for routes with a next hop of a gateway load balancer and then verify the targets in the target group are healthy are have firewalls as the targets\n"
        "When needed perform a detailed firewall policy analysis, and verify source and destination addresses, service and action. If 'Action' is 'deny' then traffic is not allowed.\n"
        "To determine firewall instances look up instances with 'palo' in the name.\n"
        "Examples:\n"
        "- 'Show me a list of routes for this subnet.'\n"
        "- 'Show the account and VPC information for this CIDR.'\n"
        "- 'Show the network path from 1.1.1.1 to 2.2.2.2.'"
    )
)

# Memory setup
memory = InMemorySaver()

# LLM Setup
llm = ChatOpenAI(model_name="gpt-4o", temperature=0)


# Agent State
class NetworkState(TypedDict):
    messages: Annotated[list, add_messages]

# Tool Specs
@tool
def get_vpcs_tool() -> List[dict]:
    """List all AWS VPCs."""
    return get_vpcs()

@tool
def get_subnets_tool() -> List[dict]:
    """List all AWS subnets."""
    return get_subnets()

@tool
def get_route_tables_tool() -> List[dict]:
    """List all AWS route tables."""
    return get_route_tables()

@tool
def get_network_interfaces_tool() -> List[dict]:
    """List all AWS network interfaces."""
    return get_network_interfaces()

@tool
def get_ec2_instances_tool() -> List[dict]:
    """List all AWS EC2 instances."""
    return get_ec2_instances()

@tool
def get_security_groups_tool() -> List[dict]:
    """List all AWS security groups."""
    return get_security_groups()

@tool
def get_firewall_policies_tool() -> List[dict]:
    """List all Palo Alto Firewall policies"""
    return get_rules_all()
@tool
def get_firewall_zones_tool() -> List[dict]:
    """List all Palo Alto Firewall zones"""
    return get_zones_all()
@tool
def get_firewall_interfaces_tool() -> List[dict]:
    """List all Palo Alto Firewall interfaces"""
    return get_interfaces_all()

@tool
def get_firewall_routes_tool() -> List[dict]:
    """List all Palo Alto Firewall interfaces"""
    return get_routes_all()

@tool
def get_transit_gateway_route_tables_tool() -> List[dict]:
    """List all AWS Transit Gateway route tables"""
    return get_transit_gateway_route_tables()

@tool
def get_transit_gateway_vpc_attachments_tool() -> List[dict]:
    """List all AWS Transit Gateway VPC attachments"""
    return get_transit_gateway_vpc_attachments()

@tool
def get_transit_gateway_attachments_tool() -> List[dict]:
    """List all AWS Transit Gateway attachments"""
    return get_transit_gateway_attachments()

@tool
def get_transit_gateway_routes_tool(transit_gateway_route_table_id) -> List[dict]:
    """Get AWS Transit Gateway route table routes"""
    return get_transit_gateway_routes(transit_gateway_route_table_id)

@tool
def get_load_balancers_tool() -> List[dict]:
    """List all AWS Elastic Load balancers including gateway load balancers"""
    return get_load_balancers()

@tool
def get_target_groups_tool() -> List[dict]:
    """List all AWS Elastic load balancer target groups"""
    return get_target_groups()

@tool
def get_target_group_health_tool(target_group_arn) -> List[dict]:
    """List all AWS Elastic load balancer target group health"""
    return get_target_group_health(target_group_arn)

# Bind tools
tools = [
    get_vpcs_tool,
    get_subnets_tool,
    get_route_tables_tool,
    get_network_interfaces_tool,
    get_ec2_instances_tool,
    get_security_groups_tool,
    get_transit_gateway_route_tables_tool,
    get_transit_gateway_vpc_attachments_tool,
    get_transit_gateway_attachments_tool,
    get_load_balancers_tool,
    get_target_groups_tool,
    get_target_group_health_tool,
    get_transit_gateway_routes_tool,
    get_firewall_policies_tool,
    get_firewall_interfaces_tool,
    get_firewall_zones_tool,
    get_firewall_routes_tool,
]

model_with_tools = llm.bind_tools(tools)

# LangGraph Nodes
tool_node = ToolNode(tools=tools) 

def bot_node(state: NetworkState) -> NetworkState:
    messages = state["messages"]
    if not isinstance(messages[0], SystemMessage):
        messages = [SYSTEM_PROMPT] + messages
    
    response = model_with_tools.invoke(messages)
    return {"messages": [response]}

# LangGraph Definition
graph_builder = StateGraph(NetworkState)
graph_builder.add_node("bot", bot_node)
graph_builder.add_node("tools", tool_node)
graph_builder.set_entry_point("bot")
graph_builder.add_conditional_edges("bot", tools_condition)
graph_builder.add_edge("tools", "bot")
graph = graph_builder.compile(checkpointer=memory)

# State Memory thread ID
config = {"configurable": {"thread_id": "1"}}

if __name__ == "__main__":
    while True:
        user_input = input("User: ")
        if user_input.lower() in ["quit", "exit", "q"]:
            print("Goodbye")
            break
        state = {"messages": [HumanMessage(content=user_input)]}
        final_ai_message = None
        for event in graph.stream(state, config=config):
            for value in event.values():
                # Find and store the last AIMessage only
                for msg in value["messages"]:
                    if isinstance(msg, AIMessage):
                        final_ai_message = msg

        if final_ai_message:
            print("Agent: ", final_ai_message.content)
