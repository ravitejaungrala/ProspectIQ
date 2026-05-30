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

<<<<<<< HEAD
// Chat Assistant
export const sendChatMessage = (messages, context) =>
  request('/chat', { method: 'POST', body: JSON.stringify({ messages, context }) });
=======
// ── Research Agent ──────────────────────────────────────────────
export const researchAllLeads = (campaignId) =>
  request(`/agents/research/campaign/${campaignId}/all`, { method: 'POST' });
export const researchLead = (leadId) =>
  request(`/agents/research/lead/${leadId}`, { method: 'POST' });
export const getLeadHooks = (leadId) =>
  request(`/agents/research/lead/${leadId}/hooks`);
export const researchCompany = (domain) =>
  request('/agents/research/company', { method: 'POST', body: JSON.stringify({ domain }) });

// ── Lead Identification (KP) Agent ─────────────────────────────
export const scoreLeads = (campaignId) =>
  request(`/agents/kp/campaign/${campaignId}/score`, { method: 'POST' });
export const getKeyPersons = (campaignId) =>
  request(`/agents/kp/campaign/${campaignId}/key-persons`);
export const getBestContact = (campaignId, domain) =>
  request(`/agents/kp/campaign/${campaignId}/best-contact?domain=${encodeURIComponent(domain)}`);
export const flagWeakLeads = (campaignId, threshold = 30) =>
  request(`/agents/kp/campaign/${campaignId}/flag-weak?threshold=${threshold}`, { method: 'POST' });

// ── Personalization Agent ───────────────────────────────────────
export const batchPersonalize = (campaignId) =>
  request(`/agents/personalization/campaign/${campaignId}/batch`, { method: 'POST' });
export const personalizeStep = (stepId) =>
  request(`/agents/personalization/step/${stepId}`, { method: 'POST' });
export const previewPersonalization = (leadId, campaignId) =>
  request(`/agents/personalization/lead/${leadId}/preview?campaign_id=${campaignId}`);
export const getOpeningLine = (leadId, campaignId) =>
  request(`/agents/personalization/lead/${leadId}/opening-line?campaign_id=${campaignId}`);

// ── Outreach Agent ──────────────────────────────────────────────
export const getSendQueue = (campaignId) =>
  request(`/agents/outreach/campaign/${campaignId}/queue`);
export const batchApproveAndSend = (campaignId, highPriorityOnly = false) =>
  request(`/agents/outreach/campaign/${campaignId}/batch-send?high_priority_only=${highPriorityOnly}`, { method: 'POST' });
export const runFullPipeline = (campaignId) =>
  request(`/agents/outreach/campaign/${campaignId}/run-pipeline`, { method: 'POST' });
export const getOutreachStats = (campaignId) =>
  request(`/agents/outreach/campaign/${campaignId}/stats`);

// ── Response Handling Agent ─────────────────────────────────────
export const getResponseQueue = (campaignId) =>
  request(`/agents/response/campaign/${campaignId}/queue`);
export const autoRespond = (replyId) =>
  request(`/agents/response/reply/${replyId}/auto-respond`, { method: 'POST' });
export const handleAllUnhandled = (campaignId, autoSendLowRisk = false) =>
  request(`/agents/response/campaign/${campaignId}/handle-all`, {
    method: 'POST',
    body: JSON.stringify({ auto_send_low_risk: autoSendLowRisk }),
  });

// ── Booking Agent ───────────────────────────────────────────────
export const getHotLeads = (campaignId) =>
  request(`/agents/booking/campaign/${campaignId}/hot-leads`);
export const sendBookingLink = (leadId, campaignId, customMessage = '') =>
  request(`/agents/booking/lead/${leadId}/send-link?campaign_id=${campaignId}`, {
    method: 'POST',
    body: JSON.stringify({ custom_message: customMessage }),
  });
export const confirmBooking = (leadId, campaignId, meetingInfo = {}) =>
  request(`/agents/booking/lead/${leadId}/confirm?campaign_id=${campaignId}`, {
    method: 'POST',
    body: JSON.stringify(meetingInfo),
  });
export const followUpUnbooked = (campaignId) =>
  request(`/agents/booking/campaign/${campaignId}/follow-up`, { method: 'POST' });
export const getBookingPipeline = (campaignId) =>
  request(`/agents/booking/campaign/${campaignId}/pipeline`);
>>>>>>> e1b1ab5fd342c1204855fe7b165408539da5ce35
