import boto3
from typing import TypedDict, List, Annotated
import boto3

# AWS SDK Tools
def get_vpcs() -> List[dict]:
    ec2 = boto3.client("ec2")
    return ec2.describe_vpcs().get("Vpcs", [])

def get_subnets() -> List[dict]:
    ec2 = boto3.client("ec2")
    return ec2.describe_subnets().get("Subnets", [])

def get_route_tables() -> List[dict]:
    ec2 = boto3.client("ec2")
    return ec2.describe_route_tables().get("RouteTables", [])

def get_network_interfaces() -> List[dict]:
    ec2 = boto3.client("ec2")
    return ec2.describe_network_interfaces().get("NetworkInterfaces", [])

def get_ec2_instances() -> List[dict]:
    ec2 = boto3.client("ec2")
    return ec2.describe_instances().get("Reservations", [])

def get_security_groups() -> List[dict]:
    ec2 = boto3.client("ec2")
    return ec2.describe_security_groups().get("SecurityGroups", [])

def get_transit_gateway_route_tables():
    ec2 = boto3.client("ec2")
    return ec2.describe_transit_gateway_route_tables().get("TransitGatewayRouteTables", [])

def get_transit_gateway_vpc_attachments():
    ec2 = boto3.client("ec2")
    return ec2.describe_transit_gateway_vpc_attachments().get("TransitGatewayVpcAttachments", [])

def get_transit_gateway_attachments():
    ec2 = boto3.client("ec2")
    return ec2.describe_transit_gateway_attachments().get("TransitGatewayAttachments", [])

def get_transit_gateway_routes(transit_gateway_route_table_id: str):
    ec2 = boto3.client("ec2")
    return ec2.search_transit_gateway_routes(
        TransitGatewayRouteTableId=transit_gateway_route_table_id,
        Filters=[
            {
                'Name': 'state',
                'Values': ['active', 'blackhole']
            }
        ]).get("Routes", [])

def get_load_balancers():
    elb = boto3.client('elbv2')
    return elb.describe_load_balancers().get("LoadBalancers", [])

def get_target_groups():
    elb = boto3.client('elbv2')
    return elb.describe_target_groups().get("TargetGroups", [])

def get_target_group_health(target_group_arn):
    elb = boto3.client('elbv2')
    return elb.describe_target_health(TargetGroupArn=target_group_arn).get("TargetHealthDescriptions", [])