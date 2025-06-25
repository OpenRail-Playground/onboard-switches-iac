"""
Nomad Switch Discovery Implementation
"""
import re
import sys
import os
from typing import Dict, List, Any

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from .BaseDiscovery import BaseDiscovery
from ssh_client import SSHClient
from data_model import SwitchInfo, NeighborInfo
from logging_config import get_logger


class NomadDiscovery(BaseDiscovery):
    """Nomad switch discovery implementation."""
    
    def __init__(self, host: str, username: str, password: str, port: int = 22):
        super().__init__(host, username, password, port)
        self.ssh_client = None
        self.vendor = "nomad"
        self.logger = get_logger(__name__)  # Initialize logger
    
    def connect(self) -> bool:
        """Establish SSH connection to Nomad switch."""
        try:
            self.ssh_client = SSHClient(
                host=self.host,
                username=self.username,
                password=self.password,
                port=self.port
            )
            
            if self.ssh_client.connect() and self.ssh_client.start_shell():
                self.ssh_client.send_command_to_shell("", 1.0)  # Clear initial prompt
                self.ssh_client.send_command_to_shell("terminal length 0", 1.0) # disable interactive prompt
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Connection failed to {self.host}: {e}")
            return False
    
    def disconnect(self) -> None:
        """Close SSH connection to the switch."""
        if self.ssh_client:
            self.ssh_client.disconnect()
            self.ssh_client = None
    
    def get_basic_info(self) -> Dict[str, Any]:
        """Get essential system information: vendor, IP, and MAC address."""
        try:
            output = self.ssh_client.send_command_to_shell("show version", 3.0)
            if output and ("luton" in output or "tpes" in output.lower()):
                return self._parse_basic_info(output)
            
            return {"vendor": "nomad", "ip": self.host, "mac": None}
            
        except Exception:
            return {"vendor": "nomad", "ip": self.host, "mac": None}
    
    def _parse_basic_info(self, output: str) -> Dict[str, Any]:
        """Parse essential information from system info output."""
        info = {"vendor": "luton", "ip": self.host, "mac": None}
        
        # Extract MAC address
        mac_match = re.search(r"MAC address\.+(.+)", output, re.IGNORECASE)
        if mac_match:
            info["mac"] = mac_match.group(1).strip()
        
        return info

    def get_neighbors(self) -> List[NeighborInfo]:
        """Get neighbor information from LLDP."""
        try:
            output = self.ssh_client.send_command_to_shell("show lldp neighbors", 3.0)
            if output:
                return self._parse_lldp_neighbors(output)
            return []
            
        except Exception as e:
            print(f"Failed to get neighbor info: {e}")
            return []
        
    def _parse_lldp_neighbors(self, output: str) -> List[NeighborInfo]:
        """Parse LLDP output and extract essential neighbor information."""
        neighbors = []
        lines = output.split('\n')
        current_neighbor = {}
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Extract IPv4 Management address
            if 'Management Address' in line:
                ip_match = re.search(r'(\d+\.\d+\.\d+\.\d+)', line)
                if ip_match:
                    current_neighbor['ip'] = ip_match.group(1)
            
            # Extract Chassis ID (MAC address)
            elif 'Chassis ID' in line:
                mac_match = re.search(r'([0-9a-fA-F]{2}[:-]){5}[0-9a-fA-F]{2}', line)
                if mac_match:
                    current_neighbor['mac'] = mac_match.group(0)
            
            # Determine neighbor type from System description
            elif 'System Description' in line:
                line_lower = line.lower()
                if 'hirschmann' in line_lower:
                    current_neighbor['type'] = 'hirschmann'
                elif 'lantech' in line_lower:
                    current_neighbor['type'] = 'lantech'
                elif 'kontron' in line_lower:
                    current_neighbor['type'] = 'kontron'
                elif 'nomad' in line_lower:
                    current_neighbor['type'] = 'nomad'
                else:
                    current_neighbor['type'] = 'unknown'
            
            # Process complete neighbor entry
            elif line.startswith('PoE Priority') and current_neighbor:
                if 'ip' in current_neighbor:
                    neighbors.append(NeighborInfo(
                        ip=current_neighbor.get('ip'),
                        mac=current_neighbor.get('mac'),
                        type=current_neighbor.get('type', 'unknown')
                    ))
                current_neighbor = {}
        
        # Add the last neighbor if exists
        if current_neighbor and 'ip' in current_neighbor:
            neighbors.append(NeighborInfo(
                ip=current_neighbor.get('ip'),
                mac=current_neighbor.get('mac'),
                type=current_neighbor.get('type', 'unknown')
            ))
        
        return neighbors
    
    def get_switch_info(self) -> SwitchInfo:
        """Get essential switch information for network discovery."""
        try:
            self.logger.debug(f"Attempting to connect to {self.host} with username: {self.username}")
            if not self.connect():
                self.logger.error(f"Failed to connect to {self.host}")
                return SwitchInfo(ip=self.host, mac=None, type='nomad', neighbors=[])
            
            self.logger.info(f"Successfully connected to {self.host}")
            
            # Get basic info (vendor, IP, MAC)
            basic_info = self.get_basic_info()
            self.logger.debug(f"System info retrieved: {list(basic_info.keys()) if basic_info else 'None'}")
            
            # Get neighbor information
            self.logger.debug("Getting neighbor information...")
            neighbors = self.get_neighbors()
            self.logger.info(f"Found {len(neighbors)} neighbors")
            
            self.disconnect()
            self.logger.debug(f"Disconnected from {self.host}")
            
            return SwitchInfo(
                ip=basic_info.get('ip', self.host),
                mac=basic_info.get('mac'),
                type=basic_info.get('vendor', 'nomad'),
                neighbors=neighbors
            )
            
        except Exception as e:
            self.logger.error(f"Failed to get switch info: {e}")
            try:
                self.disconnect()
            except:
                pass
            return SwitchInfo(ip=self.host, mac=None, type='nomad', neighbors=[])

    # Compatibility methods required by BaseDiscovery
    def get_system_info(self) -> Dict[str, Any]:
        """Get basic system information (backward compatibility)."""
        return self.get_basic_info()
    
    def get_neighbor_info(self) -> List[Dict[str, Any]]:
        """Get neighbor information (backward compatibility)."""
        neighbors = self.get_neighbors()
        return [{"ip": n.ip, "mac": n.mac, "type": n.type} for n in neighbors]

