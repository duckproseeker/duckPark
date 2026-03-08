import { JsonBlock } from '../../components/common/JsonBlock';
import { PageHeader } from '../../components/common/PageHeader';
import { Panel } from '../../components/common/Panel';

const settingsNotes = {
  frontend: {
    stack: ['React 19', 'TypeScript', 'Vite', 'React Router', 'TanStack Query'],
    polling_strategy: 'REST polling first, no WebSocket in phase 1',
    api_base_url: 'Use VITE_API_BASE_URL or Vite proxy'
  },
  backend: {
    runs: ['/runs', '/runs/:run_id', '/runs/:run_id/events'],
    gateways: ['/gateways', '/gateways/:gateway_id'],
    captures: ['/captures', '/captures/:capture_id', '/captures/:capture_id/frames']
  }
};

export function SettingsPage() {
  return (
    <div className="page-stack">
      <PageHeader
        title="Settings"
        description="这里只放开发环境说明，不做用户配置。目标是让远端容器里的人一眼知道前后端边界。"
      />
      <Panel title="前后端约定">
        <JsonBlock value={settingsNotes} />
      </Panel>
    </div>
  );
}
