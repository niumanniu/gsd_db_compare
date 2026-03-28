import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import apiClient from '../api/client';
import type { Connection, ConnectionCreate } from '../types';

export function useConnections() {
  const queryClient = useQueryClient();

  const { data: connections, isLoading } = useQuery<Connection[]>({
    queryKey: ['connections'],
    queryFn: () => apiClient.get('/api/connections').then(r => r.data),
  });

  const createMutation = useMutation<Connection, Error, ConnectionCreate>({
    mutationFn: (data) => apiClient.post('/api/connections', data).then(r => r.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['connections'] });
    },
  });

  const deleteMutation = useMutation<void, Error, number>({
    mutationFn: (id: number) => apiClient.delete(`/api/connections/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['connections'] });
    },
  });

  const getTablesMutation = useMutation({
    mutationFn: (id: number) => apiClient.get(`/api/connections/${id}/tables`).then(r => r.data),
  });

  return {
    connections: connections || [],
    isLoading,
    createConnection: createMutation.mutateAsync,
    deleteConnection: deleteMutation.mutateAsync,
    getTables: getTablesMutation.mutateAsync,
    isCreating: createMutation.isPending,
    isDeleting: deleteMutation.isPending,
  };
}
