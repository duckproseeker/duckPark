import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';

import { listBenchmarkDefinitions, listBenchmarkTasks } from '../../api/benchmarks';
import { listProjects } from '../../api/projects';
import { listEvaluationProfiles, listScenarioCatalog } from '../../api/scenarios';
import { EmptyState } from '../../components/common/EmptyState';
import { MetricCard } from '../../components/common/MetricCard';
import { PageHeader } from '../../components/common/PageHeader';
import { Panel } from '../../components/common/Panel';
import { StatusPill } from '../../components/common/StatusPill';

export function BenchmarksPage() {
  const definitionsQuery = useQuery({ queryKey: ['benchmark-definitions'], queryFn: listBenchmarkDefinitions });
  const tasksQuery = useQuery({ queryKey: ['benchmark-tasks'], queryFn: () => listBenchmarkTasks(), refetchInterval: 5000 });
  const projectsQuery = useQuery({ queryKey: ['projects'], queryFn: listProjects });
  const catalogQuery = useQuery({ queryKey: ['scenario-catalog'], queryFn: listScenarioCatalog });
  const profilesQuery = useQuery({ queryKey: ['evaluation-profiles'], queryFn: listEvaluationProfiles });

  const definitions = definitionsQuery.data ?? [];
  const projects = projectsQuery.data ?? [];
  const activeProjectIds = new Set(projects.map((item) => item.project_id));
  const tasks = (tasksQuery.data ?? []).filter((task) => activeProjectIds.has(task.project_id));
  const catalogItems = catalogQuery.data ?? [];
  const profiles = profilesQuery.data ?? [];
  const activeTasks = tasks.filter((task) => task.status === 'RUNNING').length;
  const nativeScenarioCount = catalogItems.filter((item) => item.execution_support === 'native').length;

  return (
    <div className="page-stack">
      <PageHeader
        title="基准任务"
        eyebrow="Benchmarks / Templates"
        chips={['指标协议', '任务模板', '覆盖矩阵']}
        description="基准任务定义的是要跑什么、关注什么指标、最后产出什么报告。它不是单个 run，而是面向测评项目的业务级模板。"
        actions={
          <Link className="horizon-button" to="/executions">
            去执行中心排程
          </Link>
        }
      />

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard accent="blue" label="任务定义" value={definitions.length} hint="后端基准定义模型" />
        <MetricCard accent="violet" label="评测协议" value={profiles.length} hint="后端 evaluation profiles" />
        <MetricCard accent="teal" label="可用场景" value={nativeScenarioCount} hint="当前可直接执行的 native 场景" />
        <MetricCard accent="orange" label="运行中任务" value={activeTasks} hint="正在执行中的基准任务" />
      </div>

      <div className="grid gap-5 xl:grid-cols-[minmax(0,1.45fr)_420px]">
        <Panel title="测评模板库" subtitle="模板定义业务意图，执行中心负责把模板展开成多个 run。">
          {definitions.length === 0 ? (
            <EmptyState title="没有基准定义" description="后端还没有返回基准任务定义。" />
          ) : (
            <div className="grid gap-4 xl:grid-cols-2">
              {definitions.map((definition) => {
                const definitionTasks = tasks.filter((task) => task.benchmark_definition_id === definition.benchmark_definition_id);

                return (
                  <div key={definition.benchmark_definition_id} className="rounded-[26px] border border-secondaryGray-200 bg-secondaryGray-50/60 p-5 shadow-card">
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <strong className="block text-xl font-extrabold tracking-[-0.03em] text-navy-900">{definition.name}</strong>
                        <p className="mt-2 text-sm leading-6 text-secondaryGray-600">{definition.description}</p>
                      </div>
                      <StatusPill status={definitionTasks.length > 0 ? 'ACTIVE' : 'READY'} />
                    </div>

                    <div className="mt-5 grid gap-3 sm:grid-cols-2">
                      <div className="rounded-[18px] border border-white/80 bg-white px-4 py-3">
                        <span className="block text-[11px] font-extrabold uppercase tracking-[0.16em] text-secondaryGray-500">节奏</span>
                        <strong className="mt-2 block text-sm text-navy-900">{definition.cadence}</strong>
                      </div>
                      <div className="rounded-[18px] border border-white/80 bg-white px-4 py-3">
                        <span className="block text-[11px] font-extrabold uppercase tracking-[0.16em] text-secondaryGray-500">任务实例</span>
                        <strong className="mt-2 block text-sm text-navy-900">{definitionTasks.length}</strong>
                      </div>
                    </div>

                    <div className="mt-4 flex flex-wrap gap-2">
                      {definition.focus_metrics.map((metric) => (
                        <span key={metric} className="rounded-full bg-white px-3 py-1 text-xs font-semibold text-secondaryGray-600">
                          {metric}
                        </span>
                      ))}
                    </div>

                    <div className="mt-4 flex flex-wrap gap-2">
                      {definition.project_ids.map((projectId) => (
                        <span key={projectId} className="rounded-full bg-brand-50 px-3 py-1 text-xs font-semibold text-brand-600">
                          {projects.find((item) => item.project_id === projectId)?.name ?? projectId}
                        </span>
                      ))}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </Panel>

        <div className="flex flex-col gap-5">
          <Panel title="评测协议" subtitle="这里直接映射后端 evaluation profiles。">
            {profiles.length === 0 ? (
              <EmptyState title="暂无协议" description="后端还没有返回 evaluation profile。" />
            ) : (
              <div className="flex flex-col gap-4">
                {profiles.map((profile) => (
                  <div key={profile.profile_name} className="rounded-[20px] border border-secondaryGray-200 bg-secondaryGray-50/70 px-4 py-4">
                    <strong className="block text-base font-extrabold text-navy-900">{profile.display_name}</strong>
                    <p className="mt-1 text-sm text-secondaryGray-600">{profile.description}</p>
                    <div className="mt-3 flex flex-wrap gap-2">
                      {profile.metrics.map((metric) => (
                        <span key={metric} className="rounded-full bg-white px-3 py-1 text-xs font-semibold text-secondaryGray-600">
                          {metric}
                        </span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </Panel>

          <Panel title="最近任务样例" subtitle="这里只展示任务摘要，不直接暴露一整块原始 JSON。">
            {tasks.length === 0 ? (
              <EmptyState title="暂无基准任务" description="去执行中心创建第一批测评任务后，这里会显示最近任务摘要。" />
            ) : (
              <div className="flex flex-col gap-3">
                {tasks.slice(0, 4).map((task) => (
                  <div key={task.benchmark_task_id} className="rounded-[20px] border border-secondaryGray-200 bg-secondaryGray-50/70 px-4 py-4">
                    <div className="flex items-center justify-between gap-3">
                      <div className="min-w-0">
                        <strong className="block truncate text-sm font-bold text-navy-900">{task.project_name}</strong>
                        <p className="mt-1 truncate text-xs text-secondaryGray-500">
                          {task.benchmark_name} / {task.dut_model ?? '未登记 DUT'}
                        </p>
                      </div>
                      <StatusPill status={task.status} />
                    </div>
                  </div>
                ))}
              </div>
            )}
          </Panel>
        </div>
      </div>
    </div>
  );
}
