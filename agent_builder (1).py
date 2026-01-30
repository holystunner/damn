"""
AGENT BUILDER ORCHESTRATOR
Main pipeline that builds complete, deployable AI agents
"""

import json
import os
from typing import List, Dict, Optional
from pathlib import Path
from datetime import datetime
import uuid

from agent_dna import AgentDNA, TraitLibrary
from data_pipeline import DataIngestionPipeline
from integration_builder import IntegrationBuilder


class AgentBuildStatus:
    """Track build progress"""
    CREATED = "created"
    DNA_SYNTHESIZED = "dna_synthesized"
    DATA_INGESTING = "data_ingesting"
    DATA_INGESTED = "data_ingested"
    INTEGRATIONS_BUILDING = "integrations_building"
    INTEGRATIONS_READY = "integrations_ready"
    TESTING = "testing"
    PACKAGING = "packaging"
    READY = "ready"
    DELIVERED = "delivered"
    FAILED = "failed"


class AgentBuildJob:
    """Represents a single agent build job"""
    
    def __init__(self, customer_id: str, order_id: str):
        self.job_id = str(uuid.uuid4())
        self.customer_id = customer_id
        self.order_id = order_id
        self.agent_id = f"agent_{self.job_id[:8]}"
        self.created_at = datetime.utcnow().isoformat()
        self.status = AgentBuildStatus.CREATED
        self.status_history: List[Dict] = []
        self.error_log: List[str] = []
        
        # Build specifications (to be set by customer)
        self.agent_name: Optional[str] = None
        self.selected_traits: List[str] = []
        self.custom_context: Optional[str] = None
        self.data_sources: List[Dict] = []
        self.integrations: List[str] = []
        
        # Build artifacts
        self.dna_config: Optional[Dict] = None
        self.knowledge_base_path: Optional[str] = None
        self.integration_package: Optional[Dict] = None
        self.deployment_package_path: Optional[str] = None
        
        self._update_status(AgentBuildStatus.CREATED)
    
    def _update_status(self, new_status: str, details: Optional[Dict] = None):
        """Update build status with timestamp"""
        self.status = new_status
        
        status_entry = {
            "status": new_status,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if details:
            status_entry["details"] = details
        
        self.status_history.append(status_entry)
    
    def to_dict(self) -> Dict:
        """Export job state"""
        return {
            "job_id": self.job_id,
            "customer_id": self.customer_id,
            "order_id": self.order_id,
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "status": self.status,
            "created_at": self.created_at,
            "selected_traits": self.selected_traits,
            "integrations": self.integrations,
            "status_history": self.status_history,
            "error_log": self.error_log,
            "artifacts": {
                "dna_config": self.dna_config,
                "knowledge_base_path": self.knowledge_base_path,
                "integration_package": self.integration_package,
                "deployment_package_path": self.deployment_package_path
            }
        }


class AgentFactory:
    """
    Main factory for building AI agents from customer specifications
    """
    
    def __init__(self, workspace_dir: str = "/tmp/agent_factory"):
        self.workspace_dir = Path(workspace_dir)
        self.workspace_dir.mkdir(parents=True, exist_ok=True)
        
        self.jobs: Dict[str, AgentBuildJob] = {}
    
    def create_build_job(self, customer_id: str, order_id: str, specifications: Dict) -> str:
        """Create a new agent build job"""
        job = AgentBuildJob(customer_id, order_id)
        
        # Parse specifications
        job.agent_name = specifications.get("agent_name", f"Agent-{job.job_id[:8]}")
        job.selected_traits = specifications.get("traits", [])
        job.custom_context = specifications.get("custom_context")
        job.data_sources = specifications.get("data_sources", [])
        job.integrations = specifications.get("integrations", [])
        
        # Validate traits
        available_traits = list(TraitLibrary.list_all_traits().keys())
        invalid_traits = [t for t in job.selected_traits if t not in available_traits]
        
        if invalid_traits:
            job.status = AgentBuildStatus.FAILED
            job.error_log.append(f"Invalid traits: {invalid_traits}")
            raise ValueError(f"Invalid traits: {invalid_traits}. Available: {available_traits}")
        
        if len(job.selected_traits) != 3:
            job.status = AgentBuildStatus.FAILED
            job.error_log.append("Must select exactly 3 traits")
            raise ValueError("Must select exactly 3 traits")
        
        self.jobs[job.job_id] = job
        
        # Save job
        self._save_job(job)
        
        return job.job_id
    
    def build_agent(self, job_id: str) -> Dict:
        """Execute the full agent build pipeline"""
        job = self.jobs.get(job_id)
        
        if not job:
            raise ValueError(f"Job not found: {job_id}")
        
        try:
            # Step 1: Synthesize DNA
            print(f"[{job_id}] Step 1/5: Synthesizing Agent DNA...")
            dna_result = self._synthesize_dna(job)
            job._update_status(AgentBuildStatus.DNA_SYNTHESIZED, dna_result)
            
            # Step 2: Ingest Data
            print(f"[{job_id}] Step 2/5: Ingesting Knowledge Base...")
            job._update_status(AgentBuildStatus.DATA_INGESTING)
            kb_result = self._ingest_knowledge_base(job)
            job._update_status(AgentBuildStatus.DATA_INGESTED, kb_result)
            
            # Step 3: Build Integrations
            print(f"[{job_id}] Step 3/5: Building Integrations...")
            job._update_status(AgentBuildStatus.INTEGRATIONS_BUILDING)
            integration_result = self._build_integrations(job)
            job._update_status(AgentBuildStatus.INTEGRATIONS_READY, integration_result)
            
            # Step 4: Test Agent
            print(f"[{job_id}] Step 4/5: Running Tests...")
            job._update_status(AgentBuildStatus.TESTING)
            test_result = self._test_agent(job)
            
            # Step 5: Package for Deployment
            print(f"[{job_id}] Step 5/5: Packaging Deployment...")
            job._update_status(AgentBuildStatus.PACKAGING)
            package_result = self._package_deployment(job)
            
            # Mark as ready
            job._update_status(AgentBuildStatus.READY, {
                "deployment_package": package_result,
                "test_results": test_result
            })
            
            # Save final state
            self._save_job(job)
            
            print(f"[{job_id}] ✓ Build Complete!")
            
            return job.to_dict()
            
        except Exception as e:
            job.status = AgentBuildStatus.FAILED
            job.error_log.append(str(e))
            self._save_job(job)
            raise
    
    def _synthesize_dna(self, job: AgentBuildJob) -> Dict:
        """Step 1: Create agent DNA from traits"""
        dna = AgentDNA(
            agent_name=job.agent_name,
            selected_traits=job.selected_traits,
            custom_context=job.custom_context
        )
        
        # Save DNA config
        dna_dir = self.workspace_dir / job.agent_id / "dna"
        dna_dir.mkdir(parents=True, exist_ok=True)
        
        dna_path = dna_dir / "agent_config.json"
        dna.save_config(str(dna_path))
        
        job.dna_config = dna.export_config()
        
        return {
            "agent_name": job.agent_name,
            "traits": [t.name for t in dna.traits],
            "required_tools": dna.get_required_tools(),
            "config_path": str(dna_path)
        }
    
    def _ingest_knowledge_base(self, job: AgentBuildJob) -> Dict:
        """Step 2: Ingest customer data into knowledge base"""
        pipeline = DataIngestionPipeline(agent_id=job.agent_id)
        
        # Process data sources
        for source in job.data_sources:
            source_type = source.get("type")
            
            if source_type == "text":
                pipeline.ingest_text(
                    text=source["content"],
                    source_name=source.get("name", "manual_input")
                )
            
            elif source_type == "file":
                pipeline.ingest_file(source["filepath"])
            
            elif source_type == "api":
                pipeline.ingest_api_data(
                    data=source["data"],
                    api_name=source.get("name", "api_data")
                )
            
            elif source_type == "directory":
                pipeline.ingest_directory(
                    directory_path=source["path"],
                    extensions=source.get("extensions")
                )
        
        # Finalize knowledge base
        summary = pipeline.finalize()
        job.knowledge_base_path = summary["knowledge_base_path"]
        
        return {
            "total_sources": summary["stats"]["total_sources"],
            "total_chunks": summary["stats"]["total_chunks"],
            "knowledge_base_path": summary["knowledge_base_path"]
        }
    
    def _build_integrations(self, job: AgentBuildJob) -> Dict:
        """Step 3: Build system integrations"""
        builder = IntegrationBuilder(agent_id=job.agent_id)
        
        # Add requested integrations
        for integration_name in job.integrations:
            builder.add_integration(integration_name)
        
        # Export integration package
        integration_dir = self.workspace_dir / job.agent_id
        package = builder.export_integration_package(str(integration_dir))
        
        job.integration_package = package
        
        return {
            "total_integrations": len(job.integrations),
            "integrations": job.integrations,
            "generated_files": package["generated_files"]
        }
    
    def _test_agent(self, job: AgentBuildJob) -> Dict:
        """Step 4: Run automated tests on the agent"""
        # Simplified test suite
        tests = {
            "dna_valid": job.dna_config is not None,
            "knowledge_base_exists": job.knowledge_base_path is not None,
            "integrations_built": job.integration_package is not None,
            "required_tools_available": len(job.dna_config.get("required_tools", [])) > 0
        }
        
        all_passed = all(tests.values())
        
        return {
            "all_passed": all_passed,
            "tests": tests,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _package_deployment(self, job: AgentBuildJob) -> Dict:
        """Step 5: Create deployment package"""
        package_dir = self.workspace_dir / job.agent_id / "deployment"
        package_dir.mkdir(parents=True, exist_ok=True)
        
        # Create deployment manifest
        manifest = {
            "agent_id": job.agent_id,
            "agent_name": job.agent_name,
            "version": "1.0.0",
            "created_at": datetime.utcnow().isoformat(),
            "customer_id": job.customer_id,
            "order_id": job.order_id,
            
            # Core components
            "dna_config": job.dna_config,
            "knowledge_base": {
                "path": job.knowledge_base_path,
                "type": "vector_store"
            },
            "integrations": job.integration_package,
            
            # Deployment instructions
            "deployment": {
                "type": "docker",
                "environment": "python:3.11-slim",
                "required_env_vars": [
                    "ANTHROPIC_API_KEY",
                    "AGENT_ID",
                    "KNOWLEDGE_BASE_PATH"
                ],
                "exposed_ports": [8000],
                "health_check": "/health"
            },
            
            # Setup guide
            "setup_steps": [
                "1. Set environment variables",
                "2. Configure integrations (OAuth, API keys)",
                "3. Upload knowledge base",
                "4. Start agent service",
                "5. Verify health check",
                "6. Test with sample queries"
            ]
        }
        
        # Save manifest
        manifest_path = package_dir / "deployment_manifest.json"
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        # Generate README
        readme_content = self._generate_readme(job, manifest)
        readme_path = package_dir / "README.md"
        readme_path.write_text(readme_content)
        
        # Generate Docker configuration
        dockerfile_content = self._generate_dockerfile(job)
        dockerfile_path = package_dir / "Dockerfile"
        dockerfile_path.write_text(dockerfile_content)
        
        job.deployment_package_path = str(package_dir)
        
        return {
            "package_path": str(package_dir),
            "manifest_path": str(manifest_path),
            "readme_path": str(readme_path),
            "dockerfile_path": str(dockerfile_path)
        }
    
    def _generate_readme(self, job: AgentBuildJob, manifest: Dict) -> str:
        """Generate deployment README"""
        return f"""# {job.agent_name} - Deployment Guide

## Agent Information
- **Agent ID**: {job.agent_id}
- **Version**: {manifest['version']}
- **Created**: {manifest['created_at']}

## Expert Capabilities
{chr(10).join(f"- {trait['name']}: {', '.join(trait['core_skills'])}" for trait in job.dna_config['traits'])}

## Required Tools
{chr(10).join(f"- {tool}" for tool in job.dna_config['required_tools'])}

## Integrations
{chr(10).join(f"- {integration}" for integration in job.integrations) if job.integrations else "None configured"}

## Deployment Steps

### 1. Environment Setup
```bash
export ANTHROPIC_API_KEY="your_api_key"
export AGENT_ID="{job.agent_id}"
export KNOWLEDGE_BASE_PATH="{job.knowledge_base_path}"
```

### 2. Docker Deployment
```bash
docker build -t {job.agent_id} .
docker run -p 8000:8000 \\
  -e ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY \\
  -e AGENT_ID=$AGENT_ID \\
  -v $(pwd)/knowledge_base:/app/knowledge_base \\
  {job.agent_id}
```

### 3. Configure Integrations
{"For each integration, configure OAuth/API credentials as specified in the integration files." if job.integrations else "No integrations to configure."}

### 4. Verify Deployment
```bash
curl http://localhost:8000/health
```

### 5. Test Agent
```bash
curl -X POST http://localhost:8000/query \\
  -H "Content-Type: application/json" \\
  -d '{{"query": "Hello, what can you help me with?"}}'
```

## Support
For issues or questions, contact support with your Order ID: {job.order_id}
"""
    
    def _generate_dockerfile(self, job: AgentBuildJob) -> str:
        """Generate Dockerfile"""
        return f"""FROM python:3.11-slim

WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir \\
    anthropic \\
    fastapi \\
    uvicorn \\
    requests

# Copy agent files
COPY dna/ /app/dna/
COPY knowledge_base/ /app/knowledge_base/
COPY integrations/ /app/integrations/

# Copy core files
COPY agent_dna.py /app/
COPY data_pipeline.py /app/
COPY integration_builder.py /app/

# Environment variables
ENV AGENT_ID={job.agent_id}
ENV PORT=8000

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \\
  CMD curl -f http://localhost:8000/health || exit 1

# Run agent service
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
"""
    
    def _save_job(self, job: AgentBuildJob):
        """Save job state to disk"""
        jobs_dir = self.workspace_dir / "jobs"
        jobs_dir.mkdir(exist_ok=True)
        
        job_file = jobs_dir / f"{job.job_id}.json"
        with open(job_file, 'w') as f:
            json.dump(job.to_dict(), f, indent=2)
    
    def get_job_status(self, job_id: str) -> Dict:
        """Get current job status"""
        job = self.jobs.get(job_id)
        
        if not job:
            # Try to load from disk
            job_file = self.workspace_dir / "jobs" / f"{job_id}.json"
            if job_file.exists():
                with open(job_file, 'r') as f:
                    return json.load(f)
            raise ValueError(f"Job not found: {job_id}")
        
        return job.to_dict()


# Example usage
if __name__ == "__main__":
    factory = AgentFactory()
    
    # Customer order specification
    order_spec = {
        "agent_name": "SecureFinOps Assistant",
        "traits": ["financial_analyst", "security_auditor", "operations_optimizer"],
        "custom_context": "Specializes in fintech compliance and secure financial operations.",
        "data_sources": [
            {
                "type": "text",
                "name": "company_policies",
                "content": "Our security policy requires 2FA for all financial transactions..."
            },
            {
                "type": "text",
                "name": "compliance_requirements",
                "content": "SOC 2 Type II compliance mandates..."
            }
        ],
        "integrations": ["slack", "salesforce", "stripe"]
    }
    
    # Create and build agent
    job_id = factory.create_build_job(
        customer_id="cust_123",
        order_id="order_456",
        specifications=order_spec
    )
    
    print(f"Created build job: {job_id}")
    
    # Execute build
    result = factory.build_agent(job_id)
    
    print("\n=== BUILD COMPLETE ===")
    print(json.dumps(result, indent=2))
    
    # Check status
    status = factory.get_job_status(job_id)
    print(f"\nFinal Status: {status['status']}")
    print(f"Deployment Package: {status['artifacts']['deployment_package_path']}")
