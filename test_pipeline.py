"""
COMPLETE PIPELINE TEST
Tests the entire agent factory from order to delivery
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core'))

import json
from agent_builder import AgentFactory
from delivery_workflow import DeliveryWorkflow


def test_complete_pipeline():
    """Test the full order-to-delivery pipeline"""
    
    print("=" * 80)
    print("🧪 TESTING COMPLETE AGENT FACTORY PIPELINE")
    print("=" * 80)
    
    # Initialize systems
    print("\n[1/6] Initializing systems...")
    workflow = DeliveryWorkflow(workspace_dir="/tmp/test_agent_factory")
    print("✓ Workflow system initialized")
    
    # Create test order
    print("\n[2/6] Creating test order...")
    order_data = {
        "order_id": "TEST-001",
        "customer_id": "TEST-CUST-001",
        "customer_email": "test@example.com",
        "specifications": {
            "agent_name": "TestSecureFinOps Assistant",
            "traits": ["financial_analyst", "security_auditor", "operations_optimizer"],
            "custom_context": "This is a test agent for validating the build pipeline. Specializes in fintech compliance.",
            "data_sources": [
                {
                    "type": "text",
                    "name": "test_company_policies",
                    "content": """
                    Company Security Policies:
                    1. All financial transactions require 2FA
                    2. Data encryption at rest and in transit
                    3. Regular security audits every quarter
                    4. Compliance with SOC 2 Type II
                    5. Annual penetration testing
                    """
                },
                {
                    "type": "text",
                    "name": "test_faq",
                    "content": """
                    Frequently Asked Questions:
                    
                    Q: What is our refund policy?
                    A: We offer a 30-day money-back guarantee on all products.
                    
                    Q: Do you offer enterprise support?
                    A: Yes, 24/7 support is included with enterprise plans.
                    
                    Q: How secure is our platform?
                    A: We maintain SOC 2 Type II compliance and use bank-level encryption.
                    """
                }
            ],
            "integrations": ["slack", "stripe"]
        }
    }
    
    try:
        order_id = workflow.receive_order(order_data)
        print(f"✓ Order created: {order_id}")
        
        # Check initial status
        print("\n[3/6] Validating order...")
        status = workflow.get_order_status(order_id)
        print(f"✓ Order status: {status['status']}")
        assert status['status'] in ['received', 'validated'], "Order should be validated"
        
        # Process order through build pipeline
        print("\n[4/6] Processing order (this may take a moment)...")
        result = workflow.process_order(order_id)
        print(f"✓ Build completed: {result['status']}")
        
        # Verify build artifacts
        print("\n[5/6] Verifying build artifacts...")
        final_status = workflow.get_order_status(order_id)
        
        print(f"  • Build Job ID: {final_status.get('build_job_id')}")
        print(f"  • Delivery URL: {final_status.get('delivery_url')}")
        print(f"  • Status: {final_status['status']}")
        
        assert final_status.get('build_job_id'), "Build job ID should exist"
        assert final_status['status'] in ['ready_for_delivery', 'delivered'], "Order should be ready"
        print("✓ All artifacts verified")
        
        # Display results
        print("\n[6/6] Test Results Summary")
        print("-" * 80)
        print(json.dumps({
            "order_id": order_id,
            "customer_email": order_data['customer_email'],
            "agent_name": order_data['specifications']['agent_name'],
            "selected_traits": order_data['specifications']['traits'],
            "integrations": order_data['specifications']['integrations'],
            "final_status": final_status['status'],
            "build_job_id": final_status.get('build_job_id'),
            "delivery_ready": final_status.get('delivery_url') is not None
        }, indent=2))
        
        print("\n" + "=" * 80)
        print("✅ PIPELINE TEST PASSED")
        print("=" * 80)
        
        return True
        
    except Exception as e:
        print("\n" + "=" * 80)
        print("❌ PIPELINE TEST FAILED")
        print("=" * 80)
        print(f"\nError: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_individual_components():
    """Test individual components separately"""
    
    print("\n" + "=" * 80)
    print("🔧 TESTING INDIVIDUAL COMPONENTS")
    print("=" * 80)
    
    all_passed = True
    
    # Test 1: Agent DNA
    print("\n[TEST 1] Agent DNA System")
    try:
        from agent_dna import AgentDNA, TraitLibrary
        
        # List traits
        traits = TraitLibrary.list_all_traits()
        print(f"  ✓ Available traits: {len(traits)}")
        
        # Create agent DNA
        dna = AgentDNA(
            agent_name="Test Agent",
            selected_traits=["financial_analyst", "security_auditor", "operations_optimizer"],
            custom_context="Test context"
        )
        print(f"  ✓ DNA synthesized for: {dna.agent_name}")
        print(f"  ✓ Required tools: {len(dna.get_required_tools())}")
        
    except Exception as e:
        print(f"  ❌ Failed: {e}")
        all_passed = False
    
    # Test 2: Data Pipeline
    print("\n[TEST 2] Data Ingestion Pipeline")
    try:
        from data_pipeline import DataIngestionPipeline
        
        pipeline = DataIngestionPipeline(agent_id="test_agent")
        
        # Ingest test data
        pipeline.ingest_text(
            text="This is test content for the knowledge base.",
            source_name="test_source"
        )
        
        # Finalize
        summary = pipeline.finalize()
        print(f"  ✓ Knowledge base created with {summary['stats']['total_chunks']} chunks")
        
    except Exception as e:
        print(f"  ❌ Failed: {e}")
        all_passed = False
    
    # Test 3: Integration Builder
    print("\n[TEST 3] Integration Builder")
    try:
        from integration_builder import IntegrationBuilder, IntegrationTemplates
        
        # List integrations
        integrations = IntegrationTemplates.list_available()
        print(f"  ✓ Available integrations: {len(integrations)}")
        
        # Build integration
        builder = IntegrationBuilder(agent_id="test_agent")
        builder.add_integration("slack")
        builder.add_integration("stripe")
        
        print(f"  ✓ Built {len(builder.integrations)} integrations")
        
    except Exception as e:
        print(f"  ❌ Failed: {e}")
        all_passed = False
    
    if all_passed:
        print("\n✅ All component tests passed")
    else:
        print("\n❌ Some component tests failed")
    
    return all_passed


if __name__ == "__main__":
    print("\n🚀 Starting Agent Factory Tests\n")
    
    # Test individual components first
    components_ok = test_individual_components()
    
    if components_ok:
        print("\n" + "=" * 80)
        print("Proceeding to full pipeline test...")
        print("=" * 80)
        
        # Test complete pipeline
        pipeline_ok = test_complete_pipeline()
        
        if pipeline_ok:
            print("\n🎉 ALL TESTS PASSED - System is ready for production!")
            sys.exit(0)
        else:
            print("\n⚠️  Pipeline test failed - review errors above")
            sys.exit(1)
    else:
        print("\n⚠️  Component tests failed - fix components before testing pipeline")
        sys.exit(1)
