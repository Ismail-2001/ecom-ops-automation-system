import { useEffect, useRef, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { getWsUrl } from '../api/client';

export interface WebSocketMessage {
  type: string;
  payload: any;
}

export const useWebSocket = (onToast?: (title: string, message: string, type: 'info' | 'success' | 'warning' | 'error') => void) => {
  const queryClient = useQueryClient();
  const [isConnected, setIsConnected] = useState(false);
  const [isPipelineRunning, setIsPipelineRunning] = useState(false);
  const socketRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<any>(null);

  const connect = () => {
    try {
      const wsUrl = getWsUrl();
      console.log(`Connecting to WebSocket: ${wsUrl}`);
      const socket = new WebSocket(wsUrl);
      socketRef.current = socket;

      socket.onopen = () => {
        console.log('WebSocket connection established');
        setIsConnected(true);
        if (reconnectTimeoutRef.current) {
          clearTimeout(reconnectTimeoutRef.current);
        }
      };

      socket.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          console.log('Received WebSocket message:', message);

          switch (message.type) {
            case 'action_updated':
              // Invalidate approval queue cache
              queryClient.invalidateQueries({ queryKey: ['approvals'] });
              queryClient.invalidateQueries({ queryKey: ['approval', message.payload.id] });
              queryClient.invalidateQueries({ queryKey: ['analytics'] });
              
              if (onToast) {
                const actionLabel = message.payload.action_type.replace('_', ' ');
                const status = message.payload.status;
                if (status === 'executed') {
                  onToast(
                    'Action Executed',
                    `The ${actionLabel} request was approved and executed successfully.`,
                    'success'
                  );
                } else if (status === 'rejected') {
                  onToast(
                    'Action Rejected',
                    `The ${actionLabel} request was successfully rejected.`,
                    'info'
                  );
                } else if (status === 'executing') {
                  onToast(
                    'Executing Action',
                    `Applying the ${actionLabel} request to your store...`,
                    'info'
                  );
                } else if (status === 'failed') {
                  onToast(
                    'Execution Failed',
                    `Failed to execute ${actionLabel} request. Check the audit log for details.`,
                    'error'
                  );
                }
              }
              break;

            case 'agent_status':
              queryClient.invalidateQueries({ queryKey: ['agents-status'] });
              queryClient.invalidateQueries({ queryKey: ['settings'] });
              if (onToast && message.payload.settings_updated) {
                onToast('Settings Updated', 'Dynamic safety thresholds have been saved.', 'success');
              }
              break;

            case 'pipeline_started':
              setIsPipelineRunning(true);
              queryClient.invalidateQueries({ queryKey: ['agents-status'] });
              if (onToast) {
                onToast('Pipeline Triggered', 'Multi-agent operations cycle is running...', 'info');
              }
              break;

            case 'pipeline_completed':
              setIsPipelineRunning(false);
              queryClient.invalidateQueries({ queryKey: ['approvals'] });
              queryClient.invalidateQueries({ queryKey: ['agents-status'] });
              queryClient.invalidateQueries({ queryKey: ['analytics'] });
              if (onToast) {
                onToast(
                  'Pipeline Complete',
                  `Pipeline run complete. Generated ${message.payload.action_count} new decisions for review.`,
                  'success'
                );
              }
              break;

            case 'pipeline_failed':
              setIsPipelineRunning(false);
              if (onToast) {
                onToast('Pipeline Failed', `Pipeline execution failed: ${message.payload.error}`, 'error');
              }
              break;

            case 'notification':
              if (onToast) {
                const kind = message.payload.kind || 'notification';
                const titleMap: Record<string, string> = {
                  hitl_request: 'Human Review Needed',
                  pipeline_failed: 'Pipeline Failure',
                  agent_graduated: 'Agent Promoted',
                };
                onToast(
                  titleMap[kind] || kind.replace(/_/g, ' ').replace(/\b\w/g, (c: string) => c.toUpperCase()),
                  message.payload.message || '',
                  kind === 'pipeline_failed' ? 'error' : kind === 'hitl_request' ? 'warning' : 'info',
                );
              }
              break;

            default:
              break;
          }
        } catch (err) {
          console.error('Error parsing WebSocket message:', err);
        }
      };

      socket.onclose = (event) => {
        console.log(`WebSocket connection closed: ${event.reason}. Retrying in 5s.`);
        setIsConnected(false);
        // Retry connection after 5 seconds
        reconnectTimeoutRef.current = setTimeout(() => {
          connect();
        }, 5000);
      };

      socket.onerror = (err) => {
        console.error('WebSocket connection error:', err);
        socket.close();
      };
    } catch (e) {
      console.error('Failed to establish WebSocket:', e);
      setIsConnected(false);
      reconnectTimeoutRef.current = setTimeout(() => {
        connect();
      }, 5000);
    }
  };

  useEffect(() => {
    connect();

    return () => {
      if (socketRef.current) {
        socketRef.current.close();
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, []);

  return { isConnected, isPipelineRunning };
};
