import { useState, useCallback, useEffect } from 'react';
import { QueryClient, QueryClientProvider, useQuery } from '@tanstack/react-query';
import { ConfigProvider, Tabs, message } from 'antd';
import { ConnectionList } from './components/ConnectionList';
import { TableBrowser } from './components/TableBrowser';
import { SchemaDiffViewer } from './components/SchemaDiffViewer';
import { ReportViewer } from './components/ReportViewer';
import { DataDiffViewer } from './components/DataDiffViewer';
import { ScheduledTasksPage } from './components/ScheduledTasksPage';
import { HistoryPage } from './components/HistoryPage';
import { useConnections } from './hooks/useConnections';
import { useComparison } from './hooks/useComparison';
import type { TableInfo } from './types';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

function ComparisonView() {
  const { connections, isLoading: connectionsLoading } = useConnections();
  const { compareSchemas, isComparing, comparisonResult, resetComparison } = useComparison();

  const [sourceConnectionId, setSourceConnectionId] = useState<number | null>(null);
  const [targetConnectionId, setTargetConnectionId] = useState<number | null>(null);
  const [sourceTable, setSourceTable] = useState<string | null>(null);
  const [targetTable, setTargetTable] = useState<string | null>(null);
  const [sourceDbInfo, setSourceDbInfo] = useState({ name: '', type: 'mysql' });
  const [targetDbInfo, setTargetDbInfo] = useState({ name: '', type: 'mysql' });
  const [comparisonMode, setComparisonMode] = useState<'schema' | 'data'>('schema');

  // Fetch source tables when connection changes
  const { data: sourceTables = [], isLoading: loadingSourceTables } = useQuery<TableInfo[]>({
    queryKey: ['connection-tables', sourceConnectionId],
    queryFn: () =>
      sourceConnectionId
        ? fetch(`/api/connections/${sourceConnectionId}/tables`).then(r => r.json())
        : Promise.resolve([]),
    enabled: !!sourceConnectionId,
  });

  // Fetch target tables when connection changes
  const { data: targetTables = [], isLoading: loadingTargetTables } = useQuery<TableInfo[]>({
    queryKey: ['connection-tables', targetConnectionId],
    queryFn: () =>
      targetConnectionId
        ? fetch(`/api/connections/${targetConnectionId}/tables`).then(r => r.json())
        : Promise.resolve([]),
    enabled: !!targetConnectionId,
  });

  // Update database info when connections change
  useEffect(() => {
    if (connections.length > 0) {
      const sourceConn = connections.find(c => c.id === sourceConnectionId);
      if (sourceConn) {
        setSourceDbInfo({ name: sourceConn.name, type: sourceConn.db_type });
      }
      const targetConn = connections.find(c => c.id === targetConnectionId);
      if (targetConn) {
        setTargetDbInfo({ name: targetConn.name, type: targetConn.db_type });
      }
    }
  }, [connections, sourceConnectionId, targetConnectionId]);

  const handleCompare = useCallback(async () => {
    if (!sourceConnectionId || !targetConnectionId || !sourceTable || !targetTable) {
      message.error('Please select both connections and tables');
      return;
    }

    try {
      await compareSchemas({
        source_connection_id: sourceConnectionId,
        source_table: sourceTable,
        target_connection_id: targetConnectionId,
        target_table: targetTable,
      });
      message.success('Comparison complete!');
    } catch (error) {
      console.error('Comparison failed:', error);
      message.error('Failed to compare schemas. Please check your connections.');
    }
  }, [sourceConnectionId, targetConnectionId, sourceTable, targetTable, compareSchemas]);

  const handleReset = useCallback(() => {
    resetComparison();
    setSourceTable(null);
    setTargetTable(null);
    setComparisonMode('schema');
  }, [resetComparison]);

  const isLoadingTables = loadingSourceTables || loadingTargetTables;

  return (
    <div>
      {/* Mode Switcher */}
      <Tabs
        activeKey={comparisonMode}
        onChange={(key) => {
          setComparisonMode(key as 'schema' | 'data');
          if (comparisonResult) resetComparison();
        }}
        items={[
          { key: 'schema', label: 'Schema Comparison' },
          { key: 'data', label: 'Data Comparison' },
        ]}
        size="small"
        style={{ marginBottom: 16 }}
      />

      <TableBrowser
        connections={connections}
        sourceConnectionId={sourceConnectionId}
        targetConnectionId={targetConnectionId}
        onSourceConnectionChange={(id) => {
          setSourceConnectionId(id);
          setSourceTable(null);
          if (comparisonResult) resetComparison();
        }}
        onTargetConnectionChange={(id) => {
          setTargetConnectionId(id);
          setTargetTable(null);
          if (comparisonResult) resetComparison();
        }}
        sourceTables={sourceTables}
        targetTables={targetTables}
        sourceTable={sourceTable}
        targetTable={targetTable}
        onSourceTableChange={setSourceTable}
        onTargetTableChange={setTargetTable}
        onCompare={handleCompare}
        isComparing={isComparing}
        isLoadingTables={isLoadingTables}
      />

      {comparisonResult && comparisonMode === 'schema' && (
        <>
          <div style={{ textAlign: 'center', marginBottom: 16 }}>
            <ConfigProvider theme={{}} >
              <button
                onClick={handleReset}
                style={{
                  padding: '8px 16px',
                  cursor: 'pointer',
                  backgroundColor: '#fff',
                  border: '1px solid #d9d9d9',
                  borderRadius: 4,
                }}
              >
                Compare Different Tables
              </button>
            </ConfigProvider>
          </div>
          <SchemaDiffViewer
            diffResult={comparisonResult}
            sourceDbName={sourceDbInfo.name}
            targetDbName={targetDbInfo.name}
            sourceDbType={sourceDbInfo.type}
            targetDbType={targetDbInfo.type}
          />
          <ReportViewer
            diffResult={comparisonResult}
            sourceDb={sourceDbInfo.name}
            targetDb={targetDbInfo.name}
          />
        </>
      )}

      {comparisonResult && comparisonMode === 'data' && (
        <>
          <div style={{ textAlign: 'center', marginBottom: 16 }}>
            <ConfigProvider theme={{}} >
              <button
                onClick={handleReset}
                style={{
                  padding: '8px 16px',
                  cursor: 'pointer',
                  backgroundColor: '#fff',
                  border: '1px solid #d9d9d9',
                  borderRadius: 4,
                }}
              >
                Compare Different Tables
              </button>
            </ConfigProvider>
          </div>
          <DataDiffViewer
            sourceConnectionId={sourceConnectionId!}
            targetConnectionId={targetConnectionId!}
            sourceTable={sourceTable!}
            targetTable={targetTable!}
          />
        </>
      )}
    </div>
  );
}

