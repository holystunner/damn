"""
AGENT DNA TEMPLATE SYSTEM
Dynamic expert trait injection and personality synthesis
"""

from typing import List, Dict, Optional
from dataclasses import dataclass
import json

@dataclass
class ExpertTrait:
    """Defines a single expert trait with its capabilities"""
    name: str
    domain: str
    core_skills: List[str]
    system_prompt_fragment: str
    tool_requirements: List[str]
    
    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "domain": self.domain,
            "core_skills": self.core_skills,
            "system_prompt_fragment": self.system_prompt_fragment,
            "tool_requirements": self.tool_requirements
        }


class TraitLibrary:
    """Master catalog of all available expert traits"""
    
    TRAITS = {
        "financial_analyst": ExpertTrait(
            name="Financial Analyst",
            domain="finance",
            core_skills=["financial modeling", "risk assessment", "market analysis", "forecasting"],
            system_prompt_fragment="""You have deep expertise in financial analysis. You can:
- Build financial models and projections
- Analyze market trends and investment opportunities
- Assess risk and return profiles
- Generate actionable insights from financial data""",
            tool_requirements=["calculator", "data_analysis", "chart_generation"]
        ),
        
        "content_strategist": ExpertTrait(
            name="Content Strategist",
            domain="marketing",
            core_skills=["content planning", "SEO optimization", "audience analysis", "brand voice"],
            system_prompt_fragment="""You are a master content strategist. Your capabilities include:
- Developing comprehensive content strategies
- Optimizing content for search engines and engagement
- Analyzing audience behavior and preferences
- Maintaining consistent brand voice across channels""",
            tool_requirements=["web_search", "sentiment_analysis", "text_generation"]
        ),
        
        "code_reviewer": ExpertTrait(
            name="Code Reviewer",
            domain="engineering",
            core_skills=["code quality assessment", "security auditing", "performance optimization", "best practices"],
            system_prompt_fragment="""You are an expert code reviewer with capabilities in:
- Identifying bugs, vulnerabilities, and code smells
- Suggesting performance optimizations
- Ensuring adherence to best practices and design patterns
- Providing actionable feedback for improvement""",
            tool_requirements=["code_execution", "static_analysis", "security_scanner"]
        ),
        
        "data_scientist": ExpertTrait(
            name="Data Scientist",
            domain="analytics",
            core_skills=["statistical analysis", "machine learning", "data visualization", "predictive modeling"],
            system_prompt_fragment="""You are a skilled data scientist capable of:
- Performing advanced statistical analysis
- Building and deploying ML models
- Creating insightful data visualizations
- Extracting patterns and predictions from complex datasets""",
            tool_requirements=["python_execution", "data_analysis", "ml_libraries"]
        ),
        
        "customer_support_specialist": ExpertTrait(
            name="Customer Support Specialist",
            domain="support",
            core_skills=["empathetic communication", "problem resolution", "knowledge management", "escalation handling"],
            system_prompt_fragment="""You are a customer support expert who excels at:
- Providing empathetic, helpful responses
- Resolving customer issues efficiently
- Escalating complex problems appropriately
- Maintaining detailed knowledge bases""",
            tool_requirements=["ticketing_system", "knowledge_base", "sentiment_analysis"]
        ),
        
        "sales_enablement": ExpertTrait(
            name="Sales Enablement Specialist",
            domain="sales",
            core_skills=["lead qualification", "objection handling", "proposal generation", "CRM management"],
            system_prompt_fragment="""You are a sales enablement expert focused on:
- Qualifying and scoring leads effectively
- Handling objections and closing deals
- Generating compelling proposals and presentations
- Managing pipeline and CRM data""",
            tool_requirements=["crm_integration", "document_generation", "email_automation"]
        ),
        
        "security_auditor": ExpertTrait(
            name="Security Auditor",
            domain="security",
            core_skills=["vulnerability assessment", "compliance checking", "threat modeling", "security policy"],
            system_prompt_fragment="""You are a security auditing specialist with expertise in:
- Identifying vulnerabilities and security risks
- Ensuring compliance with security standards
- Developing threat models and mitigation strategies
- Creating and enforcing security policies""",
            tool_requirements=["security_scanner", "compliance_checker", "threat_intelligence"]
        ),
        
        "operations_optimizer": ExpertTrait(
            name="Operations Optimizer",
            domain="operations",
            core_skills=["process improvement", "workflow automation", "resource allocation", "metrics tracking"],
            system_prompt_fragment="""You specialize in operations optimization with skills in:
- Identifying process inefficiencies and bottlenecks
- Designing automated workflows
- Optimizing resource allocation and scheduling
- Tracking and reporting on operational metrics""",
            tool_requirements=["workflow_automation", "analytics", "project_management"]
        ),
        
        "legal_advisor": ExpertTrait(
            name="Legal Advisor",
            domain="legal",
            core_skills=["contract review", "compliance guidance", "risk mitigation", "legal research"],
            system_prompt_fragment="""You are a legal advisor capable of:
- Reviewing and analyzing contracts and agreements
- Providing compliance guidance
- Identifying legal risks and mitigation strategies
- Conducting legal research and precedent analysis""",
            tool_requirements=["document_analysis", "legal_database", "compliance_checker"]
        ),
        
        "product_manager": ExpertTrait(
            name="Product Manager",
            domain="product",
            core_skills=["roadmap planning", "user research", "feature prioritization", "stakeholder management"],
            system_prompt_fragment="""You are an experienced product manager who excels at:
- Developing product roadmaps and strategies
- Conducting user research and gathering feedback
- Prioritizing features based on impact and effort
- Managing stakeholder expectations and communication""",
            tool_requirements=["user_analytics", "project_management", "survey_tools"]
        )
    }
    
    @classmethod
    def get_trait(cls, trait_id: str) -> Optional[ExpertTrait]:
        """Retrieve a trait by its ID"""
        return cls.TRAITS.get(trait_id)
    
    @classmethod
    def list_all_traits(cls) -> Dict[str, ExpertTrait]:
        """Get all available traits"""
        return cls.TRAITS.copy()
    
    @classmethod
    def get_traits_by_domain(cls, domain: str) -> List[ExpertTrait]:
        """Get all traits in a specific domain"""
        return [trait for trait in cls.TRAITS.values() if trait.domain == domain]


