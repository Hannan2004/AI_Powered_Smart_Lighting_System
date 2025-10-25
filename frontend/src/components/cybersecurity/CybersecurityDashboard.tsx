'use client';
import React, { useState, useEffect } from 'react';
import { getCybersecurityAgentStatus, triggerCybersecurityAnalysis, getCybersecurityMetrics } from '@/utils/api';
import Card from '@/components/shared/Card';
import LoadingSpinner from '@/components/shared/LoadingSpinner';

const CybersecurityDashboard: React.FC = () => {
  const [status, setStatus] = useState<any>(null);
  const [metrics, setMetrics] = useState<any>(null);
  const [analysisResult, setAnalysisResult] = useState<any>(null);
  const [isLoadingStatus, setIsLoadingStatus] = useState(true);
  const [isLoadingMetrics, setIsLoadingMetrics] = useState(true);
  const [isLoadingAnalysis, setIsLoadingAnalysis] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      setIsLoadingStatus(true);
      setIsLoadingMetrics(true);
      setError(null);
      try {
        const [statusData, metricsData] = await Promise.all([
          getCybersecurityAgentStatus(),
          getCybersecurityMetrics()
        ]);

        if (statusData.error) throw new Error(`Status fetch failed: ${statusData.message}`);
        setStatus(statusData);

        if (metricsData.error) throw new Error(`Metrics fetch failed: ${metricsData.message}`);
        setMetrics(metricsData);

      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch initial data');
        console.error(err);
      } finally {
        setIsLoadingStatus(false);
        setIsLoadingMetrics(false);
      }
    };
    fetchData();
  }, []);

  const handleRunAnalysis = async () => {
    setIsLoadingAnalysis(true);
    setError(null);
    setAnalysisResult(null);
    try {
      const result = await triggerCybersecurityAnalysis();
      if (result.error) throw new Error(`Analysis trigger failed: ${result.message}`);
      setAnalysisResult(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to run analysis');
      console.error(err);
    } finally {
      setIsLoadingAnalysis(false);
    }
  };

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-semibold text-gray-800 dark:text-gray-100">Cybersecurity Agent</h2>

      {error && <Card title="Error" className="bg-red-100 border-red-400 text-red-700 dark:bg-red-900 dark:border-red-700 dark:text-red-200">{error}</Card>}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
         <Card title="Agent Status">
          {isLoadingStatus ? <LoadingSpinner /> : (
            status ? <pre className="text-xs whitespace-pre-wrap">{JSON.stringify(status.agents || status, null, 2)}</pre> : <p>No status data</p>
          )}
        </Card>

        <Card title="Security Metrics">
          {isLoadingMetrics ? <LoadingSpinner /> : (
            metrics ? <pre className="text-xs whitespace-pre-wrap">{JSON.stringify(metrics.current_status || metrics.metrics || metrics, null, 2)}</pre> : <p>No metrics data</p>
          )}
        </Card>

         <Card title="Run Analysis">
          <button
            onClick={handleRunAnalysis}
            disabled={isLoadingAnalysis}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
          >
            {isLoadingAnalysis ? 'Running...' : 'Trigger Full Analysis'}
          </button>
         </Card>
      </div>

       {analysisResult && (
        <Card title={`Analysis Result (${analysisResult?.analysis_id})`}>
          {isLoadingAnalysis ? <LoadingSpinner /> : (
             <pre className="text-xs whitespace-pre-wrap">{JSON.stringify(analysisResult.result || analysisResult, null, 2)}</pre>
           )}
        </Card>
      )}

      {/* Add more specific widgets here later */}
      {/* e.g., <ThreatLevelWidget />, <RecentEventsWidget /> */}
    </div>
  );
};

export default CybersecurityDashboard;