"""
AUTOMATED DELIVERY WORKFLOW
Orchestrates the complete order-to-delivery pipeline
"""

import json
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path
from enum import Enum
import asyncio
from dataclasses import dataclass


class OrderStatus(Enum):
    """Order lifecycle statuses"""
    RECEIVED = "received"
    VALIDATED = "validated"
    QUEUED = "queued"
    BUILDING = "building"
    TESTING = "testing"
    PACKAGING = "packaging"
    READY_FOR_DELIVERY = "ready_for_delivery"
    DELIVERED = "delivered"
    FAILED = "failed"


@dataclass
class CustomerOrder:
    """Represents a customer order"""
    order_id: str
    customer_id: str
    customer_email: str
    order_date: str
    specifications: Dict
    status: OrderStatus = OrderStatus.RECEIVED
    build_job_id: Optional[str] = None
    delivery_url: Optional[str] = None
    error_message: Optional[str] = None


class DeliveryWorkflow:
    """
    Automated workflow from order placement to delivery
    """
    
    def __init__(self, workspace_dir: str = "/tmp/delivery_workflow"):
        self.workspace_dir = Path(workspace_dir)
        self.workspace_dir.mkdir(parents=True, exist_ok=True)
        
        self.orders_dir = self.workspace_dir / "orders"
        self.orders_dir.mkdir(exist_ok=True)
        
        self.deliveries_dir = self.workspace_dir / "deliveries"
        self.deliveries_dir.mkdir(exist_ok=True)
        
        self.active_orders: Dict[str, CustomerOrder] = {}
        self.order_queue: List[str] = []
    
    def receive_order(self, order_data: Dict) -> str:
        """Step 1: Receive and validate customer order"""
        order = CustomerOrder(
            order_id=order_data["order_id"],
            customer_id=order_data["customer_id"],
            customer_email=order_data["customer_email"],
            order_date=datetime.utcnow().isoformat(),
            specifications=order_data["specifications"],
            status=OrderStatus.RECEIVED
        )
        
        # Validate order
        validation_result = self._validate_order(order)
        
        if not validation_result["valid"]:
            order.status = OrderStatus.FAILED
            order.error_message = validation_result["error"]
            self._save_order(order)
            raise ValueError(f"Order validation failed: {validation_result['error']}")
        
        order.status = OrderStatus.VALIDATED
        self.active_orders[order.order_id] = order
        self.order_queue.append(order.order_id)
        
        # Save order
        self._save_order(order)
        
        # Send confirmation email (simulated)
        self._send_email(
            to=order.customer_email,
            subject=f"Order {order.order_id} Received",
            body=f"""
Thank you for your order!

Order ID: {order.order_id}
Agent Name: {order.specifications.get('agent_name', 'Custom Agent')}
Selected Traits: {', '.join(order.specifications.get('traits', []))}

Your AI agent is being built and will be ready shortly.
You can track your order status at: https://dashboard.example.com/orders/{order.order_id}

- Your AI Agent Factory Team
            """
        )
        
        return order.order_id
    
    def process_order(self, order_id: str) -> Dict:
        """Step 2: Process the order through the build pipeline"""
        order = self.active_orders.get(order_id)
        
        if not order:
            # Try to load from disk
            order = self._load_order(order_id)
            if order:
                self.active_orders[order_id] = order
            else:
                raise ValueError(f"Order not found: {order_id}")
        
        try:
            # Update status
            order.status = OrderStatus.QUEUED
            self._save_order(order)
            
            # Import here to avoid circular dependency
            from agent_builder import AgentFactory
            
            # Initialize factory
            factory = AgentFactory(workspace_dir=str(self.workspace_dir / "builds"))
            
            # Create build job
            order.status = OrderStatus.BUILDING
            self._save_order(order)
            
            build_job_id = factory.create_build_job(
                customer_id=order.customer_id,
                order_id=order.order_id,
                specifications=order.specifications
            )
            
            order.build_job_id = build_job_id
            
            # Send build started notification
            self._send_email(
                to=order.customer_email,
                subject=f"Your AI Agent is Being Built",
                body=f"""
Your AI agent is now being built!

Build ID: {build_job_id}
Estimated completion: 5-10 minutes

You'll receive another email when your agent is ready.
                """
            )
            
            # Execute build
            build_result = factory.build_agent(build_job_id)
            
            # Update order status
            order.status = OrderStatus.TESTING
            self._save_order(order)
            
            # Package for delivery
            order.status = OrderStatus.PACKAGING
            delivery_package = self._create_delivery_package(order, build_result)
            
            order.status = OrderStatus.READY_FOR_DELIVERY
            order.delivery_url = delivery_package["download_url"]
            self._save_order(order)
            
            # Send ready notification
            self._send_email(
                to=order.customer_email,
                subject=f"Your AI Agent is Ready! 🚀",
                body=f"""
Great news! Your AI agent is ready for deployment.

Agent Name: {order.specifications.get('agent_name')}
Build ID: {build_job_id}

Download your deployment package: {delivery_package['download_url']}

Your package includes:
- Complete agent configuration
- Docker deployment files
- Integration setup guides
- Knowledge base
- Setup documentation

Need help? Check out our deployment guide or contact support.

- Your AI Agent Factory Team
                """
            )
            
            return {
                "order_id": order.order_id,
                "status": order.status.value,
                "build_job_id": build_job_id,
                "delivery_package": delivery_package
            }
            
        except Exception as e:
            order.status = OrderStatus.FAILED
            order.error_message = str(e)
            self._save_order(order)
            
            # Send failure notification
            self._send_email(
                to=order.customer_email,
                subject=f"Issue with Order {order.order_id}",
                body=f"""
We encountered an issue building your AI agent.

Error: {str(e)}

Our team has been notified and will contact you shortly.

- Your AI Agent Factory Team
                """
            )
            
            raise
    
    async def process_queue(self, max_concurrent: int = 3):
        """Process orders from queue with concurrency limit"""
        while self.order_queue:
            # Get next batch
            batch = self.order_queue[:max_concurrent]
            
            # Process batch concurrently
            tasks = [
                asyncio.create_task(self._process_order_async(order_id))
                for order_id in batch
            ]
            
            # Wait for batch completion
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Remove processed orders from queue
            for order_id in batch:
                self.order_queue.remove(order_id)
            
            # Log results
            for order_id, result in zip(batch, results):
                if isinstance(result, Exception):
                    print(f"[{order_id}] Failed: {result}")
                else:
                    print(f"[{order_id}] Completed: {result['status']}")
    
    async def _process_order_async(self, order_id: str) -> Dict:
        """Async wrapper for order processing"""
        return await asyncio.to_thread(self.process_order, order_id)
    
    def _validate_order(self, order: CustomerOrder) -> Dict:
        """Validate order specifications"""
        specs = order.specifications
        
        # Required fields
        required = ["agent_name", "traits"]
        missing = [field for field in required if field not in specs]
        
        if missing:
            return {
                "valid": False,
                "error": f"Missing required fields: {missing}"
            }
        
        # Validate traits
        traits = specs.get("traits", [])
        if len(traits) != 3:
            return {
                "valid": False,
                "error": f"Must select exactly 3 traits (got {len(traits)})"
            }
        
        # Validate integrations
        integrations = specs.get("integrations", [])
        from integration_builder import IntegrationTemplates
        available_integrations = IntegrationTemplates.list_available()
        invalid = [i for i in integrations if i not in available_integrations]
        
        if invalid:
            return {
                "valid": False,
                "error": f"Invalid integrations: {invalid}"
            }
        
        return {"valid": True}
    
    def _create_delivery_package(self, order: CustomerOrder, build_result: Dict) -> Dict:
        """Create customer delivery package"""
        package_id = f"delivery_{order.order_id}"
        package_dir = self.deliveries_dir / package_id
        package_dir.mkdir(exist_ok=True)
        
        # Copy deployment artifacts
        deployment_path = Path(build_result["artifacts"]["deployment_package_path"])
        
        # Create delivery manifest
        delivery_manifest = {
            "order_id": order.order_id,
            "customer_id": order.customer_id,
            "agent_id": build_result["agent_id"],
            "agent_name": build_result["agent_name"],
            "delivered_at": datetime.utcnow().isoformat(),
            "package_contents": {
                "deployment_files": str(deployment_path),
                "knowledge_base": build_result["artifacts"]["knowledge_base_path"],
                "integrations": build_result["artifacts"]["integration_package"]
            },
            "quick_start": {
                "step_1": "Download and extract the package",
                "step_2": "Configure environment variables",
                "step_3": "Run: docker-compose up",
                "step_4": "Access at http://localhost:8000"
            }
        }
        
        # Save manifest
        manifest_path = package_dir / "delivery_manifest.json"
        with open(manifest_path, 'w') as f:
            json.dump(delivery_manifest, f, indent=2)
        
        # Generate download URL (in production, this would be a signed S3 URL or similar)
        download_url = f"https://downloads.example.com/packages/{package_id}.zip"
        
        # Mark as delivered
        order.status = OrderStatus.DELIVERED
        self._save_order(order)
        
        return {
            "package_id": package_id,
            "download_url": download_url,
            "manifest_path": str(manifest_path),
            "expires_at": None  # Could add expiration
        }
    
    def _send_email(self, to: str, subject: str, body: str):
        """Send email notification (simulated)"""
        # In production, integrate with SendGrid, AWS SES, etc.
        email_log_dir = self.workspace_dir / "email_logs"
        email_log_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        email_file = email_log_dir / f"{timestamp}_{to.replace('@', '_at_')}.txt"
        
        email_content = f"""
To: {to}
Subject: {subject}
Date: {datetime.utcnow().isoformat()}

{body}
        """
        
        email_file.write_text(email_content)
        print(f"[EMAIL] Sent to {to}: {subject}")
    
    def _save_order(self, order: CustomerOrder):
        """Save order to disk"""
        order_file = self.orders_dir / f"{order.order_id}.json"
        
        order_data = {
            "order_id": order.order_id,
            "customer_id": order.customer_id,
            "customer_email": order.customer_email,
            "order_date": order.order_date,
            "status": order.status.value,
            "specifications": order.specifications,
            "build_job_id": order.build_job_id,
            "delivery_url": order.delivery_url,
            "error_message": order.error_message
        }
        
        with open(order_file, 'w') as f:
            json.dump(order_data, f, indent=2)
    
    def _load_order(self, order_id: str) -> Optional[CustomerOrder]:
        """Load order from disk"""
        order_file = self.orders_dir / f"{order_id}.json"
        
        if not order_file.exists():
            return None
        
        with open(order_file, 'r') as f:
            data = json.load(f)
        
        return CustomerOrder(
            order_id=data["order_id"],
            customer_id=data["customer_id"],
            customer_email=data["customer_email"],
            order_date=data["order_date"],
            specifications=data["specifications"],
            status=OrderStatus(data["status"]),
            build_job_id=data.get("build_job_id"),
            delivery_url=data.get("delivery_url"),
            error_message=data.get("error_message")
        )
    
    def get_order_status(self, order_id: str) -> Dict:
        """Get current order status"""
        order = self.active_orders.get(order_id)
        
        if not order:
            order = self._load_order(order_id)
        
        if not order:
            raise ValueError(f"Order not found: {order_id}")
        
        return {
            "order_id": order.order_id,
            "status": order.status.value,
            "customer_email": order.customer_email,
            "build_job_id": order.build_job_id,
            "delivery_url": order.delivery_url,
            "error_message": order.error_message
        }


# Example usage
if __name__ == "__main__":
    workflow = DeliveryWorkflow()
    
    # Simulate customer order
    order_data = {
        "order_id": "ORD-001",
        "customer_id": "CUST-123",
        "customer_email": "customer@example.com",
        "specifications": {
            "agent_name": "SecureFinOps Assistant",
            "traits": ["financial_analyst", "security_auditor", "operations_optimizer"],
            "custom_context": "Specializes in fintech compliance.",
            "data_sources": [
                {
                    "type": "text",
                    "name": "policies",
                    "content": "Security policy: All transactions require 2FA..."
                }
            ],
            "integrations": ["slack", "stripe"]
        }
    }
    
    # Process order
    print("=== RECEIVING ORDER ===")
    order_id = workflow.receive_order(order_data)
    print(f"Order received: {order_id}")
    
    print("\n=== PROCESSING ORDER ===")
    result = workflow.process_order(order_id)
    
    print("\n=== ORDER COMPLETE ===")
    print(json.dumps(result, indent=2))
    
    # Check status
    status = workflow.get_order_status(order_id)
    print(f"\nOrder Status: {status['status']}")
    print(f"Download URL: {status['delivery_url']}")
