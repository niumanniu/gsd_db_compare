import { useState, useCallback, useEffect } from 'react';
import { QueryClient, QueryClientProvider, useQuery } from '@tanstack/react-query';
import { ConfigProvider, Tabs, message, Button } from 'antd';
import { ConnectionList } from './components/ConnectionList';
import { TableBrowser } from './components/TableBrowser';
import { SchemaDiffViewer } from './components/SchemaDiffViewer';
import { ReportViewer } from './components/ReportViewer';
import { DataDiffViewer } from './components/DataDiffViewer';
import { MultiTableDiffViewer, DatabaseDiffViewer } from './components/MultiTableDiffViewer';
import { ScheduledTasksPage } from './components/ScheduledTasksPage';
import { HistoryPage } from './components/HistoryPage';
import { MultiTableDataCompareForm } from './components/MultiTableDataCompareForm';
import { SchemaDataCompareForm } from './components/SchemaDataCompareForm';
import { useConnections } from './hooks/useConnections';
import { useComparison } from './hooks/useComparison';
import type { TableInfo, SchemaInfo } from './types';

type CompareMode = 'single' | 'multi' | 'database';
type DataCompareMode = 'single-table' | 'multi-table' | 'schema-level';

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
  const {
    compareSchemas,
    isComparing,
    comparisonResult,
    resetComparison,
    compareBatch,
    isComparingBatch,
    batchComparisonResult,
    compareDatabase,
    isComparingDatabase,
    databaseComparisonResult,
  } = useComparison();

  const [sourceConnectionId, setSourceConnectionId] = useState<number | null>(null);
  const [targetConnectionId, setTargetConnectionId] = useState<number | null>(null);
  const [sourceTable, setSourceTable] = useState<string | null>(null);
  const [targetTable, setTargetTable] = useState<string | null>(null);
  const [sourceDbInfo, setSourceDbInfo] = useState({ name: '', type: 'mysql' });
  const [targetDbInfo, setTargetDbInfo] = useState({ name: '', type: 'mysql' });
  const [comparisonMode, setComparisonMode] = useState<'schema' | 'data'>('schema');
  const [compareMode, setCompareMode] = useState<CompareMode>('single');

  // Data comparison mode
  const [dataCompareMode, setDataCompareMode] = useState<DataCompareMode>('single-table');

  // Multi-table selection state
  const [sourceTablesSelected, setSourceTablesSelected] = useState<string[]>([]);
  const [targetTablesSelected, setTargetTablesSelected] = useState<string[]>([]);

  // Database compare exclude patterns
  const [excludePatterns, setExcludePatterns] = useState<string[]>([]);

  // Schema selection state for database-level mode
  const [sourceSchema, setSourceSchema] = useState<string | null>(null);
  const [targetSchema, setTargetSchema] = useState<string | null>(null);

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

  // Fetch source schemas when connection changes (for database-level mode)
  const { data: sourceSchemas = [], isLoading: loadingSourceSchemas } = useQuery<SchemaInfo[]>({
    queryKey: ['connection-schemas', sourceConnectionId],
    queryFn: () =>
      sourceConnectionId
        ? fetch(`/api/connections/${sourceConnectionId}/schemas`).then(r => r.json())
        : Promise.resolve([]),
    enabled: !!sourceConnectionId,
  });

  // Fetch target schemas when connection changes (for database-level mode)
  const { data: targetSchemas = [], isLoading: loadingTargetSchemas } = useQuery<SchemaInfo[]>({
    queryKey: ['connection-schemas', targetConnectionId],
    queryFn: () =>
      targetConnectionId
        ? fetch(`/api/connections/${targetConnectionId}/schemas`).then(r => r.json())
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

  // Reset selections when mode changes
  useEffect(() => {
    if (compareMode === 'single') {
      setSourceTablesSelected([]);
      setTargetTablesSelected([]);
      setExcludePatterns([]);
      setSourceSchema(null);
      setTargetSchema(null);
    } else if (compareMode === 'multi') {
      setSourceTable(null);
      setTargetTable(null);
      setExcludePatterns([]);
      setSourceSchema(null);
      setTargetSchema(null);
    } else if (compareMode === 'database') {
      setSourceTable(null);
      setTargetTable(null);
      setSourceTablesSelected([]);
      setTargetTablesSelected([]);
    }
  }, [compareMode]);

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

  const handleCompareBatch = useCallback(async () => {
    if (!sourceConnectionId || !targetConnectionId) {
      message.error('Please select both connections');
      return;
    }

    try {
      await compareBatch({
        source_connection_id: sourceConnectionId,
        target_connection_id: targetConnectionId,
        source_tables: sourceTablesSelected,
        target_tables: targetTablesSelected,
      });
      message.success('Batch comparison complete!');
    } catch (error) {
      console.error('Batch comparison failed:', error);
      message.error('Failed to compare schemas. Please check your connections.');
    }
  }, [sourceConnectionId, targetConnectionId, sourceTablesSelected, targetTablesSelected, compareBatch]);

  const handleCompareDatabase = useCallback(async () => {
    if (!sourceConnectionId || !targetConnectionId) {
      message.error('Please select both connections');
      return;
    }

    try {
      await compareDatabase({
        source_connection_id: sourceConnectionId,
        target_connection_id: targetConnectionId,
        exclude_patterns: excludePatterns,
      });
      message.success('Database comparison complete!');
    } catch (error) {
      console.error('Database comparison failed:', error);
      message.error('Failed to compare databases. Please check your connections.');
    }
  }, [sourceConnectionId, targetConnectionId, excludePatterns, compareDatabase]);

  const handleReset = useCallback(() => {
    resetComparison();
    setSourceTable(null);
    setTargetTable(null);
    setComparisonMode('schema');
  }, [resetComparison]);

  const isLoadingTables = loadingSourceTables || loadingTargetTables;
  const isFetchingSchemas = loadingSourceSchemas || loadingTargetSchemas;

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

      {comparisonMode === 'schema' && (
        <>
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
            // Multi-table and database comparison props
            compareMode={compareMode}
            onCompareModeChange={setCompareMode}
            sourceTablesSelected={sourceTablesSelected}
            targetTablesSelected={targetTablesSelected}
            onSourceTablesSelectedChange={setSourceTablesSelected}
            onTargetTablesSelectedChange={setTargetTablesSelected}
            onCompareBatch={handleCompareBatch}
            isComparingBatch={isComparingBatch}
            excludePatterns={excludePatterns}
            onExcludePatternsChange={setExcludePatterns}
            onCompareDatabase={handleCompareDatabase}
            isComparingDatabase={isComparingDatabase}
            // Schema selection props
            sourceSchema={sourceSchema}
            targetSchema={targetSchema}
            onSourceSchemaChange={setSourceSchema}
            onTargetSchemaChange={setTargetSchema}
            sourceSchemas={sourceSchemas}
            targetSchemas={targetSchemas}
            isFetchingSchemas={isFetchingSchemas}
          />

          {/* Single Table Comparison Result */}
          {comparisonResult && compareMode === 'single' && (
            <>
              <div style={{ textAlign: 'center', marginBottom: 16 }}>
                <Button
                  onClick={handleReset}
                  size="middle"
                  style={{
                    padding: '6px 16px',
                    borderRadius: 6,
                  }}
                >
                  Compare Different Tables
                </Button>
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

          {/* Multi-Table Comparison Result */}
          {batchComparisonResult && compareMode === 'multi' && (
            <MultiTableDiffViewer result={batchComparisonResult} />
          )}

          {/* Database Comparison Result */}
          {databaseComparisonResult && compareMode === 'database' && (
            <DatabaseDiffViewer result={databaseComparisonResult} />
          )}
        </>
      )}

      {comparisonMode === 'data' && (
        <>
          {/* Data Comparison Mode Switcher */}
          <Tabs
            activeKey={dataCompareMode}
            onChange={(key) => {
              setDataCompareMode(key as DataCompareMode);
            }}
            items={[
              { key: 'single-table', label: 'Single Table' },
              { key: 'multi-table', label: 'Multi-Table' },
              { key: 'schema-level', label: 'Schema-Level' },
            ]}
            size="small"
            style={{ marginBottom: 16 }}
          />

          {/* Single Table Data Comparison */}
          {dataCompareMode === 'single-table' && (
            <>
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

              {comparisonResult && (
                <>
                  <div style={{ textAlign: 'center', marginBottom: 16 }}>
                    <Button
                      onClick={handleReset}
                      size="middle"
                      style={{
                        padding: '6px 16px',
                        borderRadius: 6,
                      }}
                    >
                      Compare Different Tables
                    </Button>
                  </div>
                  <DataDiffViewer
                    sourceConnectionId={sourceConnectionId!}
                    targetConnectionId={targetConnectionId!}
                    sourceTable={sourceTable!}
                    targetTable={targetTable!}
                  />
                </>
              )}
            </>
          )}

          {/* Multi-Table Data Comparison */}
          {dataCompareMode === 'multi-table' && (
            <MultiTableDataCompareForm
              connections={connections}
            />
          )}

          {/* Schema-Level Data Comparison */}
          {dataCompareMode === 'schema-level' && (
            <SchemaDataCompareForm
              connections={connections}
            />
          )}
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
    testConnection,
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
        onTestConnection={testConnection}
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

  return (
    <Tabs
      defaultActiveKey="compare"
      items={items}
      size="large"
      style={{
        backgroundColor: '#ffffff',
        padding: 24,
        borderRadius: 8,
        boxShadow: '0 1px 2px 0 rgba(0, 0, 0, 0.03), 0 1px 6px -1px rgba(0, 0, 0, 0.02), 0 2px 4px 0 rgba(0, 0, 0, 0.02)',
      }}
    />
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ConfigProvider
        theme={{
          token: {
            colorPrimary: '#1677ff',
            colorBgLayout: '#f5f7fa',
            colorBgContainer: '#ffffff',
            colorBgElevated: '#ffffff',
            borderRadius: 6,
            fontSize: 14,
            colorText: 'rgba(0, 0, 0, 0.88)',
            colorTextSecondary: 'rgba(0, 0, 0, 0.65)',
            colorTextTertiary: 'rgba(0, 0, 0, 0.45)',
            colorBorder: '#d9d9d9',
            colorFillContent: '#f5f5f5',
            boxShadow: '0 1px 2px 0 rgba(0, 0, 0, 0.03), 0 1px 6px -1px rgba(0, 0, 0, 0.02), 0 2px 4px 0 rgba(0, 0, 0, 0.02)',
            boxShadowSecondary: '0 3px 6px -4px rgba(0, 0, 0, 0.12), 0 6px 16px 0 rgba(0, 0, 0, 0.08), 0 9px 28px 8px rgba(0, 0, 0, 0.05)',
          },
          components: {
            Tabs: {
              colorBgContainer: '#ffffff',
              colorText: 'rgba(0, 0, 0, 0.88)',
              colorTextHeading: 'rgba(0, 0, 0, 0.88)',
            },
            Table: {
              colorBgContainer: '#ffffff',
              colorText: 'rgba(0, 0, 0, 0.88)',
              colorTextSecondary: 'rgba(0, 0, 0, 0.65)',
            },
            Card: {
              colorBgContainer: '#ffffff',
              colorText: 'rgba(0, 0, 0, 0.88)',
            },
          },
        }}
      >
        <div style={{ padding: '24px 32px', maxWidth: 1400, margin: '0 auto' }}>
          <h1 style={{
            marginBottom: 24,
            fontSize: '24px',
            fontWeight: 600,
            color: 'rgba(0, 0, 0, 0.88)',
            letterSpacing: '-0.02em',
          }}>
            DB Compare
          </h1>
          <AppContent />
        </div>
      </ConfigProvider>
    </QueryClientProvider>
  );
}

export default App;
