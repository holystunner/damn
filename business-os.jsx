import React, { useState, useEffect } from 'react';
import { BarChart, Bar, LineChart, Line, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { Activity, Package, Users, TrendingUp, AlertCircle, CheckCircle, Clock, Zap, Send, Bot, Settings, Database, Play, Pause } from 'lucide-react';

// ═══════════════════════════════════════════════════════════════
// 🎨 STYLING & THEME
// ═══════════════════════════════════════════════════════════════

const theme = {
  bg: '#0a0e1a',
  surface: '#151b2e',
  surfaceLight: '#1f2937',
  accent: '#3b82f6',
  accentHover: '#2563eb',
  success: '#10b981',
  warning: '#f59e0b',
  danger: '#ef4444',
  text: '#e5e7eb',
  textMuted: '#9ca3af',
  border: '#374151'
};

// ═══════════════════════════════════════════════════════════════
// 💾 DATA LAYER - Local Storage Persistence
// ═══════════════════════════════════════════════════════════════

const StorageManager = {
  get: (key) => {
    try {
      const item = localStorage.getItem(key);
      return item ? JSON.parse(item) : null;
    } catch (e) {
      console.error('Storage get error:', e);
      return null;
    }
  },
  set: (key, value) => {
    try {
      localStorage.setItem(key, JSON.stringify(value));
    } catch (e) {
      console.error('Storage set error:', e);
    }
  }
};

// ═══════════════════════════════════════════════════════════════
// 🤖 AI AGENT INFRASTRUCTURE
// ═══════════════════════════════════════════════════════════════

const AIAgent = {
  async callClaude(prompt, context = {}) {
    try {
      const response = await fetch("https://api.anthropic.com/v1/messages", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          model: "claude-sonnet-4-20250514",
          max_tokens: 1000,
          messages: [
            {
              role: "user",
              content: `${prompt}\n\nContext: ${JSON.stringify(context)}`
            }
          ]
        })
      });

      const data = await response.json();
      const text = data.content
        .map(item => (item.type === "text" ? item.text : ""))
        .join("\n");
      
      return { success: true, response: text };
    } catch (error) {
      console.error('Claude API error:', error);
      return { success: false, error: error.message };
    }
  },

  async overseer(action, data) {
    const prompts = {
      analyze_order: `Analyze this order and provide fulfillment recommendations:\nOrder: ${JSON.stringify(data)}`,
      score_lead: `Score this sales lead from 0-100 based on the data:\nLead: ${JSON.stringify(data)}`,
      triage_ticket: `Triage this support ticket and assign priority (low/medium/high/critical):\nTicket: ${JSON.stringify(data)}`
    };
    
    return await this.callClaude(prompts[action] || action, data);
  },

  async vanguard(operation, leadData) {
    const actions = {
      score: `Analyze this lead and provide a detailed score breakdown:\n${JSON.stringify(leadData)}`,
      deploy_swarm: `Create an outreach strategy for this lead:\n${JSON.stringify(leadData)}`,
      analyze_pipeline: `Analyze the current sales pipeline and provide strategic recommendations:\n${JSON.stringify(leadData)}`
    };
    
    return await this.callClaude(actions[operation], leadData);
  },

  async logos(task, orderData) {
    const tasks = {
      process_order: `Process this order and create a fulfillment plan:\n${JSON.stringify(orderData)}`,
      optimize_delivery: `Optimize delivery routes for these orders:\n${JSON.stringify(orderData)}`,
      inventory_check: `Check inventory levels and suggest reordering:\n${JSON.stringify(orderData)}`
    };
    
    return await this.callClaude(tasks[task], orderData);
  }
};

// ═══════════════════════════════════════════════════════════════
// 📊 MOCK DATA GENERATORS
// ═══════════════════════════════════════════════════════════════

