import React, { useState, useEffect } from 'react';
import { api, getSavedUser, setSavedUser, removeToken } from './api';
import Navbar from './components/Navbar';
import LandingPage from './components/LandingPage';
import AuthModal from './components/AuthModal';

// Dashboards
import LeadInvestigatorDashboard from './components/dashboards/LeadInvestigatorDashboard';
import ForensicDashboard from './components/dashboards/ForensicDashboard';
import FinancialDashboard from './components/dashboards/FinancialDashboard';
import JudicialDashboard from './components/dashboards/JudicialDashboard';

// Modules
import EvidenceVault from './components/modules/EvidenceVault';
import CorrelatedTimeline from './components/modules/CorrelatedTimeline';
import ReconstructionStudio from './components/modules/ReconstructionStudio';
import GapsConflictsRadar from './components/modules/GapsConflictsRadar';
import EntityNetwork from './components/modules/EntityNetwork';
import CopilotChat from './components/modules/CopilotChat';
import DossierViewer from './components/modules/DossierViewer';

export default function App() {
  const [user, setUser] = useState(getSavedUser());
  const [authModalOpen, setAuthModalOpen] = useState(false);
  const [activeTab, setActiveTab] = useState('overview');

  // Case Data
  const [cases, setCases] = useState([]);
  const [activeCase, setActiveCase] = useState(null);
  const [evidence, setEvidence] = useState([]);
  const [timelineEvents, setTimelineEvents] = useState([]);
  const [hypotheses, setHypotheses] = useState([]);
  const [gapsConflicts, setGapsConflicts] = useState([]);
  const [entities, setEntities] = useState([]);

  const [loading, setLoading] = useState(false);
  const [reconstructionLoading, setReconstructionLoading] = useState(false);

  // Load cases on mount or when user changes
  useEffect(() => {
    if (user) {
      loadInitialData();
    }
  }, [user]);

  // Load case details when activeCase changes
  useEffect(() => {
    if (activeCase?.id) {
      loadCaseDetails(activeCase.id);
    }
  }, [activeCase?.id]);

  const loadInitialData = async () => {
    setLoading(true);
    try {
      const caseList = await api.cases.list();
      setCases(caseList);
      if (caseList && caseList.length > 0) {
        setActiveCase(caseList[0]);
      }
    } catch (err) {
      console.error("Failed to load cases:", err);
    } finally {
      setLoading(false);
    }
  };

  const loadCaseDetails = async (caseId) => {
    try {
      const [evList, tlData, hypList, gcList, entList] = await Promise.allSettled([
        api.evidence.list(caseId),
        api.timelines.getCorrelated(caseId),
        api.reconstruction.list(caseId),
        api.gapsConflicts.list(caseId),
        api.entities.list(caseId)
      ]);

      if (evList.status === 'fulfilled') setEvidence(evList.value || []);
      if (tlData.status === 'fulfilled') {
        const events = tlData.value?.events || tlData.value || [];
        setTimelineEvents(Array.isArray(events) ? events : []);
      }
      if (hypList.status === 'fulfilled') setHypotheses(hypList.value || []);
      if (gcList.status === 'fulfilled') setGapsConflicts(gcList.value || []);
      if (entList.status === 'fulfilled') setEntities(entList.value || []);
    } catch (err) {
      console.error("Error loading case details:", err);
    }
  };

  const handleAuthSuccess = (userData) => {
    setUser(userData);
  };

  const handleLogout = () => {
    removeToken();
    setUser(null);
    setActiveCase(null);
    setCases([]);
  };

  const handleSelectCase = (caseId) => {
    const found = cases.find(c => c.id === caseId);
    if (found) {
      setActiveCase(found);
    }
  };

  const handleTriggerReconstruction = async () => {
    if (!activeCase?.id) return;
    setReconstructionLoading(true);
    try {
      const result = await api.reconstruction.generate(activeCase.id);
      await loadCaseDetails(activeCase.id);
      setActiveTab('reconstruction');
    } catch (err) {
      alert("Reconstruction failed: " + err.message);
    } finally {
      setReconstructionLoading(false);
    }
  };

  // Render Public Landing Page if not logged in
  if (!user) {
    return (
      <>
        <LandingPage
          onOpenAuth={() => setAuthModalOpen(true)}
        />
        <AuthModal
          isOpen={authModalOpen}
          onClose={() => setAuthModalOpen(false)}
          onAuthSuccess={handleAuthSuccess}
        />
      </>
    );
  }

  // Render Authenticated Platform
  return (
    <div style={{ minHeight: '100vh', backgroundColor: 'var(--bg-app)', display: 'flex', flexDirection: 'column' }}>
      <Navbar
        user={user}
        onLogout={handleLogout}
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        cases={cases}
        activeCase={activeCase}
        onSelectCase={handleSelectCase}
      />

      <main className="container-xl" style={{ flex: 1, padding: '24px 16px' }}>
        {activeTab === 'overview' && (
          <>
            {user.role === 'FORENSIC_SPECIALIST' ? (
              <ForensicDashboard
                caseData={activeCase}
                evidence={evidence}
                onNavigate={setActiveTab}
              />
            ) : user.role === 'FINANCIAL_AUDITOR' ? (
              <FinancialDashboard
                caseData={activeCase}
                evidence={evidence}
                onNavigate={setActiveTab}
              />
            ) : user.role === 'PROSECUTOR_JUDGE' ? (
              <JudicialDashboard
                caseData={activeCase}
                hypotheses={hypotheses}
                evidence={evidence}
                onNavigate={setActiveTab}
              />
            ) : (
              <LeadInvestigatorDashboard
                caseData={activeCase}
                evidence={evidence}
                timelineEvents={timelineEvents}
                hypotheses={hypotheses}
                gapsConflicts={gapsConflicts}
                entities={entities}
                onNavigate={setActiveTab}
                onTriggerReconstruction={handleTriggerReconstruction}
                reconstructionLoading={reconstructionLoading}
              />
            )}
          </>
        )}

        {activeTab === 'evidence' && (
          <EvidenceVault
            caseId={activeCase?.id}
            evidence={evidence}
            onRefresh={() => loadCaseDetails(activeCase?.id)}
          />
        )}

        {activeTab === 'timeline' && (
          <CorrelatedTimeline
            timelineEvents={timelineEvents}
          />
        )}

        {activeTab === 'reconstruction' && (
          <ReconstructionStudio
            reconstructions={hypotheses}
            onTriggerReconstruction={handleTriggerReconstruction}
            reconstructionLoading={reconstructionLoading}
          />
        )}

        {activeTab === 'gaps' && (
          <GapsConflictsRadar
            caseId={activeCase?.id}
            gapsConflicts={gapsConflicts}
            onRefresh={() => loadCaseDetails(activeCase?.id)}
          />
        )}

        {activeTab === 'entities' && (
          <EntityNetwork
            caseId={activeCase?.id}
            entities={entities}
            onRefresh={() => loadCaseDetails(activeCase?.id)}
          />
        )}

        {activeTab === 'copilot' && (
          <CopilotChat
            caseId={activeCase?.id}
          />
        )}

        {activeTab === 'dossier' && (
          <DossierViewer
            caseData={activeCase}
            evidence={evidence}
            timelineEvents={timelineEvents}
            hypotheses={hypotheses}
            gapsConflicts={gapsConflicts}
          />
        )}
      </main>

      <AuthModal
        isOpen={authModalOpen}
        onClose={() => setAuthModalOpen(false)}
        onAuthSuccess={handleAuthSuccess}
      />
    </div>
  );
}
