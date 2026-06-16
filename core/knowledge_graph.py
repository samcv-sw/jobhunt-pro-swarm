"""
JobHunt Pro v13 - Job Market Knowledge Graph
Mathematically maps relationships between Target Companies, Open Jobs, 
and Recruiters to identify backdoor referral opportunities.
"""

import logging
from collections import defaultdict

logger = logging.getLogger(__name__)

class JobKnowledgeGraph:
    """
    In-memory knowledge graph for the current session.
    A true persistence layer would store this in Neo4j or Postgres recursive tables,
    but for $0 footprint we use a lightweight Python memory graph structure.
    """
    def __init__(self):
        self.nodes = {}
        self.edges = defaultdict(list)
        self._check_dependencies()
        
    def _check_dependencies(self):
        try:
            import networkx as nx
            self.G = nx.DiGraph()
            self.has_nx = True
        except ImportError:
            logger.warning("networkx not installed. Falling back to simple dict-based graph.")
            self.G = None
            self.has_nx = False

    def add_node(self, node_id: str, node_type: str, attributes: dict = None):
        """Add a node (Company, Job, Recruiter, Candidate)"""
        if not attributes:
            attributes = {}
            
        attributes["type"] = node_type
        self.nodes[node_id] = attributes
        
        if self.has_nx:
            self.G.add_node(node_id, **attributes)
            
        logger.debug(f"Added Graph Node: {node_type} [{node_id}]")

    def add_edge(self, source_id: str, target_id: str, relationship: str, weight: float = 1.0):
        """
        Add a relationship edge:
        - Recruiter -> "HIRES_FOR" -> Company
        - Job -> "BELONGS_TO" -> Company
        - Candidate -> "APPLIED_TO" -> Job
        """
        self.edges[source_id].append({"target": target_id, "rel": relationship, "weight": weight})
        
        if self.has_nx:
            self.G.add_edge(source_id, target_id, relationship=relationship, weight=weight)
            
        logger.debug(f"Added Graph Edge: [{source_id}] -({relationship})-> [{target_id}]")

    def find_backdoor_routes(self, target_company_id: str) -> list:
        """
        Calculates the shortest paths to reach a Target Company using known Recruiters.
        If we know Recruiter A hires for Company B, and Company B is connected to Company C,
        this reveals potential networking routes.
        """
        if not self.has_nx:
            return []
            
        import networkx as nx
        routes = []
        
        # Find all recruiters
        recruiters = [n for n, attr in self.G.nodes(data=True) if attr.get("type") == "Recruiter"]
        
        for recruiter in recruiters:
            if nx.has_path(self.G, recruiter, target_company_id):
                path = nx.shortest_path(self.G, recruiter, target_company_id)
                # If path length is short, it's a direct or 2nd degree connection
                if len(path) <= 3:
                    routes.append({
                        "recruiter_id": recruiter,
                        "path": path,
                        "degrees_of_separation": len(path) - 1
                    })
                    
        return sorted(routes, key=lambda x: x["degrees_of_separation"])

    def ingest_job_listing(self, job_data: dict):
        """Automatically construct graph components from raw job data."""
        job_id = f"job_{job_data.get('id', 'unknown')}"
        company_id = f"comp_{job_data.get('company', 'unknown').replace(' ', '_').lower()}"
        
        # Add Nodes
        self.add_node(company_id, "Company", {"name": job_data.get('company')})
        self.add_node(job_id, "Job", {"title": job_data.get('title')})
        
        # Add Edge
        self.add_edge(job_id, company_id, "BELONGS_TO")
        
        # If recruiter is known, map them
        recruiter_email = job_data.get("email")
        if recruiter_email:
            recruiter_id = f"rec_{recruiter_email.replace('@', '_')}"
            self.add_node(recruiter_id, "Recruiter", {"email": recruiter_email})
            self.add_edge(recruiter_id, company_id, "HIRES_FOR")
            self.add_edge(recruiter_id, job_id, "MANAGES")

knowledge_engine = JobKnowledgeGraph()