const generateMockData = () => {
  const statuses = ['processing', 'shipped', 'delivered', 'pending'];
  const priorities = ['low', 'medium', 'high', 'critical'];
  const sources = ['Website', 'LinkedIn', 'Cold Email', 'Referral'];
  
  return {
    orders: Array.from({ length: 12 }, (_, i) => ({
      id: `ORD-${1000 + i}`,
      customer: `Customer ${i + 1}`,
      amount: Math.floor(Math.random() * 5000) + 500,
      status: statuses[Math.floor(Math.random() * statuses.length)],
      date: new Date(Date.now() - Math.random() * 7 * 24 * 60 * 60 * 1000).toISOString(),
      items: Math.floor(Math.random() * 5) + 1
    })),
    
    leads: Array.from({ length: 15 }, (_, i) => ({
      id: `LEAD-${2000 + i}`,
      name: `Lead ${i + 1}`,
      company: `Company ${String.fromCharCode(65 + (i % 26))}`,
      score: Math.floor(Math.random() * 100),
      source: sources[Math.floor(Math.random() * sources.length)],
      stage: ['new', 'contacted', 'qualified', 'proposal'][Math.floor(Math.random() * 4)],
      value: Math.floor(Math.random() * 50000) + 5000,
      assignedAgent: i % 3 === 0 ? 'Swarm-Alpha' : i % 3 === 1 ? 'Swarm-Beta' : null
    })),
    
    tickets: Array.from({ length: 10 }, (_, i) => ({
      id: `TIX-${3000 + i}`,
      subject: ['Login Issue', 'Billing Question', 'Feature Request', 'Bug Report'][Math.floor(Math.random() * 4)],
      priority: priorities[Math.floor(Math.random() * priorities.length)],
      status: ['open', 'in-progress', 'resolved'][Math.floor(Math.random() * 3)],
      customer: `User ${i + 1}`,
      created: new Date(Date.now() - Math.random() * 3 * 24 * 60 * 60 * 1000).toISOString()
    })),
    
    swarms: [
      { id: 'swarm-alpha', name: 'Alpha Hunter', status: 'active', leads: 8, conversionRate: 23 },
      { id: 'swarm-beta', name: 'Beta Closer', status: 'active', leads: 12, conversionRate: 31 },
      { id: 'swarm-gamma', name: 'Gamma Qualifier', status: 'paused', leads: 5, conversionRate: 18 }
    ]
  };
};

// ═══════════════════════════════════════════════════════════════
// 🎯 MAIN COMPONENT
// ═══════════════════════════════════════════════════════════════

