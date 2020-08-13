import os
from nornir import InitNornir
from nornir.plugins.tasks.networking import netmiko_send_command
from rich import print

nr = InitNornir()
CLEAR = "clear"
os.system(CLEAR)

good_list = []
bad_list = []

def ospf_check(task):
    get_brief = task.run(task=netmiko_send_command, command_string="show ip ospf int brief", use_genie=True)
    get_inter = task.run(task=netmiko_send_command, command_string="show interfaces", use_genie=True)
    get_neighbor = task.run(task=netmiko_send_command, command_string="show ip ospf neighbor", use_genie=True)
    get_ospf = task.run(task=netmiko_send_command, command_string="show ip ospf", use_genie=True)
    task.host["brief_facts"] = get_brief.result
    task.host["inter_facts"] = get_inter.result
    task.host["neigh_facts"] = get_neighbor.result
    task.host["ospf_facts"] = get_ospf.result
    outer = task.host["brief_facts"]["instance"]
    interface_outer = task.host["inter_facts"]
    neigh_outer = task.host["neigh_facts"]['interfaces']
    ip_ospf_outer = task.host["ospf_facts"]['vrf']['default']['address_family']['ipv4']['instance']
    for inner in outer:
        areas = outer[inner]['areas']
        ip_ospf_instance = ip_ospf_outer[inner]['areas']
        for area in areas:
            split_area = area.split(".")
            short_area = split_area[3]
            interfaces = areas[area]['interfaces']
            area_type = ip_ospf_instance[area]['area_type']
            try:
                for ospf_intf in interfaces:
                    ipaddr = interfaces[ospf_intf]['ip_address']
                    mtu = interface_outer[ospf_intf]['mtu']
                    neigh_inner = neigh_outer[ospf_intf]['neighbors']
                    for key in neigh_inner:
                        state = neigh_inner[key]['state']
                        neigh_ip = neigh_inner[key]['address']
                        good_output = (f"{task.host}: {ospf_intf}"\
                                f" is in Area {short_area} with IP: {ipaddr}"\
                                f" - neighboring {neigh_ip}")

                        bad_output = (f"ERROR: {task.host}:"\
                                f" {ospf_intf} (IP = {ipaddr} | MTU = {mtu})"\
                                f" is in Area {short_area} (Type: {area_type})"\
                                "- neighbor in DOWN/EXSTART!")

                        if "EXSTART" in state:
                            bad_list.append(bad_output)
                        elif "DOWN" in state:
                            bad_list.append(bad_output)
                        elif "2WAY" in state:
                            good_list.append(good_output)
                        elif "FULL" in state:
                            good_list.append(good_output)

            except KeyError:
                bad_output = (f"ERROR: {task.host}:"\
                        f" {ospf_intf} (IP = {ipaddr} | MTU = {mtu})"\
                        f" is in Area {short_area} (Type: {area_type}) with no neighbor!")
                bad_list.append(bad_output)

results = nr.run(task=ospf_check)
print("[green][u]******** PASSED ********[/u][/green]\n")
for good in good_list:
    print(f"[cyan]{good}[/cyan]")
print("\n[red][u]******** FAILED ********[/u][/red]\n")
for bad in bad_list:
    print(f"[red]{bad}[/red]")
