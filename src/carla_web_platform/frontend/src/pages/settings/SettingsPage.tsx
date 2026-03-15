import { CompactPageHeader } from '../../components/common/CompactPageHeader';
import { DetailPanel } from '../../components/common/DetailPanel';
import { JsonBlock } from '../../components/common/JsonBlock';
import { ThemeModeSwitch } from '../../components/layout/ThemeModeSwitch';
import { useTheme } from '../../features/theme/state';

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
  const { preference, resolvedTheme } = useTheme();

  return (
    <div className="page-stack">
      <CompactPageHeader
        stepLabel="Settings"
        title="界面设置"
        description="主题模式支持 light / dark / system，并会持久化到本地。"
        contextSummary={`当前偏好: ${preference} / 生效主题: ${resolvedTheme}`}
      />

      <DetailPanel subtitle="全局主题会作用于 AppShell、步骤条、列表、图表等组件" title="主题模式">
        <ThemeModeSwitch />
      </DetailPanel>

      <DetailPanel subtitle="前后端边界和运行约定" title="平台约定">
        <JsonBlock value={settingsNotes} />
      </DetailPanel>
    </div>
  );
}
