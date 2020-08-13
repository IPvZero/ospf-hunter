import os
from nornir import InitNornir
from nornir.plugins.tasks.networking import netmiko_send_command
from rich import print

nr = InitNornir()
CLEAR = "clear"
os.system(CLEAR)

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
                        neigh_ip = neigh_inner[key]['address']
                        print(f"{task.host}: [green]{ospf_intf}"\
                                f"is in Area {short_area} with IP: {ipaddr}"\
                                f"- neighboring {neigh_ip}[/green]")

            except KeyError:
                print(f"[red]ERROR:[/red] {task.host}:"\
                        f"{ospf_intf} (IP = {ipaddr} | MTU = {mtu})"\
                        f" is in [red]Area {short_area} (Type: {area_type})[/red] with no neighbor!")

results = nr.run(task=ospf_check)