export default function BusinessOS() {
  const [activeView, setActiveView] = useState('command');
  const [data, setData] = useState(() => {
    const stored = StorageManager.get('businessOS_data');
    return stored || generateMockData();
  });
  const [agents, setAgents] = useState({
    overseer: { active: true, tasksCompleted: 0 },
    vanguard: { active: true, leadsProcessed: 0 },
    logos: { active: true, ordersProcessed: 0 }
  });
  const [aiResponse, setAiResponse] = useState(null);
  const [processing, setProcessing] = useState(false);

  useEffect(() => {
    StorageManager.set('businessOS_data', data);
  }, [data]);

  // ═══════════════════════════════════════════════════════════════
  // 🔄 AUTOMATION WORKFLOWS
  // ═══════════════════════════════════════════════════════════════

  const runAutomation = async (type, item) => {
    setProcessing(true);
    
    try {
      let result;
      
      switch(type) {
        case 'order':
          result = await AIAgent.logos('process_order', item);
          setAgents(prev => ({
            ...prev,
            logos: { ...prev.logos, ordersProcessed: prev.logos.ordersProcessed + 1 }
          }));
          break;
          
        case 'lead':
          result = await AIAgent.vanguard('score', item);
          setAgents(prev => ({
            ...prev,
            vanguard: { ...prev.vanguard, leadsProcessed: prev.vanguard.leadsProcessed + 1 }
          }));
          break;
          
        case 'ticket':
          result = await AIAgent.overseer('triage_ticket', item);
          setAgents(prev => ({
            ...prev,
            overseer: { ...prev.overseer, tasksCompleted: prev.overseer.tasksCompleted + 1 }
          }));
          break;
      }
      
      setAiResponse(result);
    } catch (error) {
      console.error('Automation error:', error);
    } finally {
      setProcessing(false);
    }
  };

  const deploySwarm = async (leadId) => {
    const lead = data.leads.find(l => l.id === leadId);
    if (!lead) return;
    
    setProcessing(true);
    const result = await AIAgent.vanguard('deploy_swarm', lead);
    
    setData(prev => ({
      ...prev,
      leads: prev.leads.map(l => 
        l.id === leadId 
          ? { ...l, assignedAgent: 'Swarm-' + ['Alpha', 'Beta', 'Gamma'][Math.floor(Math.random() * 3)] }
          : l
      )
    }));
    
    setAiResponse(result);
    setProcessing(false);
  };

  // ═══════════════════════════════════════════════════════════════
  // 📊 ANALYTICS CALCULATIONS
  // ═══════════════════════════════════════════════════════════════

  const analytics = {
    totalRevenue: data.orders.reduce((sum, o) => sum + o.amount, 0),
    activeOrders: data.orders.filter(o => o.status !== 'delivered').length,
    avgLeadScore: Math.round(data.leads.reduce((sum, l) => sum + l.score, 0) / data.leads.length),
    openTickets: data.tickets.filter(t => t.status !== 'resolved').length,
    pipelineValue: data.leads.reduce((sum, l) => sum + l.value, 0),
    conversionRate: 24 // Mock
  };

  // ═══════════════════════════════════════════════════════════════
  // 🎨 UI COMPONENTS
  // ═══════════════════════════════════════════════════════════════

  const StatCard = ({ icon: Icon, label, value, subtext, color = theme.accent }) => (
    <div style={{
      background: theme.surface,
      border: `1px solid ${theme.border}`,
      borderRadius: '12px',
      padding: '20px',
      display: 'flex',
      alignItems: 'center',
      gap: '16px'
    }}>
      <div style={{
        background: `${color}20`,
        borderRadius: '10px',
        padding: '12px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center'
      }}>
        <Icon size={24} color={color} />
      </div>
      <div style={{ flex: 1 }}>
        <div style={{ color: theme.textMuted, fontSize: '13px', marginBottom: '4px' }}>{label}</div>
        <div style={{ color: theme.text, fontSize: '24px', fontWeight: '700' }}>{value}</div>
        {subtext && <div style={{ color: theme.textMuted, fontSize: '12px', marginTop: '4px' }}>{subtext}</div>}
      </div>
    </div>
  );

  const CommandView = () => (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '20px' }}>
      <StatCard 
        icon={Package} 
        label="Total Revenue" 
        value={`$${(analytics.totalRevenue / 1000).toFixed(1)}k`}
        subtext={`${analytics.activeOrders} active orders`}
        color={theme.success}
      />
      <StatCard 
        icon={TrendingUp} 
        label="Pipeline Value" 
        value={`$${(analytics.pipelineValue / 1000).toFixed(0)}k`}
        subtext={`${analytics.avgLeadScore} avg lead score`}
        color={theme.accent}
      />
      <StatCard 
        icon={AlertCircle} 
        label="Support Tickets" 
        value={analytics.openTickets}
        subtext={`${data.tickets.length} total tickets`}
        color={theme.warning}
      />
      <StatCard 
        icon={Bot} 
        label="Active Swarms" 
        value={data.swarms.filter(s => s.status === 'active').length}
        subtext={`${data.swarms.reduce((sum, s) => sum + s.leads, 0)} leads engaged`}
        color={theme.accent}
      />

      <div style={{
        gridColumn: '1 / -1',
        background: theme.surface,
        border: `1px solid ${theme.border}`,
        borderRadius: '12px',
        padding: '24px'
      }}>
        <h3 style={{ color: theme.text, marginBottom: '20px', fontSize: '18px' }}>AI Agent Status</h3>
        <div style={{ display: 'grid', gap: '16px' }}>
          {Object.entries(agents).map(([name, agent]) => (
            <div key={name} style={{
              background: theme.surfaceLight,
              borderRadius: '8px',
              padding: '16px',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <div style={{
                  width: '8px',
                  height: '8px',
                  borderRadius: '50%',
                  background: agent.active ? theme.success : theme.textMuted
                }} />
                <div>
                  <div style={{ color: theme.text, fontWeight: '600', textTransform: 'capitalize' }}>{name}</div>
                  <div style={{ color: theme.textMuted, fontSize: '13px' }}>
                    {name === 'overseer' && `${agent.tasksCompleted} tasks completed`}
                    {name === 'vanguard' && `${agent.leadsProcessed} leads processed`}
                    {name === 'logos' && `${agent.ordersProcessed} orders processed`}
                  </div>
                </div>
              </div>
              <div style={{ color: agent.active ? theme.success : theme.textMuted, fontSize: '13px', fontWeight: '600' }}>
                {agent.active ? 'ACTIVE' : 'PAUSED'}
              </div>
            </div>
          ))}
        </div>
      </div>

      <div style={{
        gridColumn: '1 / -1',
        background: theme.surface,
        border: `1px solid ${theme.border}`,
        borderRadius: '12px',
        padding: '24px'
      }}>
        <h3 style={{ color: theme.text, marginBottom: '20px', fontSize: '18px' }}>Revenue Trend (Last 7 Days)</h3>
        <ResponsiveContainer width="100%" height={250}>
          <LineChart data={[
            { day: 'Mon', revenue: 12500 },
            { day: 'Tue', revenue: 15200 },
            { day: 'Wed', revenue: 13800 },
            { day: 'Thu', revenue: 18900 },
            { day: 'Fri', revenue: 21400 },
            { day: 'Sat', revenue: 19200 },
            { day: 'Sun', revenue: 16800 }
          ]}>
            <CartesianGrid strokeDasharray="3 3" stroke={theme.border} />
            <XAxis dataKey="day" stroke={theme.textMuted} />
            <YAxis stroke={theme.textMuted} />
            <Tooltip 
              contentStyle={{ background: theme.surface, border: `1px solid ${theme.border}`, borderRadius: '8px' }}
              labelStyle={{ color: theme.text }}
            />
            <Line type="monotone" dataKey="revenue" stroke={theme.accent} strokeWidth={3} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );

  const OpsView = () => (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <h2 style={{ color: theme.text, fontSize: '24px', fontWeight: '700' }}>Operations Center</h2>
        <button
          onClick={() => runAutomation('order', data.orders[0])}
          disabled={processing}
          style={{
            background: theme.accent,
            color: 'white',
            border: 'none',
            borderRadius: '8px',
            padding: '10px 20px',
            cursor: processing ? 'not-allowed' : 'pointer',
            opacity: processing ? 0.6 : 1,
            fontWeight: '600'
          }}
        >
          {processing ? 'Processing...' : 'Run AI Analysis'}
        </button>
      </div>

      <div style={{ background: theme.surface, border: `1px solid ${theme.border}`, borderRadius: '12px', overflow: 'hidden' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ background: theme.surfaceLight }}>
              <th style={{ padding: '16px', textAlign: 'left', color: theme.text, fontWeight: '600' }}>Order ID</th>
              <th style={{ padding: '16px', textAlign: 'left', color: theme.text, fontWeight: '600' }}>Customer</th>
              <th style={{ padding: '16px', textAlign: 'left', color: theme.text, fontWeight: '600' }}>Amount</th>
              <th style={{ padding: '16px', textAlign: 'left', color: theme.text, fontWeight: '600' }}>Status</th>
              <th style={{ padding: '16px', textAlign: 'left', color: theme.text, fontWeight: '600' }}>Items</th>
              <th style={{ padding: '16px', textAlign: 'left', color: theme.text, fontWeight: '600' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {data.orders.slice(0, 8).map(order => (
              <tr key={order.id} style={{ borderTop: `1px solid ${theme.border}` }}>
                <td style={{ padding: '16px', color: theme.text }}>{order.id}</td>
                <td style={{ padding: '16px', color: theme.text }}>{order.customer}</td>
                <td style={{ padding: '16px', color: theme.text }}>${order.amount}</td>
                <td style={{ padding: '16px' }}>
                  <span style={{
                    padding: '4px 12px',
                    borderRadius: '12px',
                    fontSize: '12px',
                    fontWeight: '600',
                    background: order.status === 'delivered' ? `${theme.success}20` : `${theme.warning}20`,
                    color: order.status === 'delivered' ? theme.success : theme.warning
                  }}>
                    {order.status}
                  </span>
                </td>
                <td style={{ padding: '16px', color: theme.text }}>{order.items}</td>
                <td style={{ padding: '16px' }}>
                  <button
                    onClick={() => runAutomation('order', order)}
                    style={{
                      background: theme.accent,
                      color: 'white',
                      border: 'none',
                      borderRadius: '6px',
                      padding: '6px 12px',
                      cursor: 'pointer',
                      fontSize: '12px',
                      fontWeight: '600'
                    }}
                  >
                    AI Process
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {aiResponse && (
        <div style={{
          marginTop: '24px',
          background: theme.surface,
          border: `1px solid ${theme.accent}`,
          borderRadius: '12px',
          padding: '20px'
        }}>
          <h3 style={{ color: theme.accent, marginBottom: '12px', fontSize: '16px', fontWeight: '600' }}>
            AI Agent Response
          </h3>
          <div style={{ color: theme.text, whiteSpace: 'pre-wrap', lineHeight: '1.6' }}>
            {aiResponse.success ? aiResponse.response : `Error: ${aiResponse.error}`}
          </div>
        </div>
      )}
    </div>
  );

  const SalesView = () => (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <h2 style={{ color: theme.text, fontSize: '24px', fontWeight: '700' }}>Sales Pipeline</h2>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px', marginBottom: '24px' }}>
        {['new', 'contacted', 'qualified', 'proposal'].map(stage => {
          const stageLeads = data.leads.filter(l => l.stage === stage);
          return (
            <div key={stage} style={{
              background: theme.surface,
              border: `1px solid ${theme.border}`,
              borderRadius: '12px',
              padding: '16px'
            }}>
              <div style={{ color: theme.textMuted, fontSize: '12px', textTransform: 'uppercase', marginBottom: '8px' }}>
                {stage}
              </div>
              <div style={{ color: theme.text, fontSize: '24px', fontWeight: '700' }}>
                {stageLeads.length}
              </div>
              <div style={{ color: theme.textMuted, fontSize: '12px', marginTop: '4px' }}>
                ${(stageLeads.reduce((sum, l) => sum + l.value, 0) / 1000).toFixed(0)}k value
              </div>
            </div>
          );
        })}
      </div>

      <div style={{ background: theme.surface, border: `1px solid ${theme.border}`, borderRadius: '12px', overflow: 'hidden' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ background: theme.surfaceLight }}>
              <th style={{ padding: '16px', textAlign: 'left', color: theme.text, fontWeight: '600' }}>Lead</th>
              <th style={{ padding: '16px', textAlign: 'left', color: theme.text, fontWeight: '600' }}>Company</th>
              <th style={{ padding: '16px', textAlign: 'left', color: theme.text, fontWeight: '600' }}>Score</th>
              <th style={{ padding: '16px', textAlign: 'left', color: theme.text, fontWeight: '600' }}>Value</th>
              <th style={{ padding: '16px', textAlign: 'left', color: theme.text, fontWeight: '600' }}>Agent</th>
              <th style={{ padding: '16px', textAlign: 'left', color: theme.text, fontWeight: '600' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {data.leads.slice(0, 10).map(lead => (
              <tr key={lead.id} style={{ borderTop: `1px solid ${theme.border}` }}>
                <td style={{ padding: '16px', color: theme.text }}>{lead.name}</td>
                <td style={{ padding: '16px', color: theme.text }}>{lead.company}</td>
                <td style={{ padding: '16px' }}>
                  <div style={{
                    width: '60px',
                    height: '6px',
                    background: theme.surfaceLight,
                    borderRadius: '3px',
                    overflow: 'hidden'
                  }}>
                    <div style={{
                      width: `${lead.score}%`,
                      height: '100%',
                      background: lead.score > 70 ? theme.success : lead.score > 40 ? theme.warning : theme.danger
                    }} />
                  </div>
                </td>
                <td style={{ padding: '16px', color: theme.text }}>${(lead.value / 1000).toFixed(0)}k</td>
                <td style={{ padding: '16px' }}>
                  {lead.assignedAgent ? (
                    <span style={{
                      padding: '4px 10px',
                      borderRadius: '12px',
                      fontSize: '11px',
                      fontWeight: '600',
                      background: `${theme.accent}20`,
                      color: theme.accent
                    }}>
                      {lead.assignedAgent}
                    </span>
                  ) : (
                    <span style={{ color: theme.textMuted, fontSize: '12px' }}>Unassigned</span>
                  )}
                </td>
                <td style={{ padding: '16px' }}>
                  <button
                    onClick={() => deploySwarm(lead.id)}
                    disabled={processing || lead.assignedAgent}
                    style={{
                      background: lead.assignedAgent ? theme.surfaceLight : theme.accent,
                      color: lead.assignedAgent ? theme.textMuted : 'white',
                      border: 'none',
                      borderRadius: '6px',
                      padding: '6px 12px',
                      cursor: lead.assignedAgent || processing ? 'not-allowed' : 'pointer',
                      fontSize: '12px',
                      fontWeight: '600'
                    }}
                  >
                    Deploy Swarm
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );

  const SwarmView = () => (
    <div>
      <h2 style={{ color: theme.text, fontSize: '24px', fontWeight: '700', marginBottom: '24px' }}>
        AI Sales Agent Swarms
      </h2>

      <div style={{ display: 'grid', gap: '20px' }}>
        {data.swarms.map(swarm => (
          <div key={swarm.id} style={{
            background: theme.surface,
            border: `1px solid ${theme.border}`,
            borderRadius: '12px',
            padding: '24px'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '20px' }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
                  <h3 style={{ color: theme.text, fontSize: '20px', fontWeight: '700' }}>{swarm.name}</h3>
                  <span style={{
                    padding: '4px 12px',
                    borderRadius: '12px',
                    fontSize: '12px',
                    fontWeight: '600',
                    background: swarm.status === 'active' ? `${theme.success}20` : `${theme.textMuted}20`,
                    color: swarm.status === 'active' ? theme.success : theme.textMuted
                  }}>
                    {swarm.status}
                  </span>
                </div>
                <div style={{ color: theme.textMuted, fontSize: '14px' }}>
                  {swarm.leads} leads engaged • {swarm.conversionRate}% conversion rate
                </div>
              </div>
              <button style={{
                background: swarm.status === 'active' ? theme.warning : theme.success,
                color: 'white',
                border: 'none',
                borderRadius: '8px',
                padding: '8px 16px',
                cursor: 'pointer',
                fontWeight: '600',
                fontSize: '14px'
              }}>
                {swarm.status === 'active' ? <Pause size={16} /> : <Play size={16} />}
              </button>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px' }}>
              <div style={{
                background: theme.surfaceLight,
                borderRadius: '8px',
                padding: '16px'
              }}>
                <div style={{ color: theme.textMuted, fontSize: '12px', marginBottom: '8px' }}>Total Outreach</div>
                <div style={{ color: theme.text, fontSize: '24px', fontWeight: '700' }}>{swarm.leads * 3}</div>
              </div>
              <div style={{
                background: theme.surfaceLight,
                borderRadius: '8px',
                padding: '16px'
              }}>
                <div style={{ color: theme.textMuted, fontSize: '12px', marginBottom: '8px' }}>Responses</div>
                <div style={{ color: theme.text, fontSize: '24px', fontWeight: '700' }}>
                  {Math.floor(swarm.leads * 3 * 0.4)}
                </div>
              </div>
              <div style={{
                background: theme.surfaceLight,
                borderRadius: '8px',
                padding: '16px'
              }}>
                <div style={{ color: theme.textMuted, fontSize: '12px', marginBottom: '8px' }}>Conversions</div>
                <div style={{ color: theme.text, fontSize: '24px', fontWeight: '700' }}>
                  {Math.floor(swarm.leads * swarm.conversionRate / 100)}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div style={{
        marginTop: '24px',
        background: theme.surface,
        border: `1px solid ${theme.border}`,
        borderRadius: '12px',
        padding: '24px'
      }}>
        <h3 style={{ color: theme.text, fontSize: '18px', fontWeight: '700', marginBottom: '16px' }}>
          Deploy New Swarm
        </h3>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr auto', gap: '12px', alignItems: 'end' }}>
          <div>
            <label style={{ color: theme.textMuted, fontSize: '13px', display: 'block', marginBottom: '8px' }}>
              Swarm Name
            </label>
            <input
              type="text"
              placeholder="e.g., Enterprise Hunter"
              style={{
                width: '100%',
                background: theme.surfaceLight,
                border: `1px solid ${theme.border}`,
                borderRadius: '8px',
                padding: '10px 14px',
                color: theme.text,
                fontSize: '14px'
              }}
            />
          </div>
          <div>
            <label style={{ color: theme.textMuted, fontSize: '13px', display: 'block', marginBottom: '8px' }}>
              Target Segment
            </label>
            <select style={{
              width: '100%',
              background: theme.surfaceLight,
              border: `1px solid ${theme.border}`,
              borderRadius: '8px',
              padding: '10px 14px',
              color: theme.text,
              fontSize: '14px'
            }}>
              <option>High-value leads</option>
              <option>Cold prospects</option>
              <option>Warm leads</option>
              <option>Re-engagement</option>
            </select>
          </div>
          <button style={{
            background: theme.accent,
            color: 'white',
            border: 'none',
            borderRadius: '8px',
            padding: '10px 24px',
            cursor: 'pointer',
            fontWeight: '600',
            fontSize: '14px',
            display: 'flex',
            alignItems: 'center',
            gap: '8px'
          }}>
            <Zap size={16} /> Deploy Swarm
          </button>
        </div>
      </div>
    </div>
  );

  // ═══════════════════════════════════════════════════════════════
  // 🎯 RENDER
  // ═══════════════════════════════════════════════════════════════

  return (
    <div style={{
      minHeight: '100vh',
      background: theme.bg,
      color: theme.text,
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'
    }}>
      {/* Header */}
      <header style={{
        background: theme.surface,
        borderBottom: `1px solid ${theme.border}`,
        padding: '20px 32px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <Zap size={28} color={theme.accent} />
          <h1 style={{ fontSize: '24px', fontWeight: '800', margin: 0 }}>
            ULTIMATE BUSINESS OS
          </h1>
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          <div style={{
            background: `${theme.success}20`,
            color: theme.success,
            padding: '6px 12px',
            borderRadius: '20px',
            fontSize: '12px',
            fontWeight: '600',
            display: 'flex',
            alignItems: 'center',
            gap: '6px'
          }}>
            <div style={{
              width: '6px',
              height: '6px',
              borderRadius: '50%',
              background: theme.success
            }} />
            All Systems Active
          </div>
        </div>
      </header>

      {/* Navigation */}
      <nav style={{
        background: theme.surface,
        borderBottom: `1px solid ${theme.border}`,
        padding: '0 32px',
        display: 'flex',
        gap: '8px'
      }}>
        {[
          { id: 'command', label: 'Command Deck', icon: Activity },
          { id: 'ops', label: 'Operations', icon: Package },
          { id: 'sales', label: 'Sales Pipeline', icon: TrendingUp },
          { id: 'swarm', label: 'Agent Swarms', icon: Bot }
        ].map(view => (
          <button
            key={view.id}
            onClick={() => setActiveView(view.id)}
            style={{
              background: activeView === view.id ? theme.surfaceLight : 'transparent',
              color: activeView === view.id ? theme.accent : theme.textMuted,
              border: 'none',
              borderBottom: activeView === view.id ? `2px solid ${theme.accent}` : '2px solid transparent',
              padding: '16px 20px',
              cursor: 'pointer',
              fontWeight: '600',
              fontSize: '14px',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              transition: 'all 0.2s'
            }}
          >
            <view.icon size={18} />
            {view.label}
          </button>
        ))}
      </nav>

      {/* Main Content */}
      <main style={{ padding: '32px' }}>
        {activeView === 'command' && <CommandView />}
        {activeView === 'ops' && <OpsView />}
        {activeView === 'sales' && <SalesView />}
        {activeView === 'swarm' && <SwarmView />}
      </main>
    </div>
  );
}
