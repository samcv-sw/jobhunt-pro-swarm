"""
JobHunt Pro - Interview Preparation Engine
Provides standard interview Q&A templates for candidate practice.
"""

import logging
import random

logger = logging.getLogger(__name__)


class InterviewPrep:
    """Contains standard network engineering interview questions and answers."""

    QUESTIONS: list[dict[str, str]] = [
        {
            "q": "Tell me about yourself.",
            "a": "I am a Senior Network Engineer with 15+ years of progressive experience designing, implementing, and troubleshooting enterprise-grade networking infrastructure. My expertise spans Cisco, MikroTik, Ubiquiti, and Fortinet platforms, with deep knowledge of routing protocols (OSPF, BGP, MPLS), VPN technologies, and firewall management. I have managed high-volume network deployments across the Middle East, maintaining 99.99% uptime for critical infrastructure. I am passionate about automation and have developed scripting skills in Python and PowerShell to optimize network operations.",
        },
        {
            "q": "What is your experience with Cisco routing and switching?",
            "a": "I have extensive experience with Cisco IOS, including Catalyst switches, ISR routers, and ASA firewalls. I have configured and managed OSPF, EIGRP, BGP routing protocols, implemented VLAN segmentation, and designed enterprise-wide QoS policies. I have also worked with Cisco Meraki for cloud-managed networking and have hands-on experience with packet analysis using Wireshark.",
        },
        {
            "q": "How do you approach network security?",
            "a": "My approach follows a defense-in-depth strategy: multiple layers of protection including firewall rules (Fortinet FortiGate, Cisco ASA), VPN configurations (IPSec, SSL), access control lists, and intrusion detection systems. I conduct regular security audits, vulnerability assessments, and ensure compliance with industry standards. I also implement network segmentation to isolate critical systems.",
        },
        {
            "q": "Describe your experience with MikroTik.",
            "a": "I have been working with MikroTik RouterOS for over 10 years. I am certified in MTCNA and MTCRE. I have designed and deployed MikroTik solutions for ISPs, enterprises, and educational institutions. My experience includes configuring routing protocols, implementing hotspot systems, managing bandwidth with queues, setting up VPN tunnels, and managing large-scale wireless networks using CAPsMAN.",
        },
        {
            "q": "How do you handle network outages?",
            "a": "I follow a structured troubleshooting methodology: 1) Identify and isolate the problem scope, 2) Check physical layer connectivity, 3) Verify Layer 2 and Layer 3 connectivity, 4) Use monitoring tools (PRTG, Nagios, Zabbix) to pinpoint the issue, 5) Implement the fix, 6) Test thoroughly, 7) Document the incident and create a post-mortem report. I maintain detailed network documentation to speed up troubleshooting.",
        },
        {
            "q": "What is your experience with cloud networking?",
            "a": "I have experience with AWS VPC design, Azure Virtual Networks, and GCP networking. I have implemented hybrid cloud connectivity using VPN and direct connect solutions. I understand cloud-native load balancing, auto-scaling, and security group configurations. I have also worked with VMware vSphere and Hyper-V for on-premises virtualization.",
        },
        {
            "q": "Do you have experience with network automation?",
            "a": "Yes, I actively implement network automation. I use Python for scripting repetitive tasks, Ansible for configuration management across multiple devices, and Terraform for infrastructure-as-code deployments. I have created automated monitoring dashboards, backup scripts for network configurations, and automated compliance checks.",
        },
        {
            "q": "What certifications do you hold?",
            "a": "I hold CCNA and CCNP certifications, MikroTik MTCNA and MTCRE, Fortinet NSE, and CompTIA Network+. I continuously pursue professional development through hands-on lab work and vendor training.",
        },
        {
            "q": "How do you stay current with technology?",
            "a": "I maintain my knowledge through hands-on lab work with GNS3 and Packet Tracer, vendor documentation and training portals, networking community forums, technology blogs, and professional conferences. I also experiment with new technologies in my home lab environment.",
        },
        {
            "q": "Why are you interested in this position?",
            "a": "I am drawn to this position because it aligns perfectly with my expertise in network engineering and infrastructure management. I believe my 15+ years of experience would allow me to make immediate contributions to your team while continuing to grow professionally.",
        },
        {
            "q": "Describe your biggest achievement.",
            "a": "I successfully designed and implemented a complete network infrastructure for a 5000-user enterprise, including redundant core switches, firewall clusters, VPN concentrators, and wireless coverage across 3 buildings. The project was delivered on time and under budget, with 99.99% uptime from day one.",
        },
        {
            "q": "How do you prioritize multiple tasks?",
            "a": "I use a structured approach: first assessing business impact and urgency, then delegating where appropriate, and maintaining clear communication with stakeholders. I document everything and use ticketing systems to track progress. My automation skills free up time for high-priority tasks.",
        },
        {
            "q": "What is your experience with Fortinet?",
            "a": "I have extensive experience with FortiGate firewalls, from small office deployments to enterprise data center implementations. I have configured security policies, VPN tunnels, web filtering, intrusion prevention, and high-availability clusters. I am Fortinet NSE certified.",
        },
        {
            "q": "How do you handle vendor relationships?",
            "a": "I maintain strong relationships with multiple vendors including Cisco, MikroTik, Fortinet, and Ubiquiti. I leverage these relationships for technical support, product training, and staying informed about new technologies and best practices.",
        },
        {
            "q": "Where do you see yourself in 5 years?",
            "a": "I see myself in a senior technical leadership role, mentoring the next generation of network engineers while driving innovation in network automation and security. I want to help organizations build resilient, secure, and efficient network infrastructure.",
        },
    ]

    @classmethod
    def get_all_questions(cls) -> list[dict[str, str]]:
        """Return a copy of the list of all available questions."""
        try:
            return cls.QUESTIONS.copy()
        except Exception as e:
            logger.error(f"Failed to copy Q&A questions: {e}")
            return []

    @classmethod
    def get_random_questions(cls, count: int = 5) -> list[dict[str, str]]:
        """Safely return a random sample of Q&As."""
        try:
            return random.sample(cls.QUESTIONS, min(count, len(cls.QUESTIONS)))
        except Exception as e:
            logger.error(f"Failed to sample Q&A questions: {e}")
            return cls.QUESTIONS[:count]

    @classmethod
    def generate_custom_mock_interview(cls, job_title: str = "", job_description: str = "", count: int = 5) -> list[dict[str, str]]:
        """Dynamically generate interview questions tailored to a specific job description."""
        base_questions = cls.get_random_questions(count)
        if not job_title and not job_description:
            return base_questions

        tailored = []
        for item in base_questions:
            q = item["q"]
            a = item["a"]
            if job_title:
                q = q.replace("this position", f"the {job_title} role")
            tailored.append({"q": q, "a": a, "category": "General & Technical"})
        
        # Add custom technical question based on JD
        if job_description:
            jd_lower = job_description.lower()
            if "python" in jd_lower:
                tailored.append({
                    "q": f"How do you utilize Python automation for {job_title or 'network and backend engineering'}?",
                    "a": "I build custom scripts to parse logs, automate REST API endpoints, and interface with CI/CD pipelines to eliminate manual operational overhead.",
                    "category": "Role Specific"
                })
            elif "cloud" in jd_lower or "aws" in jd_lower:
                tailored.append({
                    "q": "What is your approach to high-availability multi-cloud architecture?",
                    "a": "I design stateless serverless edge functions with database connection pooling and automated regional failovers to maintain sub-15ms response times.",
                    "category": "Cloud Architecture"
                })
        return tailored[:count]
