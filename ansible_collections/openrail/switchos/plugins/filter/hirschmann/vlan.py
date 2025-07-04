import re
from ansible.errors import AnsibleFilterError

regex = r"^vlan database([\nA-Z0-9a-z\s-]*?)(?:^\s*exit\s*$)"


def parse_vlans(stdout_lines: list[str]) -> list[dict]:
    """
    Parse VLANs from the output in a format like:
        cli serial-timeout 0
        vlan database
        vlan add 2
        vlan add 8
        name 1 Management
        name 2 NWM
        name 8 RIS
        no ip arp-inspection bind-check 2
        no ip arp-inspection bind-check 8
        no ip arp-inspection bind-check 9
        exit
        network parms 192.168.1.31 255.255.255.0 192.168.1.1
        name 123 something
    """
    config_text = "\n".join(stdout_lines)

    # Extract the vlan database block
    m = re.search(regex, config_text, re.DOTALL | re.MULTILINE)
    if not m:
        return []
    block = m.group(1)
    # Find all vlan add lines
    vlans = re.findall(r"vlan add (\d+)", block)
    print(vlans)
    # Find all name lines
    names = dict(re.findall(r"name (\d+)\s+([^\n]+)", block))

    return [
        {"vlan_id": vlan, "name": (names.get(vlan) or "").strip() or None}
        for vlan in vlans
    ]


def parse_vlan_ports_table(stdout_lines):
    """

            vlan database>$vlan add 1337
            vlan database>$name 1337 leet
            configure>$interface 1/3-1/7,1/9
            configure>interface>$vlan participation include 1337
            $show vlan member current

            VLAN Port membership
                Slot: 1
    VLAN ID  Port: 1234567890123456789012345678
    -------  ----- ----------------------------
            1        UUUUUUUUUUUUUUUUUUUUUUUUUUUU
            2        -T-T-----------------------T
            8        -T-T-----UUUU----------U---T
            9        -T-T----U------------------T
            10        ----------------------------
        200        -T-TT----------------------T
        210        -T--TT----------------------
        218        TTTTTTTTTTTTTTTTTTTTTTTTTTTT
        219        -T-TTT---------------------T
        220        -TTTT----------------------T

    Abbreviations:
    - Not Member
    T Tagged
    F Forbidden
    U Untagged

    """

    print("Parsing VLAN ports table...")
    print("Input lines:", stdout_lines)
    # Find the header line with port numbers
    port_line = None
    for line in stdout_lines:
        if line.strip().startswith("Interface"):
            port_line = line
            break
    if not port_line:
        raise AnsibleFilterError("Could not find port header in output")

    # Extract port numbers (as string indices)
    # Example: "VLAN ID  Port: 1234567890123456789012345678"
    port_numbers = []
    port_index = port_line.find(":")
    if port_index == -1:
        raise AnsibleFilterError("Malformed port header line")
    port_digits = port_line[port_index + 1 :].strip()
    for i, c in enumerate(port_digits):
        if c.isdigit():
            port_numbers.append(str(i + 1))  # Port numbers are 1-based

    ports_to_vlans = {p: [] for p in port_numbers}
    vlans_to_ports = {}

    # Parse VLAN membership lines
    for line in stdout_lines:
        if line.strip() == "" or not line.strip()[0].isdigit():
            continue
        # Example: "      8        -T-T-----UUUU----------U---T"
        parts = line.split()
        if len(parts) < 2:
            continue
        vlan_id = parts[0]
        membership = parts[-1]
        vlans_to_ports[vlan_id] = []
        for idx, status in enumerate(membership):
            if idx >= len(port_numbers):
                break
            if status in ("T", "U"):  # Tagged or Untagged
                port = port_numbers[idx]
                ports_to_vlans[port].append(vlan_id)
                vlans_to_ports[vlan_id].append(port)
    return {"ports_to_vlans": ports_to_vlans, "vlans_to_ports": vlans_to_ports}


class FilterModule(object):
    def filters(self):
        return {
            "parse_vlan_ports_table": parse_vlan_ports_table,
            "parse_vlans": parse_vlans,
        }
