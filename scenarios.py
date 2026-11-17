"""Simulated network faults for demo mode.

Each scenario maps a tool name to the text that tool would return on a
machine with that fault. This lets you demo the agent on a healthy
connection, and lets the tests run without touching the real network.
"""

SCENARIOS = {
    "dns_failure": {
        "description": "Connected to Wi-Fi, gateway and internet reachable by IP, but DNS lookups fail.",
        "get_ipconfig": (
            "Wireless LAN adapter Wi-Fi:\n"
            "   IPv4 Address. . . . . . . . . . . : 192.168.1.42\n"
            "   Subnet Mask . . . . . . . . . . . : 255.255.255.0\n"
            "   Default Gateway . . . . . . . . . : 192.168.1.1\n"
            "   DNS Servers . . . . . . . . . . . : 10.99.99.99\n"
        ),
        "ping_gateway": "Reply from 192.168.1.1: bytes=32 time=3ms TTL=64\n4 sent, 4 received, 0% loss",
        "ping_dns": "Reply from 8.8.8.8: bytes=32 time=21ms TTL=117\n4 sent, 4 received, 0% loss",
        "dns_lookup": "FAILED: could not resolve 'www.microsoft.com' (DNS server not responding)",
        "check_network_adapter": "Wi-Fi: Enabled, Connected, SSID 'HomeNet', signal 82%",
    },
    "gateway_unreachable": {
        "description": "Has an IP address, but the router/gateway does not respond.",
        "get_ipconfig": (
            "Wireless LAN adapter Wi-Fi:\n"
            "   IPv4 Address. . . . . . . . . . . : 192.168.1.42\n"
            "   Subnet Mask . . . . . . . . . . . : 255.255.255.0\n"
            "   Default Gateway . . . . . . . . . : 192.168.1.1\n"
            "   DNS Servers . . . . . . . . . . . : 192.168.1.1\n"
        ),
        "ping_gateway": "Request timed out.\n4 sent, 0 received, 100% loss",
        "ping_dns": "Request timed out.\n4 sent, 0 received, 100% loss",
        "dns_lookup": "FAILED: could not resolve 'www.microsoft.com'",
        "check_network_adapter": "Wi-Fi: Enabled, Connected, SSID 'HomeNet', signal 14%",
    },
    "no_ip_address": {
        "description": "Adapter connected but no valid IP (169.254.x.x self-assigned address).",
        "get_ipconfig": (
            "Wireless LAN adapter Wi-Fi:\n"
            "   Autoconfiguration IPv4 Address. . : 169.254.88.17\n"
            "   Subnet Mask . . . . . . . . . . . : 255.255.0.0\n"
            "   Default Gateway . . . . . . . . . : \n"
        ),
        "ping_gateway": "FAILED: no default gateway configured",
        "ping_dns": "Request timed out.\n4 sent, 0 received, 100% loss",
        "dns_lookup": "FAILED: could not resolve 'www.microsoft.com'",
        "check_network_adapter": "Wi-Fi: Enabled, Connected, SSID 'HomeNet', signal 76%",
    },
    "adapter_disabled": {
        "description": "The Wi-Fi adapter is switched off or disabled.",
        "get_ipconfig": "Wireless LAN adapter Wi-Fi:\n   Media State . . . . . . . . . . . : Media disconnected\n",
        "ping_gateway": "FAILED: no default gateway configured",
        "ping_dns": "FAILED: General failure",
        "dns_lookup": "FAILED: could not resolve 'www.microsoft.com'",
        "check_network_adapter": "Wi-Fi: Disabled",
    },
    "isp_outage": {
        "description": "Local network fine, but nothing beyond the router works (likely ISP outage).",
        "get_ipconfig": (
            "Wireless LAN adapter Wi-Fi:\n"
            "   IPv4 Address. . . . . . . . . . . : 192.168.1.42\n"
            "   Subnet Mask . . . . . . . . . . . : 255.255.255.0\n"
            "   Default Gateway . . . . . . . . . : 192.168.1.1\n"
            "   DNS Servers . . . . . . . . . . . : 192.168.1.1\n"
        ),
        "ping_gateway": "Reply from 192.168.1.1: bytes=32 time=2ms TTL=64\n4 sent, 4 received, 0% loss",
        "ping_dns": "Request timed out.\n4 sent, 0 received, 100% loss",
        "dns_lookup": "FAILED: could not resolve 'www.microsoft.com'",
        "check_network_adapter": "Wi-Fi: Enabled, Connected, SSID 'HomeNet', signal 88%",
    },
    "healthy": {
        "description": "Everything works; the problem is probably the app or website, not the network.",
        "get_ipconfig": (
            "Wireless LAN adapter Wi-Fi:\n"
            "   IPv4 Address. . . . . . . . . . . : 192.168.1.42\n"
            "   Subnet Mask . . . . . . . . . . . : 255.255.255.0\n"
            "   Default Gateway . . . . . . . . . : 192.168.1.1\n"
            "   DNS Servers . . . . . . . . . . . : 192.168.1.1\n"
        ),
        "ping_gateway": "Reply from 192.168.1.1: bytes=32 time=2ms TTL=64\n4 sent, 4 received, 0% loss",
        "ping_dns": "Reply from 8.8.8.8: bytes=32 time=19ms TTL=117\n4 sent, 4 received, 0% loss",
        "dns_lookup": "OK: www.microsoft.com -> 20.70.246.20",
        "check_network_adapter": "Wi-Fi: Enabled, Connected, SSID 'HomeNet', signal 90%",
    },
}
