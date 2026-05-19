import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Campaigns from './pages/Campaigns'
import CampaignDetail from './pages/CampaignDetail'
import Leads from './pages/Leads'
import Outreach from './pages/Outreach'
import Replies from './pages/Replies'
import Analytics from './pages/Analytics'
import Agents from './pages/Agents'

export default function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/campaigns" element={<Campaigns />} />
        <Route path="/campaigns/:id" element={<CampaignDetail />} />
        <Route path="/leads/:campaignId" element={<Leads />} />
        <Route path="/outreach/:campaignId" element={<Outreach />} />
        <Route path="/replies" element={<Replies />} />
        <Route path="/analytics" element={<Analytics />} />
        <Route path="/agents" element={<Agents />} />
      </Routes>
    </Layout>
  )
}
