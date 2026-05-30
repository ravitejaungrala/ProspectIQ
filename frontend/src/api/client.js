const API_BASE = '/api';

async function request(endpoint, options = {}) {
  const url = `${API_BASE}${endpoint}`;
  const config = {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  };

  const response = await fetch(url, config);

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Request failed' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

// Dashboard
export const getDashboardStats = () => request('/dashboard/stats');

// Campaigns
export const getCampaigns = () => request('/campaigns');
export const getCampaign = (id) => request(`/campaigns/${id}`);
export const createCampaign = (data) =>
  request('/campaigns', { method: 'POST', body: JSON.stringify(data) });
export const updateCampaign = (id, data) =>
  request(`/campaigns/${id}`, { method: 'PATCH', body: JSON.stringify(data) });
export const deleteCampaign = (id) =>
  request(`/campaigns/${id}`, { method: 'DELETE' });

// Leads
export const getCampaignLeads = (campaignId, status) =>
  request(`/leads/campaign/${campaignId}${status ? `?status=${status}` : ''}`);
export const findLeads = (campaignId, params) =>
  request(`/leads/campaign/${campaignId}/find`, { method: 'POST', body: JSON.stringify(params) });
export const verifyLeads = (campaignId) =>
  request(`/leads/campaign/${campaignId}/verify`, { method: 'POST' });

// Outreach
export const enrollLeads = (campaignId) =>
  request(`/outreach/campaign/${campaignId}/enroll`, { method: 'POST' });
export const getCampaignOutreach = (campaignId) =>
  request(`/outreach/campaign/${campaignId}/steps`);
export const getLeadOutreach = (leadId) =>
  request(`/outreach/lead/${leadId}/steps`);
export const markStepSent = (stepId) =>
  request(`/outreach/step/${stepId}/send`, { method: 'PATCH' });
export const sendCampaignEmails = (campaignId) =>
  request(`/outreach/campaign/${campaignId}/send`, { method: 'POST' });
export const getTemplateTypes = () =>
  request('/outreach/templates/types');
export const getStepPreviewUrl = (stepId) =>
  `/api/outreach/step/${stepId}/preview`;
export const getTemplatePreviewUrl = (type, role, campaignId) => {
  let url = `/api/outreach/templates/preview?template_type=${type}&role_category=${role}`;
  if (campaignId) url += `&campaign_id=${campaignId}`;
  return url;
};

// Replies
export const getAllReplies = () => request('/replies');
export const getCampaignReplies = (campaignId) =>
  request(`/replies/campaign/${campaignId}`);
export const createReply = (data) =>
  request('/replies', { method: 'POST', body: JSON.stringify(data) });
export const markReplyHandled = (replyId) =>
  request(`/replies/${replyId}/handle`, { method: 'PATCH' });

// Analytics
export const getGlobalAnalytics = () => request('/analytics/overview');
export const getCampaignAnalytics = (campaignId) =>
  request(`/analytics/campaign/${campaignId}`);
export const getLeadsActivity = (campaignId) =>
  request(`/analytics/campaign/${campaignId}/leads-activity`);

// Outreach approval
export const approveStep = (stepId) =>
  request(`/outreach/step/${stepId}/approve`, { method: 'PATCH' });
export const approveAllSteps = (campaignId) =>
  request(`/outreach/campaign/${campaignId}/approve-all`, { method: 'PATCH' });

// Agents
export const processReply = (data) =>
  request('/agents/reply/process', { method: 'POST', body: JSON.stringify(data) });
export const classifyReply = (body) =>
  request('/agents/reply/classify', { method: 'POST', body: JSON.stringify({ body }) });
export const getNoReplyLeads = (campaignId, days = 3) =>
  request(`/agents/mail/campaign/${campaignId}/no-reply?days=${days}`);
export const autoAdvanceSequence = (campaignId) =>
  request(`/agents/mail/campaign/${campaignId}/auto-advance`, { method: 'POST' });
export const getMailStatus = (campaignId) =>
  request(`/agents/mail/campaign/${campaignId}/status`);
export const analyzePerformance = (campaignId) =>
  request(`/agents/performance/campaign/${campaignId}`);
export const buildContext = (campaignId) =>
  request(`/agents/context/campaign/${campaignId}/build`, { method: 'POST' });
export const getContext = (campaignId) =>
  request(`/agents/context/campaign/${campaignId}`);
export const askContextQuestion = (campaignId, question) =>
  request(`/agents/context/campaign/${campaignId}/ask`, { method: 'POST', body: JSON.stringify({ question }) });
export const getAgentOverview = (campaignId) =>
  request(`/agents/overview/campaign/${campaignId}`);
export const getAgentLogs = (campaignId) =>
  request(`/agents/logs/campaign/${campaignId}`);
export const getAllAgentLogs = () =>
  request('/agents/logs');

// Chat Assistant
export const sendChatMessage = (messages, context) =>
  request('/chat', { method: 'POST', body: JSON.stringify({ messages, context }) });