function ConnectionsView() {
  const {
    connections,
    isLoading,
    createConnection,
    deleteConnection,
    getTables,
    isCreating,
    isDeleting,
  } = useConnections();

  return (
    <div>
      <ConnectionList
        connections={connections}
        isLoading={isLoading}
        onCreate={async (data) => { await createConnection(data); }}
        onDelete={deleteConnection}
        onGetTables={getTables}
        isCreating={isCreating}
        isDeleting={isDeleting}
      />
    </div>
  );
}

function AppContent() {
  const items = [
    {
      key: 'connections',
      label: 'Connections',
      children: <ConnectionsView />,
    },
    {
      key: 'compare',
      label: 'Schema Comparison',
      children: <ComparisonView />,
    },
    {
      key: 'scheduled-tasks',
      label: 'Scheduled Tasks',
      children: <ScheduledTasksPage />,
    },
    {
      key: 'history',
      label: 'History',
      children: <HistoryPage />,
    },
  ];

  return <Tabs defaultActiveKey="compare" items={items} size="large" />;
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ConfigProvider
        theme={{
          token: {
            colorPrimary: '#1890ff',
          },
        }}
      >
        <div style={{ padding: 24, maxWidth: 1400, margin: '0 auto' }}>
          <h1 style={{ marginBottom: 24 }}>DB Compare - Schema Comparison Tool</h1>
          <AppContent />
        </div>
      </ConfigProvider>
    </QueryClientProvider>
  );
}

export default App;