class AgentDNA:
    """
    Synthesizes custom agent DNA from selected expert traits
    """
    
    def __init__(self, agent_name: str, selected_traits: List[str], custom_context: Optional[str] = None):
        self.agent_name = agent_name
        self.traits = [TraitLibrary.get_trait(t) for t in selected_traits if TraitLibrary.get_trait(t)]
        self.custom_context = custom_context or ""
        
        if len(self.traits) != len(selected_traits):
            missing = set(selected_traits) - {t.name for t in self.traits if t}
            raise ValueError(f"Invalid traits: {missing}")
    
    def synthesize_system_prompt(self) -> str:
        """Generate the master system prompt from combined traits"""
        
        base = f"""You are {self.agent_name}, a specialized AI agent with the following expert capabilities:

"""
        
        # Add trait fragments
        for i, trait in enumerate(self.traits, 1):
            base += f"\n## Expert Trait {i}: {trait.name}\n"
            base += trait.system_prompt_fragment + "\n"
        
        # Add custom context if provided
        if self.custom_context:
            base += f"\n## Custom Business Context\n{self.custom_context}\n"
        
        base += """
## Core Behavior
- Combine your expert capabilities to provide comprehensive solutions
- Ask clarifying questions when needed
- Provide actionable, specific recommendations
- Maintain security and privacy best practices
- Cite sources and show your reasoning
"""
        
        return base
    
    def get_required_tools(self) -> List[str]:
        """Get deduplicated list of all required tools"""
        tools = set()
        for trait in self.traits:
            tools.update(trait.tool_requirements)
        return sorted(list(tools))
    
    def get_skill_matrix(self) -> Dict[str, List[str]]:
        """Get organized skill matrix by domain"""
        matrix = {}
        for trait in self.traits:
            if trait.domain not in matrix:
                matrix[trait.domain] = []
            matrix[trait.domain].extend(trait.core_skills)
        return matrix
    
    def export_config(self) -> Dict:
        """Export complete agent configuration"""
        return {
            "agent_name": self.agent_name,
            "traits": [t.to_dict() for t in self.traits],
            "system_prompt": self.synthesize_system_prompt(),
            "required_tools": self.get_required_tools(),
            "skill_matrix": self.get_skill_matrix(),
            "custom_context": self.custom_context
        }
    
    def save_config(self, filepath: str):
        """Save configuration to JSON file"""
        with open(filepath, 'w') as f:
            json.dump(self.export_config(), f, indent=2)


# Example usage and testing
if __name__ == "__main__":
    # Create an agent with 3 traits
    agent = AgentDNA(
        agent_name="SecureFinOps Assistant",
        selected_traits=["financial_analyst", "security_auditor", "operations_optimizer"],
        custom_context="Specializes in fintech compliance and secure financial operations for startups."
    )
    
    print("=== AGENT DNA SYNTHESIS ===")
    print(f"\nAgent: {agent.agent_name}")
    print(f"\nTraits: {[t.name for t in agent.traits]}")
    print(f"\nRequired Tools: {agent.get_required_tools()}")
    print(f"\n=== SYSTEM PROMPT ===\n{agent.synthesize_system_prompt()}")
    
    # Save config
    agent.save_config("/tmp/agent_config.json")
    print("\n✓ Configuration saved to /tmp/agent_config.json")
