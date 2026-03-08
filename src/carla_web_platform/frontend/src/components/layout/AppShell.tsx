import { NavLink, Outlet, useLocation } from 'react-router-dom';
import {
  HiOutlineBookOpen,
  HiOutlineChartBarSquare,
  HiOutlineDocumentChartBar,
  HiOutlineMagnifyingGlass,
  HiOutlinePlayCircle,
  HiOutlineRadio,
  HiOutlineSquares2X2
} from 'react-icons/hi2';

const navigation = [
  { to: '/projects', label: '项目', caption: '芯片项目与首页总览', icon: HiOutlineSquares2X2 },
  { to: '/benchmarks', label: '基准任务', caption: '评测模板与指标协议', icon: HiOutlineChartBarSquare },
  { to: '/scenario-sets', label: '场景集', caption: '场景、地图、天气、传感器组合', icon: HiOutlineBookOpen },
  { to: '/executions', label: '执行中心', caption: '批量任务展开与执行跟踪', icon: HiOutlinePlayCircle },
  { to: '/reports', label: '报告中心', caption: '运营看板与工程分析', icon: HiOutlineDocumentChartBar },
  { to: '/devices', label: '设备中心', caption: '网关、采集与底层运维', icon: HiOutlineRadio }
];

export function AppShell() {
  const location = useLocation();
  const currentItem = navigation.find((item) => location.pathname === item.to || location.pathname.startsWith(`${item.to}/`));

  return (
    <div className="min-h-screen bg-transparent px-4 py-4 md:px-6 md:py-6">
      <div className="mx-auto grid max-w-[1600px] gap-6 xl:grid-cols-[310px_minmax(0,1fr)]">
        <aside className="horizon-card sticky top-6 hidden h-[calc(100vh-3rem)] flex-col gap-5 overflow-hidden bg-white/90 p-5 backdrop-blur xl:flex">
          <div className="overflow-hidden rounded-[28px] bg-gradient-to-br from-[#16367f] via-brand-600 to-[#39a8ff] p-6 text-white shadow-glow">
            <div className="mb-3 flex items-center justify-between gap-3">
              <span className="rounded-full bg-white/15 px-3 py-1 text-[11px] font-bold uppercase tracking-[0.18em] text-white/90">
                CARLA Benchmark
              </span>
              <span className="rounded-full bg-white/10 px-3 py-1 text-xs font-semibold text-cyan-100">Platform UI</span>
            </div>
            <p className="text-[11px] uppercase tracking-[0.28em] text-white/70">CHIP / SCENARIO / EXECUTION / REPORT</p>
            <h1 className="mt-3 text-4xl font-extrabold tracking-[-0.04em]">DuckPark</h1>
            <p className="mt-3 text-sm leading-6 text-white/80">
              面向算法工程师和测试工程师的芯片测评平台，围绕场景集、批量执行和报告沉淀组织工作流。
            </p>
            <div className="mt-5 grid grid-cols-3 gap-3">
              <div className="rounded-2xl border border-white/10 bg-white/10 px-3 py-3">
                <span className="block text-[11px] uppercase tracking-[0.16em] text-white/60">Project</span>
                <strong className="mt-1 block text-sm">多芯片</strong>
              </div>
              <div className="rounded-2xl border border-white/10 bg-white/10 px-3 py-3">
                <span className="block text-[11px] uppercase tracking-[0.16em] text-white/60">Scene</span>
                <strong className="mt-1 block text-sm">CARLA</strong>
              </div>
              <div className="rounded-2xl border border-white/10 bg-white/10 px-3 py-3">
                <span className="block text-[11px] uppercase tracking-[0.16em] text-white/60">Report</span>
                <strong className="mt-1 block text-sm">可扩展</strong>
              </div>
            </div>
          </div>

          <div>
            <div className="mb-3 px-1 text-[11px] font-extrabold uppercase tracking-[0.22em] text-secondaryGray-500">
              Console
            </div>
            <nav className="flex flex-col gap-2">
              {navigation.map((item) => {
                const Icon = item.icon;
                return (
                  <NavLink
                    key={item.to}
                    to={item.to}
                    className={({ isActive }) =>
                      [
                        'group rounded-[20px] border px-3 py-3 transition',
                        isActive
                          ? 'border-brand-100 bg-brand-50/80 shadow-card'
                          : 'border-transparent bg-white/0 hover:border-secondaryGray-200 hover:bg-secondaryGray-50/70'
                      ].join(' ')
                    }
                  >
                    <div className="grid grid-cols-[44px_minmax(0,1fr)] items-center gap-3">
                      <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-brand-50 text-brand-600 transition group-hover:bg-brand-100">
                        <Icon className="h-5 w-5" />
                      </div>
                      <div className="min-w-0">
                        <span className="block text-[15px] font-bold text-navy-900">{item.label}</span>
                        <small className="block truncate text-xs text-secondaryGray-600">{item.caption}</small>
                      </div>
                    </div>
                  </NavLink>
                );
              })}
            </nav>
          </div>

          <div className="mt-auto rounded-[24px] border border-secondaryGray-200 bg-secondaryGray-50/70 p-4">
            <span className="block text-[11px] font-extrabold uppercase tracking-[0.22em] text-secondaryGray-500">
              Platform
            </span>
            <strong className="mt-2 block text-lg font-bold text-navy-900">FastAPI + React</strong>
            <p className="mt-2 text-sm leading-6 text-secondaryGray-600">
              项目、基准任务和报告已经下沉为后端一等模型，执行中心负责把任务展开成多 run。
            </p>
            <div className="mt-4 grid grid-cols-2 gap-3">
              <div className="rounded-2xl border border-white/80 bg-white p-3">
                <span className="block text-[11px] uppercase tracking-[0.16em] text-secondaryGray-500">Theme</span>
                <strong className="mt-1 block text-sm text-navy-900">运营看板式</strong>
              </div>
              <div className="rounded-2xl border border-white/80 bg-white p-3">
                <span className="block text-[11px] uppercase tracking-[0.16em] text-secondaryGray-500">Mode</span>
                <strong className="mt-1 block text-sm text-navy-900">批量测评</strong>
              </div>
            </div>
          </div>
        </aside>

        <main className="min-w-0">
          <div className="mb-6 flex flex-col gap-4 rounded-[28px] border border-white/80 bg-white/80 px-5 py-4 shadow-card backdrop-blur md:flex-row md:items-center md:justify-between">
            <div>
              <p className="text-sm font-semibold text-secondaryGray-500">Pages / Chip Benchmark Platform</p>
              <h2 className="mt-1 text-2xl font-extrabold tracking-[-0.04em] text-navy-900">
                {currentItem?.label ?? 'Control Surface'}
              </h2>
            </div>
            <div className="flex flex-col gap-3 md:flex-row md:items-center">
              <div className="flex min-w-[280px] items-center gap-3 rounded-full border border-secondaryGray-200 bg-secondaryGray-50/80 px-4 py-3">
                <HiOutlineMagnifyingGlass className="h-5 w-5 text-secondaryGray-500" />
                <span className="text-sm text-secondaryGray-500">搜索项目、芯片、场景、执行 ID...</span>
              </div>
              <div className="flex items-center gap-3">
                <span className="rounded-full bg-brand-50 px-3 py-2 text-xs font-extrabold uppercase tracking-[0.14em] text-brand-600">
                  Live
                </span>
                <div className="flex h-11 w-11 items-center justify-center rounded-full bg-gradient-to-br from-brand-500 to-accent-500 text-sm font-bold text-white shadow-glow">
                  KP
                </div>
              </div>
            </div>
          </div>

          <Outlet />
        </main>
      </div>
    </div>
  );
}
