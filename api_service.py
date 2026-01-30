"""
AGENT FACTORY API SERVICE
REST API for automated agent building and delivery
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr
from typing import List, Dict, Optional
from datetime import datetime
import uuid
import asyncio

from delivery_workflow import DeliveryWorkflow, OrderStatus
from agent_builder import AgentFactory


# Initialize FastAPI app
app = FastAPI(
    title="AI Agent Factory API",
    description="Automated custom AI agent building and delivery",
    version="1.0.0"
)

# Initialize workflow manager
workflow = DeliveryWorkflow(workspace_dir="/tmp/agent_factory")
factory = AgentFactory(workspace_dir="/tmp/agent_factory/builds")


# Pydantic models for API
class TraitSelection(BaseModel):
    """Selected expert traits"""
    traits: List[str]
    
    class Config:
        json_schema_extra = {
            "example": {
                "traits": ["financial_analyst", "security_auditor", "operations_optimizer"]
            }
        }


class DataSource(BaseModel):
    """Data source configuration"""
    type: str  # 'text', 'file', 'api', 'directory'
    name: Optional[str] = None
    content: Optional[str] = None
    filepath: Optional[str] = None
    data: Optional[Dict] = None
    path: Optional[str] = None
    extensions: Optional[List[str]] = None


class OrderSpecification(BaseModel):
    """Complete order specification"""
    agent_name: str
    traits: List[str]
    custom_context: Optional[str] = None
    data_sources: Optional[List[DataSource]] = []
    integrations: Optional[List[str]] = []
    
    class Config:
        json_schema_extra = {
            "example": {
                "agent_name": "SecureFinOps Assistant",
                "traits": ["financial_analyst", "security_auditor", "operations_optimizer"],
                "custom_context": "Specializes in fintech compliance and secure operations.",
                "data_sources": [
                    {
                        "type": "text",
                        "name": "company_policies",
                        "content": "Our security policy requires..."
                    }
                ],
                "integrations": ["slack", "salesforce", "stripe"]
            }
        }


class OrderRequest(BaseModel):
    """New order request"""
    customer_id: str
    customer_email: EmailStr
    specifications: OrderSpecification


class OrderResponse(BaseModel):
    """Order response"""
    order_id: str
    status: str
    message: str
    estimated_completion_minutes: int = 10


class StatusResponse(BaseModel):
    """Order status response"""
    order_id: str
    status: str
    build_job_id: Optional[str]
    delivery_url: Optional[str]
    error_message: Optional[str]


# API Endpoints

@app.get("/")
async def root():
    """API health check"""
    return {
        "service": "AI Agent Factory",
        "status": "operational",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "active_orders": len(workflow.active_orders),
        "queue_length": len(workflow.order_queue),
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/traits")
async def list_available_traits():
    """List all available expert traits"""
    from agent_dna import TraitLibrary
    
    traits = TraitLibrary.list_all_traits()
    
    return {
        "total_traits": len(traits),
        "traits": {
            trait_id: {
                "name": trait.name,
                "domain": trait.domain,
                "core_skills": trait.core_skills
            }
            for trait_id, trait in traits.items()
        }
    }


@app.get("/integrations")
async def list_available_integrations():
    """List all available system integrations"""
    from integration_builder import IntegrationTemplates
    
    integrations = IntegrationTemplates.TEMPLATES
    
    return {
        "total_integrations": len(integrations),
        "integrations": {
            name: {
                "system_name": config["system_name"],
                "integration_type": config["integration_type"],
                "required_scopes": config["required_scopes"]
            }
            for name, config in integrations.items()
        }
    }


@app.post("/orders", response_model=OrderResponse)
async def create_order(order: OrderRequest, background_tasks: BackgroundTasks):
    """
    Create a new agent build order
    
    This endpoint receives customer specifications and initiates the automated build pipeline.
    """
    try:
        # Generate order ID
        order_id = f"ORD-{uuid.uuid4().hex[:8].upper()}"
        
        # Prepare order data
        order_data = {
            "order_id": order_id,
            "customer_id": order.customer_id,
            "customer_email": order.customer_email,
            "specifications": order.specifications.dict()
        }
        
        # Receive order (validates and saves)
        received_order_id = workflow.receive_order(order_data)
        
        # Queue for processing in background
        background_tasks.add_task(workflow.process_order, received_order_id)
        
        return OrderResponse(
            order_id=received_order_id,
            status="received",
            message="Order received and queued for processing",
            estimated_completion_minutes=10
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@app.get("/orders/{order_id}", response_model=StatusResponse)
async def get_order_status(order_id: str):
    """
    Get order status
    
    Track the progress of your agent build.
    """
    try:
        status = workflow.get_order_status(order_id)
        
        return StatusResponse(
            order_id=status["order_id"],
            status=status["status"],
            build_job_id=status.get("build_job_id"),
            delivery_url=status.get("delivery_url"),
            error_message=status.get("error_message")
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@app.post("/orders/{order_id}/reprocess")
async def reprocess_failed_order(order_id: str, background_tasks: BackgroundTasks):
    """
    Reprocess a failed order
    
    Retry building an agent that previously failed.
    """
    try:
        status = workflow.get_order_status(order_id)
        
        if status["status"] != OrderStatus.FAILED.value:
            raise HTTPException(
                status_code=400,
                detail=f"Order is not in failed state (current: {status['status']})"
            )
        
        # Requeue for processing
        background_tasks.add_task(workflow.process_order, order_id)
        
        return {
            "order_id": order_id,
            "message": "Order requeued for processing",
            "previous_error": status.get("error_message")
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@app.post("/webhook/order-placed")
async def webhook_order_placed(request: Request, background_tasks: BackgroundTasks):
    """
    Webhook endpoint for external order systems
    
    Receives orders from payment processors, CRM systems, etc.
    """
    try:
        # Parse webhook payload
        payload = await request.json()
        
        # Extract order information (format depends on webhook source)
        order_data = {
            "order_id": payload.get("order_id") or f"ORD-{uuid.uuid4().hex[:8].upper()}",
            "customer_id": payload["customer_id"],
            "customer_email": payload["customer_email"],
            "specifications": payload["specifications"]
        }
        
        # Receive and process order
        order_id = workflow.receive_order(order_data)
        background_tasks.add_task(workflow.process_order, order_id)
        
        return {
            "status": "received",
            "order_id": order_id,
            "message": "Order received from webhook"
        }
        
    except KeyError as e:
        raise HTTPException(status_code=400, detail=f"Missing required field: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@app.get("/stats")
async def get_statistics():
    """
    Get factory statistics
    
    Overview of all orders and build jobs.
    """
    # Count orders by status
    status_counts = {}
    
    for order in workflow.active_orders.values():
        status = order.status.value
        status_counts[status] = status_counts.get(status, 0) + 1
    
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "total_active_orders": len(workflow.active_orders),
        "queue_length": len(workflow.order_queue),
        "orders_by_status": status_counts
    }


@app.post("/admin/process-queue")
async def process_order_queue(max_concurrent: int = 3):
    """
    Admin endpoint to manually trigger queue processing
    
    Process pending orders with specified concurrency limit.
    """
    if not workflow.order_queue:
        return {
            "message": "Queue is empty",
            "processed": 0
        }
    
    queue_size = len(workflow.order_queue)
    
    # Process queue asynchronously
    await workflow.process_queue(max_concurrent=max_concurrent)
    
    return {
        "message": "Queue processing complete",
        "processed": queue_size,
        "max_concurrent": max_concurrent
    }


# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Custom HTTP exception handler"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "timestamp": datetime.utcnow().isoformat()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Catch-all exception handler"""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc),
            "timestamp": datetime.utcnow().isoformat()
        }
    )


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    print("🚀 AI Agent Factory API Starting...")
    print(f"📦 Workspace: {workflow.workspace_dir}")
    print(f"✅ Service Ready")


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print("🛑 AI Agent Factory API Shutting Down...")


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "api_service:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
