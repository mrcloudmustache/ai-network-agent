import os
from dotenv import load_dotenv
from panos.firewall import Firewall
from panos.network import Zone
from panos.policies import Rulebase, SecurityRule
import xml.etree.ElementTree as ET
import xmltodict

load_dotenv()
pa_vm_ip = os.environ['PA_VM_IP']
pa_vm_username = os.environ['PA_VM_USERNAME']
pa_vm_password = os.environ['PA_VM_PASSWORD']

# Setup firewall object
fw = Firewall(pa_vm_ip, pa_vm_username, pa_vm_password, vsys="vsys1")

def get_rules_all():
    """ Return all Palo Alto firewall policies"""
    rulebase = fw.add(Rulebase())
    rules = SecurityRule.refreshall(rulebase)

    return [x.about() for x in rules]

def get_zones_all():
    """Get all Palo Alto firewall zones with interface details"""
    zones = Zone.refreshall(fw)

    return [x.about() for x in zones]

def get_interfaces_all():
    """Convert the full Palo Alto interface XML output to JSON/dict structure"""
    try:
        # Get XML Element
        root = fw.op('show interface "all"')

        # Convert to string first
        xml_str = ET.tostring(root, encoding='unicode')

        # Convert XML to OrderedDict
        parsed = xmltodict.parse(xml_str)

        # Access the interface entries
        entries = parsed['response']['result']['ifnet']['entry']

        # If there's only one interface, wrap in a list
        if isinstance(entries, dict):
            entries = [entries]

        return entries

    except Exception as e:
        print(f"Error parsing interface XML: {e}")
        return []

def get_routes_all(vr_name=None):
    """Get all routes from the Palo Alto routing table as a list of dictionaries."""
    try:
        # Build the command
        if vr_name:
            cmd = f'show routing route virtual-router {vr_name}'
        else:
            cmd = 'show routing route'

        # Run the command (returns an Element)
        root = fw.op(cmd)

        # Convert Element to string
        xml_str = ET.tostring(root, encoding='unicode')

        # Convert to dict
        parsed = xmltodict.parse(xml_str)

        # Navigate to the list of route entries
        entries = parsed['response']['result']['entry']

        # Ensure it's a list
        if isinstance(entries, dict):
            entries = [entries]

        return entries

    except Exception as e:
        print(f"Error retrieving routes: {e}")
        return []
